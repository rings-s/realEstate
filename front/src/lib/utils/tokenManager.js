/**
 * Token Manager
 * Utility for managing authentication tokens in the frontend
 */

import { browser } from '$app/environment';
import { TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY } from '$lib/config/constants';
import { isAuthenticated, currentUser } from '$lib/stores/auth';

/**
 * Check if token exists
 * @returns {boolean} Whether the token exists
 */
export const hasToken = () => {
  if (!browser) return false;
  return Boolean(localStorage.getItem(TOKEN_KEY));
};

/**
 * Get access token
 * @returns {string|null} Access token
 */
export const getAccessToken = () => {
  if (!browser) return null;
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Get refresh token
 * @returns {string|null} Refresh token
 */
export const getRefreshToken = () => {
  if (!browser) return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Check if token is expired
 * Note: Simple token auth doesn't have built-in expiry
 * @returns {boolean} Whether the token is expired
 */
export const isTokenExpired = () => {
  // With Django's simple token authentication, tokens don't expire automatically
  // Return false to indicate token is valid as long as it exists
  return !hasToken();
};

/**
 * Set tokens in localStorage
 * @param {Object} params - Token parameters
 * @param {string} params.access - Access token
 * @param {string} params.refresh - Refresh token (optional)
 */
export const setTokens = ({ access, refresh }) => {
  if (!browser) return;

  if (access) {
    localStorage.setItem(TOKEN_KEY, access);
  }
  
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }

  // Update authentication state
  isAuthenticated.set(true);
};

/**
 * Set user data
 * @param {Object} userData - User data
 */
export const setUserData = (userData) => {
  if (!browser || !userData) return;

  try {
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
    currentUser.set(userData);
  } catch (error) {
    console.error('Error storing user data:', error);
  }
};

/**
 * Get user data from localStorage
 * @returns {Object|null} User data
 */
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

/**
 * Clear all tokens and user data
 */
export const clearTokens = () => {
  if (!browser) return;

  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);

  // Update authentication state
  isAuthenticated.set(false);
  currentUser.set(null);
};

/**
 * Check if user is authenticated
 * @returns {boolean} Whether the user is authenticated
 */
export const checkAuth = () => {
  if (!browser) return false;
  
  // Check if token exists
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    isAuthenticated.set(false);
    return false;
  }
  
  // Token exists, user is authenticated
  isAuthenticated.set(true);
  return true;
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
  checkAuth
};