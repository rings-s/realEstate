/**
 * File utility functions for handling files, images, and uploads
 */

/**
 * Check if the file type is allowed
 * @param {File} file - The file object to check
 * @param {Array} allowedTypes - Array of allowed MIME types
 * @returns {boolean} True if the file type is allowed
 */
export function isAllowedFileType(file, allowedTypes = []) {
	if (!file || !file.type) return false;

	// If no specific types provided, use default image types
	if (allowedTypes.length === 0) {
		allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
	}

	return allowedTypes.includes(file.type);
}

/**
 * Check if the file size is within allowed limit
 * @param {File} file - The file object to check
 * @param {number} maxSizeMB - Maximum file size in MB
 * @returns {boolean} True if the file size is allowed
 */
export function isAllowedFileSize(file, maxSizeMB = 5) {
	if (!file || !file.size) return false;

	const maxSizeBytes = maxSizeMB * 1024 * 1024;
	return file.size <= maxSizeBytes;
}

/**
 * Get file extension from filename or path
 * @param {string} filename - The filename or path
 * @returns {string} Lowercase file extension without dot
 */
export function getFileExtension(filename) {
	if (!filename) return '';

	return filename.split('.').pop().toLowerCase();
}

/**
 * Convert file size to human-readable format
 * @param {number} bytes - File size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Human-readable file size (e.g., "2.5 MB")
 */
export function formatFileSize(bytes, decimals = 2) {
	if (!bytes || bytes === 0) return '0 Bytes';

	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));

	return parseFloat((bytes / Math.pow(1024, i)).toFixed(decimals)) + ' ' + sizes[i];
}

/**
 * Generate a unique filename with original extension
 * @param {string} originalFilename - Original filename
 * @returns {string} Unique filename with original extension
 */
export function generateUniqueFilename(originalFilename) {
	if (!originalFilename) return '';

	const extension = getFileExtension(originalFilename);
	const timestamp = Date.now();
	const randomString = Math.random().toString(36).substring(2, 10);

	return `${timestamp}-${randomString}.${extension}`;
}

/**
 * Create a URL for a file object (for previews)
 * @param {File} file - The file object
 * @returns {string} Object URL for the file
 */
export function createFilePreviewUrl(file) {
	if (!file) return '';

	return URL.createObjectURL(file);
}

/**
 * Release a previously created object URL
 * @param {string} url - Object URL to release
 */
export function revokeFilePreviewUrl(url) {
	if (url && url.startsWith('blob:')) {
		URL.revokeObjectURL(url);
	}
}

/**
 * Check if a file is an image
 * @param {File} file - The file object to check
 * @returns {boolean} True if the file is an image
 */
export function isImageFile(file) {
	if (!file || !file.type) return false;

	return file.type.startsWith('image/');
}

/**
 * Convert a base64 string to a Blob
 * @param {string} base64 - Base64 string
 * @param {string} mimeType - MIME type of the content
 * @returns {Blob} Blob object
 */
export function base64ToBlob(base64, mimeType = 'application/octet-stream') {
	const byteCharacters = atob(base64.split(',')[1]);
	const byteArrays = [];

	for (let offset = 0; offset < byteCharacters.length; offset += 512) {
		const slice = byteCharacters.slice(offset, offset + 512);

		const byteNumbers = new Array(slice.length);
		for (let i = 0; i < slice.length; i++) {
			byteNumbers[i] = slice.charCodeAt(i);
		}

		const byteArray = new Uint8Array(byteNumbers);
		byteArrays.push(byteArray);
	}

	return new Blob(byteArrays, { type: mimeType });
}

/**
 * Create a thumbnail from an image file
 * @param {File} imageFile - The image file
 * @param {number} maxWidth - Maximum width of thumbnail
 * @param {number} maxHeight - Maximum height of thumbnail
 * @param {string} format - Image format (jpeg, png)
 * @param {number} quality - Image quality (0-1)
 * @returns {Promise<Blob>} Thumbnail as Blob
 */
export function createImageThumbnail(
	imageFile,
	maxWidth = 200,
	maxHeight = 200,
	format = 'jpeg',
	quality = 0.8
) {
	return new Promise((resolve, reject) => {
		if (!isImageFile(imageFile)) {
			reject(new Error('Not an image file'));
			return;
		}

		const img = new Image();
		const objectUrl = createFilePreviewUrl(imageFile);

		img.onload = () => {
			// Calculate thumbnail dimensions
			let width = img.width;
			let height = img.height;

			if (width > maxWidth || height > maxHeight) {
				const ratio = Math.min(maxWidth / width, maxHeight / height);
				width = Math.round(width * ratio);
				height = Math.round(height * ratio);
			}

			// Create canvas and context
			const canvas = document.createElement('canvas');
			canvas.width = width;
			canvas.height = height;
			const ctx = canvas.getContext('2d');

			// Draw image on canvas
			ctx.drawImage(img, 0, 0, width, height);

			// Convert to blob
			canvas.toBlob(
				(blob) => {
					revokeFilePreviewUrl(objectUrl);
					resolve(blob);
				},
				`image/${format}`,
				quality
			);
		};

		img.onerror = (error) => {
			revokeFilePreviewUrl(objectUrl);
			reject(error);
		};

		img.src = objectUrl;
	});
}

/**
 * Convert a file to base64 string
 * @param {File} file - The file to convert
 * @returns {Promise<string>} Base64 string representation
 */
export function fileToBase64(file) {
	return new Promise((resolve, reject) => {
		if (!file) {
			reject(new Error('No file provided'));
			return;
		}

		const reader = new FileReader();

		reader.onload = () => {
			resolve(reader.result);
		};

		reader.onerror = (error) => {
			reject(error);
		};

		reader.readAsDataURL(file);
	});
}

/**
 * Parse a CSV file
 * @param {File} file - CSV file
 * @returns {Promise<Array>} Parsed CSV data as array of objects
 */
export function parseCSVFile(file) {
	return new Promise((resolve, reject) => {
		if (!file || getFileExtension(file.name) !== 'csv') {
			reject(new Error('Not a CSV file'));
			return;
		}

		const reader = new FileReader();

		reader.onload = async (event) => {
			try {
				// Use papaparse if available
				const Papa = window.Papa;
				if (Papa) {
					Papa.parse(event.target.result, {
						header: true,
						skipEmptyLines: true,
						complete: (results) => {
							resolve(results.data);
						},
						error: (error) => {
							reject(error);
						}
					});
				} else {
					// Simple CSV parsing if papaparse not available
					const text = event.target.result;
					const lines = text.split('\n');
					const headers = lines[0].split(',').map((h) => h.trim());

					const data = lines.slice(1).map((line) => {
						const values = line.split(',');
						const obj = {};
						headers.forEach((header, i) => {
							obj[header] = values[i]?.trim() || '';
						});
						return obj;
					});

					resolve(data);
				}
			} catch (error) {
				reject(error);
			}
		};

		reader.onerror = (error) => {
			reject(error);
		};

		reader.readAsText(file);
	});
}

/**
 * Download data as a file
 * @param {Blob|string} data - Data to download
 * @param {string} filename - Suggested filename
 * @param {string} mimeType - MIME type of the content
 */
export function downloadFile(data, filename, mimeType = 'application/octet-stream') {
	// Create blob if data is a string
	const blob = typeof data === 'string' ? new Blob([data], { type: mimeType }) : data;

	// Create URL
	const url = URL.createObjectURL(blob);

	// Create download link
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;

	// Trigger download
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);

	// Clean up
	setTimeout(() => {
		URL.revokeObjectURL(url);
	}, 100);
}

/**
 * Extract text content from a PDF file using PDF.js
 * This requires PDF.js to be included in your project
 * @param {File} file - PDF file
 * @returns {Promise<string>} Extracted text
 */
export async function extractTextFromPDF(file) {
	// Check if PDF.js is available
	if (!window.pdfjsLib) {
		throw new Error('PDF.js library not found');
	}

	// Convert file to ArrayBuffer
	const arrayBuffer = await file.arrayBuffer();

	// Load PDF document
	const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;

	let text = '';

	// Extract text from each page
	for (let i = 1; i <= pdf.numPages; i++) {
		const page = await pdf.getPage(i);
		const content = await page.getTextContent();
		const pageText = content.items.map((item) => item.str).join(' ');

		text += pageText + '\n\n';
	}

	return text;
}
