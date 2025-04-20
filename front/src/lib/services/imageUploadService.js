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
	{ isPrimary = false, caption = '', alt_text = '', order = 0, onProgress = null } = {}
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

		// Always include alt_text and caption even if empty
		formData.append('alt_text', alt_text || '');
		formData.append('caption', caption || '');

		if (order !== undefined && order !== null) {
			formData.append('order', order.toString());
		}

		// Log what's being sent for debugging
		console.log(`Uploading image for property ${propertyId}:`, {
			fileType: imageFile.type,
			fileSize: imageFile.size,
			fileName: imageFile.name,
			isPrimary,
			hasCaption: !!caption,
			hasAltText: !!alt_text,
			order
		});

		// Debug the form data
		console.log('FormData contents:');
		for (let [key, value] of formData.entries()) {
			console.log(`${key}: ${value instanceof File ? value.name : value}`);
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
					alt_text: image.alt_text || image.file.name || '', // Use filename as alt_text if not provided
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
