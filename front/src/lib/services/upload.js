// front/src/lib/services/upload.js
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

			// Append each image with field name 'files' to match backend expectations
			Array.from(images).forEach((file) => {
				formData.append('files', file);
			});

			// Make sure propertyId is provided and valid
			if (!propertyId) {
				throw new Error('Property ID is required for image upload');
			}

			// Use the corrected API endpoint that matches the backend URL pattern
			return await api.upload(`properties/${propertyId}/uploads/`, formData);
		} catch (error) {
			console.error('Image upload error:', error);
			throw handleApiError(error);
		}
	}
};
