// front/src/lib/services/directUpload.js

/**
 * A simplified, direct approach to uploading property images
 * that exactly matches the Django backend's expectations
 */

// Get API base URL from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Direct property image upload function with minimal abstraction
 * Designed to exactly match Django's BaseUploadView expectations
 *
 * @param {number} propertyId - The property ID
 * @param {FileList|File[]} files - The files to upload
 * @param {Function} progressCallback - Optional progress callback function
 * @returns {Promise} - Promise resolving to the server response
 */
export async function uploadPropertyImages(propertyId, files, progressCallback = null) {
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
		// Create form data exactly as Django expects
		const formData = new FormData();

		// Use 'files' as the field name to match Django's expectation
		// for multiple file uploads
		Array.from(files).forEach((file) => {
			console.log(
				`Adding file to FormData: ${file.name}, type: ${file.type}, size: ${file.size} bytes`
			);
			formData.append('files', file);
		});

		// Get authentication token
		const token = localStorage.getItem('access_token');
		if (!token) {
			console.error('Authentication token not found');
			throw new Error('Authentication token required');
		}

		// Construct exact URL that matches Django's URL pattern
		const uploadUrl = `${API_BASE_URL}/properties/${propertyId}/upload-images/`;
		console.log(`Upload URL: ${uploadUrl}`);

		// Create request with progress tracking if callback provided
		if (progressCallback) {
			return uploadWithProgress(uploadUrl, formData, token, progressCallback);
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
 * Helper function to handle file upload with progress tracking
 */
function uploadWithProgress(url, formData, token, progressCallback) {
	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();

		// Set up progress handler
		xhr.upload.onprogress = (event) => {
			if (event.lengthComputable) {
				const percentComplete = Math.round((event.loaded / event.total) * 100);
				console.log(`Upload progress: ${percentComplete}%`);
				progressCallback(percentComplete);
			}
		};

		// Set up completion handler
		xhr.onload = function () {
			if (xhr.status >= 200 && xhr.status < 300) {
				console.log(`Upload completed with status: ${xhr.status}`);
				try {
					// Try to parse as JSON first
					const data = JSON.parse(xhr.responseText);
					console.log('Upload successful, server response:', data);
					resolve(data);
				} catch (e) {
					// If not JSON, return text
					console.log('Upload successful, server response (text):', xhr.responseText);
					resolve({ success: true, message: xhr.responseText });
				}
			} else {
				console.error(`Upload failed with status ${xhr.status}: ${xhr.responseText}`);
				reject(new Error(`Upload failed: ${xhr.statusText}`));
			}
		};

		// Set up error handler
		xhr.onerror = function () {
			console.error('XHR error during upload');
			reject(new Error('Network error during upload'));
		};

		// Open connection and send
		xhr.open('POST', url);
		xhr.setRequestHeader('Authorization', `Bearer ${token}`);
		xhr.send(formData);
	});
}

export default {
	uploadPropertyImages
};
