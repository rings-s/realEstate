/**
 * Auction Service
 * Handles API calls for auction management
 */

import { ENDPOINTS } from '$lib/config/api';
import { get, post, put, patch, del, uploadFiles } from '$lib/utils/api';

/**
 * Get auction listings with filters
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.page_size - Number of items per page
 * @param {string} params.auction_type - Filter by auction type
 * @param {string} params.status - Filter by status
 * @param {boolean} params.is_published - Filter by published status
 * @param {boolean} params.is_featured - Filter by featured status
 * @param {boolean} params.is_private - Filter by private status
 * @param {string} params.search - Search term
 * @param {string} params.ordering - Order by field
 * @returns {Promise<Object>} Auction listings response
 */
export const getAuctions = async (params = {}) => {
	return get(ENDPOINTS.AUCTION.LIST, { params });
};

/**
 * Get auction details by slug
 * @param {string} slug - Auction slug
 * @returns {Promise<Object>} Auction details response
 */
export const getAuctionBySlug = async (slug) => {
	return get(ENDPOINTS.AUCTION.DETAIL(slug));
};

/**
 * Create a new auction
 * @param {Object} auctionData - Auction data
 * @returns {Promise<Object>} Created auction response
 */
export const createAuction = async (auctionData) => {
	return post(ENDPOINTS.AUCTION.CREATE, formatAuctionData(auctionData));
};

/**
 * Update an auction
 * @param {string} slug - Auction slug
 * @param {Object} auctionData - Updated auction data
 * @param {boolean} partial - Whether to use PATCH (partial update)
 * @returns {Promise<Object>} Updated auction response
 */
export const updateAuction = async (slug, auctionData, partial = false) => {
	const formattedData = formatAuctionData(auctionData);

	if (partial) {
		return patch(ENDPOINTS.AUCTION.UPDATE(slug), formattedData);
	} else {
		return put(ENDPOINTS.AUCTION.UPDATE(slug), formattedData);
	}
};

/**
 * Delete an auction
 * @param {string} slug - Auction slug
 * @returns {Promise<Object>} Response
 */
export const deleteAuction = async (slug) => {
	return del(ENDPOINTS.AUCTION.DELETE(slug));
};

/**
 * Get auction images
 * @param {string} auctionId - Auction ID
 * @returns {Promise<Object>} Auction images response
 */
export const getAuctionImages = async (auctionId) => {
	return get(ENDPOINTS.AUCTION.IMAGES(auctionId));
};

/**
 * Upload an auction image
 * @param {string} auctionId - Auction ID
 * @param {File} imageFile - Image file
 * @param {Object} metadata - Image metadata
 * @param {boolean} isPrimary - Whether this is the primary image
 * @param {string} caption - Image caption
 * @param {number} order - Display order
 * @returns {Promise<Object>} Uploaded image response
 */
export const uploadAuctionImage = async (
	auctionId,
	imageFile,
	{ isPrimary = false, caption = '', order = 0 } = {}
) => {
	const formData = new FormData();
	formData.append('image', imageFile);
	formData.append('is_primary', isPrimary);

	if (caption) {
		formData.append('caption', caption);
	}

	if (order) {
		formData.append('order', order);
	}

	return uploadFiles(ENDPOINTS.AUCTION.IMAGES(auctionId), formData);
};

/**
 * Delete an auction image
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const deleteAuctionImage = async (imageId) => {
	return del(ENDPOINTS.AUCTION.IMAGE_DELETE(imageId));
};

/**
 * Set an auction image as primary
 * @param {string} imageId - Image ID
 * @returns {Promise<Object>} Response
 */
export const setAuctionImageAsPrimary = async (imageId) => {
	return patch(ENDPOINTS.AUCTION.IMAGE_UPDATE(imageId), {
		is_primary: true
	});
};

/**
 * Get property views for an auction
 * @param {string} auctionId - Auction ID
 * @returns {Promise<Object>} Property views response
 */
export const getPropertyViews = async (auctionId) => {
	return get(ENDPOINTS.AUCTION.PROPERTY_VIEWS(auctionId));
};

/**
 * Get bids for an auction
 * @param {string} auctionId - Auction ID
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Bids response
 */
export const getAuctionBids = async (auctionId, params = {}) => {
	return get(ENDPOINTS.BID.LIST(auctionId), { params });
};

/**
 * Place a bid on an auction
 * @param {string} auctionId - Auction ID
 * @param {number} bidAmount - Bid amount
 * @param {boolean} isAutoBid - Whether this is an auto bid
 * @param {number} maxAutoBid - Maximum auto bid amount
 * @param {string} notes - Bid notes
 * @returns {Promise<Object>} Bid response
 */
export const placeBid = async (
	auctionId,
	bidAmount,
	isAutoBid = false,
	maxAutoBid = null,
	notes = ''
) => {
	const bidData = {
		bid_amount: bidAmount,
		is_auto_bid: isAutoBid
	};

	if (isAutoBid && maxAutoBid) {
		bidData.max_auto_bid = maxAutoBid;
	}

	if (notes) {
		bidData.notes = notes;
	}

	return post(ENDPOINTS.BID.CREATE(auctionId), bidData);
};

/**
 * Get bid suggestions for an auction
 * @param {string} auctionId - Auction ID
 * @returns {Promise<Object>} Bid suggestions response
 */
export const getBidSuggestions = async (auctionId) => {
	return get(ENDPOINTS.BID.SUGGESTIONS(auctionId));
};

/**
 * Format auction data for API
 * This handles JSON fields that need special formatting
 * @param {Object} auctionData - Auction data from form
 * @returns {Object} Formatted auction data
 */
export const formatAuctionData = (auctionData) => {
	const formattedData = { ...auctionData };

	// Handle date fields to ensure they are in ISO format
	if (formattedData.start_date && typeof formattedData.start_date === 'object') {
		formattedData.start_date = formattedData.start_date.toISOString();
	}

	if (formattedData.end_date && typeof formattedData.end_date === 'object') {
		formattedData.end_date = formattedData.end_date.toISOString();
	}

	if (
		formattedData.registration_deadline &&
		typeof formattedData.registration_deadline === 'object'
	) {
		formattedData.registration_deadline = formattedData.registration_deadline.toISOString();
	}

	// Convert arrays/objects to JSON strings
	if (Array.isArray(formattedData.viewing_dates)) {
		formattedData.viewing_dates = JSON.stringify(formattedData.viewing_dates);
	}

	if (Array.isArray(formattedData.timeline)) {
		formattedData.timeline = JSON.stringify(formattedData.timeline);
	}

	if (typeof formattedData.financial_terms === 'object' && formattedData.financial_terms !== null) {
		formattedData.financial_terms = JSON.stringify(formattedData.financial_terms);
	}

	if (typeof formattedData.analytics === 'object' && formattedData.analytics !== null) {
		formattedData.analytics = JSON.stringify(formattedData.analytics);
	}

	return formattedData;
};
