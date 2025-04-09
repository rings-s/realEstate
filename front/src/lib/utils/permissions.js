/**
 * Permissions Utility
 * Handles role-based access control for the application
 */

// Role definitions
export const ROLES = {
	ADMIN: 'admin',
	SELLER: 'seller',
	BUYER: 'buyer',
	INSPECTOR: 'inspector',
	LEGAL: 'legal',
	AGENT: 'agent',
	APPRAISER: 'appraiser'
};

// Role display names
export const ROLE_NAMES = {
	[ROLES.ADMIN]: 'Admin',
	[ROLES.SELLER]: 'Seller',
	[ROLES.BUYER]: 'Buyer',
	[ROLES.INSPECTOR]: 'Inspector',
	[ROLES.LEGAL]: 'Legal Representative',
	[ROLES.AGENT]: 'Real Estate Agent',
	[ROLES.APPRAISER]: 'Appraiser'
};

// Permission definitions
export const PERMISSIONS = {
	// User management
	MANAGE_USERS: 'can_manage_users',
	MANAGE_ROLES: 'can_manage_roles',

	// Property permissions
	VIEW_PROPERTIES: 'can_view_properties',
	CREATE_PROPERTY: 'can_create_property',
	EDIT_OWN_PROPERTY: 'can_edit_own_property',
	EDIT_ANY_PROPERTY: 'can_edit_any_property',
	DELETE_OWN_PROPERTY: 'can_delete_own_property',
	DELETE_ANY_PROPERTY: 'can_delete_any_property',

	// Auction permissions
	VIEW_AUCTIONS: 'can_view_auctions',
	CREATE_AUCTION: 'can_create_auction',
	MANAGE_OWN_AUCTIONS: 'can_manage_own_auctions',
	MANAGE_ANY_AUCTION: 'can_manage_any_auction',
	PLACE_BID: 'can_place_bid',

	// Document permissions
	UPLOAD_DOCUMENTS: 'can_upload_documents',
	VERIFY_DOCUMENTS: 'can_verify_documents',

	// Contract permissions
	CREATE_CONTRACT: 'can_create_contract',
	MANAGE_OWN_CONTRACTS: 'can_manage_own_contracts',
	MANAGE_ANY_CONTRACT: 'can_manage_any_contract',
	REVIEW_CONTRACTS: 'can_review_contracts',

	// Inspection permissions
	INSPECT_PROPERTIES: 'can_inspect_properties',
	CREATE_INSPECTION_REPORTS: 'can_create_inspection_reports',

	// Analytics permissions
	VIEW_OWN_ANALYTICS: 'can_view_own_analytics',
	VIEW_ANY_ANALYTICS: 'can_view_any_analytics',

	// System permissions
	MANAGE_SYSTEM: 'can_manage_system'
};

// Map of role-based permissions
export const ROLE_PERMISSIONS = {
	// Admin has all permissions
	[ROLES.ADMIN]: Object.values(PERMISSIONS),

	// Seller permissions
	[ROLES.SELLER]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.CREATE_PROPERTY,
		PERMISSIONS.EDIT_OWN_PROPERTY,
		PERMISSIONS.DELETE_OWN_PROPERTY,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.CREATE_AUCTION,
		PERMISSIONS.MANAGE_OWN_AUCTIONS,
		PERMISSIONS.UPLOAD_DOCUMENTS,
		PERMISSIONS.MANAGE_OWN_CONTRACTS,
		PERMISSIONS.VIEW_OWN_ANALYTICS
	],

	// Buyer permissions
	[ROLES.BUYER]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.PLACE_BID,
		PERMISSIONS.MANAGE_OWN_CONTRACTS,
		PERMISSIONS.VIEW_OWN_ANALYTICS
	],

	// Inspector permissions
	[ROLES.INSPECTOR]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.INSPECT_PROPERTIES,
		PERMISSIONS.CREATE_INSPECTION_REPORTS,
		PERMISSIONS.VERIFY_DOCUMENTS
	],

	// Legal representative permissions
	[ROLES.LEGAL]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.VERIFY_DOCUMENTS,
		PERMISSIONS.REVIEW_CONTRACTS,
		PERMISSIONS.MANAGE_OWN_CONTRACTS
	],

	// Real estate agent permissions
	[ROLES.AGENT]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.CREATE_PROPERTY,
		PERMISSIONS.EDIT_OWN_PROPERTY,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.CREATE_AUCTION,
		PERMISSIONS.MANAGE_OWN_AUCTIONS,
		PERMISSIONS.UPLOAD_DOCUMENTS,
		PERMISSIONS.MANAGE_OWN_CONTRACTS,
		PERMISSIONS.VIEW_OWN_ANALYTICS
	],

	// Appraiser permissions
	[ROLES.APPRAISER]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.INSPECT_PROPERTIES,
		PERMISSIONS.UPLOAD_DOCUMENTS
	]
};

/**
 * Check if user has permission based on their roles
 * @param {Array} userRoles - User's roles
 * @param {string} permission - Permission to check
 * @returns {boolean} True if user has permission
 */
export const hasPermission = (userRoles, permission) => {
	// Admin has all permissions
	if (userRoles.includes(ROLES.ADMIN)) {
		return true;
	}

	// Check each role the user has
	for (const role of userRoles) {
		const rolePermissions = ROLE_PERMISSIONS[role] || [];
		if (rolePermissions.includes(permission)) {
			return true;
		}
	}

	return false;
};

/**
 * Check if user has any of the specified permissions
 * @param {Array} userRoles - User's roles
 * @param {Array} permissions - Permissions to check
 * @returns {boolean} True if user has any of the permissions
 */
export const hasAnyPermission = (userRoles, permissions) => {
	return permissions.some((permission) => hasPermission(userRoles, permission));
};

/**
 * Check if user has all of the specified permissions
 * @param {Array} userRoles - User's roles
 * @param {Array} permissions - Permissions to check
 * @returns {boolean} True if user has all of the permissions
 */
export const hasAllPermissions = (userRoles, permissions) => {
	return permissions.every((permission) => hasPermission(userRoles, permission));
};

/**
 * Check if user is owner of a resource
 * @param {Object} user - Current user
 * @param {Object} resource - Resource to check
 * @param {string} ownerField - Field name to check for ownership
 * @returns {boolean} True if user is owner
 */
export const isOwner = (user, resource, ownerField = 'owner') => {
	if (!user || !resource) return false;

	// Check if resource has owner ID
	if (resource[`${ownerField}_id`]) {
		return user.id === resource[`${ownerField}_id`];
	}

	// Check if resource has owner object
	if (resource[ownerField] && resource[ownerField].id) {
		return user.id === resource[ownerField].id;
	}

	return false;
};

/**
 * Check if user can access a resource
 * @param {Object} user - Current user
 * @param {Array} userRoles - User's roles
 * @param {Object} resource - Resource to check
 * @param {string} permission - Permission required for non-owners
 * @param {string} ownerField - Field name to check for ownership
 * @returns {boolean} True if user can access the resource
 */
export const canAccessResource = (user, userRoles, resource, permission, ownerField = 'owner') => {
	// Admin can access any resource
	if (userRoles.includes(ROLES.ADMIN)) {
		return true;
	}

	// Check if user is the owner
	if (isOwner(user, resource, ownerField)) {
		return true;
	}

	// Check if user has the required permission
	return hasPermission(userRoles, permission);
};
