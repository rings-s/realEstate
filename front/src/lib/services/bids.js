import api, { handleApiError } from './api';

/**
 * Bid management services
 */
export default {
	/**
	 * Get bids for an auction
	 * @param {string} auctionId - Auction ID
	 */
	getBidsByAuction: async (auctionId) => {
		try {
			return await api.get(`/bids/?auction=${auctionId}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get bid details
	 * @param {string} id - Bid ID
	 */
	getBid: async (id) => {
		try {
			return await api.get(`/bids/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Place a bid on an auction
	 * @param {string} auctionId - Auction ID
	 * @param {number} bidAmount - Bid amount
	 * @param {number} maxBidAmount - Maximum bid amount for auto-bidding (optional)
	 */
	placeBid: async (auctionId, bidAmount, maxBidAmount = null) => {
		try {
			return await api.post(`/auctions/${auctionId}/place-bid/`, {
				bid_amount: bidAmount,
				max_bid_amount: maxBidAmount,
				is_auto_bid: !!maxBidAmount
			});
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own bids
	 * @param {string} auctionId - Optional filter by auction
	 */
	getMyBids: async (auctionId = null) => {
		try {
			const queryParams = auctionId ? `?auction_id=${auctionId}` : '';
			return await api.get(`/bids/my-bids/${queryParams}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Mark a bid as winning (for auction creator/auctioneer)
	 * @param {string} bidId - Bid ID
	 */
	markAsWinning: async (bidId) => {
		try {
			return await api.post(`/bids/${bidId}/mark-winning/`);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
