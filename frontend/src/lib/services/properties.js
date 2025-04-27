import { writable } from 'svelte/store';
import api from '$lib/services/api';

// Store for properties
export const properties = writable([]);
export const currentProperty = writable(null);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

/**
 * Fetch properties with optional filter parameters
 * @param {Object} params - Query parameters for filtering
 * @returns {Promise<Object>} - Properties data with results and count
 */
export async function fetchProperties(params = {}) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		// Build query string from params
		const queryParams = new URLSearchParams();
		for (const [key, value] of Object.entries(params)) {
			if (value !== undefined && value !== null && value !== '') {
				queryParams.append(key, value);
			}
		}

		const queryString = queryParams.toString();
		const endpoint = queryString ? `/properties/?${queryString}` : '/properties/';

		// Make API request using ApiService
		const data = await api.fetch(endpoint, { method: 'GET' });

		// Assuming the API returns { success: true, data: { results: [...], count: ... } }
		if (data && data.success && data.data) {
			properties.set(data.data.results || []);
			return {
				results: data.data.results || [],
				count: data.data.count || 0
			};
		} else {
			// Handle cases where the structure might be different or success is false
			throw new Error(data?.error?.message || 'Invalid response structure from server');
		}

	} catch (error) {
		console.error('Error fetching properties:', error);
		propertyError.set(error.message);
		properties.set([]);
		return {
			results: [],
			count: 0
		};
	} finally {
		loadingProperties.set(false);
	}
}

/**
 * Fetch a single property by its slug
 * @param {string} slug - Property slug
 * @returns {Promise<Object | null>} - Property data or null on error
 */
export async function fetchPropertyBySlug(slug) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const endpoint = `/properties/${slug}/`;
		const data = await api.fetch(endpoint, { method: 'GET' });

		if (data && data.success && data.data) {
			currentProperty.set(data.data);
			return data.data;
		} else {
			throw new Error(data?.error?.message || 'Failed to fetch property details');
		}
	} catch (error) {
		console.error('Error fetching property:', error);
		propertyError.set(error.message);
		currentProperty.set(null);
		return null;
	} finally {
		loadingProperties.set(false);
	}
}

/**
 * Create a new property using FormData
 * @param {FormData} formData - The FormData object containing property data and files
 * @returns {Promise<Object>} - Result object with success status and created property data or error
 */
export async function createProperty(formData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		console.log('Sending FormData to ApiService...');

		const data = await api.fetch('/properties/', {
			method: 'POST',
			body: formData
		});

		console.log('Response from ApiService:', data);

		if (data && data.success) {
			return { success: true, data: data.data };
		} else {
			throw new Error(data?.error || 'Failed to create property');
		}

	} catch (error) {
		console.error('Error in createProperty service:', error);
		propertyError.set(error.message);
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}
