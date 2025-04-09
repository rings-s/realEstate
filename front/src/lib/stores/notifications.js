import { writable, derived } from 'svelte/store';
import { get } from 'svelte/store';
import { uiStore } from '$lib/stores/ui';
import { t } from '$lib/config/translations';
import { language } from '$lib/stores/ui';
import notificationsService from '$lib/services/notificationsService';

// Initial state
const initialState = {
	notificationsList: [],
	unreadCount: 0,
	isLoading: false,
	error: null,
	filters: {
		notification_type: '',
		is_read: '',
		is_important: '',
		search: '',
		page: 1,
		page_size: 20
	},
	pagination: {
		page: 1,
		totalPages: 1,
		totalItems: 0,
		hasNext: false,
		hasPrev: false
	}
};

// Create store
function createNotificationsStore() {
	const { subscribe, set, update } = writable({ ...initialState });

	return {
		subscribe,

		/**
		 * Reset store to initial state
		 */
		reset: () => set({ ...initialState }),

		/**
		 * Load notifications with optional filters
		 * @param {object} filters - Filter parameters
		 */
		loadNotifications: async (filters = {}) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				// Merge existing filters with new filters
				const mergedFilters = {
					...get({ subscribe }).filters,
					...filters,
					page: filters.page || get({ subscribe }).filters.page,
					page_size: filters.page_size || get({ subscribe }).filters.page_size
				};

				const response = await notificationsService.getNotifications(mergedFilters);

				// Update pagination info
				const pagination = {
					page: response.page || 1,
					totalPages: response.total_pages || 1,
					totalItems: response.count || 0,
					hasNext: response.page < response.total_pages,
					hasPrev: response.page > 1
				};

				update((state) => ({
					...state,
					notificationsList: response.results || [],
					filters: mergedFilters,
					pagination,
					isLoading: false
				}));

				// Also update unread count
				notificationsStore.getUnreadCount();

				return response.results || [];
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to load notifications'
				}));

				addToast(
					t('notifications_load_error', get(language), { default: 'فشل تحميل الإشعارات' }),
					'error'
				);

				return [];
			}
		},

		/**
		 * Get notification unread count
		 */
		getUnreadCount: async () => {
			try {
				const result = await notificationsService.getUnreadCount();

				update((state) => ({
					...state,
					unreadCount: result.unread_count || 0
				}));

				return result.unread_count || 0;
			} catch (error) {
				console.error('Failed to get unread notification count:', error);
				return 0;
			}
		},

		/**
		 * Mark a notification as read
		 * @param {string} notificationId - Notification ID
		 */
		markAsRead: async (notificationId) => {
			try {
				const updatedNotification = await notificationsService.updateNotification(notificationId, {
					is_read: true,
					read_at: new Date().toISOString()
				});

				update((state) => ({
					...state,
					notificationsList: state.notificationsList.map((n) =>
						n.id === notificationId ? updatedNotification : n
					),
					unreadCount: Math.max(0, state.unreadCount - 1)
				}));

				return updatedNotification;
			} catch (error) {
				console.error('Failed to mark notification as read:', error);
				return null;
			}
		},

		/**
		 * Mark all notifications as read
		 */
		markAllAsRead: async () => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await notificationsService.markAllAsRead();

				update((state) => ({
					...state,
					notificationsList: state.notificationsList.map((n) => ({
						...n,
						is_read: true,
						read_at: n.read_at || new Date().toISOString()
					})),
					unreadCount: 0,
					isLoading: false
				}));

				addToast(
					t('all_marked_read', get(language), { default: 'تم تحديد جميع الإشعارات كمقروءة' }),
					'success'
				);

				return true;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to mark all notifications as read'
				}));

				addToast(
					t('mark_all_read_error', get(language), { default: 'فشل تحديد جميع الإشعارات كمقروءة' }),
					'error'
				);

				return false;
			}
		},

		/**
		 * Delete a notification
		 * @param {string} notificationId - Notification ID
		 */
		deleteNotification: async (notificationId) => {
			try {
				await notificationsService.deleteNotification(notificationId);

				update((state) => ({
					...state,
					notificationsList: state.notificationsList.filter((n) => n.id !== notificationId),
					// If the notification was unread, decrement the unread count
					unreadCount: state.notificationsList.find((n) => n.id === notificationId && !n.is_read)
						? Math.max(0, state.unreadCount - 1)
						: state.unreadCount
				}));

				return true;
			} catch (error) {
				console.error('Failed to delete notification:', error);
				return false;
			}
		},

		/**
		 * Clear all notifications
		 */
		clearAllNotifications: async () => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await notificationsService.clearAllNotifications();

				update((state) => ({
					...state,
					notificationsList: [],
					unreadCount: 0,
					isLoading: false
				}));

				addToast(
					t('notifications_cleared', get(language), { default: 'تم مسح جميع الإشعارات' }),
					'success'
				);

				return true;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to clear notifications'
				}));

				addToast(
					t('clear_notifications_error', get(language), { default: 'فشل مسح الإشعارات' }),
					'error'
				);

				return false;
			}
		},

		/**
		 * Change page in pagination
		 * @param {number} page - Page number
		 */
		changePage: (page) => {
			update((state) => {
				// Don't allow invalid page numbers
				if (page < 1 || page > state.pagination.totalPages) {
					return state;
				}

				// Update filters with new page number
				const newFilters = {
					...state.filters,
					page
				};

				// Load notifications with new page
				notificationsStore.loadNotifications(newFilters);

				return {
					...state,
					filters: newFilters
				};
			});
		},

		/**
		 * Update filters and load notifications
		 * @param {object} newFilters - New filter values
		 */
		updateFilters: (newFilters) => {
			// Reset to page 1 when filters change
			const filtersWithPage = {
				...newFilters,
				page: 1
			};

			notificationsStore.loadNotifications(filtersWithPage);
		},

		/**
		 * Poll for new notifications
		 * @param {number} interval - Polling interval in ms (default: 30000)
		 * @returns {function} Function to stop polling
		 */
		startPolling: (interval = 30000) => {
			const intervalId = setInterval(async () => {
				await notificationsStore.getUnreadCount();

				// If we're on the notifications page, also refresh the list
				const currentFilters = get({ subscribe }).filters;
				if (window.location.pathname.includes('/notifications')) {
					await notificationsStore.loadNotifications(currentFilters);
				}
			}, interval);

			// Return function to stop polling
			return () => clearInterval(intervalId);
		},

		/**
		 * Process a new push notification
		 * @param {object} notification - Notification data
		 */
		processPushNotification: (notification) => {
			// Add the notification to the list if it's not already there
			update((state) => {
				// Check if notification already exists
				const exists = state.notificationsList.some((n) => n.id === notification.id);

				if (!exists) {
					// Add to list and increment unread count
					return {
						...state,
						notificationsList: [notification, ...state.notificationsList],
						unreadCount: state.unreadCount + 1
					};
				}

				return state;
			});

			// Show toast for the notification
			addToast(
				notification.title || t('new_notification', get(language), { default: 'إشعار جديد' }),
				'info',
				7000
			);
		}
	};
}

// Create store instance
const notificationsStore = createNotificationsStore();

// Create derived stores for convenience
export const notificationsList = derived(
	notificationsStore,
	($notifications) => $notifications.notificationsList
);

export const unreadCount = derived(
	notificationsStore,
	($notifications) => $notifications.unreadCount
);

export const isLoading = derived(notificationsStore, ($notifications) => $notifications.isLoading);

export const error = derived(notificationsStore, ($notifications) => $notifications.error);

export const filters = derived(notificationsStore, ($notifications) => $notifications.filters);

export const pagination = derived(
	notificationsStore,
	($notifications) => $notifications.pagination
);

// Export the store and its methods
export default notificationsStore;
