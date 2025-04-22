from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .utils import check_user_permission

class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users"""
    message = _('You must be an administrator to perform this action.')

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsVerifiedUser(permissions.BasePermission):
    """Allow access only to email-verified users"""
    message = _('You must verify your email address to perform this action.')

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified

class HasPermission(permissions.BasePermission):
    """Allow access based on specific permissions"""

    def __init__(self, required_permission=None):
        self.required_permission = required_permission
        self.message = _(f'You do not have the required permission to perform this action.')

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin users have all permissions
        if request.user.is_staff:
            return True

        # Check if user has the required permission
        if self.required_permission:
            return check_user_permission(request.user, self.required_permission)

        return True

class IsObjectOwner(permissions.BasePermission):
    """
    Object-level permission allowing owners to edit their objects.
    Customizable via owner_field attribute on the view.
    """
    message = _('You must be the owner of this object to perform this action.')

    def has_object_permission(self, request, view, obj):
        # READ permissions allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # Get owner field name from view or use default
        owner_field = getattr(view, 'owner_field', 'owner')

        # Handle nested ownership via '.' notation
        if '.' in owner_field:
            parts = owner_field.split('.')
            current = obj
            for part in parts:
                if not hasattr(current, part):
                    return False
                current = getattr(current, part)
            return current == request.user

        # Direct ownership
        if hasattr(obj, owner_field):
            return getattr(obj, owner_field) == request.user

        return False

class IsPropertyOwner(permissions.BasePermission):
    """Allow property owners to edit their properties"""
    message = _('You must be the owner of this property to perform this action.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # READ permissions allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is property owner
        return obj.owner == request.user

class IsAuctionParticipant(permissions.BasePermission):
    """Allow auction participants to access auction data"""
    message = _('You must be a participant in this auction to perform this action.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # READ permissions for public auctions
        if request.method in permissions.SAFE_METHODS and not obj.is_private:
            return True

        # Check if user is property owner
        if obj.related_property.owner == request.user:
            return True

        # Check if user has placed a bid
        if obj.bids.filter(bidder=request.user).exists():
            return True

        return False

class IsBidOwner(permissions.BasePermission):
    """Allow bid owners to manage their bids"""
    message = _('You must be the owner of this bid to perform this action.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # READ permissions for bidder or property owner
        if request.method in permissions.SAFE_METHODS:
            if obj.bidder == request.user:
                return True
            if obj.auction.related_property.owner == request.user:
                return True

        # WRITE permissions only for bidder
        return obj.bidder == request.user

class IsDocumentAuthorized(permissions.BasePermission):
    """Control access to documents based on user relationship"""
    message = _('You do not have permission to access this document.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # Document uploader always has access
        if obj.uploaded_by == request.user:
            return True

        # Public documents are readable by anyone
        if obj.is_public and request.method in permissions.SAFE_METHODS:
            return True

        # Property owner has access to property documents
        if obj.related_property and obj.related_property.owner == request.user:
            return True

        # Contract parties have access to contract documents
        if obj.related_contract and (obj.related_contract.buyer == request.user or
                                     obj.related_contract.seller == request.user):
            return True

        # Users with specific permissions can access certain documents
        if request.user.has_perm('base.verify_documents') and obj.verification_status == 'pending':
            return True

        if request.user.has_perm('base.review_documents') and obj.document_type in ['deed', 'report', 'certificate']:
            return True

        return False

class IsMessageParticipant(permissions.BasePermission):
    """Allow only thread participants to access messages"""
    message = _('You must be a participant in this thread to access messages.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # Check if user is a thread participant
        thread = obj if hasattr(obj, 'participants') else obj.thread
        return thread.participants.filter(user=request.user, is_active=True).exists()

class IsContractParty(permissions.BasePermission):
    """Allow only contract parties to access contract details"""
    message = _('You must be a party to this contract to access details.')

    def has_object_permission(self, request, view, obj):
        # Staff users have all permissions
        if request.user.is_staff:
            return True

        # Users with verification permission can read
        if request.user.has_perm('base.verify_contracts') and request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is a contract party
        return request.user in [obj.buyer, obj.seller]

class ReadOnly(permissions.BasePermission):
    """Allow only read-only access to resources"""
    message = _('This resource is read-only.')

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners to edit objects, but others only read access"""
    message = _('You must be the owner of this object to modify it.')

    def has_object_permission(self, request, view, obj):
        # READ permissions allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Get owner field from view or use default
        owner_field = getattr(view, 'owner_field', 'owner')
        owner = getattr(obj, owner_field, None)

        return owner == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admin users full access, others only read access"""
    message = _('You must be an administrator to modify this resource.')

    def has_permission(self, request, view):
        # READ permissions allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # WRITE permissions only for staff users
        return request.user and request.user.is_authenticated and request.user.is_staff
