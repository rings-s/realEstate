/**
 * API Configuration
 */

// Base API URL
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// API Endpoints
export const ENDPOINTS = {
	// Auth endpoints
	AUTH: {
		REGISTER: '/accounts/register/',
		LOGIN: '/accounts/login/',
		LOGOUT: '/accounts/logout/',
		VERIFY_EMAIL: '/accounts/verify-email/',
		RESEND_VERIFICATION: '/accounts/resend-verification/',
		REFRESH_TOKEN: '/accounts/token/refresh/',
		VERIFY_TOKEN: '/accounts/token/verify/',
		RESET_PASSWORD: '/accounts/password/reset/confirm/',
		REQUEST_RESET: '/accounts/password/reset/',
		VERIFY_RESET_CODE: '/accounts/password/reset/verify/',
		CHANGE_PASSWORD: '/accounts/password/'
	},

	// User endpoints
	USER: {
		PROFILE: '/accounts/profile/',
		PUBLIC_PROFILE: (userId) => `/accounts/profile/${userId}/`,
		UPDATE_AVATAR: '/accounts/profile/avatar/',
		ASSIGN_ROLE: (userId) => `/accounts/roles/assign/${userId}/`,
		ROLE_DASHBOARD: '/accounts/dashboard/role/'
	},

	// Property endpoints
	PROPERTY: {
		LIST: '/api/properties/',
		DETAIL: (slug) => `/api/properties/${slug}/`,
		CREATE: '/api/properties/',
		UPDATE: (slug) => `/api/properties/${slug}/edit/`,
		DELETE: (slug) => `/api/properties/${slug}/delete/`,
		IMAGES: (propertyId) => `/api/properties/${propertyId}/images/`,
		IMAGE_DETAIL: (imageId) => `/api/property-images/${imageId}/`,
		IMAGE_UPDATE: (imageId) => `/api/property-images/${imageId}/edit/`,
		IMAGE_DELETE: (imageId) => `/api/property-images/${imageId}/delete/`
	},

	// Auction endpoints
	AUCTION: {
		LIST: '/api/auctions/',
		DETAIL: (slug) => `/api/auctions/${slug}/`,
		CREATE: '/api/auctions/',
		UPDATE: (slug) => `/api/auctions/${slug}/edit/`,
		DELETE: (slug) => `/api/auctions/${slug}/delete/`,
		IMAGES: (auctionId) => `/api/auctions/${auctionId}/images/`,
		IMAGE_DETAIL: (imageId) => `/api/auction-images/${imageId}/`,
		IMAGE_UPDATE: (imageId) => `/api/auction-images/${imageId}/edit/`,
		IMAGE_DELETE: (imageId) => `/api/auction-images/${imageId}/delete/`,
		PROPERTY_VIEWS: (auctionId) => `/api/auctions/${auctionId}/property-views/`
	},

	// Bid endpoints
	BID: {
		LIST: (auctionId) => `/api/auctions/${auctionId}/bids/`,
		DETAIL: (bidId) => `/api/bids/${bidId}/`,
		CREATE: (auctionId) => `/api/auctions/${auctionId}/bids/`,
		UPDATE: (bidId) => `/api/bids/${bidId}/edit/`,
		DELETE: (bidId) => `/api/bids/${bidId}/delete/`,
		SUGGESTIONS: (auctionId) => `/api/auctions/${auctionId}/bid-suggestions/`
	},

	// Document endpoints
	DOCUMENT: {
		LIST: '/api/documents/',
		DETAIL: (documentId) => `/api/documents/${documentId}/`,
		CREATE: '/api/documents/',
		UPDATE: (documentId) => `/api/documents/${documentId}/edit/`,
		DELETE: (documentId) => `/api/documents/${documentId}/delete/`
	},

	// Contract endpoints
	CONTRACT: {
		LIST: '/api/contracts/',
		DETAIL: (contractId) => `/api/contracts/${contractId}/`,
		CREATE: '/api/contracts/',
		UPDATE: (contractId) => `/api/contracts/${contractId}/edit/`,
		DELETE: (contractId) => `/api/contracts/${contractId}/delete/`
	},

	// Message endpoints
	MESSAGE: {
		THREADS: '/api/threads/',
		THREAD_DETAIL: (threadId) => `/api/threads/${threadId}/`,
		THREAD_UPDATE: (threadId) => `/api/threads/${threadId}/edit/`,
		THREAD_DELETE: (threadId) => `/api/threads/${threadId}/delete/`,
		THREAD_PARTICIPANTS: (threadId) => `/api/threads/${threadId}/participants/`,
		PARTICIPANT_DETAIL: (participantId) => `/api/thread-participants/${participantId}/`,
		PARTICIPANT_UPDATE: (participantId) => `/api/thread-participants/${participantId}/edit/`,
		PARTICIPANT_DELETE: (participantId) => `/api/thread-participants/${participantId}/delete/`,
		MESSAGES: (threadId) => `/api/threads/${threadId}/messages/`,
		MESSAGE_DETAIL: (messageId) => `/api/messages/${messageId}/`,
		MESSAGE_UPDATE: (messageId) => `/api/messages/${messageId}/edit/`,
		MESSAGE_DELETE: (messageId) => `/api/messages/${messageId}/delete/`
	},

	// Notification endpoints
	NOTIFICATION: {
		LIST: '/api/notifications/',
		DETAIL: (notificationId) => `/api/notifications/${notificationId}/`,
		UPDATE: (notificationId) => `/api/notifications/${notificationId}/edit/`,
		DELETE: (notificationId) => `/api/notifications/${notificationId}/delete/`
	}
};

// API Response Status Codes
export const STATUS_CODES = {
	OK: 200,
	CREATED: 201,
	BAD_REQUEST: 400,
	UNAUTHORIZED: 401,
	FORBIDDEN: 403,
	NOT_FOUND: 404,
	CONFLICT: 409,
	INTERNAL_SERVER_ERROR: 500
};

// API Error Codes
export const ERROR_CODES = {
	VALIDATION_ERROR: 'validation_error',
	INVALID_CREDENTIALS: 'invalid_credentials',
	UNAUTHORIZED: 'unauthorized',
	PERMISSION_DENIED: 'permission_denied',
	NOT_FOUND: 'not_found',
	ALREADY_EXISTS: 'already_exists',
	EXPIRED_TOKEN: 'expired_token',
	INVALID_TOKEN: 'invalid_token',
	SERVER_ERROR: 'server_error'
};
