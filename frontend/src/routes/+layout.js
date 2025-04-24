// src/routes/+layout.js
import { redirect } from '@sveltejs/kit';
import { get } from 'svelte/store';
import {
	isAuthenticated,
	isVerified,
	token,
	user,
	fetchUserProfile,
	logout
} from '$lib/stores/auth';

// Define protected routes
const authRequiredRoutes = ['/profile', '/properties/add', '/auctions/add', '/messages'];
const verificationRequiredRoutes = ['/properties/add', '/auctions/add'];

export const load = async ({ url, fetch, depends }) => {
	// Dependency for authentication state
	depends('auth:status');

	// Get current authentication state
	const authenticated = get(isAuthenticated);
	const verified = get(isVerified);
	const currentToken = get(token);
	const currentUser = get(user);

	const path = url.pathname;

	// For protected routes
	if (authRequiredRoutes.some((route) => path.startsWith(route))) {
		if (!authenticated) {
			throw redirect(302, `/login?redirect=${encodeURIComponent(path)}`);
		}
	}

	// For routes requiring verification
	if (verificationRequiredRoutes.some((route) => path.startsWith(route))) {
		if (authenticated && !verified) {
			throw redirect(302, '/verify-email');
		}
	}

	// Load user profile if authenticated but no user data
	if (authenticated && currentToken && (!currentUser || Object.keys(currentUser).length === 0)) {
		try {
			await fetchUserProfile();
		} catch (error) {
			console.error('Failed to fetch user profile:', error);
			// If profile fetch failed due to authentication issues, reset token
			if (
				error.message &&
				(error.message.includes('401') || error.message.includes('انتهت صلاحية'))
			) {
				logout();
				throw redirect(302, `/login?redirect=${encodeURIComponent(path)}`);
			}
		}
	}

	return {
		authenticated,
		verified,
		currentPath: path
	};
};
