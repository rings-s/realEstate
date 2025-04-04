import { writable, derived, get } from 'svelte/store';
import auctionsService from '$lib/services/auctions';
import bidsService from '$lib/services/bids';

const createAuctionsStore = () => {
	const initialState = {
		auctions: [],
		myAuctions: [],
		activeAuctions: [],
		currentAuction: null,
		currentBids: [],
		myBids: {},
		isLoading: false,
		error: null,
		filters: {
			status: null,
			auction_type: null,
			is_featured: null,
			is_published: null,
			search: null,
			ordering: null
		},
		pagination: {
			page: 1,
			pageSize: 10,
			totalItems: 0,
			totalPages: 0
		}
	};

	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,

		// Load auctions with optional filters
		loadAuctions: async (filters = {}, page = 1, pageSize = 10) => {
			update((state) => ({
				...state,
				isLoading: true,
				error: null,
				filters: { ...state.filters, ...filters },
				pagination: { ...state.pagination, page, pageSize }
			}));

			try {
				const queryParams = {
					...filters,
					page,
					page_size: pageSize
				};

				const response = await auctionsService.getAuctions(queryParams);

				update((state) => ({
					...state,
					auctions: response.results,
					isLoading: false,
					pagination: {
						page,
						pageSize,
						totalItems: response.count,
						totalPages: Math.ceil(response.count / pageSize)
					}
				}));
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
			}
		},

		// Load auction details by slug
		loadAuctionBySlug: async (slug) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.getAuctionBySlug(slug);
				update((state) => ({ ...state, currentAuction: response, isLoading: false }));

				// Load bids for this auction
				auctionsStore.loadBids(response.id);

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load active auctions
		loadActiveAuctions: async () => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.getAuctions({ status: 'active' });
				update((state) => ({ ...state, activeAuctions: response.results, isLoading: false }));
				return response.results;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load user's own auctions
		loadMyAuctions: async () => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.getMyAuctions();
				update((state) => ({ ...state, myAuctions: response, isLoading: false }));
				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load bids for an auction
		loadBids: async (auctionId) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await bidsService.getBidsByAuction(auctionId);
				update((state) => ({ ...state, currentBids: response.results, isLoading: false }));
				return response.results;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Load user's own bids
		loadMyBids: async (auctionId = null) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await bidsService.getMyBids(auctionId);

				if (auctionId) {
					// Store bids for specific auction
					update((state) => ({
						...state,
						myBids: {
							...state.myBids,
							[auctionId]: response
						},
						isLoading: false
					}));
				} else {
					// Group bids by auction ID
					const bidsByAuction = {};
					response.forEach((bid) => {
						if (!bidsByAuction[bid.auction]) {
							bidsByAuction[bid.auction] = [];
						}
						bidsByAuction[bid.auction].push(bid);
					});

					update((state) => ({
						...state,
						myBids: bidsByAuction,
						isLoading: false
					}));
				}

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Place a bid
		placeBid: async (auctionId, bidAmount, maxBidAmount = null) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await bidsService.placeBid(auctionId, bidAmount, maxBidAmount);

				// Update bids for this auction
				auctionsStore.loadBids(auctionId);

				// Update my bids
				auctionsStore.loadMyBids(auctionId);

				// If this is the current auction, update its current bid
				update((state) => {
					if (state.currentAuction && state.currentAuction.id === auctionId) {
						return {
							...state,
							currentAuction: {
								...state.currentAuction,
								current_bid: bidAmount
							},
							isLoading: false
						};
					}
					return { ...state, isLoading: false };
				});

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Create a new auction
		createAuction: async (auctionData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.createAuction(auctionData);

				// Add to myAuctions list
				update((state) => ({
					...state,
					myAuctions: [response, ...state.myAuctions],
					isLoading: false
				}));

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Update an existing auction
		updateAuction: async (id, auctionData) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.updateAuction(id, auctionData);

				// Update in both lists if present
				update((state) => {
					const updatedAuctions = state.auctions.map((a) => (a.id === id ? response : a));

					const updatedMyAuctions = state.myAuctions.map((a) => (a.id === id ? response : a));

					const updatedActiveAuctions = state.activeAuctions.map((a) =>
						a.id === id ? response : a
					);

					return {
						...state,
						auctions: updatedAuctions,
						myAuctions: updatedMyAuctions,
						activeAuctions: updatedActiveAuctions,
						currentAuction: state.currentAuction?.id === id ? response : state.currentAuction,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Extend auction
		extendAuction: async (id, minutes) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.extendAuction(id, minutes);

				// Reload auction details to get updated end time
				if (get({ subscribe }).currentAuction?.id === id) {
					auctionsStore.loadAuctionBySlug(get({ subscribe }).currentAuction.slug);
				}

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Close auction
		closeAuction: async (id, reason) => {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				const response = await auctionsService.closeAuction(id, reason);

				// Update auction status in lists
				update((state) => {
					const updateStatus = (a) => {
						if (a.id === id) {
							return { ...a, status: 'closed', end_reason: reason };
						}
						return a;
					};

					return {
						...state,
						auctions: state.auctions.map(updateStatus),
						myAuctions: state.myAuctions.map(updateStatus),
						activeAuctions: state.activeAuctions.filter((a) => a.id !== id),
						currentAuction:
							state.currentAuction?.id === id
								? { ...state.currentAuction, status: 'closed', end_reason: reason }
								: state.currentAuction,
						isLoading: false
					};
				});

				return response;
			} catch (error) {
				update((state) => ({ ...state, isLoading: false, error }));
				throw error;
			}
		},

		// Clear current auction
		clearCurrentAuction: () => {
			update((state) => ({
				...state,
				currentAuction: null,
				currentBids: []
			}));
		},

		// Update filters
		setFilters: (filters) => {
			update((state) => ({
				...state,
				filters: { ...state.filters, ...filters }
			}));

			// Reload auctions with new filters
			const storeState = get({ subscribe });
			return auctionsStore.loadAuctions(
				storeState.filters,
				1, // Reset to first page when filters change
				storeState.pagination.pageSize
			);
		},

		// Reset filters
		resetFilters: () => {
			const defaultFilters = {
				status: null,
				auction_type: null,
				is_featured: null,
				is_published: null,
				search: null,
				ordering: null
			};

			update((state) => ({ ...state, filters: defaultFilters }));

			// Reload auctions with reset filters
			const storeState = get({ subscribe });
			return auctionsStore.loadAuctions({}, 1, storeState.pagination.pageSize);
		},

		// Clear error state
		clearError: () => {
			update((state) => ({ ...state, error: null }));
		}
	};
};

// Create the store
export const auctionsStore = createAuctionsStore();

// Derived stores
export const auctions = derived(auctionsStore, ($store) => $store.auctions);
export const myAuctions = derived(auctionsStore, ($store) => $store.myAuctions);
export const activeAuctions = derived(auctionsStore, ($store) => $store.activeAuctions);
export const currentAuction = derived(auctionsStore, ($store) => $store.currentAuction);
export const currentBids = derived(auctionsStore, ($store) => $store.currentBids);
export const myBids = derived(auctionsStore, ($store) => $store.myBids);
export const auctionsLoading = derived(auctionsStore, ($store) => $store.isLoading);
export const auctionsError = derived(auctionsStore, ($store) => $store.error);
export const auctionFilters = derived(auctionsStore, ($store) => $store.filters);
export const auctionPagination = derived(auctionsStore, ($store) => $store.pagination);

// Derived store for getting my bids for a specific auction
export const getMyBidsForAuction = (auctionId) =>
	derived(myBids, ($myBids) => $myBids[auctionId] || []);
