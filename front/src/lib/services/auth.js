import api, { handleApiError } from './api';

/**
 * Authentication and user management services
 */
export default {
	/**
	 * Register a new user
	 * @param {Object} userData - User registration data
	 */
	register: async (userData) => {
		try {
			return await api.post('/accounts/register/', userData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Verify user email with verification code
	 * @param {string} email - User email
	 * @param {string} verificationCode - Email verification code
	 */
	verifyEmail: async (email, verificationCode) => {
		try {
			return await api.post('/accounts/verify-email/', {
				email,
				verification_code: verificationCode
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Login user and get auth tokens
	 * @param {string} email - User email
	 * @param {string} password - User password
	 */
	login: async (email, password) => {
		try {
			const response = await api.post('/accounts/login/', { email, password });
			localStorage.setItem('access_token', response.access);
			localStorage.setItem('refresh_token', response.refresh);
			return response;
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Logout user and invalidate tokens
	 * Enhanced with better error handling and no multiple requests
	 */
	logout: async () => {
		try {
			const refreshToken = localStorage.getItem('refresh_token');
			if (refreshToken) {
				// Attempt to invalidate the token server-side
				await api.post('/accounts/logout/', { refresh: refreshToken }).catch((err) => {
					// Just log the error but continue with client-side logout
					console.warn('Server logout failed but continuing with client-side logout:', err);
				});
			}
		} finally {
			// Always clean up local storage regardless of API success
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
		}
	},

	/**
	 * Get current user profile
	 */
	getProfile: async () => {
		try {
			return await api.get('/accounts/profile/');
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update user profile
	 * @param {Object} profileData - Updated profile data
	 */
	updateProfile: async (profileData) => {
		try {
			return await api.patch('/accounts/profile/', profileData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get public profile for a user
	 * @param {string} userId - User ID
	 */
	getPublicProfile: async (userId) => {
		try {
			return await api.get(`/accounts/profile/${userId}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update user avatar
	 * @param {File} avatarFile - Avatar image file
	 */
	updateAvatar: async (avatarFile) => {
		try {
			const formData = new FormData();
			formData.append('avatar', avatarFile);
			return await api.upload('/accounts/profile/avatar/', formData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Change user password
	 * @param {string} currentPassword - Current password
	 * @param {string} newPassword - New password
	 * @param {string} confirmPassword - Confirm password
	 */
	changePassword: async (currentPassword, newPassword, confirmPassword) => {
		try {
			return await api.post('/accounts/password/', {
				current_password: currentPassword,
				new_password: newPassword,
				confirm_password: confirmPassword
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Request password reset
	 * @param {string} email - User email
	 */
	requestPasswordReset: async (email) => {
		try {
			return await api.post('/accounts/password/reset/', { email });
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Verify reset code validity
	 * @param {string} email - User email
	 * @param {string} resetCode - Password reset code
	 */
	verifyResetCode: async (email, resetCode) => {
		try {
			return await api.post('/accounts/password/reset/verify/', {
				email,
				reset_code: resetCode
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Reset password using reset code
	 * @param {string} email - User email
	 * @param {string} resetCode - Password reset code
	 * @param {string} newPassword - New password
	 * @param {string} confirmPassword - Confirm password
	 */
	resetPassword: async (email, resetCode, newPassword, confirmPassword) => {
		try {
			return await api.post('/accounts/password/reset/confirm/', {
				email,
				reset_code: resetCode,
				new_password: newPassword,
				confirm_password: confirmPassword
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Resend verification email
	 * @param {string} email - User email
	 */
	resendVerification: async (email) => {
		try {
			return await api.post('/accounts/resend-verification/', { email });
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get role-based dashboard data
	 */
	getRoleDashboard: async () => {
		try {
			return await api.get('/accounts/dashboard/role/');
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
