/**
 * API Utilities
 * Handles API requests with authentication and error handling
 */

import { browser } from '$app/environment';
import {
	getAccessToken,
	getRefreshToken,
	setTokens,
	clearTokens,
	isTokenExpired
} from './tokenManager';
import { goto } from '$app/navigation';
import { API_URL } from '$lib/config/api';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
	constructor(message, status, code, details = null) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.code = code;
		this.details = details;
	}
}

/**
 * Refresh the access token using the refresh token
 * @returns {Promise<boolean>} True if token refresh was successful
 */
export const refreshAccessToken = async () => {
	try {
		const refreshToken = getRefreshToken();
		if (!refreshToken) {
			throw new Error('No refresh token available');
		}

		const response = await fetch(`${API_URL}/accounts/token/refresh/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				refresh: refreshToken
			})
		});

		if (!response.ok) {
			throw new Error('Failed to refresh token');
		}

		const data = await response.json();

		// Use the tokenManager's setTokens function
		setTokens({
			access: data.access,
			refresh: refreshToken // Keep the same refresh token
		});

		// If isAuthenticated store is available, update it
		if (typeof isAuthenticated !== 'undefined' && isAuthenticated.set) {
			isAuthenticated.set(true);
		}

		return true;
	} catch (error) {
		console.error('Error refreshing token:', error);
		clearTokens();

		// If isAuthenticated store is available, update it
		if (typeof isAuthenticated !== 'undefined' && isAuthenticated.set) {
			isAuthenticated.set(false);
		}

		return false;
	}
};

/**
 * Process JSON fields to handle stringified JSON properly
 * @param {Object} data - The data object with potential JSON string fields
 * @returns {Object} Processed data with parsed JSON fields
 */
export const processJsonFields = (data) => {
	if (!data || typeof data !== 'object') return data;

	const result = { ...data };

	// Process common JSON fields from the backend
	const jsonFields = [
		'features',
		'amenities',
		'rooms',
		'specifications',
		'location',
		'pricing_details',
		'viewing_dates',
		'timeline',
		'bid_history',
		'financial_terms',
		'analytics',
		'document_metadata',
		'verification_details',
		'payment_details',
		'payments_history',
		'parties',
		'notification_data'
	];

	jsonFields.forEach((field) => {
		if (result[field] && typeof result[field] === 'string') {
			try {
				result[field] = JSON.parse(result[field]);
			} catch (e) {
				// Keep as string if parsing fails
				console.warn(`Failed to parse JSON field: ${field}`);
			}
		}
	});

	return result;
};

/**
 * Handle API response
 * @param {Response} response - Fetch Response object
 * @returns {Promise<Object>} Processed response data
 * @throws {ApiError} If response has an error status
 */
export const handleResponse = async (response) => {
	const contentType = response.headers.get('content-type');
	const isJson = contentType && contentType.includes('application/json');

	// Parse response body based on content type
	let data;
	if (isJson) {
		data = await response.json();
	} else {
		data = await response.text();
	}

	// If response is not ok, throw an error
	if (!response.ok) {
		let errorMessage = 'An error occurred';
		let errorCode = 'unknown_error';
		let errorDetails = null;

		if (isJson && data) {
			errorMessage = data.error || data.message || errorMessage;
			errorCode = data.code || errorCode;
			errorDetails = data.details || null;
		}

		throw new ApiError(errorMessage, response.status, errorCode, errorDetails);
	}

	// Process JSON fields in the response data
	if (isJson && data) {
		return processJsonFields(data);
	}

	return data;
};

/**
 * Make an API request with authentication and error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const apiRequest = async (endpoint, options = {}, secure = true) => {
	if (!browser) {
		// For SSR, you would need to implement special handling
		// or pass cookies from the request
		return null;
	}

	const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;
	const fetchOptions = { ...options };

	// Set default headers
	fetchOptions.headers = {
		'Content-Type': 'application/json',
		...fetchOptions.headers
	};

	// Add authorization header if request is secure
	if (secure) {
		try {
			// Check if token is expired
			if (isTokenExpired()) {
				console.log('Token expired, attempting refresh');
				// Try to refresh the token
				const refreshed = await refreshAccessToken();
				if (!refreshed) {
					console.log('Token refresh failed');
					// Redirect to login if token refresh failed
					clearTokens();
					if (browser && !window.location.pathname.includes('/auth/login')) {
						console.log('Redirecting to login due to auth failure');
						goto('/auth/login?redirect=' + encodeURIComponent(window.location.pathname));
					}
					throw new ApiError('Authentication required', 401, 'auth_required');
				}
				console.log('Token refreshed successfully');
			}

			const token = getAccessToken();
			if (token) {
				fetchOptions.headers['Authorization'] = `Bearer ${token}`;
			} else {
				console.log('No token available after refresh attempt');
				throw new ApiError('No authentication token available', 401, 'no_token');
			}
		} catch (error) {
			console.error('Auth error in API request:', error);
			throw new ApiError('Authentication error', 401, 'auth_error');
		}
	}

	try {
		const response = await fetch(url, fetchOptions);
		return await handleResponse(response);
	} catch (error) {
		if (error instanceof ApiError) {
			// Handle specific error codes
			if (error.status === 401 && secure) {
				console.log('401 response from API');
				// Try to refresh the token one last time
				const refreshed = await refreshAccessToken();
				if (!refreshed) {
					// Clear tokens and redirect to login for authentication errors
					clearTokens();
					if (browser && !window.location.pathname.includes('/auth/login')) {
						goto('/auth/login?redirect=' + encodeURIComponent(window.location.pathname));
					}
				} else {
					// Try the request again with the new token
					console.log('Retrying request after refresh');
					return apiRequest(endpoint, options, secure);
				}
			}
			throw error;
		}

		// Rethrow network or other errors
		throw new ApiError(error.message || 'Network error', 0, 'network_error');
	}
};

/**
 * Shorthand for GET requests
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const get = (endpoint, options = {}, secure = true) => {
	return apiRequest(endpoint, { ...options, method: 'GET' }, secure);
};

/**
 * Shorthand for POST requests
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body data
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const post = (endpoint, data, options = {}, secure = true) => {
	return apiRequest(
		endpoint,
		{
			...options,
			method: 'POST',
			body: JSON.stringify(data)
		},
		secure
	);
};

/**
 * Shorthand for PUT requests
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body data
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const put = (endpoint, data, options = {}, secure = true) => {
	return apiRequest(
		endpoint,
		{
			...options,
			method: 'PUT',
			body: JSON.stringify(data)
		},
		secure
	);
};

/**
 * Shorthand for PATCH requests
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body data
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const patch = (endpoint, data, options = {}, secure = true) => {
	return apiRequest(
		endpoint,
		{
			...options,
			method: 'PATCH',
			body: JSON.stringify(data)
		},
		secure
	);
};

/**
 * Shorthand for DELETE requests
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const del = (endpoint, options = {}, secure = true) => {
	return apiRequest(
		endpoint,
		{
			...options,
			method: 'DELETE'
		},
		secure
	);
};

/**
 * Upload files with form data
 * @param {string} endpoint - API endpoint
 * @param {FormData} formData - Form data with files
 * @param {Object} options - Additional fetch options
 * @param {boolean} secure - Whether the request needs authentication
 * @returns {Promise<Object>} Response data
 */
export const uploadFiles = (endpoint, formData, options = {}, secure = true) => {
	return apiRequest(
		endpoint,
		{
			...options,
			method: 'POST',
			body: formData,
			headers: {
				// Don't set Content-Type, let the browser set it with the boundary
				...options.headers
			}
		},
		secure
	);
};
