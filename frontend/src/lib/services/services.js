// src/lib/services/services.js
import { get } from 'svelte/store';
import { token } from './auth';
import api from './api';

// Constants
const API_URL = 'http://localhost:8000/api';

// Helper Functions
const cleanParams = (params) => {
	const cleaned = {};
	Object.entries(params).forEach(([key, value]) => {
		if (value !== null && value !== undefined && value !== '') {
			cleaned[key] = value;
		}
	});
	return cleaned;
};

const handleFormData = (data, jsonFields = []) => {
	const formData = new FormData();

	Object.entries(data).forEach(([key, value]) => {
		if (value === null || value === undefined) return;

		if (jsonFields.includes(key) || typeof value === 'object') {
			formData.append(key, JSON.stringify(value));
		} else if (key === 'media' && Array.isArray(value)) {
			value.forEach((file) => {
				if (file instanceof File) {
					formData.append('media', file);
				}
			});
		} else {
			formData.append(key, value);
		}
	});

	return formData;
};

const defaultJsonFields = [
	'location',
	'features',
	'amenities',
	'rooms',
	'specifications',
	'pricing_details',
	'highQualityStreets'
];

const handleApiResponse = (response, errorMessage) => {
	if (response.status === 'success') {
		return {
			success: true,
			data: response.data
		};
	}
	return {
		success: false,
		error: response.error || errorMessage
	};
};

const handleApiError = (error, customMessage) => {
	console.error(`Error in ${customMessage}:`, error);
	return {
		success: false,
		error: error.message || 'An unexpected error occurred'
	};
};

// Property Services
export const propertyService = {
	async fetch(params = {}) {
		try {
			const cleanedParams = cleanParams(params);
			const response = await api.get('/properties/', cleanedParams);

			return (
				handleApiResponse(response, 'Failed to fetch properties') || {
					results: [],
					count: 0
				}
			);
		} catch (error) {
			return handleApiError(error, 'fetchProperties');
		}
	},

	async fetchBySlug(slug) {
		try {
			if (!slug) return null;
			const response = await api.get(`/properties/${slug}/`);
			return response.status === 'success' ? response.data : null;
		} catch (error) {
			return handleApiError(error, 'fetchPropertyBySlug');
		}
	},

	async create(propertyData) {
		try {
			const formData = handleFormData(propertyData, defaultJsonFields);
			const response = await api.post('/properties/', formData);
			return handleApiResponse(response, 'Failed to create property');
		} catch (error) {
			return handleApiError(error, 'createProperty');
		}
	},

	async update(slug, propertyData) {
		try {
			if (!slug) {
				return { success: false, error: 'Property slug is required' };
			}
			const formData = handleFormData(propertyData, defaultJsonFields);
			const response = await api.patch(`/properties/${slug}/`, formData);
			return handleApiResponse(response, 'Failed to update property');
		} catch (error) {
			return handleApiError(error, 'updateProperty');
		}
	},

	async delete(slug) {
		try {
			if (!slug) {
				return { success: false, error: 'Property slug is required' };
			}
			const response = await api.delete(`/properties/${slug}/`);
			return handleApiResponse(response, 'Failed to delete property');
		} catch (error) {
			return handleApiError(error, 'deleteProperty');
		}
	}
};

// Formatting Services
export const formatService = {
	price(price) {
		if (!price) return 'السعر عند الطلب';
		return new Intl.NumberFormat('ar-SA', {
			style: 'decimal',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(price);
	},

	date(dateString) {
		if (!dateString) return '';
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('ar-SA', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		}).format(date);
	}
};

// Export all services
export default {
	property: propertyService,
	format: formatService
};
