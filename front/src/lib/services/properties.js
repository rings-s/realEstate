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
			return await api.get(`/properties/${queryParams ? '?' + queryParams : ''}`);
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
			return await api.get(`/properties/by-slug/${slug}/`);
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
			return await api.get(`/properties/${id}/`);
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
			const formattedData = formatPropertyData(propertyData);
			return await api.post('/properties/', formattedData);
		} catch (error) {
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
			const formattedData = formatPropertyData(propertyData);
			return await api.patch(`/properties/${id}/`, formattedData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own properties
	 */
	getMyProperties: async () => {
		try {
			return await api.get('/properties/my-properties/');
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
			return await api.post(`/properties/${id}/verify/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload property images
	 * @param {string} id - Property ID
	 * @param {FileList} images - Property images
	 */
	uploadPropertyImages: async (id, images) => {
		try {
			const formData = new FormData();
			for (let i = 0; i < images.length; i++) {
				formData.append('images', images[i]);
			}
			return await api.upload(`/properties/${id}/upload-images/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}

	// The rest of the functions remain the same
};
