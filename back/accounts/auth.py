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

    This backend attempts to get a user by both their integer primary key (pk) and UUID field.
    This is useful if the user identifier passed to `get_user` might be either format.
    """
    def get_user(self, user_id):
        """
        Get a User object from the user_id.
        The user_id could be either an integer or a UUID string.
        Returns None if the user cannot be found by either ID or UUID.
        """
        # Check if user_id is potentially an integer first
        try:
            user_id_as_int = int(user_id)
            # Try fetching by primary key (integer)
            user = User.objects.get(pk=user_id_as_int)
            return user
        except (ValueError, TypeError, User.DoesNotExist):
            # Not a valid integer, doesn't match int PK, or other TypeError
            pass # Continue to try UUID

        # If integer lookup failed, try treating user_id as a UUID
        try:
            # Ensure user_id is a string before converting to UUID
            user_id_as_uuid = uuid.UUID(str(user_id))
            # Try fetching by the 'uuid' field
            user = User.objects.get(uuid=user_id_as_uuid)
            return user
        except (ValueError, TypeError, User.DoesNotExist):
            # Not a valid UUID string, doesn't match UUID field, or other TypeError
            return None # User not found by UUID either
        except Exception as e:
            # Log unexpected errors, but still return None as per backend contract
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f"Unexpected error in UUIDModelBackend.get_user: {e}", exc_info=True)
            return None
