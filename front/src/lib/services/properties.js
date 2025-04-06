// src/lib/services/propertyService.js
import api from './api';
import { prepareEntityData, processEntityData, PROPERTY_JSON_FIELDS } from '$lib/utils/jsonFields';

/**
 * Comprehensive property management service
 * Handles all property-related API interactions with consistent error handling and JSON field processing
 */
class PropertyService {
	/**
	 * Get list of properties with filters
	 * @param {Object} filters - Filter parameters
	 */
	async getProperties(filters = {}) {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			const endpoint = `properties/${queryParams ? '?' + queryParams : ''}`;
			const response = await api.get(endpoint);

			// Process JSON fields in response data
			if (Array.isArray(response.results)) {
				response.results = response.results.map((property) =>
					processEntityData(property, PROPERTY_JSON_FIELDS)
				);
			} else if (Array.isArray(response)) {
				return response.map((property) => processEntityData(property, PROPERTY_JSON_FIELDS));
			}

			return response;
		} catch (error) {
			this.handleError(error, 'Failed to load properties');
		}
	}

	/**
	 * Get property details by ID
	 * @param {number} id - Property ID
	 */
	async getProperty(id) {
		try {
			const response = await api.get(`properties/${id}/`);
			return processEntityData(response, PROPERTY_JSON_FIELDS);
		} catch (error) {
			this.handleError(error, `Failed to load property ${id}`);
		}
	}

	/**
	 * Get property details by slug
	 * @param {string} slug - Property slug
	 */
	async getPropertyBySlug(slug) {
		try {
			const response = await api.get(`properties/slug/${slug}/`);
			return processEntityData(response, PROPERTY_JSON_FIELDS);
		} catch (error) {
			this.handleError(error, `Failed to load property with slug ${slug}`);
		}
	}

	/**
	 * Create a new property with proper JSON field handling
	 * @param {Object} propertyData - Property data to submit
	 */
	async createProperty(propertyData) {
		try {
			// Ensure JSON fields are properly stringified
			const preparedData = prepareEntityData(propertyData, PROPERTY_JSON_FIELDS);
			console.log('Prepared property data:', preparedData);

			// Create the property
			const result = await api.post('properties/', preparedData);
			console.log('Property created successfully:', result);

			// Process the response data to parse JSON fields
			return processEntityData(result, PROPERTY_JSON_FIELDS);
		} catch (error) {
			this.handleError(error, 'Failed to create property');
		}
	}

	/**
	 * Update an existing property
	 * @param {number} id - Property ID
	 * @param {Object} propertyData - Updated property data
	 */
	async updateProperty(id, propertyData) {
		try {
			// Ensure JSON fields are properly stringified
			const preparedData = prepareEntityData(propertyData, PROPERTY_JSON_FIELDS);

			// Update the property
			const result = await api.patch(`properties/${id}/`, preparedData);
			console.log('Property updated successfully:', result);

			// Process the response data to parse JSON fields
			return processEntityData(result, PROPERTY_JSON_FIELDS);
		} catch (error) {
			this.handleError(error, `Failed to update property ${id}`);
		}
	}

	/**
	 * Delete a property
	 * @param {number} id - Property ID
	 */
	async deleteProperty(id) {
		try {
			return await api.delete(`properties/${id}/`);
		} catch (error) {
			this.handleError(error, `Failed to delete property ${id}`);
		}
	}

	/**
	 * Set a property image as primary
	 * @param {number} propertyId - Property ID
	 * @param {number} imageIndex - Index of image to set as primary
	 */
	async setPrimaryImage(propertyId, imageIndex) {
		try {
			const response = await api.post(`properties/${propertyId}/actions/set-primary-image/`, {
				image_index: imageIndex
			});

			return response;
		} catch (error) {
			this.handleError(error, 'Failed to set primary image');
		}
	}

	/**
	 * Delete a property image
	 * @param {number} propertyId - Property ID
	 * @param {number} imageIndex - Index of image to delete
	 */
	async deleteImage(propertyId, imageIndex) {
		try {
			return await api.delete(`properties/${propertyId}/actions/delete-image/${imageIndex}/`);
		} catch (error) {
			this.handleError(error, 'Failed to delete image');
		}
	}

	/**
	 * Get user's own properties
	 */
	async getMyProperties() {
		try {
			const response = await api.get('properties/my/');

			// Process JSON fields in response data
			if (Array.isArray(response)) {
				return response.map((property) => processEntityData(property, PROPERTY_JSON_FIELDS));
			}

			return response;
		} catch (error) {
			this.handleError(error, 'Failed to load your properties');
		}
	}

	/**
	 * Verify a property (for inspectors)
	 * @param {string} id - Property ID
	 */
	async verifyProperty(id) {
		try {
			return await api.post(`properties/${id}/actions/verify/`);
		} catch (error) {
			this.handleError(error, `Failed to verify property ${id}`);
		}
	}

	/**
	 * Standardized error handling
	 * @param {Error} error - Error object
	 * @param {string} defaultMessage - Default error message
	 */
	handleError(error, defaultMessage = 'An error occurred') {
		console.error(`PropertyService error: ${defaultMessage}`, error);

		// Extract useful error information
		const errorMessage = error.data?.error || error.message || defaultMessage;
		const errorCode = error.data?.error_code || 'unknown_error';

		// Throw standardized error for consistent handling
		throw {
			message: errorMessage,
			code: errorCode,
			data: error.data || {},
			originalError: error
		};
	}
}

export default new PropertyService();
