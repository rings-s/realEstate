/**
 * Token Manager
 * Handles JWT token storage, retrieval, and validation
 */

import { browser } from '$app/environment';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const TOKEN_EXPIRY_KEY = 'token_expiry';

/**
 * Set tokens in localStorage (or sessionStorage for more security)
 * @param {Object} tokens - Object containing access and refresh tokens
 * @param {string} tokens.access - Access token
 * @param {string} tokens.refresh - Refresh token
 */
export const setTokens = (tokens) => {
	if (!browser) return;

	const { access, refresh } = tokens;

	// Store tokens
	localStorage.setItem(ACCESS_TOKEN_KEY, access);
	localStorage.setItem(REFRESH_TOKEN_KEY, refresh);

	// Calculate expiry time (typically 1 hour from now for access token)
	// Decode token to get actual expiry if needed
	const expiry = new Date();
	expiry.setHours(expiry.getHours() + 1); // Default to 1 hour

	localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());
};

/**
 * Get the access token from storage
 * @returns {string|null} The access token or null if not found
 */
export const getAccessToken = () => {
	if (!browser) return null;
	return localStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * Get the refresh token from storage
 * @returns {string|null} The refresh token or null if not found
 */
export const getRefreshToken = () => {
	if (!browser) return null;
	return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Check if the access token has expired
 * @returns {boolean} True if token has expired, false otherwise
 */
export const isTokenExpired = () => {
	if (!browser) return true;

	const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
	if (!expiry) return true;

	const expiryDate = new Date(expiry);
	const now = new Date();

	return now >= expiryDate;
};

/**
 * Check if user is authenticated (has valid tokens)
 * @returns {boolean} True if authenticated, false otherwise
 */
export const isAuthenticated = () => {
	if (!browser) return false;

	const accessToken = getAccessToken();
	return !!accessToken && !isTokenExpired();
};

/**
 * Clear all authentication tokens from storage
 */
export const clearTokens = () => {
	if (!browser) return;

	localStorage.removeItem(ACCESS_TOKEN_KEY);
	localStorage.removeItem(REFRESH_TOKEN_KEY);
	localStorage.removeItem(TOKEN_EXPIRY_KEY);
};

/**
 * Parse JWT token to get payload
 * @param {string} token - JWT token
 * @returns {Object|null} Decoded token payload or null if invalid
 */
export const parseToken = (token) => {
	if (!token) return null;

	try {
		const base64Url = token.split('.')[1];
		const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
		const jsonPayload = decodeURIComponent(
			atob(base64)
				.split('')
				.map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
				.join('')
		);

		return JSON.parse(jsonPayload);
	} catch (error) {
		console.error('Failed to parse token:', error);
		return null;
	}
};

/**
 * Get user information from the stored token
 * @returns {Object|null} User information or null if not authenticated
 */
export const getUserFromToken = () => {
	const token = getAccessToken();
	if (!token) return null;

	const payload = parseToken(token);
	if (!payload) return null;

	return {
		id: payload.user_id,
		email: payload.email,
		roles: payload.roles || []
	};
};
