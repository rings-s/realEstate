/**
 * Property Service Module
 * Handles all API interactions for property management
 */

import { ENDPOINTS } from '$lib/config/api';
import { get, post, put, patch, del, uploadFiles } from '$lib/utils/api';
import { addToast } from '$lib/stores/ui';

/**
 * Get property listings with filters
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Property listings response
 */
export const getProperties = async (params = {}) => {
	try {
		return await get(ENDPOINTS.PROPERTY.LIST, { params });
	} catch (error) {
		console.error('Error fetching properties:', error);
		throw error;
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
		console.error(`Error fetching property with slug ${slug}:`, error);
		throw error;
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

	// Convert numeric fields to appropriate types
	const numericFields = [
		'size_sqm',
		'bedrooms',
		'bathrooms',
		'parking_spaces',
		'year_built',
		'market_value',
		'minimum_bid'
	];
	numericFields.forEach((field) => {
		if (
			field in formattedData &&
			formattedData[field] !== null &&
			formattedData[field] !== undefined &&
			formattedData[field] !== ''
		) {
			// Convert to number explicitly
			formattedData[field] = Number(formattedData[field]);

			// Handle NaN case
			if (isNaN(formattedData[field])) {
				formattedData[field] = null;
			}
		} else if (formattedData[field] === '') {
			// Convert empty strings to null for numeric fields
			formattedData[field] = null;
		}
	});

	// Handle arrays that should be JSON strings on the server but are objects in the client
	const arrayFields = ['features', 'amenities', 'rooms'];
	arrayFields.forEach((field) => {
		if (field in formattedData) {
			// Handle arrays
			if (Array.isArray(formattedData[field])) {
				// No need to stringify for Django REST Framework - it will handle JSON serialization
				// Just ensure it's a valid array
				if (!formattedData[field].length) {
					formattedData[field] = [];
				}
			}
			// Handle stringified arrays
			else if (typeof formattedData[field] === 'string') {
				try {
					// Try to parse if it's a JSON string
					const parsed = JSON.parse(formattedData[field]);
					formattedData[field] = parsed;
				} catch (e) {
					// If parsing fails, convert to an array with the string as an item
					formattedData[field] = formattedData[field] ? [formattedData[field]] : [];
				}
			}
			// Handle null/undefined
			else if (formattedData[field] === null || formattedData[field] === undefined) {
				formattedData[field] = [];
			}
		}
	});

	// Handle objects that should be JSON strings on the server but are objects in the client
	const objectFields = ['specifications', 'location', 'pricing_details', 'metadata'];
	objectFields.forEach((field) => {
		if (field in formattedData) {
			// Handle objects
			if (
				formattedData[field] &&
				typeof formattedData[field] === 'object' &&
				!Array.isArray(formattedData[field])
			) {
				// No need to stringify for Django REST Framework - it will handle JSON serialization
				// Just ensure it's a valid object
				if (Object.keys(formattedData[field]).length === 0) {
					formattedData[field] = {};
				}
			}
			// Handle stringified objects
			else if (typeof formattedData[field] === 'string') {
				try {
					// Try to parse if it's a JSON string
					const parsed = JSON.parse(formattedData[field]);
					formattedData[field] = parsed;
				} catch (e) {
					// If parsing fails, set to empty object
					formattedData[field] = {};
				}
			}
			// Handle null/undefined
			else if (formattedData[field] === null || formattedData[field] === undefined) {
				formattedData[field] = {};
			}
		}
	});

	// Ensure location has the required structure if it exists
	if (formattedData.location) {
		// Copy address fields to location object if they exist but aren't in location
		const addressFields = ['address', 'city', 'state', 'postal_code', 'country'];
		addressFields.forEach((field) => {
			if (formattedData[field] && !formattedData.location[field]) {
				formattedData.location[field] = formattedData[field];
			}
		});
	}

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

/**
 * Create a new property
 * @param {Object} propertyData - Property data
 * @returns {Promise<Object>} Created property response
 */
// In propertyService.js, update the createProperty function
export const createProperty = async (propertyData, maxRetries = 2) => {
	// Enhanced validation
	const requiredFields = ['title', 'property_type', 'address', 'city'];
	const missingFields = [];

	for (let field of requiredFields) {
		if (
			!propertyData[field] ||
			(typeof propertyData[field] === 'string' && propertyData[field].trim() === '')
		) {
			missingFields.push(field);
		}
	}

	if (missingFields.length > 0) {
		throw new Error(`Required fields missing: ${missingFields.join(', ')}`);
	}

	let lastError = null;
	let retryCount = 0;

	while (retryCount <= maxRetries) {
		try {
			// Format data properly before sending to API
			const formattedData = formatPropertyData(propertyData);

			// Log the exact data being sent for debugging
			console.log('Sending property data to API:', formattedData);

			// Make the API request
			const response = await post(ENDPOINTS.PROPERTY.CREATE, formattedData);
			return response;
		} catch (error) {
			lastError = error;
			console.error(`Property Creation Error (attempt ${retryCount + 1}):`, error);

			// Only retry for 500 errors
			if (error.status === 500 && retryCount < maxRetries) {
				retryCount++;
				// Wait before retrying (exponential backoff)
				await new Promise((resolve) => setTimeout(resolve, 1000 * retryCount));
				continue;
			}

			// Check for validation errors from the backend
			if (error.details) {
				const errorMessages = [];

				// Process field errors
				Object.entries(error.details).forEach(([field, messages]) => {
					if (Array.isArray(messages)) {
						errorMessages.push(`${field}: ${messages.join(', ')}`);
					} else if (typeof messages === 'string') {
						errorMessages.push(`${field}: ${messages}`);
					} else {
						errorMessages.push(`${field}: Invalid value`);
					}
				});

				if (errorMessages.length > 0) {
					throw new Error(errorMessages.join('. '));
				}
			}

			// If no specific details, throw the original error
			throw error;
		}
	}

	throw lastError;
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
		console.log(`Updating property with slug ${slug}:`, formattedData);

		if (partial) {
			return await patch(ENDPOINTS.PROPERTY.UPDATE(slug), formattedData);
		} else {
			return await put(ENDPOINTS.PROPERTY.UPDATE(slug), formattedData);
		}
	} catch (error) {
		console.error(`Error updating property with slug ${slug}:`, error);
		throw error;
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
		console.error(`Error deleting property with slug ${slug}:`, error);
		throw error;
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
		console.error(`Error fetching images for property ${propertyId}:`, error);
		throw error;
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
		console.error(`Error uploading image for property ${propertyId}:`, error);
		throw error;
	}
};

/**
 * Upload multiple property images
 * @param {string} propertyId - Property ID
 * @param {Array} images - Array of image objects with file and metadata
 * @param {Function} onProgress - Optional progress callback
 * @returns {Promise<Array>} Array of uploaded image responses
 */
export const uploadMultiplePropertyImages = async (propertyId, images, onProgress = null) => {
	if (!propertyId || !images?.length) {
		return [];
	}

	// Track upload progress
	let successCount = 0;
	let failureCount = 0;
	const totalImages = images.length;
	const uploadResults = [];

	try {
		// Process images sequentially
		for (let i = 0; i < images.length; i++) {
			const image = images[i];

			// Skip already uploaded images or images without files
			if (!image.file || image.uploaded) {
				continue;
			}

			try {
				// Upload the image with metadata
				const result = await uploadPropertyImage(propertyId, image.file, {
					isPrimary: image.is_primary || i === 0, // Make first image primary by default
					caption: image.caption || '',
					order: i,
					onProgress: (progress) => {
						if (onProgress) {
							onProgress({
								currentImage: i + 1,
								totalImages,
								progress,
								successCount,
								failureCount
							});
						}
					}
				});

				uploadResults.push(result);
				successCount++;
			} catch (error) {
				console.error(`Error uploading image ${i + 1}:`, error);
				failureCount++;
			}
		}

		return uploadResults;
	} catch (error) {
		console.error('Error in batch image upload:', error);
		throw error;
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
		console.error(`Error deleting image ${imageId}:`, error);
		throw error;
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
		console.error(`Error setting image ${imageId} as primary:`, error);
		throw error;
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
		console.error(`Error updating image ${imageId}:`, error);
		throw error;
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
		return await post(`${ENDPOINTS.PROPERTY.IMAGES(propertyId)}reorder/`, {
			images: imageOrderData
		});
	} catch (error) {
		console.error(`Error reordering images for property ${propertyId}:`, error);
		throw error;
	}
};

/**
 * Validate property data before submission
 * @param {Object} propertyData - Property data to validate
 * @returns {Object} Validation result with errors object and isValid flag
 */
export const validatePropertyData = (propertyData) => {
	const errors = {};

	// Required fields
	const requiredFields = ['title', 'property_type', 'address', 'city', 'description'];
	requiredFields.forEach((field) => {
		if (
			!propertyData[field] ||
			(typeof propertyData[field] === 'string' && propertyData[field].trim() === '')
		) {
			errors[field] = `${field.replace('_', ' ')} is required`;
		}
	});

	// Field length validations
	if (propertyData.title && propertyData.title.length > 255) {
		errors.title = 'Title must be less than 255 characters';
	}

	if (propertyData.description && propertyData.description.length > 2000) {
		errors.description = 'Description must be less than 2000 characters';
	}

	// Numeric field validations
	const numericFields = [
		{ name: 'size_sqm', min: 0, max: 1000000 },
		{ name: 'bedrooms', min: 0, max: 100, integer: true },
		{ name: 'bathrooms', min: 0, max: 100, integer: true },
		{ name: 'year_built', min: 1800, max: new Date().getFullYear(), integer: true },
		{ name: 'market_value', min: 0 },
		{ name: 'minimum_bid', min: 0 }
	];

	numericFields.forEach((field) => {
		const value = propertyData[field.name];

		if (value !== undefined && value !== null && value !== '') {
			const numValue = Number(value);

			if (isNaN(numValue)) {
				errors[field.name] = `${field.name.replace('_', ' ')} must be a number`;
			} else {
				if (field.min !== undefined && numValue < field.min) {
					errors[field.name] = `${field.name.replace('_', ' ')} must be at least ${field.min}`;
				}

				if (field.max !== undefined && numValue > field.max) {
					errors[field.name] = `${field.name.replace('_', ' ')} must be no more than ${field.max}`;
				}

				if (field.integer && !Number.isInteger(numValue)) {
					errors[field.name] = `${field.name.replace('_', ' ')} must be a whole number`;
				}
			}
		}
	});

	return {
		errors,
		isValid: Object.keys(errors).length === 0
	};
};

export default {
	getProperties,
	getPropertyBySlug,
	createProperty,
	updateProperty,
	deleteProperty,
	getPropertyImages,
	uploadPropertyImage,
	uploadMultiplePropertyImages,
	deletePropertyImage,
	setPropertyImageAsPrimary,
	updatePropertyImage,
	reorderPropertyImages,
	formatPropertyData,
	parsePropertyData,
	validatePropertyData
};
