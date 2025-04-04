# Path: accounts/auth.py
# This file contains a custom authentication backend that supports UUID lookups
# It allows Django to authenticate users by their UUID when the session contains a UUID

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
import uuid

User = get_user_model()

class UUIDModelBackend(ModelBackend):
    """
    Custom authentication backend that supports both integer ID and UUID authentication.
    
    This backend attempts to get a user by both their integer primary key and UUID field,
    which helps resolve issues when the session contains a UUID but the model expects an
    integer ID.
    """
    def get_user(self, user_id):
        """
        Get a User object from the user_id.
        The user_id could be either an integer or a UUID string.
        """
        try:
            # First try to get the user by ID (regular int PK)
            try:
                user_id_as_int = int(user_id)
                return User.objects.get(pk=user_id_as_int)
            except (ValueError, User.DoesNotExist, TypeError):
                # Not an integer or user doesn't exist with that ID
                pass
                
            # If that fails, try by UUID
            try:
                # Check if the user_id is a valid UUID
                user_id_as_uuid = uuid.UUID(str(user_id))
                return User.objects.get(uuid=user_id_as_uuid)
            except (ValueError, User.DoesNotExist, TypeError):
                # Not a valid UUID or user doesn't exist with that UUID
                pass
                
            return None
        except Exception:
            # Any other exception should be logged but not raised
            return None