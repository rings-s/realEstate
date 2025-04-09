import { API_URL } from '$lib/config/constants';

/**
 * Contracts service for managing contracts in the real estate auction platform
 */
class ContractsService {
	constructor() {
		this.baseUrl = `${API_URL}/contracts/`;
	}

	/**
	 * Get headers for API requests
	 * @returns {Object} Headers object with Authorization token
	 */
	getHeaders() {
		const headers = {
			'Content-Type': 'application/json'
		};

		const token = localStorage.getItem('auth_token');
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		return headers;
	}

	/**
	 * Get all contracts with optional filters
	 * @param {Object} filters - Filter parameters
	 * @returns {Promise<Object>} List of contracts with pagination
	 */
	async getContracts(filters = {}) {
		// Build query string from filters
		const queryParams = new URLSearchParams();

		Object.keys(filters).forEach((key) => {
			if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
				queryParams.append(key, filters[key]);
			}
		});

		const response = await fetch(`${this.baseUrl}?${queryParams.toString()}`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch contracts');
		}

		return await response.json();
	}

	/**
	 * Get a single contract by ID
	 * @param {string} contractId - Contract ID
	 * @returns {Promise<Object>} Contract details
	 */
	async getContract(contractId) {
		const response = await fetch(`${this.baseUrl}${contractId}/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch contract');
		}

		return await response.json();
	}

	/**
	 * Create a new contract
	 * @param {Object} contractData - Contract data
	 * @returns {Promise<Object>} Created contract
	 */
	async createContract(contractData) {
		const response = await fetch(this.baseUrl, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(contractData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to create contract');
		}

		return await response.json();
	}

	/**
	 * Update a contract
	 * @param {string} contractId - Contract ID
	 * @param {Object} contractData - Updated contract data
	 * @returns {Promise<Object>} Updated contract
	 */
	async updateContract(contractId, contractData) {
		const response = await fetch(`${this.baseUrl}${contractId}/edit/`, {
			method: 'PATCH',
			headers: this.getHeaders(),
			body: JSON.stringify(contractData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to update contract');
		}

		return await response.json();
	}

	/**
	 * Delete a contract
	 * @param {string} contractId - Contract ID
	 * @returns {Promise<void>}
	 */
	async deleteContract(contractId) {
		const response = await fetch(`${this.baseUrl}${contractId}/delete/`, {
			method: 'DELETE',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to delete contract');
		}

		return true;
	}

	/**
	 * Get documents for a contract
	 * @param {string} contractId - Contract ID
	 * @returns {Promise<Array>} Contract documents
	 */
	async getContractDocuments(contractId) {
		const response = await fetch(`${this.baseUrl}${contractId}/documents/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch contract documents');
		}

		return await response.json();
	}

	/**
	 * Upload a document to a contract
	 * @param {string} contractId - Contract ID
	 * @param {FormData} formData - Form data with file and document details
	 * @returns {Promise<Object>} Uploaded document
	 */
	async uploadContractDocument(contractId, formData) {
		const headers = this.getHeaders();
		delete headers['Content-Type']; // Let browser set the content type with boundary

		const response = await fetch(`${this.baseUrl}${contractId}/documents/`, {
			method: 'POST',
			headers: {
				Authorization: headers.Authorization
			},
			body: formData
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to upload document');
		}

		return await response.json();
	}

	/**
	 * Get contract counts by status
	 * @returns {Promise<Object>} Contract counts
	 */
	async getContractCounts() {
		const response = await fetch(`${this.baseUrl}counts/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch contract counts');
		}

		return await response.json();
	}

	/**
	 * Get contract timeline
	 * @param {string} contractId - Contract ID
	 * @returns {Promise<Array>} Contract timeline events
	 */
	async getContractTimeline(contractId) {
		const response = await fetch(`${this.baseUrl}${contractId}/timeline/`, {
			method: 'GET',
			headers: this.getHeaders()
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to fetch contract timeline');
		}

		return await response.json();
	}

	/**
	 * Add payment to contract
	 * @param {string} contractId - Contract ID
	 * @param {Object} paymentData - Payment details
	 * @returns {Promise<Object>} Updated contract with payment
	 */
	async addPayment(contractId, paymentData) {
		const response = await fetch(`${this.baseUrl}${contractId}/payments/`, {
			method: 'POST',
			headers: this.getHeaders(),
			body: JSON.stringify(paymentData)
		});

		if (!response.ok) {
			const error = await response.json();
			throw new Error(error.error || 'Failed to add payment');
		}

		return await response.json();
	}
}

// Create and export a singleton instance
const contractsService = new ContractsService();
export default contractsService;
