/**
 * Enhanced Property Image Upload Service
 * A robust module for handling property image uploads with retries and progress tracking
 */

import { ENDPOINTS } from '$lib/config/api';
import { uploadFiles } from '$lib/utils/api';
import { addToast } from '$lib/stores/ui';
import { t } from '$lib/config/translations';
import { get } from 'svelte/store';
import { language } from '$lib/stores/ui';

// Constants
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000;
const MAX_CONCURRENT_UPLOADS = 3; // Limit concurrent uploads to prevent overload

/**
 * Upload a single property image with retry mechanism
 * @param {string} propertyId - Property ID
 * @param {File} imageFile - Image file object
 * @param {Object} options - Upload options
 * @returns {Promise<Object>} Uploaded image data
 */
export const uploadPropertyImage = async (
	propertyId,
	imageFile,
	{ isPrimary = false, caption = '', altText = '', order = 0, onProgress = null } = {}
) => {
	let retries = 0;

	while (retries <= MAX_RETRIES) {
		try {
			// Validate inputs
			if (!propertyId) throw new Error('Property ID is required');
			if (!imageFile) throw new Error('Image file is required');

			// Log the upload attempt for debugging
			console.log(`Uploading image (attempt ${retries + 1}/${MAX_RETRIES + 1}):`, {
				propertyId,
				fileName: imageFile.name,
				fileSize: imageFile.size,
				fileType: imageFile.type,
				isPrimary
			});

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

			// Create form data with proper fields matching Django model
			const formData = new FormData();
			formData.append('image', imageFile);
			formData.append('is_primary', isPrimary ? 'true' : 'false');

			if (caption) {
				formData.append('caption', caption);
			}

			if (altText) {
				formData.append('alt_text', altText);
			}

			if (order !== undefined && order !== null) {
				formData.append('order', order.toString());
			}

			// Ensure property ID is correctly included
			formData.append('property', propertyId.toString());

			// Setup upload options
			const uploadConfig = {
				timeout: 30000, // 30 second timeout
				retryAttempts: 1 // Additional retry at API level
			};

			// Add progress tracking if provided
			if (onProgress && typeof onProgress === 'function') {
				uploadConfig.onUploadProgress = (progressEvent) => {
					// Handle progress tracking
					const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
					onProgress(percentCompleted);
				};
			}

			// Execute upload
			const response = await uploadFiles(
				ENDPOINTS.PROPERTY.IMAGES(propertyId),
				formData,
				uploadConfig
			);
			console.log('Image upload successful:', response);
			return response;
		} catch (error) {
			retries++;
			console.error(`Error uploading image (attempt ${retries}/${MAX_RETRIES + 1}):`, error);

			// If we've exhausted retries, throw the error
			if (retries > MAX_RETRIES) {
				throw error;
			}

			// Otherwise wait before retrying
			await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY * retries));
		}
	}
};

/**
 * Upload multiple property images with controlled concurrency
 * @param {string} propertyId - Property ID
 * @param {Array} images - Array of image objects with file and metadata
 * @param {Function} onProgress - Optional progress callback
 * @param {string} currentLanguage - Current language for messages
 * @returns {Promise<Object>} Upload results
 */
export const uploadMultiplePropertyImages = async (
	propertyId,
	images,
	onProgress = null,
	currentLanguage = null
) => {
	// Input validation
	if (!propertyId) {
		console.error('No property ID provided for image upload');
		return {
			success: false,
			message: 'Missing property ID',
			successCount: 0,
			failureCount: 0,
			results: []
		};
	}

	if (!images || !Array.isArray(images) || images.length === 0) {
		console.log('No images to upload');
		return {
			success: true,
			message: 'No images to upload',
			successCount: 0,
			failureCount: 0,
			results: []
		};
	}

	// Use provided language or get from store
	const lang = currentLanguage || get(language);

	// Track upload statistics
	let successCount = 0;
	let failureCount = 0;
	const totalImages = images.length;
	const results = [];

	// Start notification
	addToast(
		t('uploading_images', lang, {
			default: 'Uploading images...',
			count: totalImages
		}),
		'info'
	);

	try {
		// Process images in controlled batches to prevent overwhelming the server
		for (let i = 0; i < images.length; i += MAX_CONCURRENT_UPLOADS) {
			const batch = images.slice(i, i + MAX_CONCURRENT_UPLOADS);

			// Upload batch concurrently
			const batchPromises = batch.map((image, batchIndex) => {
				const imageIndex = i + batchIndex;

				// Skip images without files or already uploaded
				if (!image.file || image.uploaded) {
					console.log(`Skipping image ${imageIndex + 1}: already uploaded or no file`);
					return Promise.resolve(null);
				}

				// Upload with proper metadata
				return uploadPropertyImage(propertyId, image.file, {
					isPrimary: image.is_primary || imageIndex === 0, // First image is primary by default
					caption: image.caption || '',
					altText: image.alt_text || '',
					order: imageIndex,
					onProgress: (progress) => {
						if (onProgress) {
							onProgress({
								currentImage: imageIndex + 1,
								totalImages,
								progress,
								successCount,
								failureCount
							});
						}
					}
				})
					.then((result) => {
						successCount++;
						return { success: true, result, index: imageIndex };
					})
					.catch((error) => {
						failureCount++;
						console.error(`Failed to upload image ${imageIndex + 1}:`, error);
						return { success: false, error, index: imageIndex };
					});
			});

			// Wait for batch to complete
			const batchResults = await Promise.all(batchPromises);
			results.push(...batchResults.filter(Boolean));

			// Show progress after each batch
			addToast(
				t('image_upload_progress', lang, {
					default: 'Uploaded {{count}} of {{total}} images',
					count: successCount,
					total: totalImages
				}),
				'info',
				3000
			);
		}

		// Final status notification
		if (successCount > 0) {
			addToast(
				t('images_uploaded', lang, {
					default: 'Successfully uploaded {{count}} images',
					count: successCount
				}),
				'success'
			);
		}

		if (failureCount > 0) {
			addToast(
				t('some_images_failed', lang, {
					default: 'Failed to upload {{count}} images',
					count: failureCount
				}),
				'error'
			);
		}

		return {
			success: failureCount === 0,
			message:
				failureCount === 0
					? 'All images uploaded successfully'
					: `${failureCount} images failed to upload`,
			successCount,
			failureCount,
			results: results.filter((r) => r.success).map((r) => r.result)
		};
	} catch (error) {
		console.error('Fatal error in image upload process:', error);
		addToast(
			t('image_upload_error', lang, {
				default: 'Error uploading images'
			}),
			'error'
		);

		return {
			success: false,
			message: error.message || 'Unknown error during image upload',
			successCount,
			failureCount: totalImages - successCount,
			results: results.filter((r) => r.success).map((r) => r.result)
		};
	}
};

export default {
	uploadPropertyImage,
	uploadMultiplePropertyImages
};
