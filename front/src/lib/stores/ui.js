import { writable, derived } from 'svelte/store';

// Toast notification types
export const TOAST_TYPES = {
	SUCCESS: 'success',
	ERROR: 'error',
	INFO: 'info',
	WARNING: 'warning'
};

// Create UI store with default values
const createUiStore = () => {
	const initialState = {
		isLoading: false,
		loadingMessage: '',
		globalError: null,
		toasts: [],
		modals: {
			// Map of modal IDs to their open state
			// e.g. { login: false, confirmDelete: false }
		},
		activeModals: [], // Stack of active modal IDs
		sidebarOpen: false,
		theme: 'light', // 'light' or 'dark'
		direction: 'rtl', // 'rtl' for Arabic
		fontSize: 'medium', // 'small', 'medium', 'large'
		highContrast: false,
		confirmDialog: {
			isOpen: false,
			title: '',
			message: '',
			confirmText: 'نعم',
			cancelText: 'لا',
			onConfirm: null,
			onCancel: null,
			type: 'warning' // One of: info, warning, danger, success
		}
	};

	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		// Loading state
		startLoading: (message = 'جاري التحميل...') => {
			update((state) => ({ ...state, isLoading: true, loadingMessage: message }));
		},

		stopLoading: () => {
			update((state) => ({ ...state, isLoading: false, loadingMessage: '' }));
		},

		// Error handling
		setGlobalError: (error) => {
			update((state) => ({ ...state, globalError: error }));
		},

		clearGlobalError: () => {
			update((state) => ({ ...state, globalError: null }));
		},

		// Toast notifications
		addToast: (message, type = TOAST_TYPES.INFO, duration = 5000, id = Date.now()) => {
			const toast = { id, message, type, duration };

			update((state) => ({
				...state,
				toasts: [...state.toasts, toast]
			}));

			// Auto remove toast after duration
			if (duration > 0) {
				setTimeout(() => {
					uiStore.removeToast(id);
				}, duration);
			}

			return id;
		},

		removeToast: (id) => {
			update((state) => ({
				...state,
				toasts: state.toasts.filter((toast) => toast.id !== id)
			}));
		},

		clearToasts: () => {
			update((state) => ({ ...state, toasts: [] }));
		},

		// Modal management
		registerModal: (modalId, initialState = false) => {
			update((state) => ({
				...state,
				modals: {
					...state.modals,
					[modalId]: initialState
				}
			}));
		},

		openModal: (modalId) => {
			update((state) => {
				// Add to active modals stack only if not already open
				const newActiveModals = state.modals[modalId]
					? state.activeModals
					: [...state.activeModals, modalId];

				return {
					...state,
					modals: {
						...state.modals,
						[modalId]: true
					},
					activeModals: newActiveModals
				};
			});
		},

		closeModal: (modalId) => {
			update((state) => ({
				...state,
				modals: {
					...state.modals,
					[modalId]: false
				},
				// Remove from active modals stack
				activeModals: state.activeModals.filter((id) => id !== modalId)
			}));
		},

		closeAllModals: () => {
			update((state) => {
				const closedModals = {};
				Object.keys(state.modals).forEach((key) => {
					closedModals[key] = false;
				});

				return {
					...state,
					modals: closedModals,
					activeModals: []
				};
			});
		},

		// Sidebar
		toggleSidebar: () => {
			update((state) => ({ ...state, sidebarOpen: !state.sidebarOpen }));
		},

		setSidebarOpen: (isOpen) => {
			update((state) => ({ ...state, sidebarOpen: isOpen }));
		},

		// Theme and accessibility settings
		setTheme: (theme) => {
			if (theme !== 'light' && theme !== 'dark') return;

			update((state) => ({ ...state, theme }));

			// Persist theme selection
			if (typeof localStorage !== 'undefined') {
				localStorage.setItem('theme', theme);

				// Apply theme to document
				if (theme === 'dark') {
					document.documentElement.classList.add('dark');
				} else {
					document.documentElement.classList.remove('dark');
				}
			}
		},

		setDirection: (direction) => {
			if (direction !== 'rtl' && direction !== 'ltr') return;

			update((state) => ({ ...state, direction }));

			// Apply direction to document
			if (typeof document !== 'undefined') {
				document.dir = direction;
				document.documentElement.setAttribute('dir', direction);
			}
		},

		setFontSize: (fontSize) => {
			if (!['small', 'medium', 'large'].includes(fontSize)) return;

			update((state) => ({ ...state, fontSize }));

			// Apply font size to document
			if (typeof document !== 'undefined') {
				document.documentElement.classList.remove('text-small', 'text-medium', 'text-large');
				document.documentElement.classList.add(`text-${fontSize}`);
			}
		},

		setHighContrast: (enabled) => {
			update((state) => ({ ...state, highContrast: enabled }));

			// Apply high contrast to document
			if (typeof document !== 'undefined') {
				if (enabled) {
					document.documentElement.classList.add('high-contrast');
				} else {
					document.documentElement.classList.remove('high-contrast');
				}
			}
		},

		// Confirmation dialog
		showConfirmDialog: (options) => {
			const defaults = {
				title: 'تأكيد',
				message: 'هل أنت متأكد؟',
				confirmText: 'نعم',
				cancelText: 'لا',
				type: 'warning',
				onConfirm: () => {},
				onCancel: () => {}
			};

			const dialogOptions = { ...defaults, ...options };

			update((state) => ({
				...state,
				confirmDialog: {
					...dialogOptions,
					isOpen: true
				}
			}));
		},

		closeConfirmDialog: (confirmed = false) => {
			update((state) => {
				// Call appropriate callback
				if (confirmed && state.confirmDialog.onConfirm) {
					state.confirmDialog.onConfirm();
				} else if (!confirmed && state.confirmDialog.onCancel) {
					state.confirmDialog.onCancel();
				}

				return {
					...state,
					confirmDialog: {
						...state.confirmDialog,
						isOpen: false
					}
				};
			});
		},

		// Reset UI to initial state
		reset: () => {
			set(initialState);
		}
	};
};

// Create the store
export const uiStore = createUiStore();

// Derived stores
export const isLoading = derived(uiStore, ($ui) => $ui.isLoading);
export const loadingMessage = derived(uiStore, ($ui) => $ui.loadingMessage);
export const globalError = derived(uiStore, ($ui) => $ui.globalError);
export const toasts = derived(uiStore, ($ui) => $ui.toasts);
export const sidebarOpen = derived(uiStore, ($ui) => $ui.sidebarOpen);
export const theme = derived(uiStore, ($ui) => $ui.theme);
export const direction = derived(uiStore, ($ui) => $ui.direction);
export const fontSize = derived(uiStore, ($ui) => $ui.fontSize);
export const highContrast = derived(uiStore, ($ui) => $ui.highContrast);
export const confirmDialog = derived(uiStore, ($ui) => $ui.confirmDialog);
export const activeModals = derived(uiStore, ($ui) => $ui.activeModals);

// Helper to check if a specific modal is open
export const isModalOpen = (modalId) => derived(uiStore, ($ui) => !!$ui.modals[modalId]);

// Initialize theme and accessibility settings from localStorage if available
if (typeof localStorage !== 'undefined' && typeof document !== 'undefined') {
	const savedTheme = localStorage.getItem('theme');
	if (savedTheme) {
		uiStore.setTheme(savedTheme);
	} else {
		// Default to light theme
		uiStore.setTheme('light');
	}

	// Set RTL direction for Arabic
	uiStore.setDirection('rtl');
}
