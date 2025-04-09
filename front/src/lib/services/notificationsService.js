import { API_URL } from '$lib/config/constants';

/**
 * Notifications service for managing user notifications in the real estate auction platform
 */
class NotificationsService {
	constructor() {
		this.baseUrl = `${API_URL}/notifications/`;
	}

	/**
	 * Get headers for API requests
	 * @returns {Object} Headers object with Authorization token
	 */
	getHeaders() {
		const headers = {
			'Content-Type': 'application/json'
		};

		const token = localStorage.getItem('auth_token');
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		return headers;
	}

	/**
	 * Get all notifications with optional filters
	 * @param {Object} filters - Filter parameters
	 * @returns {Promise<Object>} List of notifications with pagination
	 */
	async getNotifications(filters = {}) {
		// Build query string from filters
		const queryParams = new URLSearchParams();

		Object.keys(filters).forEach((key) => {
			if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
				queryParams.append(key, filters[key]);
			}
		});

		const response = await fetch(`${this.baseUrl}?${queryParams.toString()}`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch notifications');
		}

		return await response.json();
	}

	/**
	 * Get a single notification by ID
	 * @param {string} notificationId - Notification ID
	 * @returns {Promise<Object>} Notification details
	 */
	async getNotification(notificationId) {
		const response = await fetch(`${this.baseUrl}${notificationId}/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch notification');
		}

		return await response.json();
	}

	/**
	 * Update a notification
	 * @param {string} notificationId - Notification ID
	 * @param {Object} notificationData - Updated notification data
	 * @returns {Promise<Object>} Updated notification
	 */
	async updateNotification(notificationId, notificationData) {
		const response = await fetch(`${this.baseUrl}${notificationId}/edit/`, {
			method: 'PATCH',
			headers: this.getHeaders(),
			body: JSON.stringify(notificationData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update notification');
		}

		return await response.json();
	}

	/**
	 * Delete a notification
	 * @param {string} notificationId - Notification ID
	 * @returns {Promise<boolean>} Success status
	 */
	async deleteNotification(notificationId) {
		const response = await fetch(`${this.baseUrl}${notificationId}/delete/`, {
			method: 'DELETE',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to delete notification');
		}

		return true;
	}

	/**
	 * Mark all notifications as read
	 * @returns {Promise<boolean>} Success status
	 */
	async markAllAsRead() {
		const response = await fetch(`${this.baseUrl}mark-all-read/`, {
			method: 'POST',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to mark all notifications as read');
		}

		return true;
	}

	/**
	 * Clear all notifications
	 * @returns {Promise<boolean>} Success status
	 */
	async clearAllNotifications() {
		const response = await fetch(`${this.baseUrl}clear-all/`, {
			method: 'DELETE',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to clear notifications');
		}

		return true;
	}

	/**
	 * Get unread notification count
	 * @returns {Promise<Object>} Unread count
	 */
	async getUnreadCount() {
		const response = await fetch(`${this.baseUrl}unread-count/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch unread count');
		}

		return await response.json();
	}

	/**
	 * Register push notification device token
	 * @param {string} deviceToken - Device token for push notifications
	 * @param {string} deviceType - Device type (web, ios, android)
	 * @returns {Promise<Object>} Registration result
	 */
	async registerPushToken(deviceToken, deviceType = 'web') {
		const response = await fetch(`${API_URL}/notifications/register-device/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify({
				device_token: deviceToken,
				device_type: deviceType
			})
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to register device token');
		}

		return await response.json();
	}

	/**
	 * Unregister push notification device token
	 * @param {string} deviceToken - Device token to unregister
	 * @returns {Promise<boolean>} Success status
	 */
	async unregisterPushToken(deviceToken) {
		const response = await fetch(`${API_URL}/notifications/unregister-device/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify({
				device_token: deviceToken
			})
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to unregister device token');
		}

		return true;
	}

	/**
	 * Get notification settings
	 * @returns {Promise<Object>} Notification settings
	 */
	async getNotificationSettings() {
		const response = await fetch(`${API_URL}/notifications/settings/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch notification settings');
		}

		return await response.json();
	}

	/**
	 * Update notification settings
	 * @param {Object} settings - Updated notification settings
	 * @returns {Promise<Object>} Updated settings
	 */
	async updateNotificationSettings(settings) {
		const response = await fetch(`${API_URL}/notifications/settings/`, {
			method: 'PATCH',
			headers: this.getHeaders(),
			body: JSON.stringify(settings)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update notification settings');
		}

		return await response.json();
	}
}

// Create and export a singleton instance
const notificationsService = new NotificationsService();
export default notificationsService;
