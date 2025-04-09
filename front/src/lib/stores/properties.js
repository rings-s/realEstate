/**
 * Properties Store
 * Manages state for property listings and operations
 */

import { writable, derived } from 'svelte/store';
import * as propertyService from '$lib/services/propertyService';

// Initial state
const initialState = {
	properties: [],
	currentProperty: null,
	isLoading: false,
	error: null,
	filters: {
		property_type: '',
		status: '',
		city: '',
		is_published: '',
		is_featured: '',
		search: '',
		ordering: '-created_at'
	},
	pagination: {
		page: 1,
		pageSize: 10,
		totalItems: 0,
		totalPages: 0
	}
};

// Create the properties store
function createPropertiesStore() {
	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		/**
		 * Reset store to initial state
		 */
		reset: () => set(initialState),

		/**
		 * Set loading state
		 * @param {boolean} isLoading - Loading state
		 */
		setLoading: (isLoading) => {
			update((state) => ({
				...state,
				isLoading,
				error: isLoading ? null : state.error
			}));
		},

		/**
		 * Set error message
		 * @param {string} error - Error message
		 */
		setError: (error) => {
			update((state) => ({
				...state,
				error,
				isLoading: false
			}));
		},

		/**
		 * Load properties with filters
		 * @param {Object} filters - Filter parameters
		 * @param {number} page - Page number
		 * @param {number} pageSize - Page size
		 */
		loadProperties: async (filters = {}, page = 1, pageSize = 10) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				// Merge current filters with new filters
				const mergedFilters = {
					...state.filters,
					...filters
				};

				// Prepare params for API call
				const params = {
					...mergedFilters,
					page,
					page_size: pageSize
				};

				// Clean empty filters
				Object.keys(params).forEach((key) => {
					if (params[key] === '' || params[key] === null || params[key] === undefined) {
						delete params[key];
					}
				});

				const response = await propertyService.getProperties(params);

				update((state) => ({
					...state,
					properties: response.results || [],
					pagination: {
						page: page,
						pageSize: pageSize,
						totalItems: response.count || 0,
						totalPages: Math.ceil((response.count || 0) / pageSize)
					},
					filters: mergedFilters,
					isLoading: false
				}));

				return response;
			} catch (error) {
				console.error('Error loading properties:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحميل العقارات'
				}));

				throw error;
			}
		},

		/**
		 * Load a single property by slug
		 * @param {string} slug - Property slug
		 */
		loadProperty: async (slug) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const property = await propertyService.getPropertyBySlug(slug);

				update((state) => ({
					...state,
					currentProperty: property,
					isLoading: false
				}));

				return property;
			} catch (error) {
				console.error('Error loading property:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحميل تفاصيل العقار'
				}));

				throw error;
			}
		},

		/**
		 * Create a new property
		 * @param {Object} propertyData - Property data
		 */
		createProperty: async (propertyData) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const formattedData = propertyService.formatPropertyData(propertyData);
				const newProperty = await propertyService.createProperty(formattedData);

				update((state) => ({
					...state,
					currentProperty: newProperty,
					isLoading: false
				}));

				return newProperty;
			} catch (error) {
				console.error('Error creating property:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في إنشاء العقار'
				}));

				throw error;
			}
		},

		/**
		 * Update a property
		 * @param {string} slug - Property slug
		 * @param {Object} propertyData - Updated property data
		 * @param {boolean} partial - Whether to use PATCH (partial update)
		 */
		updateProperty: async (slug, propertyData, partial = true) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const formattedData = propertyService.formatPropertyData(propertyData);
				const updatedProperty = await propertyService.updateProperty(slug, formattedData, partial);

				update((state) => ({
					...state,
					currentProperty: updatedProperty,
					isLoading: false
				}));

				return updatedProperty;
			} catch (error) {
				console.error('Error updating property:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحديث العقار'
				}));

				throw error;
			}
		},

		/**
		 * Delete a property
		 * @param {string} slug - Property slug
		 */
		deleteProperty: async (slug) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await propertyService.deleteProperty(slug);

				update((state) => ({
					...state,
					currentProperty: null,
					isLoading: false
				}));

				return true;
			} catch (error) {
				console.error('Error deleting property:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في حذف العقار'
				}));

				throw error;
			}
		},

		/**
		 * Upload property image
		 * @param {string} propertyId - Property ID
		 * @param {File} imageFile - Image file
		 * @param {Object} metadata - Image metadata
		 */
		uploadImage: async (propertyId, imageFile, metadata = {}) => {
			try {
				const response = await propertyService.uploadPropertyImage(propertyId, imageFile, metadata);

				// Update the current property images if viewing that property
				update((state) => {
					if (state.currentProperty && state.currentProperty.id === propertyId) {
						const updatedImages = [...(state.currentProperty.images || []), response];
						return {
							...state,
							currentProperty: {
								...state.currentProperty,
								images: updatedImages
							}
						};
					}
					return state;
				});

				return response;
			} catch (error) {
				console.error('Error uploading property image:', error);
				throw error;
			}
		},

		/**
		 * Update filters and reload properties
		 * @param {Object} newFilters - New filter values
		 */
		updateFilters: async (newFilters) => {
			update((state) => ({
				...state,
				filters: {
					...state.filters,
					...newFilters
				},
				pagination: {
					...state.pagination,
					page: 1 // Reset to first page on filter change
				}
			}));

			// Get the updated filters from the store
			let updatedFilters;
			update((state) => {
				updatedFilters = state.filters;
				return state;
			});

			// Reload properties with updated filters
			return properties.loadProperties(updatedFilters, 1, initialState.pagination.pageSize);
		},

		/**
		 * Change page and reload properties
		 * @param {number} page - Page number
		 */
		changePage: async (page) => {
			let currentFilters, pageSize;

			update((state) => {
				currentFilters = state.filters;
				pageSize = state.pagination.pageSize;

				return {
					...state,
					pagination: {
						...state.pagination,
						page
					}
				};
			});

			return properties.loadProperties(currentFilters, page, pageSize);
		}
	};
}

// Create and export the store
export const properties = createPropertiesStore();

// Derived stores for convenient access
export const propertiesList = derived(properties, ($properties) => $properties.properties);
export const currentProperty = derived(properties, ($properties) => $properties.currentProperty);
export const isLoading = derived(properties, ($properties) => $properties.isLoading);
export const error = derived(properties, ($properties) => $properties.error);
export const filters = derived(properties, ($properties) => $properties.filters);
export const pagination = derived(properties, ($properties) => $properties.pagination);
