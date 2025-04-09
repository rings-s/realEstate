/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */

import { ENDPOINTS } from '$lib/config/api';
import { get, post } from '$lib/utils/api';
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
	return post(ENDPOINTS.AUTH.REGISTER, userData, {}, false);
};

/**
 * Verify user email with verification code
 * @param {string} email - User email
 * @param {string} verificationCode - Verification code received via email
 * @returns {Promise<Object>} Verification response with tokens
 */
export const verifyEmail = async (email, verificationCode) => {
	const response = await post(
		ENDPOINTS.AUTH.VERIFY_EMAIL,
		{ email, verification_code: verificationCode },
		{},
		false
	);

	if (response && response.refresh && response.access) {
		setTokens({
			access: response.access,
			refresh: response.refresh
		});
	}

	return response;
};

/**
 * Resend verification email
 * @param {string} email - User email
 * @returns {Promise<Object>} Response
 */
export const resendVerification = async (email) => {
	return post(ENDPOINTS.AUTH.RESEND_VERIFICATION, { email }, {}, false);
};

/**
 * Login user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Login response with tokens and user data
 */
export const login = async (email, password) => {
	const response = await post(ENDPOINTS.AUTH.LOGIN, { email, password }, {}, false);

	if (response && response.refresh && response.access) {
		setTokens({
			access: response.access,
			refresh: response.refresh
		});
	}

	return response;
};

/**
 * Logout user
 * @returns {Promise<Object>} Logout response
 */
export const logout = async () => {
	const refreshToken = getRefreshToken();

	if (!refreshToken) {
		clearTokens();
		return { status: 'success', message: 'Logged out' };
	}

	try {
		const response = await post(ENDPOINTS.AUTH.LOGOUT, { refresh: refreshToken }, {}, true);

		clearTokens();
		return response;
	} catch (error) {
		// Clear tokens even if API request fails
		clearTokens();
		throw error;
	}
};

/**
 * Request password reset
 * @param {string} email - User email
 * @returns {Promise<Object>} Reset request response
 */
export const requestPasswordReset = async (email) => {
	return post(ENDPOINTS.AUTH.REQUEST_RESET, { email }, {}, false);
};

/**
 * Verify password reset code
 * @param {string} email - User email
 * @param {string} resetCode - Reset code received via email
 * @returns {Promise<Object>} Verification response
 */
export const verifyResetCode = async (email, resetCode) => {
	return post(ENDPOINTS.AUTH.VERIFY_RESET_CODE, { email, reset_code: resetCode }, {}, false);
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
	const response = await post(
		ENDPOINTS.AUTH.RESET_PASSWORD,
		{
			email,
			reset_code: resetCode,
			new_password: newPassword,
			confirm_password: confirmPassword
		},
		{},
		false
	);

	if (response && response.refresh && response.access) {
		setTokens({
			access: response.access,
			refresh: response.refresh
		});
	}

	return response;
};

/**
 * Change password for authenticated user
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @param {string} confirmPassword - Confirm new password
 * @returns {Promise<Object>} Change password response
 */
export const changePassword = async (currentPassword, newPassword, confirmPassword) => {
	const response = await post(
		ENDPOINTS.AUTH.CHANGE_PASSWORD,
		{
			current_password: currentPassword,
			new_password: newPassword,
			confirm_password: confirmPassword
		},
		{},
		true
	);

	if (response && response.refresh && response.access) {
		setTokens({
			access: response.access,
			refresh: response.refresh
		});
	}

	return response;
};

/**
 * Verify the validity of the current token
 * @returns {Promise<Object>} Token verification response
 */
export const verifyToken = async () => {
	return post(ENDPOINTS.AUTH.VERIFY_TOKEN, {}, {}, true);
};
