import api, { handleApiError } from './api';

/**
 * Contract management services
 */
export default {
	/**
	 * Get list of contracts with optional filters
	 * @param {Object} filters - Filter parameters
	 */
	getContracts: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/contracts/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get contract details by contract number
	 * @param {string} contractNumber - Contract number
	 */
	getContractByNumber: async (contractNumber) => {
		try {
			return await api.get(`/contracts/?contract_number=${contractNumber}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get contract details by ID
	 * @param {string} id - Contract ID
	 */
	getContract: async (id) => {
		try {
			return await api.get(`/contracts/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new contract
	 * @param {Object} contractData - Contract data
	 */
	createContract: async (contractData) => {
		try {
			return await api.post('/contracts/', contractData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update an existing contract
	 * @param {string} id - Contract ID
	 * @param {Object} contractData - Updated contract data
	 */
	updateContract: async (id, contractData) => {
		try {
			return await api.patch(`/contracts/${id}/`, contractData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Sign contract as buyer
	 * @param {string} id - Contract ID
	 */
	signAsBuyer: async (id) => {
		try {
			return await api.post(`/contracts/${id}/sign-buyer/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Sign contract as seller
	 * @param {string} id - Contract ID
	 */
	signAsSeller: async (id) => {
		try {
			return await api.post(`/contracts/${id}/sign-seller/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Sign contract as agent
	 * @param {string} id - Contract ID
	 */
	signAsAgent: async (id) => {
		try {
			return await api.post(`/contracts/${id}/sign-agent/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own contracts
	 * @param {string} status - Optional filter by status
	 */
	getMyContracts: async (status = null) => {
		try {
			const queryParams = status ? `?status=${status}` : '';
			return await api.get(`/contracts/my-contracts/${queryParams}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload contract files
	 * @param {string} id - Contract ID
	 * @param {FileList} files - Contract files
	 */
	uploadContractFiles: async (id, files) => {
		try {
			const formData = new FormData();
			for (let i = 0; i < files.length; i++) {
				formData.append('files', files[i]);
			}
			return await api.upload(`/contracts/${id}/upload-files/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
