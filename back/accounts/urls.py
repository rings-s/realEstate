from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/<uuid:user_id>/', views.PublicProfileView.as_view(), name='public-profile'),
    path('profile/avatar/', views.UpdateAvatarView.as_view(), name='update-avatar'),

    # Password management
    path('password/change/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password/reset/request/', views.PasswordResetRequestView.as_view(), name='request-password-reset'),
    path('password/reset/verify/', views.VerifyResetCodeView.as_view(), name='verify-reset-token'),
    path('password/reset/confirm/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
]

"""
API Documentation:

Authentication Endpoints:
------------------------
POST /accounts/register/
    Register a new user
    Body: {
        "email": string,
        "password": string,
        "confirm_password": string,
        "first_name": string,
        "last_name": string,
        "phone_number": string (optional),
        "date_of_birth": date (optional)
    }

POST /accounts/verify-email/
    Verify user's email address
    Body: {
        "email": string,
        "verification_code": string
    }

POST /accounts/login/
    Login user and get JWT tokens
    Body: {
        "email": string,
        "password": string
    }
    Returns: {
        "data": {
            "tokens": {
                "refresh": string,
                "access": string
            },
            "user": {...} // User profile data
        }
    }

POST /accounts/logout/
    Blacklist JWT refresh token
    Body: {
        "refresh": string
    }

POST /accounts/token/refresh/
    Refresh access token
    Body: {
        "refresh": string
    }
    Returns: {
        "data": {
            "access": string
        }
    }

POST /accounts/token/verify/
    Verify the validity of access token
    Body: {
        "token": string
    }

Profile Management:
-----------------
GET /accounts/profile/
    Get current user's profile
    Authorization: Bearer <access_token>

PATCH /accounts/profile/
    Update current user's profile
    Authorization: Bearer <access_token>
    Body: {
        "first_name": string,
        "last_name": string,
        "phone_number": string,
        "bio": string,
        "company_name": string,
        ... other profile fields
    }

POST /accounts/profile/avatar/
    Update user avatar
    Authorization: Bearer <access_token>
    Body: multipart/form-data with 'avatar' file

GET /accounts/profile/<uuid:user_id>/
    Get public profile information for a user

Password Management:
------------------
POST /accounts/password/change/
    Change password (for authenticated users)
    Authorization: Bearer <access_token>
    Body: {
        "current_password": string,
        "new_password": string,
        "confirm_password": string
    }

POST /accounts/password/reset/request/
    Request password reset
    Body: {
        "email": string
    }

POST /accounts/password/reset/verify/
    Verify password reset code
    Body: {
        "email": string,
        "reset_code": string
    }

POST /accounts/password/reset/confirm/
    Reset password using code
    Body: {
        "email": string,
        "reset_code": string,
        "new_password": string,
        "confirm_password": string
    }

POST /accounts/resend-verification/
    Resend verification email
    Body: {
        "email": string
    }
"""
