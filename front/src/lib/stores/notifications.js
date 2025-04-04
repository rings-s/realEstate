import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import notificationsService from '$lib/services/notifications';
import { isAuthenticated } from './auth';

const createNotificationsStore = () => {
	const initialState = {
		notifications: [],
		unreadCount: 0,
		isLoading: false,
		error: null,
		wsConnection: null,
		isConnected: false
	};

	const { subscribe, set, update } = writable(initialState);

	// Setup WebSocket connection
	const setupWebSocket = () => {
		try {
			if (!browser) return null;

			// Close existing connection if any
			const store = get({ subscribe });
			if (store.wsConnection) {
				store.wsConnection.close();
			}

			// Create WebSocket connection
			const { socket, close } = notificationsService.subscribeToNotifications();

			socket.onopen = () => {
				update((state) => ({ ...state, isConnected: true }));
			};

			socket.onclose = () => {
				update((state) => ({ ...state, isConnected: false, wsConnection: null }));
			};

			socket.onerror = (error) => {
				console.error('WebSocket error:', error);
				update((state) => ({ ...state, isConnected: false }));
			};

			socket.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);

					if (data.type === 'notification') {
						// Add the new notification to our store
						update((state) => ({
							...state,
							notifications: [data.notification, ...state.notifications],
							unreadCount: state.unreadCount + 1
						}));
					}
				} catch (error) {
					console.error('Error processing WebSocket message:', error);
				}
			};

			return { socket, close };
		} catch (error) {
			console.error('Error setting up WebSocket:', error);
			return null;
		}
	};

	return {
		subscribe,

		// Initialize notifications
		initialize: () => {
			if (!browser) return;

			// Load notifications
			notificationsStore.loadNotifications();

			// Setup subscription to auth store
			const unsubscribe = isAuthenticated.subscribe(($isAuthenticated) => {
				if ($isAuthenticated) {
					// Connect WebSocket when authenticated
					const connection = setupWebSocket();
					if (connection) {
						update((state) => ({ ...state, wsConnection: connection }));
					}
				} else {
					// Disconnect and clear notifications when logged out
					update((state) => {
						if (state.wsConnection) {
							state.wsConnection.close();
						}
						return {
							...initialState,
							wsConnection: null,
							isConnected: false
						};
					});
				}
			});

			// Return cleanup function
			return () => {
				unsubscribe();
				const store = get({ subscribe });
				if (store.wsConnection) {
					store.wsConnection.close();
				}
			};
		},

		// Load notifications
		loadNotifications: async (isRead = null) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const filters = {};
				if (isRead !== null) {
					filters.is_read = isRead;
				}

				const response = await notificationsService.getMyNotifications(filters);

				// Count unread notifications
				const unreadCount = isRead === true ? 0 : response.filter((n) => !n.is_read).length;

				update((state) => ({
					...state,
					notifications: response,
					unreadCount,
					isLoading: false
				}));

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load unread notifications
		loadUnreadNotifications: async () => {
			return notificationsStore.loadNotifications(false);
		},

		// Mark notification as read
		markAsRead: async (id) => {
			try {
				await notificationsService.markAsRead(id);

				update((state) => {
					const updatedNotifications = state.notifications.map((n) =>
						n.id === id ? { ...n, is_read: true } : n
					);

					// Recalculate unread count
					const unreadCount = updatedNotifications.filter((n) => !n.is_read).length;

					return {
						...state,
						notifications: updatedNotifications,
						unreadCount
					};
				});
			} catch (error) {
				console.error('Error marking notification as read:', error);
			}
		},

		// Mark all notifications as read
		markAllAsRead: async () => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				await notificationsService.markAllAsRead();

				update((state) => {
					const updatedNotifications = state.notifications.map((n) => ({ ...n, is_read: true }));

					return {
						...state,
						notifications: updatedNotifications,
						unreadCount: 0,
						isLoading: false
					};
				});
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Clear error state
		clearError: () => {
			update((state) => ({ ...state, error: null }));
		}
	};
};

// Create the store
export const notificationsStore = createNotificationsStore();

// Initialize notifications store when in browser context
if (browser) {
	const cleanup = notificationsStore.initialize();

	// Clean up on page unload if needed
	if (typeof window !== 'undefined') {
		window.addEventListener('beforeunload', cleanup);
	}
}

// Derived stores
export const notifications = derived(notificationsStore, ($store) => $store.notifications);
export const unreadNotificationsCount = derived(notificationsStore, ($store) => $store.unreadCount);
export const notificationsLoading = derived(notificationsStore, ($store) => $store.isLoading);
export const notificationsError = derived(notificationsStore, ($store) => $store.error);
export const notificationsConnected = derived(notificationsStore, ($store) => $store.isConnected);

// Derived store for getting unread notifications
export const unreadNotifications = derived(notifications, ($notifications) =>
	$notifications.filter((n) => !n.is_read)
);
