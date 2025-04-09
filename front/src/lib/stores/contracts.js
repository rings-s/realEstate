import { writable, derived } from 'svelte/store';
import { addToast } from '$lib/stores/ui';
import { t } from '$lib/config/translations';
import { language } from '$lib/stores/ui';
import { get } from 'svelte/store';
import contractsService from '$lib/services/contracts';

// Initial state
const initialState = {
  contractsList: [],
  currentContract: null,
  isLoading: false,
  error: null,
  filters: {
    status: '',
    payment_method: '',
    is_verified: '',
    search: '',
    page: 1,
    page_size: 20
  },
  pagination: {
    page: 1,
    totalPages: 1,
    totalItems: 0,
    hasNext: false,
    hasPrev: false
  }
};

// Create store
function createContractsStore() {
  const { subscribe, set, update } = writable({...initialState});

  return {
    subscribe,

    /**
     * Reset store to initial state
     */
    reset: () => set({...initialState}),

    /**
     * Load contracts with optional filters
     * @param {object} filters - Filter parameters
     */
    loadContracts: async (filters = {}) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        // Merge existing filters with new filters
        const mergedFilters = {
          ...get({ subscribe }).filters,
          ...filters,
          page: filters.page || get({ subscribe }).filters.page,
          page_size: filters.page_size || get({ subscribe }).filters.page_size
        };

        const response = await contractsService.getContracts(mergedFilters);

        // Update pagination info
        const pagination = {
          page: response.page || 1,
          totalPages: response.total_pages || 1,
          totalItems: response.count || 0,
          hasNext: response.page < response.total_pages,
          hasPrev: response.page > 1
        };

        update(state => ({
          ...state,
          contractsList: response.results || [],
          filters: mergedFilters,
          pagination,
          isLoading: false
        }));

        return response.results || [];
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to load contracts'
        }));

        addToast(
          t('contracts_load_error', get(language), { default: 'فشل تحميل العقود' }),
          'error'
        );

        return [];
      }
    },

    /**
     * Load a single contract by ID
     * @param {string} contractId - Contract ID
     */
    loadContract: async (contractId) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null,
        currentContract: null
      }));

      try {
        const contract = await contractsService.getContract(contractId);

        update(state => ({
          ...state,
          currentContract: contract,
          isLoading: false
        }));

        return contract;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to load contract'
        }));

        addToast(
          t('contract_load_error', get(language), { default: 'فشل تحميل العقد' }),
          'error'
        );

        return null;
      }
    },

    /**
     * Create a new contract
     * @param {object} contractData - Contract data
     */
    createContract: async (contractData) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        const newContract = await contractsService.createContract(contractData);

        update(state => ({
          ...state,
          currentContract: newContract,
          isLoading: false
        }));

        addToast(
          t('contract_created', get(language), { default: 'تم إنشاء العقد بنجاح' }),
          'success'
        );

        return newContract;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to create contract'
        }));

        addToast(
          t('contract_create_error', get(language), { default: 'فشل إنشاء العقد' }),
          'error'
        );

        return null;
      }
    },

    /**
     * Update a contract
     * @param {string} contractId - Contract ID
     * @param {object} contractData - Updated contract data
     */
    updateContract: async (contractId, contractData) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        const updatedContract = await contractsService.updateContract(contractId, contractData);

        update(state => ({
          ...state,
          currentContract: updatedContract,
          contractsList: state.contractsList.map(c =>
            c.id === updatedContract.id ? updatedContract : c
          ),
          isLoading: false
        }));

        addToast(
          t('contract_updated', get(language), { default: 'تم تحديث العقد بنجاح' }),
          'success'
        );

        return updatedContract;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to update contract'
        }));

        addToast(
          t('contract_update_error', get(language), { default: 'فشل تحديث العقد' }),
          'error'
        );

        return null;
      }
    },

    /**
     * Sign a contract (buyer or seller)
     * @param {string} contractId - Contract ID
     * @param {string} role - Role (buyer or seller)
     */
    signContract: async (contractId, role) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        // Prepare sign data based on role
        const signData = {};

        if (role === 'buyer') {
          signData.buyer_signed = true;
        } else if (role === 'seller') {
          signData.seller_signed = true;
        } else {
          throw new Error('Invalid role');
        }

        const updatedContract = await contractsService.updateContract(contractId, signData);

        update(state => ({
          ...state,
          currentContract: updatedContract,
          contractsList: state.contractsList.map(c =>
            c.id === updatedContract.id ? updatedContract : c
          ),
          isLoading: false
        }));

        addToast(
          t('contract_signed', get(language), { default: 'تم توقيع العقد بنجاح' }),
          'success'
        );

        return updatedContract;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to sign contract'
        }));

        addToast(
          t('contract_sign_error', get(language), { default: 'فشل توقيع العقد' }),
          'error'
        );

        return null;
      }
    },

    /**
     * Verify a contract (admin or legal)
     * @param {string} contractId - Contract ID
     */
    verifyContract: async (contractId) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        const verifyData = {
          is_verified: true
        };

        const updatedContract = await contractsService.updateContract(contractId, verifyData);

        update(state => ({
          ...state,
          currentContract: updatedContract,
          contractsList: state.contractsList.map(c =>
            c.id === updatedContract.id ? updatedContract : c
          ),
          isLoading: false
        }));

        addToast(
          t('contract_verified', get(language), { default: 'تم توثيق العقد بنجاح' }),
          'success'
        );

        return updatedContract;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to verify contract'
        }));

        addToast(
          t('contract_verify_error', get(language), { default: 'فشل توثيق العقد' }),
          'error'
        );

        return null;
      }
    },

    /**
     * Delete a contract
     * @param {string} contractId - Contract ID
     */
    deleteContract: async (contractId) => {
      update(state => ({
        ...state,
        isLoading: true,
        error: null
      }));

      try {
        await contractsService.deleteContract(contractId);

        update(state => ({
          ...state,
          contractsList: state.contractsList.filter(c => c.id !== contractId),
          currentContract: state.currentContract?.id === contractId ? null : state.currentContract,
          isLoading: false
        }));

        addToast(
          t('contract_deleted', get(language), { default: 'تم حذف العقد بنجاح' }),
          'success'
        );

        return true;
      } catch (error) {
        update(state => ({
          ...state,
          isLoading: false,
          error: error.message || 'Failed to delete contract'
        }));

        addToast(
          t('contract_delete_error', get(language), { default: 'فشل حذف العقد' }),
          'error'
        );

        return false;
      }
    },

    /**
     * Change page in pagination
     * @param {number} page - Page number
     */
    changePage: (page) => {
      update(state => {
        // Don't allow invalid page numbers
        if (page < 1 || page > state.pagination.totalPages) {
          return state;
        }

        // Update filters with new page number
        const newFilters = {
          ...state.filters,
          page
        };

        // Load contracts with new page
        contractsStore.loadContracts(newFilters);

        return {
          ...state,
          filters: newFilters
        };
      });
    },

    /**
     * Update filters and load contracts
     * @param {object} newFilters - New filter values
     */
    updateFilters: (newFilters) => {
      // Reset to page 1 when filters change
      const filtersWithPage = {
        ...newFilters,
        page: 1
      };

      contractsStore.loadContracts(filtersWithPage);
    },

    /**
     * Get user contract counts by status
     */
    getContractCounts: async () => {
      try {
        const counts = await contractsService.getContractCounts();
        return counts;
      } catch (error) {
        console.error('Failed to get contract counts:', error);
        return {
          total: 0,
          pending: 0,
          active: 0,
          fulfilled: 0,
          disputed: 0
        };
      }
    }
  };
}

// Create store instance
const contractsStore = createContractsStore();

// Create derived stores for convenience
export const contractsList = derived(
  contractsStore,
  $contracts => $contracts.contractsList
);

export const currentContract = derived(
  contractsStore,
  $contracts => $contracts.currentContract
);

export const isLoading = derived(
  contractsStore,
  $contracts => $contracts.isLoading
);

export const error = derived(
  contractsStore,
  $contracts => $contracts.error
);

export const filters = derived(
  contractsStore,
  $contracts => $contracts.filters
);

export const pagination = derived(
  contractsStore,
  $contracts => $contracts.pagination
);

// Export the store and its methods
export default contractsStore;
