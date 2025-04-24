from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.template.exceptions import TemplateSyntaxError

from .models import UserProfile
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)
from .utils import (
    send_verification_email,
    send_password_reset_email,
    EmailRateLimitExceeded,
    create_response,
    debug_request
)
from .middleware import track_successful_login
from .permissions import IsOwnerOrAdmin, IsAdminUser

logger = logging.getLogger(__name__)
User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    @transaction.atomic
    def post(self, request):
        """Register a new user"""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.save()
            verification_code = user.generate_verification_code()

            try:
                context = {
                    'user_name': f"{user.first_name} {user.last_name}",
                    'verification_code': verification_code,
                    'expiry_hours': 24
                }
                send_verification_email(user.email, verification_code, context)
                logger.info(f"Verification email sent to {user.email}")
            except EmailRateLimitExceeded as e:
                return create_response(
                    error=str(e),
                    error_code="rate_limit_exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            except Exception as email_error:
                logger.error(f"Failed to send verification email: {email_error}", exc_info=True)
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
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')

        if not all([email, verification_code]):
            return create_response(
                error="Email and verification code are required",
                error_code="missing_fields",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if user.is_verified:
                tokens = get_tokens_for_user(user)
                return create_response(
                    message="Email already verified",
                    data={
                        'tokens': tokens,
                        'user': UserProfileSerializer(user, context={'request': request}).data
                    }
                )

            if user.verify_account(verification_code):
                tokens = get_tokens_for_user(user)
                logger.info(f"Email verification successful for user {user.id}")

                return create_response(
                    message="Email verified successfully",
                    data={
                        'tokens': tokens,
                        'user': UserProfileSerializer(user, context={'request': request}).data
                    }
                )
            else:
                return create_response(
                    error="Invalid or expired verification code",
                    error_code="invalid_verification",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            return create_response(
                error="User not found",
                error_code="user_not_found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Verification error: {str(e)}", exc_info=True)
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    def post(self, request):
        """Handle user login and return JWT tokens"""
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
                return create_response(
                    error="Invalid credentials",
                    error_code="invalid_credentials",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(password):
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

            # Generate JWT tokens
            tokens = get_tokens_for_user(user)

            logger.info(f"Successful login for user: {email}")
            return create_response(
                data={
                    'tokens': tokens,
                    'user': UserProfileSerializer(user, context={'request': request}).data
                }
            )

        except Exception as e:
            logger.error(f"Login failed: {str(e)}", exc_info=True)
            return create_response(
                error="Login failed. Please try again.",
                error_code="login_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist JWT refresh token to logout"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return create_response(
                    error="Refresh token is required",
                    error_code="missing_token",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User {request.user.email} logged out successfully")
            return create_response(message="Logged out successfully")
        except TokenError:
            return create_response(
                error="Invalid token",
                error_code="invalid_token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}", exc_info=True)
            return create_response(
                error="Logout failed",
                error_code="logout_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh access token using refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return create_response(
                    error="Refresh token is required",
                    error_code="missing_token",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            refresh = RefreshToken(refresh_token)
            return create_response(
                data={
                    'access': str(refresh.access_token)
                }
            )
        except TokenError:
            return create_response(
                error="Invalid or expired refresh token",
                error_code="invalid_token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}", exc_info=True)
            return create_response(
                error="An error occurred during token refresh",
                error_code="token_refresh_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Verify the validity of the access token and return user information"""
        try:
            user = request.user

            user_data = {
                "email": user.email,
                "user_id": str(user.uuid),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "date_joined": user.date_joined.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }

            return create_response(data={"valid": True, "user": user_data})
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return create_response(
                error="An error occurred during token verification",
                error_code="token_verification_error",
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

    def patch(self, request):
        """Update user profile (partial update)"""
        try:
            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if not serializer.is_valid():
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            updated_user = serializer.save()
            logger.info(f"Profile updated for user {request.user.email}")

            return create_response(
                data={"user": UserProfileSerializer(updated_user, context={'request': request}).data},
                message="Profile updated successfully"
            )

        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}", exc_info=True)
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
            user = get_object_or_404(User, uuid=user_id)
            serializer = UserProfileSerializer(user, context={'request': request})
            data = serializer.data

            # Filter out sensitive information
            sensitive_fields = [
                'email', 'is_verified', 'phone_number', 'date_of_birth',
                'address', 'tax_id', 'credit_limit', 'company_registration'
            ]
            for field in sensitive_fields:
                if field in data:
                    data.pop(field)

            return create_response(data={"user": data})

        except Exception as e:
            logger.error(f"Error fetching public profile: {str(e)}", exc_info=True)
            return create_response(
                error="Error fetching profile",
                error_code="profile_fetch_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @debug_request
    def post(self, request):
        """Handle password reset request and send reset code via email"""
        email = request.data.get('email', '').lower().strip()
        if not email:
            return create_response(
                error="Email is required",
                error_code="email_required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
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

                except EmailRateLimitExceeded as e:
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send reset email: {str(email_error)}", exc_info=True)
                    return create_response(
                        error="Failed to send reset email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # Return same message for security
                logger.info(f"Password reset requested for non-existent email: {email}")

            # Always return success to prevent email enumeration
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

            # Check code validity
            if not user.reset_code_created or user.reset_code != reset_code:
                return create_response(
                    error="Invalid reset code",
                    error_code="invalid_code",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Check expiry time
            expiry_time = user.reset_code_created + timedelta(hours=1)
            if timezone.now() > expiry_time:
                return create_response(
                    error="Reset code has expired",
                    error_code="reset_code_expired",
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
                # Generate JWT tokens
                tokens = get_tokens_for_user(user)

                logger.info(f"Password reset successful for user {user.email}")
                return create_response(
                    message="Password reset successfully",
                    data={
                        'tokens': tokens,
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

        try:
            # Update password
            user.set_password(new_password)
            user.save()

            # Generate new JWT tokens
            tokens = get_tokens_for_user(user)

            logger.info(f"Password changed successfully for user {user.email}")
            return create_response(
                message="Password changed successfully",
                data={'tokens': tokens}
            )
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}", exc_info=True)
            return create_response(
                error="Password change failed",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Resend verification email to user"""
        email = request.data.get('email')

        if not email:
            return create_response(
                error="Email is required",
                error_code="missing_fields",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            try:
                user = User.objects.get(email=email)

                if user.is_verified:
                    return create_response(message="Email is already verified")

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

                # Generate verification code
                verification_code = user.generate_verification_code()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'verification_code': verification_code,
                        'expiry_hours': 24
                    }
                    send_verification_email(user.email, verification_code, context)
                    logger.info(f"Verification email resent to {user.email}")

                except EmailRateLimitExceeded as e:
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    logger.error(f"Failed to resend verification email: {str(email_error)}", exc_info=True)
                    return create_response(
                        error="Failed to send verification email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # Don't reveal if email exists
                logger.info(f"Verification resend requested for non-existent email: {email}")

            # Always return success for security
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
        if 'avatar' not in request.FILES:
            return create_response(
                error="No avatar file provided",
                error_code="missing_file",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        avatar_file = request.FILES['avatar']

        # Validate file size (max 2MB)
        max_size = 2 * 1024 * 1024
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

        try:
            user = request.user

            # Delete old avatar file if it exists
            if user.avatar:
                try:
                    storage, path = user.avatar.storage, user.avatar.path
                    storage.delete(path)
                except Exception as e:
                    logger.warning(f"Failed to delete old avatar: {str(e)}")

            # Save new avatar
            user.avatar = avatar_file
            user.save()

            logger.info(f"Avatar updated for user {user.email}")
            return create_response(
                data={"user": UserProfileSerializer(user, context={'request': request}).data},
                message="Avatar updated successfully"
            )

        except Exception as e:
            logger.error(f"Failed to update avatar: {str(e)}", exc_info=True)
            return create_response(
                error="Failed to update avatar",
                error_code="avatar_update_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
