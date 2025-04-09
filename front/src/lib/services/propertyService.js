/**
 * Property Service
 * Handles API calls for property management
 */

import { ENDPOINTS } from '$lib/config/api';
import { get, post, put, patch, del, uploadFiles } from '$lib/utils/api';

/**
 * Get property listings with filters
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.page_size - Number of items per page
 * @param {string} params.property_type - Filter by property type
 * @param {string} params.status - Filter by status
 * @param {string} params.city - Filter by city
 * @param {boolean} params.is_published - Filter by published status
 * @param {boolean} params.is_featured - Filter by featured status
 * @param {boolean} params.is_verified - Filter by verified status
 * @param {string} params.search - Search term
 * @param {string} params.ordering - Order by field
 * @returns {Promise<Object>} Property listings response
 */
export const getProperties = async (params = {}) => {
	return get(ENDPOINTS.PROPERTY.LIST, { params });
};

/**
 * Get property details by slug
 * @param {string} slug - Property slug
 * @returns {Promise<Object>} Property details response
 */
export const getPropertyBySlug = async (slug) => {
	return get(ENDPOINTS.PROPERTY.DETAIL(slug));
};

/**
 * Create a new property
 * @param {Object} propertyData - Property data
 * @returns {Promise<Object>} Created property response
 */
export const createProperty = async (propertyData) => {
	return post(ENDPOINTS.PROPERTY.CREATE, propertyData);
};

/**
 * Update a property
 * @param {string} slug - Property slug
 * @param {Object} propertyData - Updated property data
 * @param {boolean} partial - Whether to use PATCH (partial update)
 * @returns {Promise<Object>} Updated property response
 */
export const updateProperty = async (slug, propertyData, partial = false) => {
	if (partial) {
		return patch(ENDPOINTS.PROPERTY.UPDATE(slug), propertyData);
	} else {
		return put(ENDPOINTS.PROPERTY.UPDATE(slug), propertyData);
	}
};

/**
 * Delete a property
 * @param {string} slug - Property slug
 * @returns {Promise<Object>} Response
 */
export const deleteProperty = async (slug) => {
	return del(ENDPOINTS.PROPERTY.DELETE(slug));
};

/**
 * Get property images
 * @param {string} propertyId - Property ID
 * @returns {Promise<Object>} Property images response
 */
export const getPropertyImages = async (propertyId) => {
	return get(ENDPOINTS.PROPERTY.IMAGES(propertyId));
};

/**
 * Upload a property image
 * @param {string} propertyId - Property ID
 * @param {File} imageFile - Image file
 * @param {Object} metadata - Image metadata
 * @param {boolean} isPrimary - Whether this is the primary image
 * @param {string} caption - Image caption
 * @param {number} order - Display order
 * @returns {Promise<Object>} Uploaded image response
 */
export const uploadPropertyImage = async (
	propertyId,
	imageFile,
	{ isPrimary = false, caption = '', order = 0 } = {}
) => {
	const formData = new FormData();
	formData.append('image', imageFile);
	formData.append('is_primary', isPrimary);

	if (caption) {
		formData.append('caption', caption);
	}

	if (order) {
		formData.append('order', order);
	}

	return uploadFiles(ENDPOINTS.PROPERTY.IMAGES(propertyId), formData);
};

/**
 * Delete a property image
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const deletePropertyImage = async (imageId) => {
	return del(ENDPOINTS.PROPERTY.IMAGE_DELETE(imageId));
};

/**
 * Set a property image as primary
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const setPropertyImageAsPrimary = async (imageId) => {
	return patch(ENDPOINTS.PROPERTY.IMAGE_UPDATE(imageId), {
		is_primary: true
	});
};

/**
 * Update a property image
 * @param {string} imageId - Image ID
 * @param {Object} imageData - Updated image data
 * @returns {Promise<Object>} Updated image response
 */
export const updatePropertyImage = async (imageId, imageData) => {
	return patch(ENDPOINTS.PROPERTY.IMAGE_UPDATE(imageId), imageData);
};

/**
 * Format property data for API
 * This handles JSON fields that need special formatting
 * @param {Object} propertyData - Property data from form
 * @returns {Object} Formatted property data
 */
export const formatPropertyData = (propertyData) => {
	const formattedData = { ...propertyData };

	// Convert arrays to JSON strings if they're in array format
	if (Array.isArray(formattedData.features)) {
		formattedData.features = JSON.stringify(formattedData.features);
	}

	if (Array.isArray(formattedData.amenities)) {
		formattedData.amenities = JSON.stringify(formattedData.amenities);
	}

	if (Array.isArray(formattedData.rooms)) {
		formattedData.rooms = JSON.stringify(formattedData.rooms);
	}

	// Convert objects to JSON strings
	if (typeof formattedData.specifications === 'object' && formattedData.specifications !== null) {
		formattedData.specifications = JSON.stringify(formattedData.specifications);
	}

	if (typeof formattedData.location === 'object' && formattedData.location !== null) {
		formattedData.location = JSON.stringify(formattedData.location);
	}

	if (typeof formattedData.pricing_details === 'object' && formattedData.pricing_details !== null) {
		formattedData.pricing_details = JSON.stringify(formattedData.pricing_details);
	}

	if (typeof formattedData.metadata === 'object' && formattedData.metadata !== null) {
		formattedData.metadata = JSON.stringify(formattedData.metadata);
	}

	return formattedData;
};
