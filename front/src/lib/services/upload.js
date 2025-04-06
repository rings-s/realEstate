// src/lib/services/upload.js

/**
 * Enhanced service for handling file uploads throughout the application.
 * Improved with better error handling, retry mechanisms, and JSON field compatibility.
 */

import { browser } from '$app/environment';
import { processEntityData, PROPERTY_JSON_FIELDS } from '$lib/utils/jsonFields';

// Get API base URL from environment or use default
const API_BASE_URL = browser ? import.meta.env.VITE_API_URL || 'http://localhost:8000/api' : '';

// Maximum number of retry attempts for uploads
const MAX_RETRY_ATTEMPTS = 3;

/**
 * Upload property images to a specific property with enhanced error handling and retry mechanism
 * @param {number} propertyId - The property ID
 * @param {FileList|File[]} files - The files to upload
 * @param {Object} options - Upload options
 * @param {Function} options.onProgress - Progress callback function
 * @param {number} options.maxRetries - Maximum retry attempts (default: 3)
 * @param {boolean} options.processJsonResponse - Process JSON fields in response
 * @returns {Promise} - Promise resolving to the server response
 */
export async function uploadPropertyImages(propertyId, files, options = {}) {
	// Input validation
	if (!propertyId) {
		console.error('Property ID is required for upload');
		throw new Error('Property ID is required');
	}

	if (!files || files.length === 0) {
		console.error('No files provided for upload');
		throw new Error('No files provided');
	}

	// Set default options
	const {
		onProgress = null,
		maxRetries = MAX_RETRY_ATTEMPTS,
		processJsonResponse = true
	} = options;

	// Log upload operation
	console.log(`Starting upload of ${files.length} files to property ID: ${propertyId}`);

	// Validate files before uploading
	const fileValidation = validateImageFiles(files);
	if (fileValidation.warnings.length > 0) {
		console.warn('Upload warnings:', fileValidation.warnings);
	}

	// Only proceed with valid files
	const validFiles = fileValidation.validFiles;
	if (validFiles.length === 0) {
		throw new Error('No valid files to upload. All files were rejected during validation.');
	}

	// Implement retry logic with exponential backoff
	let attempt = 0;

	while (attempt < maxRetries) {
		try {
			// Create form data as Django expects
			const formData = new FormData();

			// Use 'images' as the field name to match Django's BaseUploadView expectation
			Array.from(validFiles).forEach((file) => {
				console.log(
					`Adding file to FormData: ${file.name}, type: ${file.type}, size: ${file.size} bytes`
				);
				formData.append('images', file);
			});

			// Get authentication token
			const token = localStorage.getItem('access_token');
			if (!token) {
				console.error('Authentication token not found');
				throw new Error('Authentication token required');
			}

			// Construct the URL that matches Django's URL pattern
			const uploadUrl = `${API_BASE_URL}/properties/${propertyId}/uploads/`;
			console.log(`Upload URL: ${uploadUrl}`);

			// Create request with progress tracking if callback provided
			let response;

			if (onProgress) {
				response = await uploadWithProgress(uploadUrl, formData, token, onProgress);
			} else {
				// Simple fetch request without progress tracking
				const fetchResponse = await fetch(uploadUrl, {
					method: 'POST',
					headers: {
						Authorization: `Bearer ${token}`
						// Don't set Content-Type - let browser set it with boundary
					},
					body: formData
				});

				// Check if request was successful
				if (!fetchResponse.ok) {
					const errorResponse = await parseErrorResponse(fetchResponse);
					throw errorResponse;
				}

				// Parse response
				response = await parseSuccessResponse(fetchResponse);
			}

			// Process JSON fields in response if requested
			if (processJsonResponse && response.images) {
				// Ensure images field is properly processed to match backend structure
				response.images = Array.isArray(response.images)
					? response.images
					: typeof response.images === 'string'
						? JSON.parse(response.images)
						: [];
			}

			console.log('Upload completed successfully');
			return response;
		} catch (error) {
			attempt++;
			console.error(`Upload attempt ${attempt} failed:`, error);

			// If we have more attempts, wait with exponential backoff before retrying
			if (attempt < maxRetries) {
				const backoffMs = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s...
				console.log(`Retrying in ${backoffMs / 1000} seconds...`);
				await new Promise((resolve) => setTimeout(resolve, backoffMs));
			} else {
				// All retries failed
				console.error(`All ${maxRetries} upload attempts failed`);
				throw error;
			}
		}
	}
}

/**
 * Parse error response with improved details
 * @param {Response} response - The fetch response object
 * @returns {Error} - Enhanced error object
 */
async function parseErrorResponse(response) {
	let errorMessage = `Upload failed with status ${response.status}`;
	let errorData = null;

	try {
		// Try to parse JSON error response
		const contentType = response.headers.get('content-type');
		if (contentType && contentType.includes('application/json')) {
			errorData = await response.json();

			if (errorData.error) {
				errorMessage = errorData.error;
			} else if (errorData.detail) {
				errorMessage = errorData.detail;
			}
		} else {
			// Fallback to text response
			const errorText = await response.text();
			if (errorText) {
				errorMessage = `${errorMessage}: ${errorText}`;
			}
		}
	} catch (e) {
		console.warn('Failed to parse error response:', e);
	}

	const error = new Error(errorMessage);
	error.status = response.status;
	error.statusText = response.statusText;
	error.data = errorData;

	return error;
}

/**
 * Parse successful response with proper content type handling
 * @param {Response} response - The fetch response object
 * @returns {Object} - Parsed response data
 */
async function parseSuccessResponse(response) {
	const contentType = response.headers.get('content-type');

	if (contentType && contentType.includes('application/json')) {
		try {
			const data = await response.json();
			console.log('Upload successful, server response:', data);
			return data;
		} catch (e) {
			console.warn('Error parsing JSON response:', e);
			const text = await response.text();
			return { success: true, message: text };
		}
	} else {
		const text = await response.text();
		console.log('Upload successful, server response (text):', text);

		// Try to parse as JSON in case content-type is incorrect
		try {
			return JSON.parse(text);
		} catch (e) {
			// Not JSON, return as text
			return { success: true, message: text };
		}
	}
}

/**
 * Upload documents to a specific entity with improved error handling and retry
 * @param {string} entityType - The entity type (e.g., 'property', 'contract')
 * @param {number} entityId - The entity ID
 * @param {FileList|File[]} files - The files to upload
 * @param {Object} options - Upload options
 * @returns {Promise} - Promise resolving to the server response
 */
export async function uploadDocuments(entityType, entityId, files, options = {}) {
	if (!entityType || !entityId) {
		throw new Error(`Entity type and ID are required`);
	}

	// Set default options
	const {
		onProgress = null,
		maxRetries = MAX_RETRY_ATTEMPTS,
		processJsonResponse = true,
		fieldName = 'files' // Allow customizing field name
	} = options;

	let attempt = 0;

	while (attempt < maxRetries) {
		try {
			const formData = new FormData();

			// Add files to form data
			Array.from(files).forEach((file) => {
				formData.append(fieldName, file);
			});

			const token = localStorage.getItem('access_token');
			if (!token) {
				throw new Error('Authentication token required');
			}

			const uploadUrl = `${API_BASE_URL}/${entityType}s/${entityId}/uploads/`;

			let response;

			if (onProgress) {
				response = await uploadWithProgress(uploadUrl, formData, token, onProgress);
			} else {
				const fetchResponse = await fetch(uploadUrl, {
					method: 'POST',
					headers: {
						Authorization: `Bearer ${token}`
					},
					body: formData
				});

				if (!fetchResponse.ok) {
					const errorResponse = await parseErrorResponse(fetchResponse);
					throw errorResponse;
				}

				response = await parseSuccessResponse(fetchResponse);
			}

			return response;
		} catch (error) {
			attempt++;
			console.error(`Upload attempt ${attempt} failed:`, error);

			if (attempt < maxRetries) {
				const backoffMs = Math.pow(2, attempt) * 1000;
				await new Promise((resolve) => setTimeout(resolve, backoffMs));
			} else {
				throw error;
			}
		}
	}
}

/**
 * Enhanced helper function to handle file upload with progress tracking and error handling
 */
function uploadWithProgress(url, formData, token, progressCallback) {
	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();

		// Set up progress handler
		xhr.upload.onprogress = (event) => {
			if (event.lengthComputable) {
				const percentComplete = Math.round((event.loaded / event.total) * 100);
				progressCallback(percentComplete);
			}
		};

		// Set up completion handler
		xhr.onload = function () {
			if (xhr.status >= 200 && xhr.status < 300) {
				try {
					// Try to parse as JSON first
					const data = JSON.parse(xhr.responseText);

					// Process JSON fields if present
					if (data.images && typeof data.images === 'string') {
						try {
							data.images = JSON.parse(data.images);
						} catch (e) {
							console.warn('Error parsing images JSON field:', e);
						}
					}

					resolve(data);
				} catch (e) {
					// If not valid JSON, return text
					console.warn('Response is not valid JSON:', e);
					resolve({ success: true, message: xhr.responseText });
				}
			} else {
				// Create error object with detailed info
				const error = new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`);
				error.status = xhr.status;
				error.statusText = xhr.statusText;

				try {
					error.data = JSON.parse(xhr.responseText);
				} catch (e) {
					error.data = xhr.responseText;
				}

				reject(error);
			}
		};

		// Set up error handler
		xhr.onerror = function () {
			reject(new Error('Network error during upload'));
		};

		// Set up timeout handler
		xhr.ontimeout = function () {
			reject(new Error('Upload request timed out'));
		};

		// Set a reasonable timeout (30 seconds)
		xhr.timeout = 30000;

		// Open connection and send
		xhr.open('POST', url);
		xhr.setRequestHeader('Authorization', `Bearer ${token}`);
		xhr.send(formData);
	});
}

/**
 * Validate image files before upload with improved validation
 * @param {FileList|File[]} files - The files to validate
 * @param {Object} options - Validation options
 * @returns {Object} - Validation results
 */
export function validateImageFiles(files, options = {}) {
	const maxFiles = options.maxFiles || 10;
	const maxSize = options.maxSize || 5 * 1024 * 1024; // 5MB
	const allowedTypes = options.allowedTypes || [
		'image/jpeg',
		'image/png',
		'image/gif',
		'image/webp'
	];
	const minSize = options.minSize || 1024; // 1KB

	const validFiles = [];
	const invalidFiles = [];
	const warnings = [];

	// Check if we have files
	if (!files || files.length === 0) {
		return { validFiles, invalidFiles, warnings: ['No files provided for validation'] };
	}

	// Check if total files exceed limit
	if (files.length > maxFiles) {
		warnings.push(`يمكنك رفع ${maxFiles} صور كحد أقصى. تم تجاهل الصور الزائدة.`);
	}

	// Validate each file
	Array.from(files)
		.slice(0, maxFiles)
		.forEach((file) => {
			// Basic file check
			if (!file || !file.name) {
				invalidFiles.push(file || {});
				warnings.push('ملف غير صالح');
				return;
			}

			// Check file type
			if (!allowedTypes.includes(file.type)) {
				invalidFiles.push(file);
				warnings.push(
					`الملف "${file.name}" ليس من نوع صورة صالح. الأنواع المسموحة: ${allowedTypes.join(', ')}`
				);
				return;
			}

			// Check file size - too large
			if (file.size > maxSize) {
				invalidFiles.push(file);
				warnings.push(
					`الملف "${file.name}" أكبر من الحد المسموح به (${Math.round(maxSize / 1024 / 1024)}MB).`
				);
				return;
			}

			// Check file size - too small (potentially corrupted)
			if (file.size < minSize) {
				invalidFiles.push(file);
				warnings.push(
					`الملف "${file.name}" صغير جدًا (${Math.round(file.size / 1024)}KB). قد يكون تالفًا.`
				);
				return;
			}

			// File passed all checks
			validFiles.push(file);
		});

	return { validFiles, invalidFiles, warnings };
}

/**
 * Create an object URL for an image file (for preview)
 * @param {File} file - The image file
 * @returns {string} - Object URL
 */
export function createImagePreviewUrl(file) {
	if (!file) return null;
	return URL.createObjectURL(file);
}

/**
 * Revoke an object URL to prevent memory leaks
 * @param {string} url - The object URL to revoke
 */
export function revokeImagePreviewUrl(url) {
	if (url && url.startsWith('blob:')) {
		URL.revokeObjectURL(url);
	}
}

/**
 * Process the upload response to ensure JSON fields are properly parsed
 * @param {Object} response - The upload response
 * @returns {Object} - Processed response
 */
export function processUploadResponse(response) {
	if (!response) return response;

	// Process images field if present
	if (response.images) {
		try {
			// If images is a string, try to parse it
			if (typeof response.images === 'string') {
				response.images = JSON.parse(response.images);
			}

			// Ensure each image has all required fields
			if (Array.isArray(response.images)) {
				response.images = response.images.map((img) => ({
					id: img.id || crypto.randomUUID(),
					url: img.url || img.path,
					path: img.path || img.url,
					name: img.name || 'image',
					size: img.size || 0,
					type: img.content_type || img.type || 'image/jpeg',
					uploaded_at: img.uploaded_at || new Date().toISOString(),
					is_primary: img.is_primary || false
				}));
			}
		} catch (e) {
			console.error('Error processing images in upload response:', e);
		}
	}

	return response;
}

export default {
	uploadPropertyImages,
	uploadDocuments,
	validateImageFiles,
	createImagePreviewUrl,
	revokeImagePreviewUrl,
	processUploadResponse
};
