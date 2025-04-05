// front/src/lib/services/properties.js
import api, { handleApiError } from './api';

/**
 * Property management services
 */
export default {
	/**
	 * Get list of properties with optional filters
	 * @param {Object} filters - Filter parameters
	 */
	getProperties: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`properties/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get property details by slug
	 * @param {string} slug - Property slug
	 */
	getPropertyBySlug: async (slug) => {
		try {
			return await api.get(`properties/by-slug/${slug}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get property details by ID
	 * @param {string} id - Property ID
	 */
	getProperty: async (id) => {
		try {
			return await api.get(`properties/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new property
	 * @param {Object} propertyData - Property data
	 */
	createProperty: async (propertyData) => {
		try {
			// We assume the property data is already correctly formatted
			console.log('Sending property data to API:', propertyData);

			return await api.post('properties/', propertyData);
		} catch (error) {
			console.error('Error creating property:', error);
			throw handleApiError(error);
		}
	},

	/**
	 * Update an existing property
	 * @param {string} id - Property ID
	 * @param {Object} propertyData - Updated property data
	 */
	updateProperty: async (id, propertyData) => {
		try {
			return await api.patch(`properties/${id}/`, propertyData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Delete a property
	 * @param {string} id - Property ID
	 */
	deleteProperty: async (id) => {
		try {
			return await api.delete(`properties/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own properties
	 */
	getMyProperties: async () => {
		try {
			return await api.get('properties/my-properties/');
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Verify a property (for inspectors)
	 * @param {string} id - Property ID
	 */
	verifyProperty: async (id) => {
		try {
			return await api.post(`properties/${id}/verify/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload property images
	 * @param {string} id - Property ID (optional, only if property exists)
	 * @param {FileList|File[]} images - Property images
	 */
	uploadPropertyImages: async (id, images) => {
		try {
			const formData = new FormData();

			// Add multiple files
			if (images && images.length) {
				for (let i = 0; i < images.length; i++) {
					formData.append('files', images[i]);
				}
			}

			// If we have an ID, use it (for existing property)
			if (id) {
				console.log(`Uploading ${images.length} images to property ${id}`);
				return await api.upload(`properties/${id}/upload-images/`, formData);
			} else {
				// For new properties or standalone uploads
				return await api.upload('properties/upload-images/', formData);
			}
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Search properties by keyword
	 * @param {string} query - Search query
	 */
	searchProperties: async (query) => {
		try {
			return await api.get(`properties/?search=${encodeURIComponent(query)}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get property statistics (for admins and agents)
	 */
	getPropertyStats: async () => {
		try {
			return await api.get('properties/stats/');
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get featured properties
	 */
	getFeaturedProperties: async (limit = 5) => {
		try {
			return await api.get(`properties/?is_featured=true&limit=${limit}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get recommended properties similar to a given property
	 * @param {string} propertyId - Property ID
	 * @param {number} limit - Number of recommendations to get
	 */
	getRecommendedProperties: async (propertyId, limit = 5) => {
		try {
			return await api.get(`properties/${propertyId}/recommended/?limit=${limit}`);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
