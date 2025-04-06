// src/lib/utils/jsonFields.js

/**
 * Utilities for handling JSON fields consistently between frontend and backend
 */

/**
 * Convert a value to a JSON string if it's an object or array
 * @param {any} value - The value to convert
 * @returns {string|null} - JSON string or null if value is empty
 */
export function toJsonString(value) {
	if (value === undefined || value === null) {
		return null;
	}

	if (typeof value === 'string') {
		// If it's already a string, check if it's valid JSON
		try {
			// If it parses, it's already JSON
			JSON.parse(value);
			return value;
		} catch (e) {
			// Not JSON, so it's a regular string - make it JSON
			return JSON.stringify(value);
		}
	}

	// Convert objects/arrays to JSON strings
	if (typeof value === 'object') {
		return JSON.stringify(value);
	}

	// Return primitives as JSON strings
	return JSON.stringify(value);
}

/**
 * Parse a string value to its JSON representation if applicable
 * @param {string} value - The value to parse
 * @param {any} defaultValue - Default value if parsing fails
 * @returns {any} - Parsed value or default value
 */
export function fromJsonString(value, defaultValue = null) {
	if (value === undefined || value === null) {
		return defaultValue;
	}

	if (typeof value !== 'string') {
		return value; // Already not a string, return as is
	}

	try {
		return JSON.parse(value);
	} catch (e) {
		// Not valid JSON, return original value
		return value;
	}
}

/**
 * Prepare entity data for API submission, ensuring all JSON fields are properly stringified
 * @param {Object} data - The data object to prepare
 * @param {Array} jsonFields - Array of field names that should be JSON strings
 * @returns {Object} - Prepared data object with JSON strings
 */
export function prepareEntityData(data, jsonFields = []) {
	const preparedData = { ...data };

	// Convert all specified fields to JSON strings
	jsonFields.forEach((field) => {
		if (field in preparedData) {
			preparedData[field] = toJsonString(preparedData[field]);
		}
	});

	return preparedData;
}

/**
 * Process entity data received from API, parsing JSON strings to objects
 * @param {Object} data - The data object from API
 * @param {Array} jsonFields - Array of field names that are JSON strings
 * @returns {Object} - Processed data with parsed JSON fields
 */
export function processEntityData(data, jsonFields = []) {
	const processedData = { ...data };

	// Parse all specified JSON string fields
	jsonFields.forEach((field) => {
		if (field in processedData && processedData[field]) {
			processedData[field] = fromJsonString(processedData[field]);
		}
	});

	return processedData;
}

// List of known JSON fields in the property model
export const PROPERTY_JSON_FIELDS = [
	'location',
	'images',
	'videos',
	'features',
	'amenities',
	'rooms',
	'outdoor_spaces',
	'street_details',
	'rental_details',
	'building_services',
	'infrastructure',
	'surroundings',
	'reference_ids',
	'documents' // Make sure 'documents' is in this list
];

// List of known JSON fields in other models
export const AUCTION_JSON_FIELDS = ['images', 'videos', 'documents', 'location'];

export const CONTRACT_JSON_FIELDS = ['files'];

export const DOCUMENT_JSON_FIELDS = ['files', 'metadata'];

export const PAYMENT_JSON_FIELDS = ['files'];

export const MESSAGE_JSON_FIELDS = ['attachments'];
