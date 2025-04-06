// src/lib/services/uploadService.js

/**
 * Unified service for handling file uploads throughout the application.
 * This consolidates functionality from upload.js, directUpload.js and the upload method in api.js
 */

import { browser } from '$app/environment';

// Get API base URL from environment or use default
const API_BASE_URL = browser ? import.meta.env.VITE_API_URL || 'http://localhost:8000/api' : '';

/**
 * Upload property images to a specific property
 * @param {number} propertyId - The property ID
 * @param {FileList|File[]} files - The files to upload
 * @param {Object} options - Upload options
 * @param {Function} options.onProgress - Progress callback function
 * @returns {Promise} - Promise resolving to the server response
 */
export async function uploadPropertyImages(propertyId, files, options = {}) {
	if (!propertyId) {
		console.error('Property ID is required for upload');
		throw new Error('Property ID is required');
	}

	if (!files || files.length === 0) {
		console.error('No files provided for upload');
		throw new Error('No files provided');
	}

	// Log what we're about to do
	console.log(`Starting upload of ${files.length} files to property ID: ${propertyId}`);

	try {
		// Create form data as Django expects
		const formData = new FormData();

		// Use 'images' as the field name to match Django's BaseUploadView expectation
		Array.from(files).forEach((file) => {
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
		if (options.onProgress) {
			return uploadWithProgress(uploadUrl, formData, token, options.onProgress);
		} else {
			// Simple fetch request without progress tracking
			const response = await fetch(uploadUrl, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
					// Don't set Content-Type - let browser set it with boundary
				},
				body: formData
			});

			// Check if request was successful
			if (!response.ok) {
				const errorText = await response.text();
				console.error(`Upload failed with status ${response.status}: ${errorText}`);
				throw new Error(`Upload failed: ${response.statusText}`);
			}

			// Parse response
			const contentType = response.headers.get('content-type');
			if (contentType && contentType.includes('application/json')) {
				const data = await response.json();
				console.log('Upload successful, server response:', data);
				return data;
			} else {
				const text = await response.text();
				console.log('Upload successful, server response (text):', text);
				return { success: true, message: text };
			}
		}
	} catch (error) {
		console.error('Upload error:', error);
		throw error;
	}
}

/**
 * Upload documents to a specific entity
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

	try {
		const formData = new FormData();

		// Use 'files' as the field name for documents
		Array.from(files).forEach((file) => {
			formData.append('files', file);
		});

		const token = localStorage.getItem('access_token');
		if (!token) {
			throw new Error('Authentication token required');
		}

		const uploadUrl = `${API_BASE_URL}/${entityType}s/${entityId}/uploads/`;

		if (options.onProgress) {
			return uploadWithProgress(uploadUrl, formData, token, options.onProgress);
		} else {
			const response = await fetch(uploadUrl, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
				},
				body: formData
			});

			if (!response.ok) {
				throw new Error(`Upload failed: ${response.statusText}`);
			}

			return await response.json();
		}
	} catch (error) {
		console.error(`Error uploading documents to ${entityType} ${entityId}:`, error);
		throw error;
	}
}

/**
 * Helper function to handle file upload with progress tracking
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
					resolve(data);
				} catch (e) {
					// If not JSON, return text
					resolve({ success: true, message: xhr.responseText });
				}
			} else {
				reject(new Error(`Upload failed: ${xhr.statusText}`));
			}
		};

		// Set up error handler
		xhr.onerror = function () {
			reject(new Error('Network error during upload'));
		};

		// Open connection and send
		xhr.open('POST', url);
		xhr.setRequestHeader('Authorization', `Bearer ${token}`);
		xhr.send(formData);
	});
}

/**
 * Validate image files before upload
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

	const validFiles = [];
	const invalidFiles = [];
	const warnings = [];

	// Check if total files exceed limit
	if (files.length > maxFiles) {
		warnings.push(`يمكنك رفع ${maxFiles} صور كحد أقصى. تم تجاهل الصور الزائدة.`);
	}

	// Validate each file
	Array.from(files)
		.slice(0, maxFiles)
		.forEach((file) => {
			// Check file type
			if (!allowedTypes.includes(file.type)) {
				invalidFiles.push(file);
				warnings.push(`الملف "${file.name}" ليس من نوع صورة صالح.`);
				return;
			}

			// Check file size
			if (file.size > maxSize) {
				invalidFiles.push(file);
				warnings.push(
					`الملف "${file.name}" أكبر من الحد المسموح به (${Math.round(maxSize / 1024 / 1024)}MB).`
				);
				return;
			}

			validFiles.push(file);
		});

	return { validFiles, invalidFiles, warnings };
}

export default {
	uploadPropertyImages,
	uploadDocuments,
	validateImageFiles
};
