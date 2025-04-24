// src/lib/stores/auth.js
import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';

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

/**
 * Register a new user
 */
export async function register(userData) {
	try {
		const response = await api.post('/accounts/register/', userData);
		return { success: true, email: userData.email, message: response.message };
	} catch (error) {
		return { success: false, error: error.message };
	}
}

/**
 * Verify email with verification code
 */
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

/**
 * Login user with email and password
 */
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

/**
 * Logout user and clear credentials
 */
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
			goto('/login');
		}
	}
}

/**
 * Request a password reset code
 */
export async function resetPasswordRequest(email) {
	try {
		// Use the correct API endpoint from your backend urls.py
		const response = await api.post('/accounts/password/reset/request/', { email });
		return {
			success: true,
			message: response.message || 'تم إرسال رمز إعادة التعيين إلى بريدك الإلكتروني'
		};
	} catch (error) {
		// Show a user-friendly error but log the actual error
		console.error('Password reset request error:', error);
		return {
			success: false,
			error: error.message || 'حدث خطأ أثناء إرسال طلب إعادة تعيين كلمة المرور'
		};
	}
}

/**
 * Verify a password reset code
 */
export async function verifyResetCode(email, reset_code) {
	try {
		const response = await api.post('/accounts/password/reset/verify/', { email, reset_code });
		return { success: true, message: response.message || 'تم التحقق من الرمز بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'رمز غير صالح أو منتهي الصلاحية' };
	}
}

/**
 * Reset password with code
 */
export async function resetPassword(email, reset_code, new_password, confirm_password) {
	try {
		const response = await api.post('/accounts/password/reset/confirm/', {
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

		return { success: true, message: response.message || 'تم إعادة تعيين كلمة المرور بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في إعادة تعيين كلمة المرور' };
	}
}

/**
 * Change password for authenticated user
 */
export async function changePassword(current_password, new_password, confirm_password) {
	try {
		const response = await api.post('/accounts/password/change/', {
			current_password,
			new_password,
			confirm_password
		});

		if (response.data?.tokens) {
			token.set(response.data.tokens.access);
			refreshToken.set(response.data.tokens.refresh);
		}

		return { success: true, message: response.message || 'تم تغيير كلمة المرور بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في تغيير كلمة المرور' };
	}
}

/**
 * Fetch current user profile
 */
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

		// If unauthorized, clear token and user
		if (error.message && error.message.includes('401')) {
			token.set(null);
			user.set(null);
			refreshToken.set(null);

			if (browser) {
				addToast('انتهت جلستك. يرجى تسجيل الدخول مرة أخرى', 'warning');
				goto('/login');
			}
		}

		return null;
	}
}

/**
 * Update user profile
 */
export async function updateUserProfile(profileData) {
	try {
		const response = await api.patch('/accounts/profile/', profileData);

		if (response.data?.user) {
			user.set(response.data.user);
			return { success: true, data: response.data.user };
		}

		return { success: false, error: 'بيانات غير كاملة' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في تحديث الملف الشخصي' };
	}
}

/**
 * Update user avatar
 */
export async function updateAvatar(formData) {
	try {
		const response = await api.uploadFile('/accounts/profile/avatar/', formData);

		if (response.data?.user) {
			user.set(response.data.user);
			return { success: true };
		}

		return { success: false, error: 'فشل في تحديث الصورة' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في تحديث الصورة الشخصية' };
	}
}

/**
 * Resend verification email
 */
export async function resendVerification(email) {
	try {
		const response = await api.post('/accounts/resend-verification/', { email });
		return { success: true, message: response.message || 'تم إعادة إرسال رمز التحقق بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في إعادة إرسال رمز التحقق' };
	}
}

export default {
	token,
	refreshToken,
	user,
	isAuthenticated,
	isVerified,
	isAdmin,
	register,
	verifyEmail,
	login,
	logout,
	resetPasswordRequest,
	verifyResetCode,
	resetPassword,
	changePassword,
	fetchUserProfile,
	updateUserProfile,
	updateAvatar,
	resendVerification
};
