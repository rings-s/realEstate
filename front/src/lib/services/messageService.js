import { API_URL } from '$lib/config/constants';

/**
 * Messages service for managing threads and messages in the real estate auction platform
 */
class MessagesService {
	constructor() {
		this.baseUrl = `${API_URL}/threads/`;
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
	 * Get all threads with optional filters
	 * @param {Object} filters - Filter parameters
	 * @returns {Promise<Object>} List of threads with pagination
	 */
	async getThreads(filters = {}) {
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
			throw new Error(error.error || 'Failed to fetch threads');
		}

		return await response.json();
	}

	/**
	 * Get a single thread by ID
	 * @param {string} threadId - Thread ID
	 * @returns {Promise<Object>} Thread details
	 */
	async getThread(threadId) {
		const response = await fetch(`${this.baseUrl}${threadId}/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch thread');
		}

		return await response.json();
	}

	/**
	 * Create a new thread
	 * @param {Object} threadData - Thread data
	 * @returns {Promise<Object>} Created thread
	 */
	async createThread(threadData) {
		const response = await fetch(this.baseUrl, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(threadData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to create thread');
		}

		return await response.json();
	}

	/**
	 * Update a thread
	 * @param {string} threadId - Thread ID
	 * @param {Object} threadData - Updated thread data
	 * @returns {Promise<Object>} Updated thread
	 */
	async updateThread(threadId, threadData) {
		const response = await fetch(`${this.baseUrl}${threadId}/edit/`, {
			method: 'PATCH',
			headers: this.getHeaders(),
			body: JSON.stringify(threadData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update thread');
		}

		return await response.json();
	}

	/**
	 * Delete a thread
	 * @param {string} threadId - Thread ID
	 * @returns {Promise<boolean>} Success status
	 */
	async deleteThread(threadId) {
		const response = await fetch(`${this.baseUrl}${threadId}/delete/`, {
			method: 'DELETE',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to delete thread');
		}

		return true;
	}

	/**
	 * Get messages for a thread with optional filters
	 * @param {string} threadId - Thread ID
	 * @param {Object} filters - Filter parameters
	 * @returns {Promise<Object>} List of messages with pagination
	 */
	async getMessages(threadId, filters = {}) {
		// Build query string from filters
		const queryParams = new URLSearchParams();

		Object.keys(filters).forEach((key) => {
			if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
				queryParams.append(key, filters[key]);
			}
		});

		const response = await fetch(`${this.baseUrl}${threadId}/messages/?${queryParams.toString()}`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch messages');
		}

		return await response.json();
	}

	/**
	 * Send a message in a thread
	 * @param {string} threadId - Thread ID
	 * @param {Object} messageData - Message data
	 * @returns {Promise<Object>} Created message
	 */
	async sendMessage(threadId, messageData) {
		// Handle file attachments
		if (messageData.file) {
			return this.sendMessageWithFile(threadId, messageData);
		}

		const response = await fetch(`${this.baseUrl}${threadId}/messages/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(messageData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to send message');
		}

		return await response.json();
	}

	/**
	 * Send a message with file attachment
	 * @param {string} threadId - Thread ID
	 * @param {Object} messageData - Message data with file
	 * @returns {Promise<Object>} Created message
	 */
	async sendMessageWithFile(threadId, messageData) {
		const formData = new FormData();

		// Add text content
		formData.append('content', messageData.content || '');

		// Add message type
		formData.append('message_type', messageData.file.type.startsWith('image/') ? 'image' : 'file');

		// Add other fields
		if (messageData.reply_to) {
			formData.append('reply_to', messageData.reply_to);
		}

		if (messageData.is_important) {
			formData.append('is_important', messageData.is_important);
		}

		// Add file
		formData.append('attachment', messageData.file);

		// Get headers but remove Content-Type
		const headers = this.getHeaders();
		delete headers['Content-Type'];

		const response = await fetch(`${this.baseUrl}${threadId}/messages/`, {
			method: 'POST',
			headers: {
				Authorization: headers.Authorization
			},
			body: formData
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to send message with attachment');
		}

		return await response.json();
	}

	/**
	 * Update a message
	 * @param {string} messageId - Message ID
	 * @param {Object} messageData - Updated message data
	 * @returns {Promise<Object>} Updated message
	 */
	async updateMessage(messageId, messageData) {
		const response = await fetch(`${API_URL}/messages/${messageId}/edit/`, {
			method: 'PATCH',
			headers: this.getHeaders(),
			body: JSON.stringify(messageData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update message');
		}

		return await response.json();
	}

	/**
	 * Delete a message
	 * @param {string} messageId - Message ID
	 * @returns {Promise<boolean>} Success status
	 */
	async deleteMessage(messageId) {
		const response = await fetch(`${API_URL}/messages/${messageId}/delete/`, {
			method: 'DELETE',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to delete message');
		}

		return true;
	}

	/**
	 * Get participants for a thread
	 * @param {string} threadId - Thread ID
	 * @returns {Promise<Object>} List of participants
	 */
	async getParticipants(threadId) {
		const response = await fetch(`${this.baseUrl}${threadId}/participants/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch participants');
		}

		return await response.json();
	}

	/**
	 * Add a participant to a thread
	 * @param {string} threadId - Thread ID
	 * @param {Object} participantData - Participant data
	 * @returns {Promise<Object>} Created participant
	 */
	async addParticipant(threadId, participantData) {
		const response = await fetch(`${this.baseUrl}${threadId}/participants/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(participantData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to add participant');
		}

		return await response.json();
	}

	/**
	 * Remove a participant from a thread
	 * @param {string} threadId - Thread ID
	 * @param {string} participantId - Participant ID
	 * @returns {Promise<boolean>} Success status
	 */
	async removeParticipant(threadId, participantId) {
		const response = await fetch(
			`${this.baseUrl}${threadId}/participants/${participantId}/delete/`,
			{
				method: 'DELETE',
				headers: this.getHeaders()
			}
		);

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to remove participant');
		}

		return true;
	}

	/**
	 * Get unread message count
	 * @returns {Promise<Object>} Unread count
	 */
	async getUnreadCount() {
		const response = await fetch(`${API_URL}/messages/unread-count/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch unread count');
		}

		return await response.json();
	}
}

// Create and export a singleton instance
const messagesService = new MessagesService();
export default messagesService;
