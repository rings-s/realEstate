// Fix for using get with Svelte store - move this to the top to avoid reference errors
import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { t } from '$lib/config/translations';
import { language, addToast } from '$lib/stores/ui';
import {
	API_URL,
	TOKEN_KEY,
	REFRESH_TOKEN_KEY,
	TOKEN_EXPIRY_KEY,
	USER_KEY
} from '$lib/config/constants';

// Check if token exists in localStorage
const hasToken = browser ? Boolean(localStorage.getItem(TOKEN_KEY)) : false;

// Check if token is expired
const isTokenExpired = () => {
	if (!browser) return true;

	const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
	if (!expiry) return true;

	try {
		const expiryDate = new Date(expiry);
		const now = new Date();
		return now >= expiryDate;
	} catch (e) {
		console.error('Error parsing token expiry date:', e);
		return true; // If we can't parse the date, consider the token expired
	}
};

// Parse stored user data
const getUserData = () => {
	if (!browser) return null;
	const userData = localStorage.getItem(USER_KEY);
	if (userData) {
		try {
			return JSON.parse(userData);
		} catch (e) {
			console.error('Error parsing user data:', e);
			// Clear corrupted data
			localStorage.removeItem(USER_KEY);
			return null;
		}
	}
	return null;
};

// Initialize stores
const initialUser = getUserData();
export const isAuthenticated = writable(hasToken && !isTokenExpired()); // Add token expiry check
export const currentUser = writable(initialUser);
export const authLoading = writable(false);
export const authError = writable(null);

// Export derived store for user primary role
export const userRole = derived(currentUser, ($currentUser) => {
	if (!$currentUser) return null;

	if ($currentUser.primary_role) {
		// Handle primary_role as string or object
		if (typeof $currentUser.primary_role === 'string') {
			return $currentUser.primary_role;
		}
		return $currentUser.primary_role.code || $currentUser.primary_role.name;
	}

	// If primary_role doesn't exist but roles array does, take first role
	if ($currentUser.roles && Array.isArray($currentUser.roles) && $currentUser.roles.length > 0) {
		const firstRole = $currentUser.roles[0];
		if (typeof firstRole === 'string') return firstRole;
		return firstRole.code || firstRole.name;
	}

	return null;
});

// Ensure roles are always properly formatted in an array
export const userRoles = derived(currentUser, ($currentUser) => {
	// Handle different formats of roles data
	if (!$currentUser) return [];

	// Debug data structure
	console.log('User data for roles:', $currentUser);

	// If roles array exists
	if ($currentUser.roles && Array.isArray($currentUser.roles)) {
		// Format roles properly, handling both object and string formats
		return $currentUser.roles.map((role) => {
			if (typeof role === 'string') return role;
			return role.code || role.name || role;
		});
	}

	// Fallback to primary role if roles array doesn't exist
	if ($currentUser.primary_role) {
		const role = $currentUser.primary_role;
		if (typeof role === 'string') return [role];
		return [role.code || role.name || role];
	}

	// Check for role in user object directly (some API responses format it this way)
	if ($currentUser.role) {
		if (typeof $currentUser.role === 'string') return [$currentUser.role];
		return [$currentUser.role.code || $currentUser.role.name || $currentUser.role];
	}

	// Fallback to empty array if no roles found
	return [];
});

// Function to check if user has a specific role
export const hasRole = (role) => {
	if (!role) return false;

	const roles = get(userRoles);
	if (!roles || !Array.isArray(roles) || roles.length === 0) return false;

	// Normalize role to lowercase for case-insensitive comparison
	const normalizedRole = typeof role === 'string' ? role.toLowerCase() : '';
	if (!normalizedRole) return false;

	// Check against normalized roles
	return roles.some((r) => {
		const userRole = typeof r === 'string' ? r.toLowerCase() : '';
		return userRole === normalizedRole;
	});
};

/**
 * Check authentication and token validity
 * @returns {boolean} Authentication status
 */
export const checkAuth = () => {
	if (!browser) return false;

	// Check if token exists
	const token = localStorage.getItem(TOKEN_KEY);
	if (!token) {
		isAuthenticated.set(false);
		return false;
	}

	// Check if token is expired
	if (isTokenExpired()) {
		// Try to get a refresh token
		const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
		if (!refresh) {
			// No refresh token, clear auth
			isAuthenticated.set(false);
			return false;
		}

		// We have a refresh token, but we'll handle actual refresh elsewhere
		// Just return current authentication status
		console.log('Token expired, refresh token available');
		return get(isAuthenticated);
	}

	// Token exists and is valid
	isAuthenticated.set(true);
	return true;
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
			throw new Error(data.error || data.detail || 'Registration failed');
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
			throw new Error(data.error || data.detail || 'Email verification failed');
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
			throw new Error(data.error || data.detail || 'Login failed');
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

			// Log roles for debugging
			console.log(
				'User logged in with roles:',
				data.user.roles || data.user.primary_role || 'No roles found'
			);
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
			try {
				await fetch(`${API_URL}/accounts/logout/`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY)}`
					},
					body: JSON.stringify({ refresh: refreshToken })
				});
				// We don't need to check response as we'll logout locally anyway
			} catch (e) {
				console.warn('Logout API call failed, continuing with local logout:', e);
				// Continue with local logout regardless of API call result
			}
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
	} catch (error) {
		console.error('Logout error:', error);
		authLoading.set(false);

		// Force logout even if API call fails
		localStorage.removeItem(TOKEN_KEY);
		localStorage.removeItem(REFRESH_TOKEN_KEY);
		localStorage.removeItem(TOKEN_EXPIRY_KEY);
		localStorage.removeItem(USER_KEY);

		isAuthenticated.set(false);
		currentUser.set(null);

		return false;
	}
};

/**
 * Refresh auth token
 * @returns {Promise<boolean>} Token refresh success status
 */
// export const refreshToken = async () => {
// 	const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);

// 	if (!refresh) {
// 		console.warn('No refresh token available');
// 		return false;
// 	}

// 	try {
// 		// Set loading state
// 		authLoading.set(true);

// 		console.log('Attempting to refresh token...');

// 		const response = await fetch(`${API_URL}/accounts/token/refresh/`, {
// 			method: 'POST',
// 			headers: {
// 				'Content-Type': 'application/json'
// 			},
// 			body: JSON.stringify({ refresh })
// 		});

// 		if (!response.ok) {
// 			const errorData = await response.json().catch(() => ({}));
// 			throw new Error(errorData.error || errorData.detail || 'Token refresh failed');
// 		}

// 		const data = await response.json();

// 		// Store new access token
// 		localStorage.setItem(TOKEN_KEY, data.access);

// 		// Calculate token expiry (1 hour from now)
// 		const expiry = new Date();
// 		expiry.setHours(expiry.getHours() + 1);
// 		localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString());

// 		// Update authentication state
// 		isAuthenticated.set(true);

// 		// If user data is included in the response, update it
// 		if (data.user) {
// 			localStorage.setItem(USER_KEY, JSON.stringify(data.user));
// 			currentUser.set(data.user);
// 		}

// 		console.log('Token refreshed successfully');
// 		return true;
// 	} catch (error) {
// 		console.error('Token refresh failed:', error);

// 		// Clear auth data if refresh fails
// 		localStorage.removeItem(TOKEN_KEY);
// 		localStorage.removeItem(REFRESH_TOKEN_KEY);
// 		localStorage.removeItem(TOKEN_EXPIRY_KEY);
// 		localStorage.removeItem(USER_KEY);

// 		// Update stores
// 		isAuthenticated.set(false);
// 		currentUser.set(null);

// 		return false;
// 	} finally {
// 		authLoading.set(false);
// 	}
// };

export const refreshToken = async () => {
	const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);

	if (!refresh) {
		console.warn('No refresh token available');
		return false;
	}

	try {
		console.log('Attempting to refresh token...');
		console.log('Refresh token:', refresh); // Be cautious with logging sensitive data

		const response = await fetch(`${API_URL}/accounts/token/refresh/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ refresh })
		});

		console.log('Token refresh response status:', response.status);

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			console.error('Token refresh error data:', errorData);
			throw new Error(errorData.error || errorData.detail || 'Token refresh failed');
		}

		// Rest of the existing code...
	} catch (error) {
		console.error('Detailed token refresh error:', error);
		// Rest of the existing error handling...
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
			throw new Error(data.error || data.detail || 'Password reset request failed');
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
			throw new Error(data.error || data.detail || 'Invalid reset code');
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
			throw new Error(data.error || data.detail || 'Password reset failed');
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
			throw new Error(data.error || data.detail || 'Password change failed');
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
			throw new Error(data.error || data.detail || 'Profile update failed');
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
			throw new Error(data.error || data.detail || 'Avatar upload failed');
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
			throw new Error(data.error || data.detail || 'Failed to resend verification email');
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

// Auto-refresh token functionality
if (browser) {
	// Check if token is about to expire and refresh
	const setupTokenRefresh = () => {
		// Get current expiry time
		const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
		if (!expiry) return;

		try {
			const expiryTime = new Date(expiry).getTime();
			const now = new Date().getTime();

			// If token is already expired, try to refresh immediately
			if (now >= expiryTime) {
				refreshToken();
				return;
			}

			// Calculate time until expiry (refresh 5 minutes before expiry)
			const timeToRefresh = expiryTime - now - 5 * 60 * 1000;

			if (timeToRefresh > 0) {
				setTimeout(() => {
					refreshToken().then((success) => {
						if (success) {
							console.log('Token refreshed automatically');
							// Setup next refresh
							setupTokenRefresh();
						}
					});
				}, timeToRefresh);

				console.log(`Token refresh scheduled in ${Math.round(timeToRefresh / 1000 / 60)} minutes`);
			}
		} catch (e) {
			console.error('Error setting up token refresh:', e);
		}
	};

	// Initial setup of token refresh
	if (hasToken && !isTokenExpired()) {
		setupTokenRefresh();
	}

	// Check authentication on initial load
	checkAuth();
}
