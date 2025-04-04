import { writable, derived, get } from 'svelte/store';
import propertiesService from '$lib/services/properties';

const createPropertiesStore = () => {
	const initialState = {
		properties: [],
		myProperties: [],
		currentProperty: null,
		isLoading: false,
		error: null,
		filters: {
			property_type: null,
			city: null,
			district: null,
			status: null,
			bedrooms: null,
			bathrooms: null,
			search: null,
			ordering: null
		},
		pagination: {
			page: 1,
			pageSize: 10,
			totalItems: 0,
			totalPages: 0
		}
	};

	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		// Load properties with optional filters
		loadProperties: async (filters = {}, page = 1, pageSize = 10) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null,
				filters: { ...state.filters, ...filters },
				pagination: { ...state.pagination, page, pageSize }
			}));

			try {
				const queryParams = {
					...filters,
					page,
					page_size: pageSize
				};

				const response = await propertiesService.getProperties(queryParams);

				update((state) => ({
					...state,
					properties: response.results,
					isLoading: false,
					pagination: {
						page,
						pageSize,
						totalItems: response.count,
						totalPages: Math.ceil(response.count / pageSize)
					}
				}));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
			}
		},

		// Load property details by slug
		loadPropertyBySlug: async (slug) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getPropertyBySlug(slug);
				update((state) => ({ ...state, currentProperty: response, isLoading: false }));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load user's own properties
		loadMyProperties: async () => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getMyProperties();
				update((state) => ({ ...state, myProperties: response, isLoading: false }));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Create a new property
		createProperty: async (propertyData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.createProperty(propertyData);

				// Add to myProperties list
				update((state) => ({
					...state,
					myProperties: [response, ...state.myProperties],
					isLoading: false
				}));

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Update an existing property
		updateProperty: async (id, propertyData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.updateProperty(id, propertyData);

				// Update in both lists if present
				update((state) => {
					const updatedProperties = state.properties.map((p) => (p.id === id ? response : p));

					const updatedMyProperties = state.myProperties.map((p) => (p.id === id ? response : p));

					return {
						...state,
						properties: updatedProperties,
						myProperties: updatedMyProperties,
						currentProperty: state.currentProperty?.id === id ? response : state.currentProperty,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Clear current property
		clearCurrentProperty: () => {
			update((state) => ({ ...state, currentProperty: null }));
		},

		// Update filters
		setFilters: (filters) => {
			update((state) => ({
				...state,
				filters: { ...state.filters, ...filters }
			}));

			// Reload properties with new filters
			const storeState = get({ subscribe });
			return propertiesStore.loadProperties(
				storeState.filters,
				1, // Reset to first page when filters change
				storeState.pagination.pageSize
			);
		},

		// Reset filters
		resetFilters: () => {
			const defaultFilters = {
				property_type: null,
				city: null,
				district: null,
				status: null,
				bedrooms: null,
				bathrooms: null,
				search: null,
				ordering: null
			};

			update((state) => ({ ...state, filters: defaultFilters }));

			// Reload properties with reset filters
			const storeState = get({ subscribe });
			return propertiesStore.loadProperties({}, 1, storeState.pagination.pageSize);
		},

		// Clear error state
		clearError: () => {
			update((state) => ({ ...state, error: null }));
		}
	};
};

// Create the store
export const propertiesStore = createPropertiesStore();

// Derived stores
export const properties = derived(propertiesStore, ($store) => $store.properties);
export const myProperties = derived(propertiesStore, ($store) => $store.myProperties);
export const currentProperty = derived(propertiesStore, ($store) => $store.currentProperty);
export const propertiesLoading = derived(propertiesStore, ($store) => $store.isLoading);
export const propertiesError = derived(propertiesStore, ($store) => $store.error);
export const propertyFilters = derived(propertiesStore, ($store) => $store.filters);
export const propertyPagination = derived(propertiesStore, ($store) => $store.pagination);
