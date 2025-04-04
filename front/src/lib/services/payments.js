import api, { handleApiError } from './api';

/**
 * Payment management services
 */
export default {
	/**
	 * Get list of payments with optional filters
	 * @param {Object} filters - Filter parameters
	 */
	getPayments: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/payments/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get payment details by payment number
	 * @param {string} paymentNumber - Payment number
	 */
	getPaymentByNumber: async (paymentNumber) => {
		try {
			return await api.get(`/payments/?payment_number=${paymentNumber}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get payment details by ID
	 * @param {string} id - Payment ID
	 */
	getPayment: async (id) => {
		try {
			return await api.get(`/payments/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new payment
	 * @param {Object} paymentData - Payment data
	 */
	createPayment: async (paymentData) => {
		try {
			return await api.post('/payments/', paymentData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update an existing payment
	 * @param {string} id - Payment ID
	 * @param {Object} paymentData - Updated payment data
	 */
	updatePayment: async (id, paymentData) => {
		try {
			return await api.patch(`/payments/${id}/`, paymentData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Confirm a payment (for agents and staff)
	 * @param {string} id - Payment ID
	 */
	confirmPayment: async (id) => {
		try {
			return await api.post(`/payments/${id}/confirm/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own payments
	 * @param {Object} filters - Filter parameters (payment_type, direction)
	 */
	getMyPayments: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/payments/my-payments/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload payment receipt or proof
	 * @param {string} id - Payment ID
	 * @param {File} file - Receipt file
	 */
	uploadPaymentReceipt: async (id, file) => {
		try {
			const formData = new FormData();
			formData.append('file', file);
			return await api.upload(`/payments/${id}/upload-receipt/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
