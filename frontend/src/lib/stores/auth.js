// src/lib/stores/auth.js
import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';

// Initialize base stores
export const token = writable(browser ? localStorage.getItem('token') : null);
export const refreshToken = writable(browser ? localStorage.getItem('refreshToken') : null);
export const user = writable(browser ? JSON.parse(localStorage.getItem('user') || 'null') : null);

// Derived stores
export const isAuthenticated = derived(token, $token => !!$token);
export const isVerified = derived(user, $user => !!$user?.is_verified);
export const isAdmin = derived(user, $user => !!$user?.is_staff);
export const userRoles = derived(user, $user => $user?.roles || []);

// Store subscriptions for localStorage persistence
if (browser) {
  token.subscribe($token => {
    if ($token) localStorage.setItem('token', $token);
    else localStorage.removeItem('token');
  });

  refreshToken.subscribe($refreshToken => {
    if ($refreshToken) localStorage.setItem('refreshToken', $refreshToken);
    else localStorage.removeItem('refreshToken');
  });

  user.subscribe($user => {
    if ($user) localStorage.setItem('user', JSON.stringify($user));
    else localStorage.removeItem('user');
  });
}

export async function login(email, password) {
  try {
    const response = await api.post('/accounts/login/', {
      email: email.trim().toLowerCase(),
      password
    });

    console.log('Login API Response:', response);

    if (response.status === 'success' && response.data) {
      const { tokens, user: userData } = response.data;
      
      if (!tokens?.access || !userData) {
        throw new Error('Invalid response structure from server');
      }

      // Update stores
      token.set(tokens.access);
      if (tokens.refresh) refreshToken.set(tokens.refresh);
      user.set(userData);

      return { success: true };
    }

    throw new Error(response.error || 'Login failed');
  } catch (error) {
    console.error('Login error:', error);
    return {
      success: false,
      error: error.message || 'Failed to login. Please check your credentials.'
    };
  }
}

export async function logout() {
  try {
    const currentRefreshToken = get(refreshToken);
    if (currentRefreshToken) {
      await api.post('/accounts/logout/', { refresh: currentRefreshToken });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    // Clear stores
    token.set(null);
    refreshToken.set(null);
    user.set(null);
    
    if (browser) goto('/login');
  }
}

export async function register(userData) {
  try {
    const response = await api.post('/accounts/register/', userData);
    return {
      success: true,
      email: userData.email,
      message: response.data?.message || 'Registration successful'
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export async function verifyEmail(email, verification_code) {
  try {
    const response = await api.post('/accounts/verify-email/', {
      email,
      verification_code
    });

    if (response.status === 'success' && response.data) {
      const { tokens, user: userData } = response.data;
      
      if (tokens?.access && userData) {
        token.set(tokens.access);
        if (tokens.refresh) refreshToken.set(tokens.refresh);
        user.set(userData);
        return { success: true };
      }
    }

    throw new Error('Verification failed');
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export async function fetchUserProfile() {
  try {
    const response = await api.get('/accounts/profile/');

    if (response.status === 'success' && response.data?.user) {
      user.set(response.data.user);
      return response.data.user;
    }

    return null;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    if (error.message?.includes('401')) {
      logout();
      addToast('Session expired. Please login again.', 'warning');
    }
    return null;
  }
}

// Additional auth utilities
export function hasPermission(permission) {
  const currentUser = get(user);
  if (!currentUser) return false;
  if (currentUser.is_staff) return true;

  switch (permission) {
    case 'create_property':
      return currentUser.is_verified && 
        (currentUser.roles?.includes('seller') || currentUser.roles?.includes('agent'));
    case 'edit_property':
      return currentUser.is_verified && 
        (currentUser.roles?.includes('seller') || currentUser.roles?.includes('agent'));
    case 'place_bid':
      return currentUser.is_verified && currentUser.roles?.includes('bidder');
    default:
      return false;
  }
}

export function hasRole(role) {
  const currentUser = get(user);
  if (!currentUser) return false;
  if (currentUser.is_staff) return true;
  return currentUser.roles?.includes(role) || false;
}

export default {
  token,
  refreshToken,
  user,
  isAuthenticated,
  isVerified,
  isAdmin,
  userRoles,
  login,
  logout,
  register,
  verifyEmail,
  fetchUserProfile,
  hasPermission,
  hasRole
};