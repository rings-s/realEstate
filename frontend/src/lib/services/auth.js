// src/lib/services/auth.js
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { writable } from 'svelte/store';

const API_URL = 'http://localhost:8000/api';

export const user = writable(browser && JSON.parse(localStorage.getItem('user')) || null);
export const token = writable(browser && localStorage.getItem('token') || null);
export const isVerified = writable(false);

// Watch store changes and update localStorage
if (browser) {
  user.subscribe((value) => {
    if (value) localStorage.setItem('user', JSON.stringify(value));
    else localStorage.removeItem('user');

    isVerified.set(value?.is_verified || false);
  });

  token.subscribe((value) => {
    if (value) localStorage.setItem('token', value);
    else localStorage.removeItem('token');
  });
}

export async function register(userData) {
  try {
    const res = await fetch(`${API_URL}/accounts/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error?.message || 'خطأ في التسجيل');

    return { success: true, email: userData.email };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export async function verifyEmail(email, code) {
  try {
    const res = await fetch(`${API_URL}/accounts/verify-email/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, verification_code: code })
    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error?.message || 'خطأ في التحقق');

    // Set user and token if verification successful
    if (data.data?.tokens && data.data?.user) {
      token.set(data.data.tokens.access);
      user.set(data.data.user);
      return { success: true };
    }

    return { success: false, error: 'بيانات غير كاملة' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export async function login(email, password) {
  try {
    const res = await fetch(`${API_URL}/accounts/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error?.message || 'خطأ في تسجيل الدخول');

    if (data.data?.tokens && data.data?.user) {
      token.set(data.data.tokens.access);
      user.set(data.data.user);
      return { success: true };
    }

    return { success: false, error: 'بيانات غير كاملة' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export function logout() {
  token.set(null);
  user.set(null);
  goto('/login');
}

export async function resetPassword(email) {
  try {
    const res = await fetch(`${API_URL}/accounts/request-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    const data = await res.json();
    return { success: res.ok, message: data.message || 'تم إرسال رابط إعادة التعيين' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export async function fetchUserProfile() {
  try {
    const accessToken = get(token);
    if (!accessToken) return null;

    const res = await fetch(`${API_URL}/accounts/profile/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });

    if (!res.ok) {
      if (res.status === 401) {
        logout();
        return null;
      }
      throw new Error('فشل في جلب بيانات المستخدم');
    }

    const data = await res.json();
    user.set(data.data?.user || null);
    return data.data?.user;
  } catch (error) {
    console.error(error);
    return null;
  }
}
