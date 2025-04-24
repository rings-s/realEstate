// src/lib/stores/auth.js
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import api from '$lib/services/api';

// Initialize stores with localStorage values if in browser
export const token = writable((browser && localStorage.getItem('token')) || null);
export const refreshToken = writable((browser && localStorage.getItem('refreshToken')) || null);
export const user = writable(browser && JSON.parse(localStorage.getItem('user') || 'null'));

// Derived store for verification status
export const isAuthenticated = derived(token, ($token) => !!$token);
export const isVerified = derived(user, ($user) => !!$user?.is_verified);
export const isAdmin = derived(user, ($user) => !!$user?.is_staff);

// Persist store changes to localStorage
if (browser) {
	token.subscribe((value) => {
		if (value) localStorage.setItem('token', value);
		else localStorage.removeItem('token');
	});

	refreshToken.subscribe((value) => {
		if (value) localStorage.setItem('refreshToken', value);
		else localStorage.removeItem('refreshToken');
	});

	user.subscribe((value) => {
		if (value) localStorage.setItem('user', JSON.stringify(value));
		else localStorage.removeItem('user');
	});
}

export async function register(userData) {
	try {
		const response = await api.post('/accounts/register/', userData);
		return { success: true, email: userData.email, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function verifyEmail(email, verification_code) {
	try {
		const response = await api.post('/accounts/verify-email/', { email, verification_code });

		if (response.data?.tokens && response.data?.user) {
			token.set(response.data.tokens.access);
			refreshToken.set(response.data.tokens.refresh);
			user.set(response.data.user);
			return { success: true };
		}

		return { success: false, error: 'بيانات غير كاملة' };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function login(email, password) {
	try {
		const response = await api.post('/accounts/login/', { email, password });

		if (response.data?.tokens && response.data?.user) {
			token.set(response.data.tokens.access);
			refreshToken.set(response.data.tokens.refresh);
			user.set(response.data.user);
			return { success: true };
		}

		return { success: false, error: 'بيانات غير كاملة' };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function logout() {
	try {
		const currentRefreshToken = get(refreshToken);

		if (currentRefreshToken) {
			try {
				// Try to blacklist the token on server
				await api.post('/accounts/logout/', { refresh: currentRefreshToken });
			} catch (err) {
				console.error('Server logout error:', err);
				// Continue with client-side logout even if server logout fails
			}
		}
	} catch (error) {
		console.error('Error during logout:', error);
	} finally {
		// Always clear stores regardless of server response
		token.set(null);
		refreshToken.set(null);
		user.set(null);

		// Navigate to login page
		if (browser) {
			window.location.href = '/login';
		}
	}
}

export async function resetPasswordRequest(email) {
	try {
		const response = await api.post('/accounts/request-reset/', { email });
		return { success: true, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function verifyResetCode(email, reset_code) {
	try {
		const response = await api.post('/accounts/verify-reset-code/', { email, reset_code });
		return { success: true, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function resetPassword(email, reset_code, new_password, confirm_password) {
	try {
		const response = await api.post('/accounts/reset-password/', {
			email,
			reset_code,
			new_password,
			confirm_password
		});

		if (response.data?.tokens && response.data?.user) {
			token.set(response.data.tokens.access);
			refreshToken.set(response.data.tokens.refresh);
			user.set(response.data.user);
		}

		return { success: true, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function changePassword(current_password, new_password, confirm_password) {
	try {
		const response = await api.post('/accounts/change-password/', {
			current_password,
			new_password,
			confirm_password
		});

		if (response.data?.tokens) {
			token.set(response.data.tokens.access);
			refreshToken.set(response.data.tokens.refresh);
		}

		return { success: true, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function fetchUserProfile() {
	try {
		const response = await api.get('/accounts/profile/');

		if (response.data?.user) {
			user.set(response.data.user);
			return response.data.user;
		}

		return null;
	} catch (error) {
		console.error('Error fetching user profile:', error);
		return null;
	}
}

export async function updateUserProfile(profileData) {
	try {
		const response = await api.patch('/accounts/profile/', profileData);

		if (response.data?.user) {
			user.set(response.data.user);
			return { success: true, data: response.data.user };
		}

		return { success: false, error: 'بيانات غير كاملة' };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function updateAvatar(formData) {
	try {
		const response = await api.uploadFile('/accounts/update-avatar/', formData);

		if (response.data?.user) {
			user.set(response.data.user);
			return { success: true };
		}

		return { success: false, error: 'فشل في تحديث الصورة' };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

export async function resendVerification(email) {
	try {
		const response = await api.post('/accounts/resend-verification/', { email });
		return { success: true, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}
