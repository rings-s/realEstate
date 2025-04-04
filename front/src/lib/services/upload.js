// front/src/lib/services/uploads.js
import api, { handleApiError } from './api';

/**
 * Upload services for handling file uploads consistently
 */
export default {
	/**
	 * Upload property images with proper authentication
	 * @param {number} propertyId - Property ID
	 * @param {FileList|Array} images - Property images
	 * @returns {Promise<Object>} - Server response
	 */
	uploadPropertyImages: async (propertyId, images) => {
		try {
			if (!images || images.length === 0) {
				throw new Error('No images provided for upload');
			}

			const formData = new FormData();

			// Append each image - using 'files' to match what BaseUploadView expects
			Array.from(images).forEach((file) => {
				formData.append('files', file);
			});

			// Make sure propertyId is provided and valid
			if (!propertyId) {
				throw new Error('Property ID is required for image upload');
			}

			// Use the API service for consistent auth headers and error handling
			return await api.upload(`properties/${propertyId}/upload-images/`, formData);
		} catch (error) {
			console.error('Image upload error:', error);
			throw handleApiError(error);
		}
	}
};
