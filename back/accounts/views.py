# accounts/views.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
import random

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UserProfile, Role
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRoleUpdateSerializer,
)
from .utils import (
    send_verification_email,
    send_password_reset_email,
    send_role_assignment_email,
    EmailRateLimitExceeded,
    create_response,
    debug_request
)
from .middleware import track_successful_login
from .moderators import RoleRequiredPermission, IsAdminUser  # Since permissions are in moderators.py

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    @transaction.atomic
    def post(self, request):
        """Register a new user for the real estate auction platform"""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Registration validation failed: {serializer.errors}")
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.save()

            # Generate verification code using model method
            verification_code = user.generate_verification_code()

            try:
                context = {
                    'user_name': f"{user.first_name} {user.last_name}",
                    'verification_code': verification_code,
                    'expiry_hours': 24
                }
                send_verification_email(user.email, verification_code, context)
                logger.info(f"Verification email sent successfully to {user.email}")
            except EmailRateLimitExceeded as e:
                logger.warning(f"Email rate limit exceeded for {user.email}")
                return create_response(
                    error=str(e),
                    error_code="rate_limit_exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            except Exception as email_error:
                logger.error(f"Failed to send verification email to {user.email}: {email_error}", exc_info=True)
                # Still allow registration but warn user
                return create_response(
                    message="Registration successful but failed to send verification email. Please use resend option.",
                    data={"email": user.email},
                    status_code=status.HTTP_201_CREATED
                )

            return create_response(
                message="Registration successful. Please check your email for verification.",
                data={"email": user.email},
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Registration failed: {str(e)}", exc_info=True)
            return create_response(
                error="Registration failed. Please try again later.",
                error_code="registration_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    def post(self, request):
        """Verify user email with provided verification code"""
        logger.info("Starting email verification process")

        try:
            email = request.data.get('email')
            verification_code = request.data.get('verification_code')

            logger.debug(f"Extracted email: {email}, verification code: {verification_code}")

            if not all([email, verification_code]):
                logger.warning("Missing required fields for verification")
                return create_response(
                    error="Email and verification code are required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)
                logger.debug(f"User found: {user.id}, is_verified: {user.is_verified}")

                if user.is_verified:
                    logger.info(f"User {user.id} is already verified")
                    token, created = Token.objects.get_or_create(user=user)
                    return create_response(
                        message="Email already verified",
                        data={
                            'token': token.key,
                            'user': UserProfileSerializer(user, context={'request': request}).data
                        }
                    )

                # Use model method for verification
                if user.verify_account(verification_code):
                    logger.info(f"Email verification successful for user {user.id}")
                    token, created = Token.objects.get_or_create(user=user)

                    return create_response(
                        message="Email verified successfully",
                        data={
                            'token': token.key,
                            'user': UserProfileSerializer(user, context={'request': request}).data
                        }
                    )
                else:
                    logger.warning(f"Invalid/expired verification code for user {user.id}")
                    return create_response(
                        error="Invalid or expired verification code",
                        error_code="invalid_verification",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            except User.DoesNotExist:
                logger.warning(f"User not found for email {email}")
                return create_response(
                    error="User not found",
                    error_code="user_not_found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred during verification",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Verify the validity of the auth token and return extended user information.
        """
        try:
            user = request.user
            roles = list(user.roles.values_list('name', flat=True))
            primary_role = user.primary_role

            response_data = {
                "valid": True,
                "user": {
                    "email": user.email,
                    "user_id": str(user.uuid),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                    "roles": roles,
                    "primary_role": primary_role,
                    "date_joined": user.date_joined.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                }
            }

            return create_response(data=response_data)

        except Exception as e:
            logger.error(f"Error during token verification: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred during token verification",
                error_code="token_verification_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    def post(self, request):
        """Handle user login and return auth token"""
        email = request.data.get('email', request.data.get('username', '')).lower().strip()
        password = request.data.get('password', '')

        if not email or not password:
            return create_response(
                error="Email and password are required",
                error_code="missing_credentials",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"Login attempt for non-existent email: {email}")
                return create_response(
                    error="Invalid credentials",
                    error_code="invalid_credentials",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(password):
                logger.warning(f"Invalid password attempt for user: {email}")
                return create_response(
                    error="Invalid credentials",
                    error_code="invalid_credentials",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_active:
                return create_response(
                    error="Account is disabled",
                    error_code="account_disabled",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_verified:
                return create_response(
                    error="Email not verified",
                    error_code="email_not_verified",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Track successful login
            track_successful_login(user, request)

            # Generate or get existing token
            token, created = Token.objects.get_or_create(user=user)

            logger.info(f"Successful login for user: {email}")
            return create_response(
                data={
                    'token': token.key,
                    'user': UserProfileSerializer(user, context={'request': request}).data
                }
            )

        except Exception as e:
            logger.error(f"Login failed for {email}: {str(e)}", exc_info=True)
            return create_response(
                error="Login failed. Please try again.",
                error_code="login_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Delete the user's auth token to logout"""
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            logger.info(f"User {request.user.email} logged out successfully")
            return create_response(message="Logged out successfully")
        except Exception as e:
            logger.error(f"Logout failed for user {request.user.email}: {str(e)}", exc_info=True)
            return create_response(
                error="Logout failed",
                error_code="logout_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user profile information"""
        serializer = UserProfileSerializer(
            request.user,
            context={'request': request}
        )
        return create_response(data={"user": serializer.data})

    def put(self, request):
        """Update user profile (complete update)"""
        return self._update_profile(request, partial=False)

    def patch(self, request):
        """Update user profile (partial update)"""
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial=False):
        """Helper method to handle profile updates"""
        try:
            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=partial,
                context={'request': request}
            )

            if not serializer.is_valid():
                logger.warning(f"Profile update validation failed for user {request.user.email}: {serializer.errors}")
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            updated_user = serializer.save()
            logger.info(f"Profile updated successfully for user {request.user.email}")

            return create_response(
                data={
                    "user": UserProfileSerializer(updated_user, context={'request': request}).data
                },
                message="Profile updated successfully"
            )

        except Exception as e:
            logger.error(f"Profile update failed for user {request.user.email}: {str(e)}", exc_info=True)
            return create_response(
                error="Profile update failed",
                error_code="profile_update_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        """Get public profile information for a user"""
        try:
            user = get_object_or_404(User, uuid=user_id)  # Use UUID instead of ID

            serializer = UserProfileSerializer(user, context={'request': request})
            data = serializer.data

            # Filter out sensitive information
            sensitive_fields = [
                'email', 'is_verified', 'reset_code', 'verification_code',
                'license_number', 'tax_id', 'credit_limit', 'phone_number',
                'date_of_birth', 'address', 'company_registration'
            ]
            for field in sensitive_fields:
                if field in data:
                    del data[field]

            return create_response(data={"user": data})

        except Exception as e:
            logger.error(f"Error fetching public profile for user_id {user_id}: {str(e)}", exc_info=True)
            return create_response(
                error="An error occurred while fetching the profile",
                error_code="profile_fetch_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    def post(self, request):
        """Handle password reset request and send reset code via email"""
        try:
            email = request.data.get('email', '').lower().strip()
            if not email:
                return create_response(
                    error="Email is required",
                    error_code="email_required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)

                # Check for recent reset requests
                if user.reset_code_created:
                    time_since_last_request = timezone.now() - user.reset_code_created
                    if time_since_last_request < timedelta(minutes=5):
                        wait_minutes = 5 - (time_since_last_request.seconds // 60)
                        return create_response(
                            error=f"Please wait {wait_minutes} minutes before requesting another reset",
                            error_code="rate_limit",
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS
                        )

                # Generate reset code using model method
                reset_code = user.generate_reset_code()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'reset_code': reset_code,
                        'expiry_hours': 1
                    }
                    send_password_reset_email(user.email, reset_code, context)
                    logger.info(f"Password reset email sent to {user.email}")

                    return create_response(
                        message="Password reset instructions have been sent to your email"
                    )

                except EmailRateLimitExceeded as e:
                    logger.warning(f"Reset email rate limit hit for {user.email}")
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send reset email to {user.email}: {str(email_error)}", exc_info=True)
                    return create_response(
                        error="Failed to send reset email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # Return same message for security
                logger.info(f"Password reset requested for non-existent email: {email}")
                return create_response(
                    message="If an account exists with this email, password reset instructions have been sent"
                )

        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyResetCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify the reset code validity before allowing password reset"""
        try:
            email = request.data.get('email')
            reset_code = request.data.get('reset_code')

            if not all([email, reset_code]):
                return create_response(
                    error="Email and reset code are required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)

                # Check expiry time
                if not user.reset_code_created:
                    raise User.DoesNotExist

                expiry_time = user.reset_code_created + timedelta(hours=1)
                if timezone.now() > expiry_time:
                    return create_response(
                        error="Reset code has expired",
                        error_code="reset_code_expired",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                if user.reset_code != reset_code:
                    return create_response(
                        error="Invalid reset code",
                        error_code="invalid_code",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                return create_response(message="Reset code is valid")

            except User.DoesNotExist:
                return create_response(
                    error="Invalid or expired reset code",
                    error_code="invalid_code",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Error verifying reset code: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        """Reset user password using reset code"""
        try:
            email = request.data.get('email')
            reset_code = request.data.get('reset_code')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not all([email, reset_code, new_password, confirm_password]):
                return create_response(
                    error="All fields are required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return create_response(
                    error="Passwords do not match",
                    error_code="password_mismatch",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)

                # Use model method for password reset
                if user.reset_password(reset_code, new_password):
                    logger.info(f"Password reset successful for user {user.email}")

                    # Create a new token
                    Token.objects.filter(user=user).delete()
                    token = Token.objects.create(user=user)

                    return create_response(
                        message="Password reset successfully",
                        data={
                            'token': token.key,
                            'user': UserProfileSerializer(user, context={'request': request}).data
                        }
                    )
                else:
                    return create_response(
                        error="Invalid or expired reset code",
                        error_code="reset_failed",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            except User.DoesNotExist:
                return create_response(
                    error="Invalid or expired reset code",
                    error_code="invalid_code",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Change password for authenticated user"""
        try:
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not all([current_password, new_password, confirm_password]):
                return create_response(
                    error="All fields are required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return create_response(
                    error="New passwords do not match",
                    error_code="password_mismatch",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            user = request.user
            if not user.check_password(current_password):
                return create_response(
                    error="Current password is incorrect",
                    error_code="invalid_password",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            user.set_password(new_password)
            user.save()

            # Regenerate token
            Token.objects.filter(user=user).delete()
            new_token = Token.objects.create(user=user)

            logger.info(f"Password changed successfully for user {user.email}")
            return create_response(
                message="Password changed successfully",
                data={'token': new_token.key}
            )

        except Exception as e:
            logger.error(f"Password change failed for user {request.user.email}: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Resend verification email to user"""
        try:
            email = request.data.get('email')

            if not email:
                return create_response(
                    error="Email is required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)

                if user.is_verified:
                    return create_response(
                        message="Email is already verified",
                        status_code=status.HTTP_200_OK
                    )

                # Check for recent verification requests
                if user.verification_code_created:
                    time_since_last_request = timezone.now() - user.verification_code_created
                    if time_since_last_request < timedelta(minutes=5):
                        wait_minutes = 5 - (time_since_last_request.seconds // 60)
                        return create_response(
                            error=f"Please wait {wait_minutes} minutes before requesting another verification email",
                            error_code="rate_limit",
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS
                        )

                # Generate verification code using model method
                verification_code = user.generate_verification_code()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'verification_code': verification_code,
                        'expiry_hours': 24
                    }
                    send_verification_email(user.email, verification_code, context)
                    logger.info(f"Verification email resent to {user.email}")

                    return create_response(
                        message="Verification email has been sent"
                    )

                except EmailRateLimitExceeded as e:
                    logger.warning(f"Verification resend rate limit hit for {user.email}")
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    logger.error(f"Failed to resend verification email to {user.email}: {str(email_error)}", exc_info=True)
                    return create_response(
                        error="Failed to send verification email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # For security, don't reveal if email exists
                logger.info(f"Verification resend requested for non-existent email: {email}")
                return create_response(
                    message="If an account exists with this email, a verification email has been sent"
                )

        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Update user avatar"""
        try:
            if 'avatar' not in request.FILES:
                return create_response(
                    error="No avatar file provided",
                    error_code="missing_file",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            avatar_file = request.FILES['avatar']

            # Validate file size (max 2MB)
            max_size = 2 * 1024 * 1024  # 2MB
            if avatar_file.size > max_size:
                return create_response(
                    error="Avatar file too large. Maximum size is 2MB",
                    error_code="file_too_large",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar_file.content_type not in allowed_types:
                return create_response(
                    error="Invalid file type. Allowed types: JPEG, PNG, GIF",
                    error_code="invalid_file_type",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            user = request.user

            # Delete old avatar file if it exists
            if user.avatar:
                try:
                    storage, path = user.avatar.storage, user.avatar.path
                    storage.delete(path)
                except Exception as e:
                    logger.warning(f"Failed to delete old avatar for user {user.email}: {str(e)}")

            # Save new avatar
            user.avatar = avatar_file
            user.save()

            logger.info(f"Avatar updated successfully for user {user.email}")
            return create_response(
                data={
                    "user": UserProfileSerializer(user, context={'request': request}).data
                },
                message="Avatar updated successfully"
            )

        except Exception as e:
            logger.error(f"Failed to update avatar for user {request.user.email}: {str(e)}", exc_info=True)
            return create_response(
                error="Failed to update avatar",
                error_code="avatar_update_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssignRoleView(APIView):
    """
    View for assigning roles to users
    Only administrators can assign roles
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, user_id):
        """Assign roles to a user (admin only)"""
        try:
            user = get_object_or_404(User, uuid=user_id)  # Use UUID instead of ID
            role_names = request.data.get('roles', [])

            # Validate role names
            valid_roles = set([choice[0] for choice in Role.ROLE_CHOICES])
            for role_name in role_names:
                if role_name not in valid_roles:
                    return create_response(
                        error=f'Invalid role: {role_name}',
                        error_code="invalid_role",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            # Get current roles for notification
            current_roles = list(user.roles.values_list('name', flat=True))

            # Get or create the roles
            roles = []
            for role_name in role_names:
                role, created = Role.objects.get_or_create(name=role_name)
                roles.append(role)

            # Replace user's current roles
            user.roles.set(roles)

            # Prepare role display names for notification
            role_display_names = [role.get_name_display() for role in roles]

            # Determine added and removed roles
            added_roles = [role for role in role_names if role not in current_roles]
            removed_roles = [role for role in current_roles if role not in role_names]

            # Send notification email if roles changed
            if added_roles or removed_roles:
                try:
                    send_role_assignment_email(
                        user.email,
                        role_display_names,
                        [Role.objects.get(name=role).get_name_display() for role in added_roles],
                        [Role.objects.get(name=role).get_name_display() for role in removed_roles]
                    )
                except Exception as e:
                    logger.warning(f"Failed to send role assignment email to {user.email}: {str(e)}")

            logger.info(f"Roles updated for user {user.email}: {role_names}")
            return create_response(
                data={
                    'user_id': str(user.uuid),  # Return UUID as string
                    'roles': role_names
                },
                message="Roles assigned successfully"
            )

        except Exception as e:
            logger.error(f"Role assignment failed: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# class RoleDashboardView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """Get dashboard data based on user's role for real estate platform"""
#         try:
#             user = request.user
#             user_roles = user.roles.values_list('name', flat=True)

#             # Import required models for dashboard data
#             from base.models import Auction, Document, Contract, Bid, Property, PropertyView

#             dashboard_data = {}

#             # Admin dashboard
#             if Role.ADMIN in user_roles:
#                 dashboard_data['admin'] = {
#                     'active_auctions': Auction.objects.filter(status='live').count(),
#                     'total_users': User.objects.count(),
#                     'pending_approvals': Document.objects.filter(
#                         verification_status='pending'
#                     ).count(),
#                 }

#             # Seller dashboard
#             if Role.SELLER in user_roles:
#                 dashboard_data['seller'] = {
#                     'active_auctions': Auction.objects.filter(related_property__owner=user, status='live').count(),
#                     'pending_contracts': Contract.objects.filter(seller=user, status='pending').count(),
#                     'property_views': PropertyView.objects.filter(
#                         auction__related_property__owner=user
#                     ).count(),
#                 }

#             # Buyer dashboard
#             if Role.BUYER in user_roles:
#                 dashboard_data['buyer'] = {
#                     'active_bids': Bid.objects.filter(bidder=user, auction__status='live').count(),
#                     'pending_contracts': Contract.objects.filter(buyer=user, status='pending').count(),
#                     'scheduled_viewings': PropertyView.objects.filter(
#                         auction__bids__bidder=user
#                     ).distinct().count(),
#                 }

#             # Inspector dashboard
#             if Role.INSPECTOR in user_roles:
#                 pending_inspections = Property.objects.filter(
#                     auctions__status='live',
#                     documents__document_type='report',
#                     documents__verification_status='pending'
#                 ).distinct().count()

#                 dashboard_data['inspector'] = {
#                     'pending_inspections': pending_inspections,
#                     'completed_inspections': Document.objects.filter(
#                         document_type='report',
#                         verified_by=user
#                     ).count(),
#                 }

#             # Legal representative dashboard
#             if Role.LEGAL in user_roles:
#                 from django.db.models import Q

#                 dashboard_data['legal'] = {
#                     'pending_reviews': Contract.objects.filter(
#                         Q(seller=user, status='pending') |
#                         Q(buyer=user, status='pending')
#                     ).count(),
#                     'pending_title_verifications': Document.objects.filter(
#                         document_type='deed',
#                         verification_status='pending'
#                     ).count(),
#                 }

#             # Real Estate Agent dashboard
#             if Role.AGENT in user_roles:
#                 dashboard_data['agent'] = {
#                     'active_listings': Property.objects.filter(
#                         is_published=True,
#                         status='available'
#                     ).count(),
#                     'pending_viewings': PropertyView.objects.filter(
#                         auction__related_property__owner=user
#                     ).count(),
#                 }

#             return create_response(dashboard_data)

#         except Exception as e:
#             return create_response(
#                 error="An unexpected error occurred",
#                 error_code="server_error",
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
