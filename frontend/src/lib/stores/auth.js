// src/lib/stores/auth.js
import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';

// Base stores
export const token = writable((browser && localStorage.getItem('token')) || null);
export const refreshToken = writable((browser && localStorage.getItem('refreshToken')) || null);
export const user = writable(browser && JSON.parse(localStorage.getItem('user') || 'null'));

// Derived stores
export const isAuthenticated = derived(token, ($token) => !!$token);
export const isVerified = derived(user, ($user) => !!$user?.is_verified);
export const isAdmin = derived(user, ($user) => !!$user?.is_staff);
export const userRoles = derived(user, ($user) => $user?.roles || []);

// Local storage persistence
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
 * Permission checking
 */
export function hasPermission(permission) {
	const currentUser = get(user);
	if (!currentUser) return false;

	// Admin has all permissions
	if (currentUser.is_staff) return true;

	// Check specific permissions
	switch (permission) {
		case 'create_property':
			return (
				currentUser.is_verified &&
				(currentUser.roles?.includes('seller') || currentUser.roles?.includes('agent'))
			);

		case 'edit_property':
			return (
				currentUser.is_verified &&
				(currentUser.roles?.includes('seller') || currentUser.roles?.includes('agent'))
			);

		case 'delete_property':
			return currentUser.is_staff || currentUser.roles?.includes('admin');

		case 'manage_properties':
			return (
				currentUser.is_staff ||
				currentUser.roles?.includes('admin') ||
				currentUser.roles?.includes('agent')
			);

		case 'create_auction':
			return (
				currentUser.is_verified &&
				(currentUser.roles?.includes('seller') || currentUser.roles?.includes('agent'))
			);

		case 'place_bid':
			return currentUser.is_verified && currentUser.roles?.includes('bidder');

		case 'manage_users':
			return currentUser.is_staff || currentUser.roles?.includes('admin');

		case 'verify_documents':
			return (
				currentUser.is_staff ||
				currentUser.roles?.includes('admin') ||
				currentUser.roles?.includes('legal')
			);

		default:
			return false;
	}
}

/**
 * Role checking
 */
export function hasRole(role) {
	const currentUser = get(user);
	if (!currentUser) return false;

	if (currentUser.is_staff) return true;
	return currentUser.roles?.includes(role) || false;
}

/**
 * Authentication functions
 */
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
	  const response = await api.post('/accounts/login/', {
		email: email.trim().toLowerCase(),
		password
	  });
  
	  console.log('Login response:', response); // Debug log
  
	  if (response.status === 'success' && response.data?.tokens && response.data?.user) {
		// Log token before storing
		console.log('Received tokens:', {
		  access: response.data.tokens.access ? 'present' : 'missing',
		  refresh: response.data.tokens.refresh ? 'present' : 'missing'
		});
  
		// Store tokens in localStorage
		localStorage.setItem('token', response.data.tokens.access);
		localStorage.setItem('refreshToken', response.data.tokens.refresh);
		
		// Update stores
		token.set(response.data.tokens.access);
		refreshToken.set(response.data.tokens.refresh);
		user.set(response.data.user);
  
		return { success: true };
	  }
  
	  throw new Error(response.error || 'Login response missing tokens or user data');
	} catch (error) {
	  console.error('Login error:', error);
	  return { success: false, error: error.message };
	}
}

export async function logout() {
	try {
		const currentRefreshToken = get(refreshToken);
		if (currentRefreshToken) {
			try {
				await api.post('/accounts/logout/', { refresh: currentRefreshToken });
			} catch (err) {
				console.error('Server logout error:', err);
			}
		}
	} catch (error) {
		console.error('Error during logout:', error);
	} finally {
		token.set(null);
		refreshToken.set(null);
		user.set(null);
		if (browser) goto('/login');
	}
}

/**
 * Password management
 */
export async function resetPasswordRequest(email) {
	try {
		const response = await api.post('/accounts/password/reset/request/', { email });
		return {
			success: true,
			message: response.message || 'تم إرسال رمز إعادة التعيين إلى بريدك الإلكتروني'
		};
	} catch (error) {
		console.error('Password reset request error:', error);
		return {
			success: false,
			error: error.message || 'حدث خطأ أثناء إرسال طلب إعادة تعيين كلمة المرور'
		};
	}
}

export async function verifyResetCode(email, reset_code) {
	try {
		const response = await api.post('/accounts/password/reset/verify/', { email, reset_code });
		return { success: true, message: response.message || 'تم التحقق من الرمز بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'رمز غير صالح أو منتهي الصلاحية' };
	}
}

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
 * Profile management
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

		if (error.message?.includes('401')) {
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

export async function resendVerification(email) {
	try {
		const response = await api.post('/accounts/resend-verification/', { email });
		return { success: true, message: response.message || 'تم إعادة إرسال رمز التحقق بنجاح' };
	} catch (error) {
		return { success: false, error: error.message || 'فشل في إعادة إرسال رمز التحقق' };
	}
}

// Export all functions and stores
export default {
	token,
	refreshToken,
	user,
	isAuthenticated,
	isVerified,
	isAdmin,
	userRoles,
	hasPermission,
	hasRole,
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
