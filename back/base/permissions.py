from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from accounts.models import Role


class IsAdminUser(permissions.BasePermission):
    """
    Allow access only to admin users.
    """
    message = _('يتطلب الوصول إلى هذا المورد صلاحيات المشرف.')

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.has_role(Role.ADMIN)


class IsVerifiedUser(permissions.BasePermission):
    """
    Allow access only to verified users.
    """
    message = _('يجب أن يكون حسابك مُوثقاً للوصول إلى هذا المورد.')

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified


class HasRolePermission(permissions.BasePermission):
    """
    Allow access based on user role and required auction permission.
    """
    message = _('ليس لديك الدور المطلوب للوصول إلى هذا المورد.')

    def __init__(self, required_roles=None, required_permission=None):
        self.required_roles = required_roles or []
        self.required_permission = required_permission

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin users have all permissions
        if request.user.has_role(Role.ADMIN):
            return True

        # Check if user has any of the required roles
        if self.required_roles:
            for role in self.required_roles:
                if request.user.has_role(role):
                    return True
            return False

        # Check if user has the specific permission
        if self.required_permission:
            return request.user.has_auction_permission(self.required_permission)

        # If no specific requirements, authenticated users have permission
        return True


class IsPropertyOwner(permissions.BasePermission):
    """
    Object-level permission to allow property owners or their agents to edit properties.
    """
    message = _('يمكن تعديل العقار فقط من قِبل المالك أو الوكيل المفوض.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # READ permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is the property owner
        if obj.owner == request.user:
            return True

        # Check if user is an agent representing the owner
        # This requires checking if the user is an agent AND has a relationship with the owner
        if request.user.has_role(Role.AGENT):
            # This implementation assumes a relationship model between agents and sellers
            # You would need to implement this based on your specific data model
            # Example: return AgentClientRelationship.objects.filter(agent=request.user, client=obj.owner).exists()
            return False

        return False


class IsAuctionParticipant(permissions.BasePermission):
    """
    Object-level permission to allow auction participants (seller, bidders) to access auction data.
    """
    message = _('يمكن الوصول إلى هذه البيانات فقط من قبل المشاركين في المزاد.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # READ permissions for public auctions
        if request.method in permissions.SAFE_METHODS and not obj.is_private:
            return True

        # Check if user is the property owner
        if obj.related_property.owner == request.user:
            return True

        # Check if user has placed a bid in this auction
        if obj.bids.filter(bidder=request.user).exists():
            return True

        # Check if user is an agent for the property owner
        if request.user.has_role(Role.AGENT):
            # Implement agent-client relationship check here
            return False

        return False


class IsBidOwner(permissions.BasePermission):
    """
    Object-level permission to allow bid owners to edit their bids.
    """
    message = _('يمكن تعديل المزايدة فقط من قِبل المزايد نفسه.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # READ permissions for the bidder, property owner, or auction admin
        if request.method in permissions.SAFE_METHODS:
            if obj.bidder == request.user:
                return True
            if obj.auction.related_property.owner == request.user:
                return True
            # Add more conditions as needed

        # WRITE permissions only for the bidder
        return obj.bidder == request.user


class IsDocumentAuthorized(permissions.BasePermission):
    """
    Object-level permission to control access to documents based on their access settings.
    """
    message = _('ليس لديك صلاحية الوصول إلى هذه الوثيقة.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # Document uploader always has access
        if obj.uploaded_by == request.user:
            return True

        # If document is public, allow read access
        if obj.is_public and request.method in permissions.SAFE_METHODS:
            return True

        # Property owner has access to property documents
        if obj.related_property and obj.related_property.owner == request.user:
            return True

        # Contract parties have access to contract documents
        if obj.related_contract and (obj.related_contract.buyer == request.user or obj.related_contract.seller == request.user):
            return True

        # Legal users can access documents they need to verify
        if request.user.has_role(Role.LEGAL) and obj.verification_status == 'pending':
            return True

        # Inspector users can access documents they need to review
        if request.user.has_role(Role.INSPECTOR) and obj.document_type in ['deed', 'report', 'certificate']:
            return True

        return False


class IsMessageParticipant(permissions.BasePermission):
    """
    Object-level permission to allow only thread participants to access messages.
    """
    message = _('يمكن الوصول إلى الرسائل فقط من قِبل المشاركين في المحادثة.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # Check if user is a participant in the thread
        thread = obj if hasattr(obj, 'participants') else obj.thread
        return thread.participants.filter(user=request.user, is_active=True).exists()


class IsContractParty(permissions.BasePermission):
    """
    Object-level permission to allow only contract parties to access contract details.
    """
    message = _('يمكن الوصول إلى تفاصيل العقد فقط من قِبل أطراف العقد.')

    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.has_role(Role.ADMIN):
            return True

        # Allow legal users for verification
        if request.user.has_role(Role.LEGAL) and request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is a party in the contract
        return request.user in [obj.buyer, obj.seller]


class ReadOnly(permissions.BasePermission):
    """
    Allow only read-only access to the resource.
    """
    message = _('مسموح فقط بعمليات القراءة على هذا المورد.')

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


# Permission combinations for common use cases
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow owners to edit their objects,
    but allow read-only access to other authenticated users.
    """
    message = _('يمكن تعديل هذا العنصر فقط من قِبل المالك.')

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        owner_field = getattr(view, 'owner_field', 'owner')
        owner = getattr(obj, owner_field, None)

        return owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow full access to admin users, but only read access to others.
    """
    message = _('يتطلب تعديل هذا المورد صلاحيات المشرف.')

    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to admin users
        return request.user and request.user.is_authenticated and request.user.has_role(Role.ADMIN)
