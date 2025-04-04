import { writable, derived, get } from 'svelte/store';
import propertiesService from '$lib/services/properties';
import { uiStore } from './ui';

/**
 * Create a store to manage property state
 */
const createPropertiesStore = () => {
	// Initial state with empty values
	const initialState = {
		properties: [],
		myProperties: [],
		featuredProperties: [],
		recommendedProperties: [],
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

	// Create the store with the initial state
	const { subscribe, set, update } = writable(initialState);

	// Return the store with its methods
	return {
		subscribe,

		/**
		 * Load properties with optional filters
		 * @param {Object} filters - Filter parameters
		 * @param {number} page - Page number
		 * @param {number} pageSize - Items per page
		 */
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

				// Remove any null or undefined values
				Object.keys(queryParams).forEach(
					(key) => queryParams[key] == null && delete queryParams[key]
				);

				const response = await propertiesService.getProperties(queryParams);

				update((state) => ({
					...state,
					properties: response.results || response,
					isLoading: false,
					pagination: {
						page,
						pageSize,
						totalItems: response.count || response.length || 0,
						totalPages: response.count
							? Math.ceil(response.count / pageSize)
							: Math.ceil(response.length / pageSize)
					}
				}));

				return response;
			} catch (error) {
				console.error('Error loading properties:', error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Load property details by ID
		 * @param {string} id - Property ID
		 */
		loadProperty: async (id) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getProperty(id);
				update((state) => ({ ...state, currentProperty: response, isLoading: false }));
				return response;
			} catch (error) {
				console.error(`Error loading property ${id}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Load property details by slug
		 * @param {string} slug - Property slug
		 */
		loadPropertyBySlug: async (slug) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getPropertyBySlug(slug);
				update((state) => ({ ...state, currentProperty: response, isLoading: false }));
				return response;
			} catch (error) {
				console.error(`Error loading property by slug ${slug}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Load user's own properties
		 */
		loadMyProperties: async () => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getMyProperties();
				update((state) => ({ ...state, myProperties: response, isLoading: false }));
				return response;
			} catch (error) {
				console.error('Error loading my properties:', error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Load featured properties
		 * @param {number} limit - Number of featured properties to load
		 */
		loadFeaturedProperties: async (limit = 5) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getFeaturedProperties(limit);
				update((state) => ({
					...state,
					featuredProperties: response.results || response,
					isLoading: false
				}));
				return response;
			} catch (error) {
				console.error('Error loading featured properties:', error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Load recommended properties for a specific property
		 * @param {string} propertyId - Property ID to get recommendations for
		 * @param {number} limit - Number of recommendations to fetch
		 */
		loadRecommendedProperties: async (propertyId, limit = 5) => {
			if (!propertyId) return;

			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.getRecommendedProperties(propertyId, limit);
				update((state) => ({
					...state,
					recommendedProperties: response.results || response,
					isLoading: false
				}));
				return response;
			} catch (error) {
				console.error(`Error loading recommended properties for ${propertyId}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Create a new property
		 * @param {Object} propertyData - Property data
		 */
		createProperty: async (propertyData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				// Create the property
				const response = await propertiesService.createProperty(propertyData);

				// Upload any new images if they exist in the form but not in the response
				// This is used when creating a property and uploading images in the same operation
				if (propertyData.imageFiles && propertyData.imageFiles.length) {
					try {
						const uploadResponse = await propertiesService.uploadPropertyImages(
							response.id,
							propertyData.imageFiles
						);

						// Update the property with new images
						if (uploadResponse && uploadResponse.images) {
							response.images = uploadResponse.images;
						}
					} catch (uploadError) {
						console.error('Error uploading images during property creation:', uploadError);
						// Continue even if upload fails, we already have the property created
					}
				}

				// Add to myProperties list
				update((state) => ({
					...state,
					myProperties: [response, ...state.myProperties],
					currentProperty: response,
					isLoading: false
				}));

				return response;
			} catch (error) {
				console.error('Error creating property:', error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Update an existing property
		 * @param {string} id - Property ID
		 * @param {Object} propertyData - Updated property data
		 */
		updateProperty: async (id, propertyData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.updateProperty(id, propertyData);

				// Update in all lists if present
				update((state) => {
					// Update in properties list
					const updatedProperties = state.properties.map((p) => (p.id === id ? response : p));

					// Update in myProperties list
					const updatedMyProperties = state.myProperties.map((p) => (p.id === id ? response : p));

					// Update in featuredProperties list if present
					const updatedFeaturedProperties = state.featuredProperties.map((p) =>
						p.id === id ? response : p
					);

					return {
						...state,
						properties: updatedProperties,
						myProperties: updatedMyProperties,
						featuredProperties: updatedFeaturedProperties,
						currentProperty: state.currentProperty?.id === id ? response : state.currentProperty,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				console.error(`Error updating property ${id}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Delete a property
		 * @param {string} id - Property ID
		 */
		deleteProperty: async (id) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				await propertiesService.deleteProperty(id);

				// Remove from all lists
				update((state) => {
					const properties = state.properties.filter((p) => p.id !== id);
					const myProperties = state.myProperties.filter((p) => p.id !== id);
					const featuredProperties = state.featuredProperties.filter((p) => p.id !== id);

					return {
						...state,
						properties,
						myProperties,
						featuredProperties,
						currentProperty: state.currentProperty?.id === id ? null : state.currentProperty,
						isLoading: false
					};
				});

				return true;
			} catch (error) {
				console.error(`Error deleting property ${id}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Verify a property (for inspectors)
		 * @param {string} id - Property ID
		 */
		verifyProperty: async (id) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.verifyProperty(id);

				// Update property in all lists
				update((state) => {
					const updatedPropertyData = {
						...state.currentProperty,
						is_verified: true,
						verification_date: new Date().toISOString()
					};

					// Update in properties list
					const properties = state.properties.map((p) =>
						p.id === id ? { ...p, is_verified: true } : p
					);

					// Update in myProperties list
					const myProperties = state.myProperties.map((p) =>
						p.id === id ? { ...p, is_verified: true } : p
					);

					return {
						...state,
						properties,
						myProperties,
						currentProperty:
							state.currentProperty?.id === id ? updatedPropertyData : state.currentProperty,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				console.error(`Error verifying property ${id}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Upload property images
		 * @param {string} id - Property ID
		 * @param {FileList|File[]} images - Property images
		 */
		uploadPropertyImages: async (id, images) => {
			if (!id || !images || !images.length) return;

			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.uploadPropertyImages(id, images);

				// Update property with new images
				update((state) => {
					// If currentProperty is the one being updated, add the new images
					let updatedCurrentProperty = state.currentProperty;
					if (state.currentProperty && state.currentProperty.id === id) {
						// Get current images, parse if needed
						let currentImages = [];
						try {
							if (state.currentProperty.images) {
								currentImages =
									typeof state.currentProperty.images === 'string'
										? JSON.parse(state.currentProperty.images)
										: state.currentProperty.images;
							}
						} catch (e) {
							console.error('Error parsing current images:', e);
							currentImages = [];
						}

						// Add new images
						updatedCurrentProperty = {
							...state.currentProperty,
							images: [...currentImages, ...response.images]
						};
					}

					return {
						...state,
						currentProperty: updatedCurrentProperty,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				console.error(`Error uploading images for property ${id}:`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Search properties by keyword
		 * @param {string} query - Search query
		 */
		searchProperties: async (query) => {
			if (!query) return;

			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await propertiesService.searchProperties(query);

				update((state) => ({
					...state,
					properties: response.results || response,
					isLoading: false,
					filters: {
						...state.filters,
						search: query
					}
				}));

				return response;
			} catch (error) {
				console.error(`Error searching properties with query "${query}":`, error);
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		/**
		 * Clear current property
		 */
		clearCurrentProperty: () => {
			update((state) => ({ ...state, currentProperty: null }));
		},

		/**
		 * Update filters
		 * @param {Object} filters - New filter values
		 */
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

		/**
		 * Reset filters to default values
		 */
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

		/**
		 * Clear error state
		 */
		clearError: () => {
			update((state) => ({ ...state, error: null }));
		}
	};
};

// Create the store
export const propertiesStore = createPropertiesStore();

// Derived stores for easier access to specific parts of the state
export const properties = derived(propertiesStore, ($store) => $store.properties);
export const myProperties = derived(propertiesStore, ($store) => $store.myProperties);
export const featuredProperties = derived(propertiesStore, ($store) => $store.featuredProperties);
export const recommendedProperties = derived(
	propertiesStore,
	($store) => $store.recommendedProperties
);
export const currentProperty = derived(propertiesStore, ($store) => $store.currentProperty);
export const propertiesLoading = derived(propertiesStore, ($store) => $store.isLoading);
export const propertiesError = derived(propertiesStore, ($store) => $store.error);
export const propertyFilters = derived(propertiesStore, ($store) => $store.filters);
export const propertyPagination = derived(propertiesStore, ($store) => $store.pagination);
