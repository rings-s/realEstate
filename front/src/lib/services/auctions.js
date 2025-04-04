import api, { handleApiError } from './api';

/**
 * Auction management services
 */
export default {
	/**
	 * Get list of auctions with optional filters
	 * @param {Object} filters - Filter parameters
	 */
	getAuctions: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/auctions/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get auction details by slug
	 * @param {string} slug - Auction slug
	 */
	getAuctionBySlug: async (slug) => {
		try {
			return await api.get(`/auctions/by-slug/${slug}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get auction details by ID
	 * @param {string} id - Auction ID
	 */
	getAuction: async (id) => {
		try {
			return await api.get(`/auctions/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new auction
	 * @param {Object} auctionData - Auction data
	 */
	createAuction: async (auctionData) => {
		try {
			return await api.post('/auctions/', auctionData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update an existing auction
	 * @param {string} id - Auction ID
	 * @param {Object} auctionData - Updated auction data
	 */
	updateAuction: async (id, auctionData) => {
		try {
			return await api.patch(`/auctions/${id}/`, auctionData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own auctions
	 */
	getMyAuctions: async () => {
		try {
			return await api.get('/auctions/my-auctions/');
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Extend auction end time
	 * @param {string} id - Auction ID
	 * @param {number} minutes - Minutes to extend auction
	 */
	extendAuction: async (id, minutes) => {
		try {
			return await api.post(`/auctions/${id}/extend/`, { minutes });
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Close an auction before its end time
	 * @param {string} id - Auction ID
	 * @param {string} reason - Reason for closing
	 */
	closeAuction: async (id, reason) => {
		try {
			return await api.post(`/auctions/${id}/close/`, { reason });
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload auction images
	 * @param {string} id - Auction ID
	 * @param {FileList} images - Auction images
	 */
	uploadAuctionImages: async (id, images) => {
		try {
			const formData = new FormData();
			for (let i = 0; i < images.length; i++) {
				formData.append('images', images[i]);
			}
			return await api.upload(`/auctions/${id}/upload-images/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
