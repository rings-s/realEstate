import api, { handleApiError } from './api';

/**
 * Message management services
 */
export default {
	/**
	 * Get list of message threads
	 * @param {Object} filters - Filter parameters
	 */
	getThreads: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/message-threads/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get thread details by slug
	 * @param {string} slug - Thread slug
	 */
	getThreadBySlug: async (slug) => {
		try {
			return await api.get(`/message-threads/by-slug/${slug}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get thread details by ID
	 * @param {string} id - Thread ID
	 */
	getThread: async (id) => {
		try {
			return await api.get(`/message-threads/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new message thread
	 * @param {Object} threadData - Thread data
	 */
	createThread: async (threadData) => {
		try {
			return await api.post('/message-threads/', threadData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get messages in a thread
	 * @param {string} threadId - Thread ID
	 */
	getMessages: async (threadId) => {
		try {
			return await api.get(`/messages/?thread=${threadId}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Send a message in a thread
	 * @param {Object} messageData - Message data
	 */
	sendMessage: async (messageData) => {
		try {
			return await api.post('/messages/', messageData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Add participant to thread
	 * @param {string} threadId - Thread ID
	 * @param {string} userId - User ID to add
	 * @param {string} role - Participant role (optional)
	 */
	addParticipant: async (threadId, userId, role = 'member') => {
		try {
			return await api.post(`/message-threads/${threadId}/add-participant/`, {
				user_id: userId,
				role
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Remove participant from thread
	 * @param {string} threadId - Thread ID
	 * @param {string} userId - User ID to remove
	 */
	removeParticipant: async (threadId, userId) => {
		try {
			return await api.post(`/message-threads/${threadId}/remove-participant/`, {
				user_id: userId
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Mark all messages in a thread as read
	 * @param {string} threadId - Thread ID
	 */
	markThreadAsRead: async (threadId) => {
		try {
			return await api.post(`/message-threads/${threadId}/mark-read/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Mark a specific message as read
	 * @param {string} messageId - Message ID
	 */
	markMessageAsRead: async (messageId) => {
		try {
			return await api.post(`/messages/${messageId}/mark-read/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Close a thread
	 * @param {string} threadId - Thread ID
	 */
	closeThread: async (threadId) => {
		try {
			return await api.post(`/message-threads/${threadId}/close/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Reopen a closed thread
	 * @param {string} threadId - Thread ID
	 */
	reopenThread: async (threadId) => {
		try {
			return await api.post(`/message-threads/${threadId}/reopen/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's threads
	 * @param {Object} filters - Filter parameters (status, unread)
	 */
	getMyThreads: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/message-threads/my-threads/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload message attachment
	 * @param {string} messageId - Message ID
	 * @param {File} file - Attachment file
	 */
	uploadAttachment: async (messageId, file) => {
		try {
			const formData = new FormData();
			formData.append('attachment', file);
			return await api.upload(`/messages/${messageId}/upload-attachment/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
