import api, { handleApiError } from './api';

/**
 * Document management services
 */
export default {
	/**
	 * Get list of documents with optional filters
	 * @param {Object} filters - Filter parameters
	 */
	getDocuments: async (filters = {}) => {
		try {
			const queryParams = new URLSearchParams(filters).toString();
			return await api.get(`/documents/${queryParams ? '?' + queryParams : ''}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get document details by document number
	 * @param {string} documentNumber - Document number
	 */
	getDocumentByNumber: async (documentNumber) => {
		try {
			return await api.get(`/documents/?document_number=${documentNumber}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get document details by ID
	 * @param {string} id - Document ID
	 */
	getDocument: async (id) => {
		try {
			return await api.get(`/documents/${id}/`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Create a new document
	 * @param {Object} documentData - Document metadata
	 * @param {FileList} files - Document files
	 */
	createDocument: async (documentData, files) => {
		try {
			// First create document metadata
			const document = await api.post('/documents/', documentData);

			// Then upload files if provided
			if (files && files.length > 0) {
				const formData = new FormData();
				for (let i = 0; i < files.length; i++) {
					formData.append('files', files[i]);
				}
				await api.upload(`/documents/${document.id}/upload-files/`, formData);
			}

			return document;
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Update an existing document
	 * @param {string} id - Document ID
	 * @param {Object} documentData - Updated document data
	 */
	updateDocument: async (id, documentData) => {
		try {
			return await api.patch(`/documents/${id}/`, documentData);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Verify a document (for legal and inspector roles)
	 * @param {string} id - Document ID
	 * @param {string} notes - Verification notes (optional)
	 */
	verifyDocument: async (id, notes = '') => {
		try {
			return await api.post(`/documents/${id}/verify/`, { notes });
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Get list of user's own documents
	 * @param {string} documentType - Optional filter by document type
	 */
	getMyDocuments: async (documentType = null) => {
		try {
			const queryParams = documentType ? `?document_type=${documentType}` : '';
			return await api.get(`/documents/my-documents/${queryParams}`);
		} catch (error) {
			throw handleApiError(error);
		}
	},

	/**
	 * Upload document files
	 * @param {string} id - Document ID
	 * @param {FileList} files - Document files
	 */
	uploadDocumentFiles: async (id, files) => {
		try {
			const formData = new FormData();
			for (let i = 0; i < files.length; i++) {
				formData.append('files', files[i]);
			}
			return await api.upload(`/documents/${id}/upload-files/`, formData);
		} catch (error) {
			throw handleApiError(error);
		}
	}
};
