/**
 * Token Manager
 * Utility for managing JWT tokens and authentication state
 */

import { browser } from '$app/environment';
import { TOKEN_KEY, REFRESH_TOKEN_KEY, TOKEN_EXPIRY_KEY, USER_KEY } from '$lib/config/constants';
import { isAuthenticated, currentUser } from '$lib/stores/auth';

// Check if token exists
export const hasToken = () => {
	if (!browser) return false;
	return Boolean(localStorage.getItem(TOKEN_KEY));
};

// Get access token
export const getAccessToken = () => {
	if (!browser) return null;
	return localStorage.getItem(TOKEN_KEY);
};

// Get refresh token
export const getRefreshToken = () => {
	if (!browser) return null;
	return localStorage.getItem(REFRESH_TOKEN_KEY);
};

// Check if token is expired
export const isTokenExpired = () => {
	if (!browser) return true;

	const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
	if (!expiry) return true;

	try {
		const expiryDate = new Date(expiry);
		const now = new Date();
		return now >= expiryDate;
	} catch (error) {
		console.error('Error parsing token expiry date:', error);
		return true; // If we can't parse the date, consider the token expired
	}
};

// Set tokens in localStorage
export const setTokens = ({ access, refresh }) => {
	if (!browser) return;

	if (access) {
		localStorage.setItem(TOKEN_KEY, access);

		// Calculate token expiry (1 hour from now)
		const expiry = new Date();
		expiry.setHours(expiry.getHours() + 1);
		localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());
	}

	if (refresh) {
		localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
	}

	// Update authentication state
	isAuthenticated.set(true);
};

// Set user data
export const setUserData = (userData) => {
	if (!browser || !userData) return;

	try {
		localStorage.setItem(USER_KEY, JSON.stringify(userData));
		currentUser.set(userData);
	} catch (error) {
		console.error('Error storing user data:', error);
	}
};

// Get user data from localStorage
export const getUserData = () => {
	if (!browser) return null;

	try {
		const userData = localStorage.getItem(USER_KEY);
		return userData ? JSON.parse(userData) : null;
	} catch (error) {
		console.error('Error parsing user data:', error);
		return null;
	}
};

// Clear all tokens and user data
export const clearTokens = () => {
	if (!browser) return;

	localStorage.removeItem(TOKEN_KEY);
	localStorage.removeItem(REFRESH_TOKEN_KEY);
	localStorage.removeItem(TOKEN_EXPIRY_KEY);
	localStorage.removeItem(USER_KEY);

	// Update authentication state
	isAuthenticated.set(false);
	currentUser.set(null);
};

// Parse token payload
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
		console.error('Error parsing token:', error);
		return null;
	}
};

// Get token expiry time in seconds
export const getTokenExpiryTime = () => {
	if (!browser) return 0;

	const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
	if (!expiry) return 0;

	try {
		const expiryDate = new Date(expiry);
		const now = new Date();
		return Math.floor((expiryDate.getTime() - now.getTime()) / 1000);
	} catch (error) {
		console.error('Error calculating token expiry time:', error);
		return 0;
	}
};

export default {
	hasToken,
	getAccessToken,
	getRefreshToken,
	isTokenExpired,
	setTokens,
	setUserData,
	getUserData,
	clearTokens,
	parseToken,
	getTokenExpiryTime
};
