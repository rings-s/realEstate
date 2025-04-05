// front/src/lib/services/PropertyService.js
import api from './api';
import uploadService from './upload';

/**
 * Comprehensive property management service
 * Handles all property-related API interactions with consistent error handling
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
			return await api.get(endpoint);
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
			return await api.get(`properties/${id}/`);
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
			return await api.get(`properties/slug/${slug}/`);
		} catch (error) {
			this.handleError(error, `Failed to load property with slug ${slug}`);
		}
	}

	/**
	 * Create a new property with comprehensive data handling
	 * @param {Object} formData - Raw form data
	 */
	async createProperty(formData) {
		try {
			// Convert form data to API-friendly structure
			const propertyData = this.preparePropertyData(formData);

			// Create the property
			const result = await api.post('properties/', propertyData);
			console.log('Property created successfully:', result);

			return result;
		} catch (error) {
			this.handleError(error, 'Failed to create property');
		}
	}

	/**
	 * Update an existing property
	 * @param {number} id - Property ID
	 * @param {Object} formData - Updated property data
	 */
	async updateProperty(id, formData) {
		try {
			// Convert form data to API-friendly structure
			const propertyData = this.preparePropertyData(formData);

			// Update the property
			const result = await api.patch(`properties/${id}/`, propertyData);
			console.log('Property updated successfully:', result);

			return result;
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
	 * Upload images for a property
	 * @param {number} propertyId - Property ID
	 * @param {File[]} images - Array of image files
	 */
	async uploadImages(propertyId, images) {
		try {
			if (!images || images.length === 0) {
				console.warn('No images provided for upload');
				return { success: false, message: 'No images provided' };
			}

			const formData = new FormData();

			// Append each image as 'files' to match backend expectation
			images.forEach((image) => formData.append('files', image));

			// Upload images via API
			const result = await api.upload(`properties/${propertyId}/uploads/`, formData);
			console.log('Images uploaded successfully:', result);

			return result;
		} catch (error) {
			this.handleError(error, 'Failed to upload images');
		}
	}

	/**
	 * Set a property image as primary
	 * @param {number} propertyId - Property ID
	 * @param {number} imageIndex - Index of image to set as primary
	 */
	async setPrimaryImage(propertyId, imageIndex) {
		try {
			return await api.post(`properties/${propertyId}/actions/set-primary-image/`, {
				image_index: imageIndex
			});
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
			return await api.get('properties/my/');
		} catch (error) {
			this.handleError(error, 'Failed to load your properties');
		}
	}

	/**
	 * Create a comprehensive property data object from form data
	 * @param {Object} formData - Raw form data from the frontend
	 * @returns {Object} - API-ready property data
	 */
	preparePropertyData(formData) {
		// Basic fields pass directly
		const propertyData = {
			title: formData.title || '',
			description: formData.description || '',
			property_type: formData.property_type || 'apartment',
			condition: formData.condition || 'good',
			status: formData.status || 'draft',
			city: formData.city || '',
			district: formData.district || '',
			address: formData.address || '',
			postal_code: formData.postal_code || '',
			country: formData.country || 'Saudi Arabia',
			deed_number: formData.deed_number || '',
			deed_date: formData.deed_date || null,

			// Boolean fields
			is_published: Boolean(formData.is_published),
			is_featured: Boolean(formData.is_featured)
		};

		// Handle numeric fields with proper type conversion
		const numericFields = [
			'area',
			'built_up_area',
			'estimated_value',
			'asking_price',
			'bedrooms',
			'bathrooms',
			'floor_number',
			'total_floors',
			'year_built'
		];

		numericFields.forEach((field) => {
			if (formData[field] !== undefined && formData[field] !== '') {
				const value = parseFloat(formData[field]);
				propertyData[field] = isNaN(value) ? null : value;
			} else {
				propertyData[field] = null;
			}
		});

		// Handle JSON fields with proper serialization
		const jsonFields = [
			'location',
			'features',
			'amenities',
			'rooms',
			'images',
			'videos',
			'documents',
			'outdoor_spaces',
			'street_details',
			'building_services',
			'infrastructure',
			'surroundings',
			'reference_ids'
		];

		jsonFields.forEach((field) => {
			if (formData[field] !== undefined) {
				const value = formData[field];

				// If value is already a string, assume it's proper JSON
				if (typeof value === 'string') {
					propertyData[field] = value;
				}
				// Otherwise, stringify the object/array
				else {
					propertyData[field] = JSON.stringify(value || (field === 'location' ? {} : []));
				}
			}
		});

		// Special handling for location
		if (formData.location && typeof formData.location === 'object') {
			propertyData.location = JSON.stringify(formData.location);
		}

		// Log the prepared data for debugging
		console.log('Prepared property data:', propertyData);

		return propertyData;
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
