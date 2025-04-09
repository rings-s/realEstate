/**
 * Auctions Store
 * Manages state for auction listings and operations
 */

import { writable, derived } from 'svelte/store';
import * as auctionService from '$lib/services/auctionService';

// Initial state
const initialState = {
	auctions: [],
	currentAuction: null,
	bids: [],
	isLoading: false,
	error: null,
	filters: {
		auction_type: '',
		status: '',
		is_published: '',
		is_featured: '',
		is_private: '',
		search: '',
		ordering: '-start_date'
	},
	pagination: {
		page: 1,
		pageSize: 10,
		totalItems: 0,
		totalPages: 0
	}
};

// Create the auctions store
function createAuctionsStore() {
	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		/**
		 * Reset store to initial state
		 */
		reset: () => set(initialState),

		/**
		 * Set loading state
		 * @param {boolean} isLoading - Loading state
		 */
		setLoading: (isLoading) => {
			update((state) => ({
				...state,
				isLoading,
				error: isLoading ? null : state.error
			}));
		},

		/**
		 * Set error message
		 * @param {string} error - Error message
		 */
		setError: (error) => {
			update((state) => ({
				...state,
				error,
				isLoading: false
			}));
		},

		/**
		 * Load auctions with filters
		 * @param {Object} filters - Filter parameters
		 * @param {number} page - Page number
		 * @param {number} pageSize - Page size
		 */
		loadAuctions: async (filters = {}, page = 1, pageSize = 10) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				// Merge current filters with new filters
				const mergedFilters = {
					...state.filters,
					...filters
				};

				// Prepare params for API call
				const params = {
					...mergedFilters,
					page,
					page_size: pageSize
				};

				// Clean empty filters
				Object.keys(params).forEach((key) => {
					if (params[key] === '' || params[key] === null || params[key] === undefined) {
						delete params[key];
					}
				});

				const response = await auctionService.getAuctions(params);

				update((state) => ({
					...state,
					auctions: response.results || [],
					pagination: {
						page: page,
						pageSize: pageSize,
						totalItems: response.count || 0,
						totalPages: Math.ceil((response.count || 0) / pageSize)
					},
					filters: mergedFilters,
					isLoading: false
				}));

				return response;
			} catch (error) {
				console.error('Error loading auctions:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحميل المزادات'
				}));

				throw error;
			}
		},

		/**
		 * Load a single auction by slug
		 * @param {string} slug - Auction slug
		 */
		loadAuction: async (slug) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const auction = await auctionService.getAuctionBySlug(slug);

				update((state) => ({
					...state,
					currentAuction: auction,
					isLoading: false
				}));

				return auction;
			} catch (error) {
				console.error('Error loading auction:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحميل تفاصيل المزاد'
				}));

				throw error;
			}
		},

		/**
		 * Load bids for an auction
		 * @param {string} auctionId - Auction ID
		 * @param {Object} params - Query parameters
		 */
		loadBids: async (auctionId, params = {}) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const response = await auctionService.getAuctionBids(auctionId, params);

				update((state) => ({
					...state,
					bids: response.results || [],
					isLoading: false
				}));

				return response;
			} catch (error) {
				console.error('Error loading bids:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحميل المزايدات'
				}));

				throw error;
			}
		},

		/**
		 * Create a new auction
		 * @param {Object} auctionData - Auction data
		 */
		createAuction: async (auctionData) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const newAuction = await auctionService.createAuction(auctionData);

				update((state) => ({
					...state,
					currentAuction: newAuction,
					isLoading: false
				}));

				return newAuction;
			} catch (error) {
				console.error('Error creating auction:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في إنشاء المزاد'
				}));

				throw error;
			}
		},

		/**
		 * Update an auction
		 * @param {string} slug - Auction slug
		 * @param {Object} auctionData - Updated auction data
		 * @param {boolean} partial - Whether to use PATCH (partial update)
		 */
		updateAuction: async (slug, auctionData, partial = true) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const updatedAuction = await auctionService.updateAuction(slug, auctionData, partial);

				update((state) => ({
					...state,
					currentAuction: updatedAuction,
					isLoading: false
				}));

				return updatedAuction;
			} catch (error) {
				console.error('Error updating auction:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تحديث المزاد'
				}));

				throw error;
			}
		},

		/**
		 * Delete an auction
		 * @param {string} slug - Auction slug
		 */
		deleteAuction: async (slug) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				await auctionService.deleteAuction(slug);

				update((state) => ({
					...state,
					currentAuction: null,
					isLoading: false
				}));

				return true;
			} catch (error) {
				console.error('Error deleting auction:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في حذف المزاد'
				}));

				throw error;
			}
		},

		/**
		 * Place a bid on an auction
		 * @param {string} auctionId - Auction ID
		 * @param {number} bidAmount - Bid amount
		 * @param {boolean} isAutoBid - Whether this is an auto bid
		 * @param {number} maxAutoBid - Maximum auto bid amount
		 * @param {string} notes - Bid notes
		 */
		placeBid: async (auctionId, bidAmount, isAutoBid = false, maxAutoBid = null, notes = '') => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null
			}));

			try {
				const bid = await auctionService.placeBid(
					auctionId,
					bidAmount,
					isAutoBid,
					maxAutoBid,
					notes
				);

				// Update current auction if this bid is for it
				update((state) => {
					let updatedState = { ...state, isLoading: false };

					if (updatedState.currentAuction && updatedState.currentAuction.id === auctionId) {
						updatedState.currentAuction = {
							...updatedState.currentAuction,
							current_bid: bidAmount,
							bid_count: (updatedState.currentAuction.bid_count || 0) + 1
						};

						// Add new bid to bids array if we have it loaded
						if (updatedState.bids.length > 0) {
							updatedState.bids = [bid, ...updatedState.bids];
						}
					}

					return updatedState;
				});

				return bid;
			} catch (error) {
				console.error('Error placing bid:', error);

				update((state) => ({
					...state,
					isLoading: false,
					error: error.message || 'فشل في تقديم المزايدة'
				}));

				throw error;
			}
		},

		/**
		 * Get bid suggestions for an auction
		 * @param {string} auctionId - Auction ID
		 */
		getBidSuggestions: async (auctionId) => {
			try {
				return await auctionService.getBidSuggestions(auctionId);
			} catch (error) {
				console.error('Error getting bid suggestions:', error);
				throw error;
			}
		},

		/**
		 * Upload auction image
		 * @param {string} auctionId - Auction ID
		 * @param {File} imageFile - Image file
		 * @param {Object} metadata - Image metadata
		 */
		uploadImage: async (auctionId, imageFile, metadata = {}) => {
			try {
				const response = await auctionService.uploadAuctionImage(auctionId, imageFile, metadata);

				// Update the current auction images if viewing that auction
				update((state) => {
					if (state.currentAuction && state.currentAuction.id === auctionId) {
						const updatedImages = [...(state.currentAuction.images || []), response];
						return {
							...state,
							currentAuction: {
								...state.currentAuction,
								images: updatedImages
							}
						};
					}
					return state;
				});

				return response;
			} catch (error) {
				console.error('Error uploading auction image:', error);
				throw error;
			}
		},

		/**
		 * Update filters and reload auctions
		 * @param {Object} newFilters - New filter values
		 */
		updateFilters: async (newFilters) => {
			update((state) => ({
				...state,
				filters: {
					...state.filters,
					...newFilters
				},
				pagination: {
					...state.pagination,
					page: 1 // Reset to first page on filter change
				}
			}));

			// Get the updated filters from the store
			let updatedFilters;
			update((state) => {
				updatedFilters = state.filters;
				return state;
			});

			// Reload auctions with updated filters
			return auctions.loadAuctions(updatedFilters, 1, initialState.pagination.pageSize);
		},

		/**
		 * Change page and reload auctions
		 * @param {number} page - Page number
		 */
		changePage: async (page) => {
			let currentFilters, pageSize;

			update((state) => {
				currentFilters = state.filters;
				pageSize = state.pagination.pageSize;

				return {
					...state,
					pagination: {
						...state.pagination,
						page
					}
				};
			});

			return auctions.loadAuctions(currentFilters, page, pageSize);
		}
	};
}

// Create and export the store
export const auctions = createAuctionsStore();

// Derived stores for convenient access
export const auctionsList = derived(auctions, ($auctions) => $auctions.auctions);
export const currentAuction = derived(auctions, ($auctions) => $auctions.currentAuction);
export const bidsList = derived(auctions, ($auctions) => $auctions.bids);
export const isLoading = derived(auctions, ($auctions) => $auctions.isLoading);
export const error = derived(auctions, ($auctions) => $auctions.error);
export const filters = derived(auctions, ($auctions) => $auctions.filters);
export const pagination = derived(auctions, ($auctions) => $auctions.pagination);
