/**
 * Permission utilities for role-based access control
 */
import { get } from 'svelte/store';
import { auth, roles } from '$lib/stores/auth';

// Role constants
export const ROLES = {
	ADMIN: 'admin',
	SELLER: 'seller',
	BUYER: 'buyer',
	AGENT: 'agent',
	INSPECTOR: 'inspector',
	LEGAL: 'legal'
};

/**
 * Permission constants - each represents a specific action
 * These are used to create a more granular permissions system
 */
export const PERMISSIONS = {
	// Property permissions
	VIEW_PROPERTIES: 'view_properties',
	CREATE_PROPERTY: 'create_property',
	EDIT_PROPERTY: 'edit_property',
	VERIFY_PROPERTY: 'verify_property',

	// Auction permissions
	VIEW_AUCTIONS: 'view_auctions',
	CREATE_AUCTION: 'create_auction',
	EDIT_AUCTION: 'edit_auction',
	CLOSE_AUCTION: 'close_auction',
	EXTEND_AUCTION: 'extend_auction',

	// Bid permissions
	PLACE_BID: 'place_bid',
	VIEW_BIDS: 'view_bids',
	MARK_WINNING_BID: 'mark_winning_bid',

	// Document permissions
	UPLOAD_DOCUMENT: 'upload_document',
	VERIFY_DOCUMENT: 'verify_document',

	// Contract permissions
	CREATE_CONTRACT: 'create_contract',
	SIGN_CONTRACT: 'sign_contract',

	// Payment permissions
	MAKE_PAYMENT: 'make_payment',
	CONFIRM_PAYMENT: 'confirm_payment',

	// User management
	MANAGE_USERS: 'manage_users',
	ASSIGN_ROLES: 'assign_roles'
};

/**
 * Map of roles to their permissions
 */
const ROLE_PERMISSIONS = {
	[ROLES.ADMIN]: Object.values(PERMISSIONS),

	[ROLES.SELLER]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.CREATE_PROPERTY,
		PERMISSIONS.EDIT_PROPERTY,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.CREATE_AUCTION,
		PERMISSIONS.VIEW_BIDS,
		PERMISSIONS.UPLOAD_DOCUMENT,
		PERMISSIONS.SIGN_CONTRACT
	],

	[ROLES.BUYER]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.PLACE_BID,
		PERMISSIONS.VIEW_BIDS,
		PERMISSIONS.UPLOAD_DOCUMENT,
		PERMISSIONS.SIGN_CONTRACT,
		PERMISSIONS.MAKE_PAYMENT
	],

	[ROLES.AGENT]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.CREATE_PROPERTY,
		PERMISSIONS.EDIT_PROPERTY,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.CREATE_AUCTION,
		PERMISSIONS.EDIT_AUCTION,
		PERMISSIONS.CLOSE_AUCTION,
		PERMISSIONS.EXTEND_AUCTION,
		PERMISSIONS.VIEW_BIDS,
		PERMISSIONS.MARK_WINNING_BID,
		PERMISSIONS.CREATE_CONTRACT,
		PERMISSIONS.SIGN_CONTRACT,
		PERMISSIONS.CONFIRM_PAYMENT
	],

	[ROLES.INSPECTOR]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.VERIFY_PROPERTY,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.UPLOAD_DOCUMENT,
		PERMISSIONS.VERIFY_DOCUMENT
	],

	[ROLES.LEGAL]: [
		PERMISSIONS.VIEW_PROPERTIES,
		PERMISSIONS.VIEW_AUCTIONS,
		PERMISSIONS.UPLOAD_DOCUMENT,
		PERMISSIONS.VERIFY_DOCUMENT,
		PERMISSIONS.CREATE_CONTRACT
	]
};

/**
 * Check if the current user has a specific role
 * @param {string} role - Role to check
 * @returns {boolean} True if user has the role
 */
export const hasRole = (role) => {
	const userRoles = get(roles);
	return userRoles.includes(role);
};

/**
 * Check if the current user has any of the specified roles
 * @param {string[]} requiredRoles - Array of roles to check
 * @returns {boolean} True if user has any of the roles
 */
export const hasAnyRole = (requiredRoles) => {
	const userRoles = get(roles);
	return requiredRoles.some((role) => userRoles.includes(role));
};

/**
 * Check if the current user has all of the specified roles
 * @param {string[]} requiredRoles - Array of roles to check
 * @returns {boolean} True if user has all of the roles
 */
export const hasAllRoles = (requiredRoles) => {
	const userRoles = get(roles);
	return requiredRoles.every((role) => userRoles.includes(role));
};

/**
 * Check if the current user has a specific permission
 * @param {string} permission - Permission to check
 * @returns {boolean} True if user has the permission
 */
export const hasPermission = (permission) => {
	const userRoles = get(roles);

	// Admin has all permissions
	if (userRoles.includes(ROLES.ADMIN)) {
		return true;
	}

	// Check if any of the user's roles grant this permission
	return userRoles.some(
		(role) => ROLE_PERMISSIONS[role] && ROLE_PERMISSIONS[role].includes(permission)
	);
};

/**
 * Check if the current user has all of the specified permissions
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} True if user has all of the permissions
 */
export const hasAllPermissions = (permissions) => {
	return permissions.every((permission) => hasPermission(permission));
};

/**
 * Check if the current user has any of the specified permissions
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} True if user has any of the permissions
 */
export const hasAnyPermission = (permissions) => {
	return permissions.some((permission) => hasPermission(permission));
};

/**
 * Check if the current user can perform a specific action on an entity
 * @param {string} action - Action to check (e.g., 'edit', 'delete')
 * @param {Object} entity - Entity to check
 * @param {string} entityType - Type of entity (e.g., 'property', 'auction')
 * @returns {boolean} True if user can perform the action
 */
export const canPerformAction = (action, entity, entityType) => {
	if (!entity) return false;

	const userAuth = get(auth);
	if (!userAuth.isAuthenticated) return false;

	const user = userAuth.user;
	const userRoles = get(roles);

	// Admin can do anything
	if (userRoles.includes(ROLES.ADMIN)) {
		return true;
	}

	// Entity-specific permissions
	switch (entityType) {
		case 'property':
			// Property owner can edit their own properties
			if (action === 'edit' && entity.owner === user.id) {
				return true;
			}

			// Inspectors can verify properties
			if (action === 'verify' && userRoles.includes(ROLES.INSPECTOR)) {
				return true;
			}
			break;

		case 'auction':
			// Creator or auctioneer can edit/close/extend their own auctions
			if (
				['edit', 'close', 'extend'].includes(action) &&
				(entity.created_by === user.id || entity.auctioneer === user.id)
			) {
				return true;
			}
			break;

		case 'bid':
			// Users can only see their own bids in detail
			if (action === 'view' && entity.bidder === user.id) {
				return true;
			}

			// Auction creator or auctioneer can mark winning bid
			if (
				action === 'mark_winning' &&
				(entity.auction.created_by === user.id || entity.auction.auctioneer === user.id)
			) {
				return true;
			}
			break;

		case 'contract':
			// Contract parties can view and sign their contracts
			if (
				['view', 'sign'].includes(action) &&
				(entity.buyer === user.id || entity.seller === user.id || entity.agent === user.id)
			) {
				return true;
			}
			break;

		case 'document':
			// Document uploader can edit their documents
			if (action === 'edit' && entity.uploaded_by === user.id) {
				return true;
			}

			// Legal and inspector roles can verify documents
			if (
				action === 'verify' &&
				(userRoles.includes(ROLES.LEGAL) || userRoles.includes(ROLES.INSPECTOR))
			) {
				return true;
			}
			break;

		default:
			return false;
	}

	// Check role-based permissions for the action
	return hasPermission(getPermissionForAction(action, entityType));
};

/**
 * Get the permission key for a specific action on an entity type
 * @param {string} action - Action to check (e.g., 'edit', 'delete')
 * @param {string} entityType - Type of entity (e.g., 'property', 'auction')
 * @returns {string} Permission key
 */
export const getPermissionForAction = (action, entityType) => {
	const permissionMap = {
		property: {
			view: PERMISSIONS.VIEW_PROPERTIES,
			create: PERMISSIONS.CREATE_PROPERTY,
			edit: PERMISSIONS.EDIT_PROPERTY,
			verify: PERMISSIONS.VERIFY_PROPERTY
		},
		auction: {
			view: PERMISSIONS.VIEW_AUCTIONS,
			create: PERMISSIONS.CREATE_AUCTION,
			edit: PERMISSIONS.EDIT_AUCTION,
			close: PERMISSIONS.CLOSE_AUCTION,
			extend: PERMISSIONS.EXTEND_AUCTION
		},
		bid: {
			view: PERMISSIONS.VIEW_BIDS,
			create: PERMISSIONS.PLACE_BID,
			mark_winning: PERMISSIONS.MARK_WINNING_BID
		},
		document: {
			upload: PERMISSIONS.UPLOAD_DOCUMENT,
			verify: PERMISSIONS.VERIFY_DOCUMENT
		},
		contract: {
			create: PERMISSIONS.CREATE_CONTRACT,
			sign: PERMISSIONS.SIGN_CONTRACT
		},
		payment: {
			make: PERMISSIONS.MAKE_PAYMENT,
			confirm: PERMISSIONS.CONFIRM_PAYMENT
		}
	};

	return permissionMap[entityType]?.[action] || '';
};

/**
 * Filter a list of elements based on user permissions
 * @param {Array} items - List of items to filter
 * @param {Function} permissionCheck - Function to check permission for each item
 * @returns {Array} Filtered list
 */
export const filterByPermission = (items, permissionCheck) => {
	if (!items) return [];
	return items.filter((item) => permissionCheck(item));
};

/**
 * Get an array of all role objects with their permissions
 * @returns {Array} Array of role objects
 */
export const getAllRolesWithPermissions = () => {
	return Object.keys(ROLES).map((roleKey) => ({
		id: ROLES[roleKey],
		name: getRoleDisplayName(ROLES[roleKey]),
		permissions: ROLE_PERMISSIONS[ROLES[roleKey]] || []
	}));
};

/**
 * Get the Arabic display name for a role
 * @param {string} role - Role key
 * @returns {string} Role display name
 */
export const getRoleDisplayName = (role) => {
	const roleMap = {
		[ROLES.ADMIN]: 'مدير النظام',
		[ROLES.SELLER]: 'بائع',
		[ROLES.BUYER]: 'مشتري',
		[ROLES.AGENT]: 'وكيل عقاري',
		[ROLES.INSPECTOR]: 'مفتش',
		[ROLES.LEGAL]: 'مستشار قانوني'
	};

	return roleMap[role] || role;
};

export default {
	ROLES,
	PERMISSIONS,
	hasRole,
	hasAnyRole,
	hasAllRoles,
	hasPermission,
	hasAllPermissions,
	hasAnyPermission,
	canPerformAction,
	filterByPermission,
	getAllRolesWithPermissions,
	getRoleDisplayName
};
