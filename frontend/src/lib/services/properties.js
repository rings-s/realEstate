import { writable } from 'svelte/store';

// Store for properties
export const properties = writable([]);
export const currentProperty = writable(null);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

const API_URL = 'http://localhost:8000/api';

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
		const url = queryString ? `${API_URL}/properties/?${queryString}` : `${API_URL}/properties/`;

		// Make API request
		const response = await fetch(url, {
			headers: {
				'Content-Type': 'application/json',
				// Add authorization header if authenticated
				...getAuthHeader()
			}
		});

		if (!response.ok) {
			throw new Error('فشل في جلب بيانات العقارات');
		}

		const data = await response.json();
		properties.set(data.data?.results || []);
		return {
			results: data.data?.results || [],
			count: data.data?.count || 0
		};
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
 * @returns {Promise<Object>} - Property data
 */
export async function fetchPropertyBySlug(slug) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await fetch(`${API_URL}/properties/${slug}/`, {
			headers: {
				'Content-Type': 'application/json',
				...getAuthHeader()
			}
		});

		if (!response.ok) {
			throw new Error('فشل في جلب تفاصيل العقار');
		}

		const data = await response.json();
		currentProperty.set(data.data);
		return data.data;
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
 * Create a new property
 * @param {Object} propertyData - Property data
 * @returns {Promise<Object>} - Created property data
 */
export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await fetch(`${API_URL}/properties/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				...getAuthHeader()
			},
			body: JSON.stringify(propertyData)
		});

		if (!response.ok) {
			const errorData = await response.json();
			throw new Error(errorData.error?.message || 'فشل في إنشاء العقار');
		}

		const data = await response.json();
		return { success: true, data: data.data };
	} catch (error) {
		console.error('Error creating property:', error);
		propertyError.set(error.message);
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

// Helper function to get auth header if user is logged in
function getAuthHeader() {
	if (typeof localStorage !== 'undefined') {
		const token = localStorage.getItem('token');
		if (token) {
			return { Authorization: `Bearer ${token}` };
		}
	}
	return {};
}
