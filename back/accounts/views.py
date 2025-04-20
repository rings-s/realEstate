# accounts/views.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
import random
from base.decorators import api_role_required

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

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user for the real estate auction platform"""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                user = serializer.save()

                # Generate 6-digit verification code
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                user.verification_code = verification_code
                user.verification_code_created = timezone.now()
                user.save()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'verification_code': verification_code,
                        'expiry_hours': 24
                    }
                    send_verification_email(user.email, verification_code, context)

                except EmailRateLimitExceeded as e:
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )

            return create_response(
                message="Registration successful. Please check your email for verification.",
                status_code=status.HTTP_201_CREATED
            )

        except ValidationError as ve:
            return create_response(
                error=str(ve),
                error_code="email_sending_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return create_response(
                error="Registration failed. Please try again later.",
                error_code="registration_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify user email with provided verification code"""
        try:
            email = request.data.get('email')
            verification_code = request.data.get('verification_code')

            if not all([email, verification_code]):
                return create_response(
                    error="Email and verification code are required",
                    error_code="missing_fields",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(
                    email=email,
                    verification_code=verification_code,
                    verification_code_created__gt=timezone.now() - timedelta(hours=24)
                )

                if timezone.now() > user.verification_code_created + timedelta(hours=24):
                    return create_response(
                        error="Verification code has expired",
                        error_code="verification_code_expired",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                # Mark user as verified
                user.is_verified = True
                user.verification_code = ""
                user.verification_code_created = None
                user.save()

                # Create token for authenticated access
                token, created = Token.objects.get_or_create(user=user)

                # Create successful response
                response_data = {
                    'message': "Email verified successfully",
                    'token': token.key,
                    'user': UserProfileSerializer(user).data
                }

                return create_response(response_data)

            except User.DoesNotExist:
                return create_response(
                    error="Invalid or expired verification code",
                    error_code="invalid_code",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Verify the validity of the auth token.
        This endpoint checks if the token is valid and belongs to the authenticated user.
        """
        try:
            # If the user is authenticated, the token is valid
            return Response(
                {
                    "status": "success",
                    "message": "Token is valid",
                    "user": {
                        "email": request.user.email,
                        "user_id": str(request.user.id),
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "error": "An unexpected error occurred during token verification",
                    "error_code": "token_verification_error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LoginView(APIView):
    permission_classes = [AllowAny]

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
            user = User.objects.get(email=email)

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

            # Generate or get existing token
            token, created = Token.objects.get_or_create(user=user)

            # Return response with token
            return create_response({
                'token': token.key,
                'user': UserProfileSerializer(user).data
            })

        except User.DoesNotExist:
            return create_response(
                error="Invalid credentials",
                error_code="invalid_credentials",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
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
            return create_response(message="Logged out successfully")
        except Exception as e:
            return create_response(
                error="Logout failed",
                error_code="logout_failed",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user profile information"""
        serializer = UserProfileSerializer(request.user)
        return create_response({"user": serializer.data})

    def put(self, request):
        """Update user profile (complete update)"""
        return self._update_profile(request, partial=False)

    def patch(self, request):
        """Update user profile (partial update)"""
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial=False):
        """Helper method to handle profile updates"""
        try:
            # Check for immutable fields
            immutable_fields = {'email', 'is_verified', 'role'}
            if any(field in request.data for field in immutable_fields):
                return create_response(
                    error="Cannot update protected fields",
                    error_code="immutable_field_update",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=partial,
                context={'request': request}
            )

            if not serializer.is_valid():
                return create_response(
                    error=serializer.errors,
                    error_code="validation_error",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()
            return create_response({
                "user": UserProfileSerializer(request.user).data,
                "message": "Profile updated successfully"
            })

        except Exception as e:
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
            user = get_object_or_404(User, id=user_id)

            # Only return public information
            serializer = UserProfileSerializer(user, context={'request': request})

            # Filter out sensitive information
            data = serializer.data
            sensitive_fields = ['email', 'is_verified', 'reset_code', 'verification_code',
                               'license_number', 'tax_id', 'credit_limit']
            for field in sensitive_fields:
                if field in data:
                    del data[field]

            return create_response({"user": data})

        except Exception as e:
            return create_response(
                error="An error occurred while fetching the profile",
                error_code="profile_fetch_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

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
                if user.reset_code_created and timezone.now() - user.reset_code_created < timedelta(minutes=5):
                    return create_response(
                        error="Please wait 5 minutes before requesting another reset",
                        error_code="rate_limit",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )

                # Generate reset code (6-digit)
                reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                user.reset_code = reset_code
                user.reset_code_created = timezone.now()
                user.save()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'reset_code': reset_code,
                        'expiry_hours': 1
                    }
                    send_password_reset_email(user.email, reset_code, context)

                    return create_response(
                        message="Password reset instructions have been sent to your email"
                    )

                except EmailRateLimitExceeded as e:
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    return create_response(
                        error="Failed to send reset email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # Return success message even if email doesn't exist (security)
                return create_response(
                    message="If an account exists with this email, password reset instructions have been sent"
                )

        except Exception as e:
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
                user = User.objects.get(
                    email=email,
                    reset_code=reset_code,
                    reset_code_created__gt=timezone.now() - timedelta(hours=1)
                )

                if timezone.now() > user.reset_code_created + timedelta(hours=1):
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
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

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
                user = User.objects.get(
                    email=email,
                    reset_code=reset_code,
                    reset_code_created__gt=timezone.now() - timedelta(hours=1)
                )

                if timezone.now() > user.reset_code_created + timedelta(hours=1):
                    return create_response(
                        error="Reset code has expired",
                        error_code="reset_code_expired",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                # Update password and clear reset code
                user.set_password(new_password)
                user.reset_code = ""
                user.reset_code_created = None
                user.save()

                # Create a new token
                token, _ = Token.objects.get_or_create(user=user)

                return create_response({
                    'message': "Password reset successfully",
                    'token': token.key,
                    'user': UserProfileSerializer(user).data
                })

            except User.DoesNotExist:
                return create_response(
                    error="Invalid or expired reset code",
                    error_code="invalid_code",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

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

            return create_response({
                'message': "Password changed successfully",
                'token': new_token.key
            })

        except Exception as e:
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

                # Check if already verified
                if user.is_verified:
                    return create_response(
                        message="Email is already verified",
                        status_code=status.HTTP_200_OK
                    )

                # Check for recent verification requests
                if user.verification_code_created and timezone.now() - user.verification_code_created < timedelta(minutes=5):
                    return create_response(
                        error="Please wait 5 minutes before requesting another verification email",
                        error_code="rate_limit",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )

                # Generate 6-digit verification code
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                user.verification_code = verification_code
                user.verification_code_created = timezone.now()
                user.save()

                try:
                    context = {
                        'user_name': f"{user.first_name} {user.last_name}",
                        'verification_code': verification_code,
                        'expiry_hours': 24
                    }
                    send_verification_email(user.email, verification_code, context)

                    return create_response(
                        message="Verification email has been sent"
                    )

                except EmailRateLimitExceeded as e:
                    return create_response(
                        error=str(e),
                        error_code="rate_limit_exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                except Exception as email_error:
                    return create_response(
                        error="Failed to send verification email",
                        error_code="email_sending_failed",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except User.DoesNotExist:
                # For security reasons, don't reveal if email exists
                return create_response(
                    message="If an account exists with this email, a verification email has been sent"
                )

        except Exception as e:
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

            # Check file size (max 2MB)
            if avatar_file.size > 2 * 1024 * 1024:
                return create_response(
                    error="Avatar file too large. Maximum size is 2MB",
                    error_code="file_too_large",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar_file.content_type not in allowed_types:
                return create_response(
                    error="Invalid file type. Allowed types: JPEG, PNG, GIF",
                    error_code="invalid_file_type",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Update user avatar
            user = request.user

            # Delete old avatar file if it exists
            if user.avatar:
                try:
                    storage, path = user.avatar.storage, user.avatar.path
                    storage.delete(path)
                except Exception:
                    pass

            # Save new avatar
            user.avatar = avatar_file
            user.save()

            return create_response({
                "message": "Avatar updated successfully",
                "user": UserProfileSerializer(user).data
            })

        except Exception as e:
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
    def get_permissions(self):
        return [api_role_required(Role.ADMIN)]

    def post(self, request, user_id):
        """Assign roles to a user (admin only)"""
        try:
            user = get_object_or_404(User, id=user_id)
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
                except Exception:
                    pass  # Non-critical if email fails

            return create_response({
                'user_id': user.id,
                'roles': role_names
            })
        except Exception as e:
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RoleDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard data based on user's role for real estate platform"""
        try:
            user = request.user
            user_roles = user.roles.values_list('name', flat=True)

            # Import required models for dashboard data
            from base.models import Auction, Document, Contract, Bid, Property, PropertyView

            dashboard_data = {}

            # Admin dashboard
            if Role.ADMIN in user_roles:
                dashboard_data['admin'] = {
                    'active_auctions': Auction.objects.filter(status='live').count(),
                    'total_users': User.objects.count(),
                    'pending_approvals': Document.objects.filter(
                        verification_status='pending'
                    ).count(),
                }

            # Seller dashboard
            if Role.SELLER in user_roles:
                dashboard_data['seller'] = {
                    'active_auctions': Auction.objects.filter(related_property__owner=user, status='live').count(),
                    'pending_contracts': Contract.objects.filter(seller=user, status='pending').count(),
                    'property_views': PropertyView.objects.filter(
                        auction__related_property__owner=user
                    ).count(),
                }

            # Buyer dashboard
            if Role.BUYER in user_roles:
                dashboard_data['buyer'] = {
                    'active_bids': Bid.objects.filter(bidder=user, auction__status='live').count(),
                    'pending_contracts': Contract.objects.filter(buyer=user, status='pending').count(),
                    'scheduled_viewings': PropertyView.objects.filter(
                        auction__bids__bidder=user
                    ).distinct().count(),
                }

            # Inspector dashboard
            if Role.INSPECTOR in user_roles:
                pending_inspections = Property.objects.filter(
                    auctions__status='live',
                    documents__document_type='report',
                    documents__verification_status='pending'
                ).distinct().count()

                dashboard_data['inspector'] = {
                    'pending_inspections': pending_inspections,
                    'completed_inspections': Document.objects.filter(
                        document_type='report',
                        verified_by=user
                    ).count(),
                }

            # Legal representative dashboard
            if Role.LEGAL in user_roles:
                from django.db.models import Q

                dashboard_data['legal'] = {
                    'pending_reviews': Contract.objects.filter(
                        Q(seller=user, status='pending') |
                        Q(buyer=user, status='pending')
                    ).count(),
                    'pending_title_verifications': Document.objects.filter(
                        document_type='deed',
                        verification_status='pending'
                    ).count(),
                }

            # Real Estate Agent dashboard
            if Role.AGENT in user_roles:
                dashboard_data['agent'] = {
                    'active_listings': Property.objects.filter(
                        is_published=True,
                        status='available'
                    ).count(),
                    'pending_viewings': PropertyView.objects.filter(
                        auction__related_property__owner=user
                    ).count(),
                }

            return create_response(dashboard_data)

        except Exception as e:
            return create_response(
                error="An unexpected error occurred",
                error_code="server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
