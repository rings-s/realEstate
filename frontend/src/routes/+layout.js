// src/routes/+layout.js
import { redirect } from '@sveltejs/kit';
import { get } from 'svelte/store';
import { isAuthenticated, isVerified, token, user, fetchUserProfile } from '$lib/stores/auth';

// Define protected routes
const authRequiredRoutes = ['/profile', '/properties/add'];

const verificationRequiredRoutes = ['/properties/add'];

export const load = async ({ url, fetch }) => {
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
		if (!verified) {
			throw redirect(302, '/verify-email');
		}
	}

	// Load user data if authenticated but user data is missing
	if (authenticated && currentToken && (!currentUser || Object.keys(currentUser).length === 0)) {
		await fetchUserProfile();
	}

	return {
		authenticated,
		verified,
		currentPath: path
	};
};
