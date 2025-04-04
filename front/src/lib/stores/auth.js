import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import authService from '$lib/services/auth';
import { uiStore } from '$lib/stores/ui';

// Define initial state
const initialState = {
	user: null,
	isAuthenticated: false,
	isLoading: true,
	error: null,
	roles: []
};

// Create the writable store
const createAuthStore = () => {
	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		// Initialize auth state from local storage (if available)
		initialize: async () => {
			if (!browser) return;

			const accessToken = localStorage.getItem('access_token');
			const refreshToken = localStorage.getItem('refresh_token');

			if (!accessToken || !refreshToken) {
				set({ ...initialState, isLoading: false });
				return;
			}

			update((state) => ({ ...state, isLoading: true }));

			try {
				const response = await authService.getProfile();
				update((state) => ({
					user: response.user,
					isAuthenticated: true,
					isLoading: false,
					error: null,
					roles: response.user.roles?.map((r) => r.code) || []
				}));
			} catch (error) {
				console.error('Failed to initialize auth state:', error);
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				set({ ...initialState, isLoading: false, error });
			}
		},

		// Login user
		login: async (email, password) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await authService.login(email, password);
				update((state) => ({
					user: response.user,
					isAuthenticated: true,
					isLoading: false,
					error: null,
					roles: response.user.roles?.map((r) => r.code) || []
				}));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Register user
		register: async (userData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				await authService.register(userData);
				update((state) => ({ ...state, isLoading: false }));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Verify email
		verifyEmail: async (email, code) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await authService.verifyEmail(email, code);
				update((state) => ({
					user: response.user,
					isAuthenticated: true,
					isLoading: false,
					error: null,
					roles: response.user.roles?.map((r) => r.code) || []
				}));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Update user profile
		updateProfile: async (profileData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await authService.updateProfile(profileData);
				update((state) => ({
					...state,
					user: response.user,
					isLoading: false,
					roles: response.user.roles?.map((r) => r.code) || []
				}));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Logout user
		logout: async () => {
			update((state) => ({ ...state, isLoading: true }));

			try {
				// Clear toasts first to prevent toast spam
				uiStore.clearToasts();

				// Perform server-side logout
				await authService.logout();
			} catch (error) {
				console.error('Logout error:', error);
			} finally {
				// Always reset the store state regardless of API outcome
				set({ ...initialState, isLoading: false });
			}
		},

		// Reset error state
		clearError: () => {
			update((state) => ({ ...state, error: null }));
		}
	};
};

// Create the store
export const auth = createAuthStore();

// Derived stores for convenience
export const user = derived(auth, ($auth) => $auth.user);
export const isAuthenticated = derived(auth, ($auth) => $auth.isAuthenticated);
export const isLoading = derived(auth, ($auth) => $auth.isLoading);
export const roles = derived(auth, ($auth) => $auth.roles);

// Derived store for role-based authorization
export const hasRole = (requiredRole) => derived(roles, ($roles) => $roles.includes(requiredRole));

// Check if user has any of the specified roles
export const hasAnyRole = (requiredRoles) =>
	derived(roles, ($roles) => requiredRoles.some((role) => $roles.includes(role)));

// Initialize auth state when the app loads (in a client-side context)
if (browser) {
	auth.initialize();
}
