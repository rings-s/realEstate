/**
 * Enhanced Property Service Functions
 * Handles API calls for property management with improved error handling
 */

import { ENDPOINTS } from '$lib/config/api';
import { get, post, put, patch, del, uploadFiles } from '$lib/utils/api';
import { addToast } from '$lib/stores/ui';
import { refreshToken } from '$lib/stores/auth';

/**
 * Enhanced error handler for API requests
 * @param {Error} error - The error object
 * @param {string} defaultMessage - Default error message
 * @returns {Error} - Enhanced error with consistent format
 */
const handleApiError = (error, defaultMessage) => {
	console.error('Full API Error Object:', error);

	// Check if we need to refresh token (401 error)
	if (error.status === 401) {
		// Try to refresh token and let calling function retry
		refreshToken();
	}

	// Format the error message
	let errorMessage = defaultMessage;
	let errorDetails = {};

	// Check for different error formats
	if (error.response) {
		// Django REST framework error response
		console.error('Backend Error Response:', error.response);

		// Try to extract error details from different possible locations
		if (error.response.data) {
			if (typeof error.response.data === 'object') {
				// Check for specific error structures
				if (error.response.data.error) {
					errorMessage = error.response.data.error;
				} else if (error.response.data.detail) {
					errorMessage = error.response.data.detail;
				} else if (error.response.data.message) {
					errorMessage = error.response.data.message;
				}

				// Extract validation errors
				if (error.response.data.details) {
					errorDetails = error.response.data.details;
					errorMessage = Object.entries(errorDetails)
						.map(([field, messages]) => `${field}: ${messages}`)
						.join('; ');
				}
			} else if (typeof error.response.data === 'string') {
				errorMessage = error.response.data;
			}
		}

		// Fallback to status text
		if (!errorMessage) {
			errorMessage = error.response.statusText || defaultMessage;
		}
	} else if (error.message) {
		// Axios or native fetch error
		errorMessage = error.message;
	}

	// Create enhanced error object
	const enhancedError = new Error(errorMessage);
	enhancedError.originalError = error;
	enhancedError.status = error.status || 500;
	enhancedError.details = errorDetails;

	// Log the full error for debugging
	console.error('Enhanced Error:', {
		message: enhancedError.message,
		status: enhancedError.status,
		details: enhancedError.details,
		originalError: enhancedError.originalError
	});

	return enhancedError;
};

/**
 * Get property listings with filters
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Property listings response
 */
export const getProperties = async (params = {}) => {
	try {
		return await get(ENDPOINTS.PROPERTY.LIST, { params });
	} catch (error) {
		throw handleApiError(error, 'Error fetching properties');
	}
};

/**
 * Get property details by slug
 * @param {string} slug - Property slug
 * @returns {Promise<Object>} Property details response
 */
export const getPropertyBySlug = async (slug) => {
	try {
		return await get(ENDPOINTS.PROPERTY.DETAIL(slug));
	} catch (error) {
		throw handleApiError(error, `Error fetching property with slug ${slug}`);
	}
};

/**
 * Create a new property
 * @param {Object} propertyData - Property data
 * @returns {Promise<Object>} Created property response
 */
export const createProperty = async (propertyData) => {
	// Enhanced validation
	const requiredFields = ['title', 'property_type', 'address', 'city'];
	for (let field of requiredFields) {
		if (!propertyData[field]) {
			throw new Error(`${field} is required`);
		}
	}

	// Type conversions and validations
	if (propertyData.size_sqm) {
		propertyData.size_sqm = parseFloat(propertyData.size_sqm);
	}
	if (propertyData.bedrooms) {
		propertyData.bedrooms = parseInt(propertyData.bedrooms, 10);
	}
	if (propertyData.bathrooms) {
		propertyData.bathrooms = parseInt(propertyData.bathrooms, 10);
	}
	if (propertyData.year_built) {
		propertyData.year_built = parseInt(propertyData.year_built, 10);
	}

	// Ensure JSON fields are properly formatted
	const jsonFields = ['features', 'amenities', 'rooms', 'specifications', 'location', 'metadata'];
	jsonFields.forEach((field) => {
		if (propertyData[field] && typeof propertyData[field] !== 'string') {
			propertyData[field] = JSON.stringify(propertyData[field]);
		}
	});

	try {
		// Log the exact data being sent
		console.log('Property Creation Request Data:', propertyData);

		const response = await post(ENDPOINTS.PROPERTY.CREATE, propertyData);
		return response;
	} catch (error) {
		// Enhanced error handling
		console.error('Property Creation Error:', error);

		// Detailed error parsing
		if (error.details) {
			const errorMessages = Object.entries(error.details)
				.map(([field, message]) => `${field}: ${message}`)
				.join('; ');
			throw new Error(errorMessages);
		}

		// If no specific details, throw the original error
		throw error;
	}
};

/**
 * Update a property
 * @param {string} slug - Property slug
 * @param {Object} propertyData - Updated property data
 * @param {boolean} partial - Whether to use PATCH (partial update)
 * @returns {Promise<Object>} Updated property response
 */
export const updateProperty = async (slug, propertyData, partial = true) => {
	try {
		const formattedData = formatPropertyData(propertyData);
		if (partial) {
			return await patch(ENDPOINTS.PROPERTY.UPDATE(slug), formattedData);
		} else {
			return await put(ENDPOINTS.PROPERTY.UPDATE(slug), formattedData);
		}
	} catch (error) {
		throw handleApiError(error, `Error updating property with slug ${slug}`);
	}
};

/**
 * Delete a property
 * @param {string} slug - Property slug
 * @returns {Promise<Object>} Response
 */
export const deleteProperty = async (slug) => {
	try {
		return await del(ENDPOINTS.PROPERTY.DELETE(slug));
	} catch (error) {
		throw handleApiError(error, `Error deleting property with slug ${slug}`);
	}
};

/**
 * Get property images
 * @param {string} propertyId - Property ID
 * @returns {Promise<Object>} Property images response
 */
export const getPropertyImages = async (propertyId) => {
	try {
		return await get(ENDPOINTS.PROPERTY.IMAGES(propertyId));
	} catch (error) {
		throw handleApiError(error, `Error fetching images for property ${propertyId}`);
	}
};

/**
 * Upload a property image with progress tracking and error handling
 * @param {string} propertyId - Property ID
 * @param {File} imageFile - Image file
 * @param {Object} options - Image options
 * @returns {Promise<Object>} Uploaded image response
 */
export const uploadPropertyImage = async (
	propertyId,
	imageFile,
	{ isPrimary = false, caption = '', order = 0, onProgress = null } = {}
) => {
	try {
		// Validate inputs
		if (!propertyId) throw new Error('Property ID is required');
		if (!imageFile) throw new Error('Image file is required');

		// Validate file type
		const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
		if (!validTypes.includes(imageFile.type)) {
			throw new Error('Invalid image type. Only JPG, PNG, GIF, and WEBP are supported.');
		}

		// Validate file size (max 5MB)
		const maxSize = 5 * 1024 * 1024; // 5MB
		if (imageFile.size > maxSize) {
			throw new Error('Image size exceeds 5MB limit.');
		}

		// Create form data
		const formData = new FormData();
		formData.append('image', imageFile);
		formData.append('is_primary', isPrimary ? 'true' : 'false');

		if (caption) {
			formData.append('caption', caption);
		}

		if (order !== undefined && order !== null) {
			formData.append('order', order.toString());
		}

		// Upload with custom config for progress tracking
		const uploadConfig = {};

		if (onProgress && typeof onProgress === 'function') {
			uploadConfig.onUploadProgress = (progressEvent) => {
				const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
				onProgress(percentCompleted);
			};
		}

		return await uploadFiles(ENDPOINTS.PROPERTY.IMAGES(propertyId), formData, uploadConfig);
	} catch (error) {
		throw handleApiError(error, `Error uploading image for property ${propertyId}`);
	}
};

/**
 * Delete a property image
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const deletePropertyImage = async (imageId) => {
	try {
		return await del(ENDPOINTS.PROPERTY.IMAGE_DELETE(imageId));
	} catch (error) {
		throw handleApiError(error, `Error deleting image ${imageId}`);
	}
};

/**
 * Set a property image as primary
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const setPropertyImageAsPrimary = async (imageId) => {
	try {
		return await patch(ENDPOINTS.PROPERTY.IMAGE_UPDATE(imageId), {
			is_primary: true
		});
	} catch (error) {
		throw handleApiError(error, `Error setting image ${imageId} as primary`);
	}
};

/**
 * Update a property image
 * @param {string} imageId - Image ID
 * @param {Object} imageData - Updated image data
 * @returns {Promise<Object>} Updated image response
 */
export const updatePropertyImage = async (imageId, imageData) => {
	try {
		return await patch(ENDPOINTS.PROPERTY.IMAGE_UPDATE(imageId), imageData);
	} catch (error) {
		throw handleApiError(error, `Error updating image ${imageId}`);
	}
};

/**
 * Reorder property images
 * @param {string} propertyId - Property ID
 * @param {Array} imageOrderData - Array of {id, order} objects
 * @returns {Promise<Object>} Response
 */
export const reorderPropertyImages = async (propertyId, imageOrderData) => {
	try {
		return await post(`${ENDPOINTS.PROPERTY.IMAGES(propertyId)}/reorder/`, {
			images: imageOrderData
		});
	} catch (error) {
		throw handleApiError(error, `Error reordering images for property ${propertyId}`);
	}
};

/**
 * Format property data for API
 * This handles JSON fields that need special formatting
 * @param {Object} propertyData - Property data from form
 * @returns {Object} Formatted property data
 */
export const formatPropertyData = (propertyData) => {
	if (!propertyData) return {};

	const formattedData = { ...propertyData };

	// Handle arrays that should be JSON strings
	const arrayFields = ['features', 'amenities', 'rooms'];
	arrayFields.forEach((field) => {
		if (field in formattedData) {
			if (Array.isArray(formattedData[field])) {
				formattedData[field] = JSON.stringify(formattedData[field]);
			} else if (typeof formattedData[field] === 'string') {
				// Check if it's already a valid JSON string
				try {
					JSON.parse(formattedData[field]);
					// If parsing succeeds, it's already a valid JSON string
				} catch (e) {
					// If parsing fails, it's not a valid JSON string, so wrap it
					formattedData[field] = JSON.stringify(formattedData[field]);
				}
			} else if (formattedData[field] === null || formattedData[field] === undefined) {
				// Set empty array for null or undefined values
				formattedData[field] = JSON.stringify([]);
			}
		}
	});

	// Handle objects that should be JSON strings
	const objectFields = ['specifications', 'location', 'pricing_details', 'metadata'];
	objectFields.forEach((field) => {
		if (field in formattedData) {
			if (formattedData[field] && typeof formattedData[field] === 'object') {
				formattedData[field] = JSON.stringify(formattedData[field]);
			} else if (typeof formattedData[field] === 'string') {
				// Check if it's already a valid JSON string
				try {
					JSON.parse(formattedData[field]);
					// If parsing succeeds, it's already a valid JSON string
				} catch (e) {
					// If parsing fails, it's not a valid JSON string, so wrap it
					formattedData[field] = JSON.stringify({});
				}
			} else if (formattedData[field] === null || formattedData[field] === undefined) {
				// Set empty object for null or undefined values
				formattedData[field] = JSON.stringify({});
			}
		}
	});

	return formattedData;
};

/**
 * Parse property data from API
 * This handles JSON fields that need parsing
 * @param {Object} propertyData - Property data from API
 * @returns {Object} Parsed property data
 */
export const parsePropertyData = (propertyData) => {
	if (!propertyData) return null;

	const parsedData = { ...propertyData };

	// Parse JSON string fields that should be arrays
	const arrayFields = ['features', 'amenities', 'rooms'];
	arrayFields.forEach((field) => {
		if (typeof parsedData[field] === 'string') {
			try {
				parsedData[field] = JSON.parse(parsedData[field]);
			} catch (e) {
				console.warn(`Failed to parse ${field} as JSON`, e);
				parsedData[field] = [];
			}
		} else if (!Array.isArray(parsedData[field])) {
			parsedData[field] = [];
		}
	});

	// Parse JSON string fields that should be objects
	const objectFields = ['specifications', 'location', 'pricing_details', 'metadata'];
	objectFields.forEach((field) => {
		if (typeof parsedData[field] === 'string') {
			try {
				parsedData[field] = JSON.parse(parsedData[field]);
			} catch (e) {
				console.warn(`Failed to parse ${field} as JSON`, e);
				parsedData[field] = {};
			}
		} else if (!parsedData[field] || typeof parsedData[field] !== 'object') {
			parsedData[field] = {};
		}
	});

	return parsedData;
};
