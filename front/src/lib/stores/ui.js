/**
 * UI Store
 * Manages UI state like theme, language, notifications, etc.
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Initial state
const initialState = {
	theme: 'light',
	language: 'ar', // Default to Arabic
	direction: 'rtl', // Default to RTL for Arabic
	notifications: [],
	modal: {
		isOpen: false,
		component: null,
		props: {}
	},
	sidebar: {
		isOpen: false
	},
	toast: {
		isVisible: false,
		message: '',
		type: 'info',
		timeout: 3000
	},
	pageLoading: false
};

// Load saved settings from localStorage if in browser
function getInitialState() {
	if (!browser) return initialState;

	try {
		const savedTheme = localStorage.getItem('theme');
		const savedLanguage = localStorage.getItem('language');
		const savedDirection = localStorage.getItem('direction');

		return {
			...initialState,
			theme: savedTheme || initialState.theme,
			language: savedLanguage || initialState.language,
			direction: savedDirection || initialState.direction
		};
	} catch (error) {
		console.error('Error loading UI settings from localStorage:', error);
		return initialState;
	}
}

// Create the UI store
function createUIStore() {
	const { subscribe, set, update } = writable(getInitialState());

	return {
		subscribe,

		/**
		 * Set theme (light/dark)
		 * @param {string} theme - Theme name
		 */
		setTheme: (theme) => {
			update((state) => {
				if (browser) {
					localStorage.setItem('theme', theme);
					document.documentElement.setAttribute('data-theme', theme);
				}
				return { ...state, theme };
			});
		},

		/**
		 * Set language
		 * @param {string} language - Language code (e.g., 'ar', 'en')
		 */
		setLanguage: (language) => {
			update((state) => {
				if (browser) {
					localStorage.setItem('language', language);
					document.documentElement.setAttribute('lang', language);

					// Set direction based on language
					const direction = language === 'ar' ? 'rtl' : 'ltr';
					document.documentElement.setAttribute('dir', direction);
					localStorage.setItem('direction', direction);

					return {
						...state,
						language,
						direction
					};
				}
				return state;
			});
		},

		/**
		 * Set direction manually (RTL/LTR)
		 * @param {string} direction - Direction ('rtl' or 'ltr')
		 */
		setDirection: (direction) => {
			update((state) => {
				if (browser) {
					document.documentElement.setAttribute('dir', direction);
					localStorage.setItem('direction', direction);
				}
				return { ...state, direction };
			});
		},

		/**
		 * Set page loading state
		 * @param {boolean} loading - Loading state
		 */
		setPageLoading: (loading) => {
			update((state) => ({
				...state,
				pageLoading: loading
			}));
		},

		/**
		 * Add notification
		 * @param {Object} notification - Notification object
		 */
		addNotification: (notification) => {
			update((state) => {
				const id = Date.now();
				const newNotification = {
					id,
					timestamp: new Date(),
					read: false,
					...notification
				};

				return {
					...state,
					notifications: [newNotification, ...state.notifications]
				};
			});
		},

		/**
		 * Mark notification as read
		 * @param {number} id - Notification ID
		 */
		markNotificationAsRead: (id) => {
			update((state) => {
				const updatedNotifications = state.notifications.map((notification) =>
					notification.id === id ? { ...notification, read: true } : notification
				);

				return {
					...state,
					notifications: updatedNotifications
				};
			});
		},

		/**
		 * Remove notification
		 * @param {number} id - Notification ID
		 */
		removeNotification: (id) => {
			update((state) => {
				const updatedNotifications = state.notifications.filter(
					(notification) => notification.id !== id
				);

				return {
					...state,
					notifications: updatedNotifications
				};
			});
		},

		/**
		 * Open modal
		 * @param {Component} component - Svelte component to render in modal
		 * @param {Object} props - Props to pass to component
		 */
		openModal: (component, props = {}) => {
			update((state) => ({
				...state,
				modal: {
					isOpen: true,
					component,
					props
				}
			}));
		},

		/**
		 * Close modal
		 */
		closeModal: () => {
			update((state) => ({
				...state,
				modal: {
					isOpen: false,
					component: null,
					props: {}
				}
			}));
		},

		/**
		 * Toggle sidebar
		 * @param {boolean} isOpen - Force open/closed state (optional)
		 */
		toggleSidebar: (isOpen) => {
			update((state) => ({
				...state,
				sidebar: {
					isOpen: isOpen !== undefined ? isOpen : !state.sidebar.isOpen
				}
			}));
		},

		/**
		 * Show toast notification
		 * @param {string} message - Toast message
		 * @param {string} type - Toast type (info, success, warning, error)
		 * @param {number} timeout - Auto-close timeout in ms
		 */
		showToast: (message, type = 'info', timeout = 3000) => {
			update((state) => ({
				...state,
				toast: {
					isVisible: true,
					message,
					type,
					timeout
				}
			}));

			// Auto-hide toast after timeout
			if (timeout > 0) {
				setTimeout(() => {
					uiStore.hideToast();
				}, timeout);
			}
		},

		/**
		 * Hide toast notification
		 */
		hideToast: () => {
			update((state) => ({
				...state,
				toast: {
					...state.toast,
					isVisible: false
				}
			}));
		},

		/**
		 * Initialize UI settings (call on app start)
		 */
		init: () => {
			if (!browser) return;

			update((state) => {
				// Apply theme to document
				document.documentElement.setAttribute('data-theme', state.theme);

				// Apply language to document
				document.documentElement.setAttribute('lang', state.language);

				// Apply direction to document
				document.documentElement.setAttribute('dir', state.direction);

				return state;
			});
		}
	};
}

// Create and export the store
export const uiStore = createUIStore();

// Derived stores for convenient access
export const theme = derived(uiStore, ($uiStore) => $uiStore.theme);
export const language = derived(uiStore, ($uiStore) => $uiStore.language);
export const direction = derived(uiStore, ($uiStore) => $uiStore.direction);
export const isRTL = derived(direction, ($direction) => $direction === 'rtl');
export const darkMode = derived(theme, ($theme) => $theme === 'dark');
export const pageLoading = derived(uiStore, ($uiStore) => $uiStore.pageLoading);
export const notifications = derived(uiStore, ($uiStore) => $uiStore.notifications);
export const unreadNotifications = derived(notifications, ($notifications) =>
	$notifications.filter((n) => !n.read)
);
export const modal = derived(uiStore, ($uiStore) => $uiStore.modal);
export const sidebar = derived(uiStore, ($uiStore) => $uiStore.sidebar);
export const toast = derived(uiStore, ($uiStore) => $uiStore.toast);
export const isSidebarOpen = derived(uiStore, ($uiStore) => $uiStore.sidebar.isOpen);

// Arabic text direction utility
export const textClass = derived(direction, ($direction) =>
	$direction === 'rtl' ? 'text-right' : 'text-left'
);

// Export text alignment class for flex items
export const flexClass = derived(direction, ($direction) =>
	$direction === 'rtl' ? 'justify-end' : 'justify-start'
);

// Export convenience functions
export const addToast = (message, type = 'info', timeout = 3000) =>
	uiStore.showToast(message, type, timeout);

// Export toggleSidebar function
export const toggleSidebar = (isOpen) => uiStore.toggleSidebar(isOpen);
