import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { t } from '$lib/config/translations';
import { uiStore } from '$lib/stores/ui';
import {
	API_URL,
	TOKEN_KEY,
	REFRESH_TOKEN_KEY,
	TOKEN_EXPIRY_KEY,
	USER_KEY
} from '$lib/config/constants';

// Check if token exists in localStorage
const hasToken = browser ? Boolean(localStorage.getItem(TOKEN_KEY)) : false;

// Parse stored user data
const getUserData = () => {
	if (!browser) return null;
	const userData = localStorage.getItem(USER_KEY);
	if (userData) {
		try {
			return JSON.parse(userData);
		} catch (e) {
			return null;
		}
	}
	return null;
};

// Initialize stores
const initialUser = getUserData();
export const isAuthenticated = writable(hasToken);
export const currentUser = writable(initialUser);
export const authLoading = writable(false);
export const authError = writable(null);

// Export derived store for user primary role
export const userRole = derived(
	currentUser,
	($currentUser) => $currentUser?.primary_role?.code || null
);

// Export derived store for user roles array
export const userRoles = derived(
	currentUser,
	($currentUser) => $currentUser?.roles?.map((r) => r.code) || []
);

// Function to check if user has a specific role
export const hasRole = (role) => {
	const roles = get(userRoles);
	return roles.includes(role);
};

/**
 * Register a new user
 * @param {Object} userData - User registration data
 * @returns {Promise<Object>} Registration result
 */
export const register = async (userData) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/register/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(userData)
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Registration failed');
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('register_success', get(language), {
				default: 'تم التسجيل بنجاح. يرجى التحقق من بريدك الإلكتروني للتأكيد.'
			}),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message || t('register_error', get(language), { default: 'فشل التسجيل' }),
			'error'
		);

		throw error;
	}
};

/**
 * Verify email with code
 * @param {string} email - User email
 * @param {string} code - Verification code
 * @returns {Promise<Object>} Verification result
 */
export const verifyEmail = async (email, code) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/verify-email/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email,
				verification_code: code
			})
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Email verification failed');
		}

		// Store auth tokens and user data
		if (data.access && data.refresh && data.user) {
			localStorage.setItem(TOKEN_KEY, data.access);
			localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);

			// Calculate token expiry (1 hour from now)
			const expiry = new Date();
			expiry.setHours(expiry.getHours() + 1);
			localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());

			// Store user data
			localStorage.setItem(USER_KEY, JSON.stringify(data.user));

			// Update stores
			isAuthenticated.set(true);
			currentUser.set(data.user);
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('email_verified', get(language), { default: 'تم التحقق من البريد الإلكتروني بنجاح' }),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('verify_error', get(language), { default: 'فشل التحقق من البريد الإلكتروني' }),
			'error'
		);

		throw error;
	}
};

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Login result
 */
export const login = async (email, password) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/login/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email, password })
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Login failed');
		}

		// Store auth tokens and user data
		if (data.access && data.refresh && data.user) {
			localStorage.setItem(TOKEN_KEY, data.access);
			localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);

			// Calculate token expiry (1 hour from now)
			const expiry = new Date();
			expiry.setHours(expiry.getHours() + 1);
			localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());

			// Store user data
			localStorage.setItem(USER_KEY, JSON.stringify(data.user));

			// Update stores
			isAuthenticated.set(true);
			currentUser.set(data.user);
		}

		authLoading.set(false);

		// Show success message
		addToast(t('login_success', get(language), { default: 'تم تسجيل الدخول بنجاح' }), 'success');

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message || t('login_error', get(language), { default: 'فشل تسجيل الدخول' }),
			'error'
		);

		throw error;
	}
};

/**
 * Logout user
 * @returns {Promise<boolean>} Logout success status
 */
export const logout = async () => {
	authLoading.set(true);

	try {
		const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

		if (refreshToken) {
			// Call logout API
			const response = await fetch(`${API_URL}/accounts/logout/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`
				},
				body: JSON.stringify({ refresh: refreshToken })
			});

			// We don't need to check response as we'll logout locally anyway
			await response.json();
		}
	} catch (error) {
		console.error('Logout API call failed:', error);
		// Continue with local logout regardless of API call result
	}

	// Clear local storage
	localStorage.removeItem(TOKEN_KEY);
	localStorage.removeItem(REFRESH_TOKEN_KEY);
	localStorage.removeItem(TOKEN_EXPIRY_KEY);
	localStorage.removeItem(USER_KEY);

	// Update stores
	isAuthenticated.set(false);
	currentUser.set(null);
	authLoading.set(false);

	// Show logout message
	addToast(t('logout_success', get(language), { default: 'تم تسجيل الخروج بنجاح' }), 'success');

	// Redirect to home page
	goto('/');

	return true;
};

/**
 * Refresh auth token
 * @returns {Promise<boolean>} Token refresh success status
 */
export const refreshToken = async () => {
	const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);

	if (!refresh) {
		return false;
	}

	try {
		const response = await fetch(`${API_URL}/accounts/token/refresh/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ refresh })
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Token refresh failed');
		}

		// Store new access token
		localStorage.setItem(TOKEN_KEY, data.access);

		// Calculate token expiry (1 hour from now)
		const expiry = new Date();
		expiry.setHours(expiry.getHours() + 1);
		localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());

		return true;
	} catch (error) {
		console.error('Token refresh failed:', error);

		// Clear auth data if refresh fails
		localStorage.removeItem(TOKEN_KEY);
		localStorage.removeItem(REFRESH_TOKEN_KEY);
		localStorage.removeItem(TOKEN_EXPIRY_KEY);
		localStorage.removeItem(USER_KEY);

		// Update stores
		isAuthenticated.set(false);
		currentUser.set(null);

		return false;
	}
};

/**
 * Request password reset
 * @param {string} email - User email
 * @returns {Promise<Object>} Reset request result
 */
export const requestPasswordReset = async (email) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/password/reset/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email })
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Password reset request failed');
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('reset_email_sent', get(language), {
				default: 'تم إرسال تعليمات إعادة تعيين كلمة المرور إلى بريدك الإلكتروني'
			}),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('reset_request_error', get(language), { default: 'فشل طلب إعادة تعيين كلمة المرور' }),
			'error'
		);

		throw error;
	}
};

/**
 * Verify reset code before allowing password reset
 * @param {string} email - User email
 * @param {string} resetCode - Password reset code
 * @returns {Promise<boolean>} Code validity status
 */
export const verifyResetCode = async (email, resetCode) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/password/reset/verify/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email,
				reset_code: resetCode
			})
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Invalid reset code');
		}

		authLoading.set(false);
		return true;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('invalid_reset_code', get(language), { default: 'رمز إعادة التعيين غير صالح' }),
			'error'
		);

		return false;
	}
};

/**
 * Reset password using reset code
 * @param {string} email - User email
 * @param {string} resetCode - Password reset code
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 * @returns {Promise<Object>} Reset result
 */
export const resetPassword = async (email, resetCode, newPassword, confirmPassword) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/password/reset/confirm/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email,
				reset_code: resetCode,
				new_password: newPassword,
				confirm_password: confirmPassword
			})
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Password reset failed');
		}

		// Store auth tokens and user data if provided
		if (data.access && data.refresh && data.user) {
			localStorage.setItem(TOKEN_KEY, data.access);
			localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);

			// Calculate token expiry (1 hour from now)
			const expiry = new Date();
			expiry.setHours(expiry.getHours() + 1);
			localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());

			// Store user data
			localStorage.setItem(USER_KEY, JSON.stringify(data.user));

			// Update stores
			isAuthenticated.set(true);
			currentUser.set(data.user);
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('password_reset_success', get(language), { default: 'تم إعادة تعيين كلمة المرور بنجاح' }),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('password_reset_error', get(language), { default: 'فشل إعادة تعيين كلمة المرور' }),
			'error'
		);

		throw error;
	}
};

/**
 * Change password for authenticated user
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 * @returns {Promise<Object>} Password change result
 */
export const changePassword = async (currentPassword, newPassword, confirmPassword) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/password/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`
			},
			body: JSON.stringify({
				current_password: currentPassword,
				new_password: newPassword,
				confirm_password: confirmPassword
			})
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Password change failed');
		}

		// Update tokens if provided
		if (data.access && data.refresh) {
			localStorage.setItem(TOKEN_KEY, data.access);
			localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh);

			// Calculate token expiry (1 hour from now)
			const expiry = new Date();
			expiry.setHours(expiry.getHours() + 1);
			localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('password_changed', get(language), { default: 'تم تغيير كلمة المرور بنجاح' }),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('password_change_error', get(language), { default: 'فشل تغيير كلمة المرور' }),
			'error'
		);

		throw error;
	}
};

/**
 * Update user profile
 * @param {Object} profileData - User profile data
 * @returns {Promise<Object>} Updated user profile
 */
export const updateProfile = async (profileData) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/profile/`, {
			method: 'PATCH',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`
			},
			body: JSON.stringify(profileData)
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Profile update failed');
		}

		// Update user data in store and localStorage
		if (data.user) {
			localStorage.setItem(USER_KEY, JSON.stringify(data.user));
			currentUser.set(data.user);
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('profile_updated', get(language), { default: 'تم تحديث الملف الشخصي بنجاح' }),
			'success'
		);

		return data.user;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('profile_update_error', get(language), { default: 'فشل تحديث الملف الشخصي' }),
			'error'
		);

		throw error;
	}
};

/**
 * Upload avatar
 * @param {File} file - Avatar image file
 * @returns {Promise<Object>} Upload result
 */
export const uploadAvatar = async (file) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const formData = new FormData();
		formData.append('avatar', file);

		const response = await fetch(`${API_URL}/accounts/profile/avatar/`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`
			},
			body: formData
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Avatar upload failed');
		}

		// Update user data in store and localStorage
		if (data.user) {
			localStorage.setItem(USER_KEY, JSON.stringify(data.user));
			currentUser.set(data.user);
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('avatar_updated', get(language), { default: 'تم تحديث الصورة الشخصية بنجاح' }),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('avatar_upload_error', get(language), { default: 'فشل تحميل الصورة الشخصية' }),
			'error'
		);

		throw error;
	}
};

/**
 * Resend verification email
 * @param {string} email - User email
 * @returns {Promise<Object>} Resend result
 */
export const resendVerification = async (email) => {
	authLoading.set(true);
	authError.set(null);

	try {
		const response = await fetch(`${API_URL}/accounts/resend-verification/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email })
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Failed to resend verification email');
		}

		authLoading.set(false);

		// Show success message
		addToast(
			t('verification_email_sent', get(language), {
				default: 'تم إرسال بريد التحقق مرة أخرى بنجاح'
			}),
			'success'
		);

		return data;
	} catch (error) {
		authLoading.set(false);
		authError.set(error.message);

		// Show error message
		addToast(
			error.message ||
				t('resend_verification_error', get(language), { default: 'فشل إعادة إرسال بريد التحقق' }),
			'error'
		);

		throw error;
	}
};

// Fix for using get with Svelte store
import { get } from 'svelte/store';
