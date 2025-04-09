/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */

import { API_URL, ENDPOINTS } from '$lib/config/api';
import { setTokens, clearTokens, getRefreshToken } from '$lib/utils/tokenManager';

/**
 * Register a new user
 * @param {Object} userData - User registration data
 * @param {string} userData.email - User email
 * @param {string} userData.password - User password
 * @param {string} userData.confirm_password - Password confirmation
 * @param {string} userData.first_name - User first name
 * @param {string} userData.last_name - User last name
 * @param {string} userData.phone_number - User phone number (optional)
 * @param {string} userData.role - User role (e.g. 'buyer', 'seller')
 * @returns {Promise<Object>} Registration response
 */
export const register = async (userData) => {
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

		return data;
	} catch (error) {
		console.error('Registration error:', error);
		throw error;
	}
};

/**
 * Verify user email with verification code
 * @param {string} email - User email
 * @param {string} verificationCode - Verification code received via email
 * @returns {Promise<Object>} Verification response with tokens
 */
export const verifyEmail = async (email, verificationCode) => {
	try {
		const response = await fetch(`${API_URL}/accounts/verify-email/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email,
				verification_code: verificationCode
			})
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Email verification failed');
		}

		if (data.refresh && data.access) {
			setTokens({
				access: data.access,
				refresh: data.refresh
			});
		}

		return data;
	} catch (error) {
		console.error('Email verification error:', error);
		throw error;
	}
};

/**
 * Resend verification email
 * @param {string} email - User email
 * @returns {Promise<Object>} Response
 */
export const resendVerification = async (email) => {
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
			throw new Error(data.error || 'Failed to resend verification');
		}

		return data;
	} catch (error) {
		console.error('Resend verification error:', error);
		throw error;
	}
};

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Login response with tokens and user data
 */
export const login = async (email, password) => {
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
			// Try to provide a better error message based on backend response
			if (data.error_code === 'email_not_verified') {
				throw new Error('email_not_verified');
			} else if (data.error_code === 'account_disabled') {
				throw new Error('account_disabled');
			} else {
				throw new Error(data.error || 'Login failed');
			}
		}

		if (data.access && data.refresh && data.user) {
			setTokens({
				access: data.access,
				refresh: data.refresh
			});
		}

		return data;
	} catch (error) {
		console.error('Login error:', error);
		throw error;
	}
};

/**
 * Logout user
 * @returns {Promise<Object>} Logout response
 */
export const logout = async () => {
	try {
		const refreshToken = getRefreshToken();

		if (!refreshToken) {
			clearTokens();
			return { status: 'success', message: 'Logged out' };
		}

		const accessToken = localStorage.getItem('access_token');

		const response = await fetch(`${API_URL}/accounts/logout/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			},
			body: JSON.stringify({ refresh: refreshToken })
		});

		// Clear tokens regardless of server response
		clearTokens();

		// Try to parse response but don't worry if it fails
		try {
			const data = await response.json();
			return data;
		} catch (e) {
			return { status: 'success', message: 'Logged out' };
		}
	} catch (error) {
		// Clear tokens even if API request fails
		clearTokens();
		console.error('Logout error:', error);
		throw error;
	}
};

/**
 * Request password reset
 * @param {string} email - User email
 * @returns {Promise<Object>} Reset request response
 */
export const requestPasswordReset = async (email) => {
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

		return data;
	} catch (error) {
		console.error('Password reset request error:', error);
		throw error;
	}
};

/**
 * Verify password reset code
 * @param {string} email - User email
 * @param {string} resetCode - Reset code received via email
 * @returns {Promise<Object>} Verification response
 */
export const verifyResetCode = async (email, resetCode) => {
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

		return data;
	} catch (error) {
		console.error('Reset code verification error:', error);
		throw error;
	}
};

/**
 * Reset password using reset code
 * @param {string} email - User email
 * @param {string} resetCode - Reset code received via email
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 * @returns {Promise<Object>} Reset response with tokens
 */
export const resetPassword = async (email, resetCode, newPassword, confirmPassword) => {
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

		if (data.access && data.refresh) {
			setTokens({
				access: data.access,
				refresh: data.refresh
			});
		}

		return data;
	} catch (error) {
		console.error('Password reset error:', error);
		throw error;
	}
};

/**
 * Change password for authenticated user
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 * @returns {Promise<Object>} Password change response
 */
export const changePassword = async (currentPassword, newPassword, confirmPassword) => {
	try {
		const accessToken = localStorage.getItem('access_token');

		const response = await fetch(`${API_URL}/accounts/password/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
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

		if (data.access && data.refresh) {
			setTokens({
				access: data.access,
				refresh: data.refresh
			});
		}

		return data;
	} catch (error) {
		console.error('Password change error:', error);
		throw error;
	}
};

/**
 * Verify the validity of the current token
 * @returns {Promise<boolean>} Token validity
 */
export const verifyToken = async () => {
	try {
		const accessToken = localStorage.getItem('access_token');

		if (!accessToken) {
			return false;
		}

		const response = await fetch(`${API_URL}/accounts/token/verify/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			}
		});

		if (!response.ok) {
			return false;
		}

		const data = await response.json();
		return data.status === 'success';
	} catch (error) {
		console.error('Token verification error:', error);
		return false;
	}
};

/**
 * Get user profile
 * @returns {Promise<Object>} User profile data
 */
export const getUserProfile = async () => {
	try {
		const accessToken = localStorage.getItem('access_token');

		if (!accessToken) {
			throw new Error('Not authenticated');
		}

		const response = await fetch(`${API_URL}/accounts/profile/`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			}
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Failed to get user profile');
		}

		return data.user;
	} catch (error) {
		console.error('Profile fetch error:', error);
		throw error;
	}
};

/**
 * Update user profile
 * @param {Object} profileData - User profile data
 * @returns {Promise<Object>} Updated user profile
 */
export const updateProfile = async (profileData) => {
	try {
		const accessToken = localStorage.getItem('access_token');

		if (!accessToken) {
			throw new Error('Not authenticated');
		}

		const response = await fetch(`${API_URL}/accounts/profile/`, {
			method: 'PATCH',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			},
			body: JSON.stringify(profileData)
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Failed to update profile');
		}

		return data.user;
	} catch (error) {
		console.error('Profile update error:', error);
		throw error;
	}
};

/**
 * Upload user avatar
 * @param {File} file - Avatar image file
 * @returns {Promise<Object>} Upload response
 */
export const uploadAvatar = async (file) => {
	try {
		const accessToken = localStorage.getItem('access_token');

		if (!accessToken) {
			throw new Error('Not authenticated');
		}

		const formData = new FormData();
		formData.append('avatar', file);

		const response = await fetch(`${API_URL}/accounts/profile/avatar/`, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${accessToken}`
			},
			body: formData
		});

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.error || 'Failed to upload avatar');
		}

		return data;
	} catch (error) {
		console.error('Avatar upload error:', error);
		throw error;
	}
};
