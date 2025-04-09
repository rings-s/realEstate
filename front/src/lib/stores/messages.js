import { writable, derived } from 'svelte/store';
import { addToast } from '$lib/stores/ui';
import { t } from '$lib/config/translations';
import { language } from '$lib/stores/ui';
import { get } from 'svelte/store';
import messagesService from '$lib/services/messages';

// Initial state
const initialState = {
	threads: [],
	currentThread: null,
	currentMessages: [],
	currentParticipants: [],
	isLoading: false,
	isLoadingMessages: false,
	error: null,
	filters: {
		thread_type: '',
		status: 'active',
		is_private: '',
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
function createMessagesStore() {
	const { subscribe, set, update } = writable({ ...initialState });

	return {
		subscribe,

		/**
		 * Reset store to initial state
		 */
		reset: () => set({ ...initialState }),

		/**
		 * Load message threads with optional filters
		 * @param {object} filters - Filter parameters
		 */
		loadThreads: async (filters = {}) => {
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

				const response = await messagesService.getThreads(mergedFilters);

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
					threads: response.results || [],
					filters: mergedFilters,
					pagination,
					isLoading: false
				}));

				return response.results || [];
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to load message threads'
				}));

				addToast(
					t('threads_load_error', get(language), { default: 'فشل تحميل المحادثات' }),
					'error'
				);

				return [];
			}
		},

		/**
		 * Load a single thread and its messages by ID
		 * @param {string} threadId - Thread ID
		 */
		loadThread: async (threadId) => {
			update((state) => ({
				...state,
				isLoading: true,
				isLoadingMessages: true,
				error: null
			}));

			try {
				// Load thread details
				const thread = await messagesService.getThread(threadId);

				update((state) => ({
					...state,
					currentThread: thread,
					isLoading: false
				}));

				// Load messages for this thread
				const messagesResponse = await messagesService.getMessages(threadId);
				const participantsResponse = await messagesService.getParticipants(threadId);

				update((state) => ({
					...state,
					currentMessages: messagesResponse.results || [],
					currentParticipants: participantsResponse.results || [],
					isLoadingMessages: false
				}));

				return {
					thread,
					messages: messagesResponse.results || [],
					participants: participantsResponse.results || []
				};
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					isLoadingMessages: false,
					error: error.message || 'Failed to load thread'
				}));

				addToast(t('thread_load_error', get(language), { default: 'فشل تحميل المحادثة' }), 'error');

				return null;
			}
		},

		/**
		 * Create a new thread
		 * @param {object} threadData - Thread data
		 */
		createThread: async (threadData) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const newThread = await messagesService.createThread(threadData);

				update((state) => ({
					...state,
					currentThread: newThread,
					threads: [newThread, ...state.threads],
					isLoading: false
				}));

				addToast(
					t('thread_created', get(language), { default: 'تم إنشاء المحادثة بنجاح' }),
					'success'
				);

				return newThread;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to create thread'
				}));

				addToast(
					t('thread_create_error', get(language), { default: 'فشل إنشاء المحادثة' }),
					'error'
				);

				return null;
			}
		},

		/**
		 * Send a message in a thread
		 * @param {string} threadId - Thread ID
		 * @param {object} messageData - Message data
		 */
		sendMessage: async (threadId, messageData) => {
			update((state) => ({
				...state,
				isLoadingMessages: true,
				error: null
			}));

			try {
				const newMessage = await messagesService.sendMessage(threadId, messageData);

				update((state) => ({
					...state,
					currentMessages: [...state.currentMessages, newMessage],
					isLoadingMessages: false
				}));

				// Also update the thread's last_message_at
				if (state.currentThread) {
					update((state) => ({
						...state,
						currentThread: {
							...state.currentThread,
							last_message_at: new Date().toISOString()
						},
						threads: state.threads.map((t) =>
							t.id === threadId ? { ...t, last_message_at: new Date().toISOString() } : t
						)
					}));
				}

				return newMessage;
			} catch (error) {
				update((state) => ({
					...state,
					isLoadingMessages: false,
					error: error.message || 'Failed to send message'
				}));

				addToast(t('message_send_error', get(language), { default: 'فشل إرسال الرسالة' }), 'error');

				return null;
			}
		},

		/**
		 * Add a participant to a thread
		 * @param {string} threadId - Thread ID
		 * @param {object} participantData - Participant data
		 */
		addParticipant: async (threadId, participantData) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const newParticipant = await messagesService.addParticipant(threadId, participantData);

				update((state) => ({
					...state,
					currentParticipants: [...state.currentParticipants, newParticipant],
					isLoading: false
				}));

				addToast(
					t('participant_added', get(language), { default: 'تمت إضافة المشارك بنجاح' }),
					'success'
				);

				return newParticipant;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to add participant'
				}));

				addToast(
					t('participant_add_error', get(language), { default: 'فشل إضافة المشارك' }),
					'error'
				);

				return null;
			}
		},

		/**
		 * Remove a participant from a thread
		 * @param {string} threadId - Thread ID
		 * @param {string} participantId - Participant ID
		 */
		removeParticipant: async (threadId, participantId) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await messagesService.removeParticipant(threadId, participantId);

				update((state) => ({
					...state,
					currentParticipants: state.currentParticipants.filter((p) => p.id !== participantId),
					isLoading: false
				}));

				addToast(
					t('participant_removed', get(language), { default: 'تمت إزالة المشارك بنجاح' }),
					'success'
				);

				return true;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to remove participant'
				}));

				addToast(
					t('participant_remove_error', get(language), { default: 'فشل إزالة المشارك' }),
					'error'
				);

				return false;
			}
		},

		/**
		 * Mark a thread as archived
		 * @param {string} threadId - Thread ID
		 */
		archiveThread: async (threadId) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const updatedThread = await messagesService.updateThread(threadId, { status: 'archived' });

				update((state) => ({
					...state,
					currentThread: state.currentThread?.id === threadId ? updatedThread : state.currentThread,
					threads: state.threads.map((t) => (t.id === threadId ? updatedThread : t)),
					isLoading: false
				}));

				addToast(
					t('thread_archived', get(language), { default: 'تم أرشفة المحادثة بنجاح' }),
					'success'
				);

				return updatedThread;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to archive thread'
				}));

				addToast(
					t('thread_archive_error', get(language), { default: 'فشل أرشفة المحادثة' }),
					'error'
				);

				return null;
			}
		},

		/**
		 * Mark a message as read
		 * @param {string} messageId - Message ID
		 */
		markMessageAsRead: async (messageId) => {
			try {
				const updatedMessage = await messagesService.updateMessage(messageId, {
					status: 'read',
					read_at: new Date().toISOString()
				});

				update((state) => ({
					...state,
					currentMessages: state.currentMessages.map((m) =>
						m.id === messageId ? updatedMessage : m
					)
				}));

				return updatedMessage;
			} catch (error) {
				console.error('Failed to mark message as read:', error);
				return null;
			}
		},

		/**
		 * Delete a message
		 * @param {string} messageId - Message ID
		 */
		deleteMessage: async (messageId) => {
			update((state) => ({
				...state,
				isLoadingMessages: true,
				error: null
			}));

			try {
				await messagesService.deleteMessage(messageId);

				update((state) => ({
					...state,
					currentMessages: state.currentMessages.filter((m) => m.id !== messageId),
					isLoadingMessages: false
				}));

				addToast(
					t('message_deleted', get(language), { default: 'تم حذف الرسالة بنجاح' }),
					'success'
				);

				return true;
			} catch (error) {
				update((state) => ({
					...state,
					isLoadingMessages: false,
					error: error.message || 'Failed to delete message'
				}));

				addToast(t('message_delete_error', get(language), { default: 'فشل حذف الرسالة' }), 'error');

				return false;
			}
		},

		/**
		 * Delete a thread and all its messages
		 * @param {string} threadId - Thread ID
		 */
		deleteThread: async (threadId) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await messagesService.deleteThread(threadId);

				update((state) => ({
					...state,
					threads: state.threads.filter((t) => t.id !== threadId),
					currentThread: state.currentThread?.id === threadId ? null : state.currentThread,
					currentMessages: state.currentThread?.id === threadId ? [] : state.currentMessages,
					currentParticipants:
						state.currentThread?.id === threadId ? [] : state.currentParticipants,
					isLoading: false
				}));

				addToast(
					t('thread_deleted', get(language), { default: 'تم حذف المحادثة بنجاح' }),
					'success'
				);

				return true;
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'Failed to delete thread'
				}));

				addToast(t('thread_delete_error', get(language), { default: 'فشل حذف المحادثة' }), 'error');

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

				// Load threads with new page
				messagesStore.loadThreads(newFilters);

				return {
					...state,
					filters: newFilters
				};
			});
		},

		/**
		 * Update filters and load threads
		 * @param {object} newFilters - New filter values
		 */
		updateFilters: (newFilters) => {
			// Reset to page 1 when filters change
			const filtersWithPage = {
				...newFilters,
				page: 1
			};

			messagesStore.loadThreads(filtersWithPage);
		},

		/**
		 * Poll for new messages in a thread
		 * @param {string} threadId - Thread ID
		 * @param {Date} lastMessageTime - Time of last received message
		 */
		pollNewMessages: async (threadId, lastMessageTime) => {
			try {
				// Get messages newer than the last one we have
				const response = await messagesService.getMessages(threadId, {
					sent_after: lastMessageTime.toISOString()
				});

				if (response.results && response.results.length > 0) {
					update((state) => ({
						...state,
						currentMessages: [...state.currentMessages, ...response.results]
					}));

					return response.results;
				}

				return [];
			} catch (error) {
				console.error('Failed to poll for new messages:', error);
				return [];
			}
		},

		/**
		 * Get unread message count
		 */
		getUnreadCount: async () => {
			try {
				const count = await messagesService.getUnreadCount();
				return count.unread_count || 0;
			} catch (error) {
				console.error('Failed to get unread message count:', error);
				return 0;
			}
		}
	};
}

// Create store instance
const messagesStore = createMessagesStore();

// Create derived stores for convenience
export const threads = derived(messagesStore, ($messages) => $messages.threads);

export const currentThread = derived(messagesStore, ($messages) => $messages.currentThread);

export const currentMessages = derived(messagesStore, ($messages) => $messages.currentMessages);

export const currentParticipants = derived(
	messagesStore,
	($messages) => $messages.currentParticipants
);

export const isLoading = derived(messagesStore, ($messages) => $messages.isLoading);

export const isLoadingMessages = derived(messagesStore, ($messages) => $messages.isLoadingMessages);

export const error = derived(messagesStore, ($messages) => $messages.error);

export const filters = derived(messagesStore, ($messages) => $messages.filters);

export const pagination = derived(messagesStore, ($messages) => $messages.pagination);

// Export the store and its methods
export default messagesStore;
