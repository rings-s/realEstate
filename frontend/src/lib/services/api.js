// src/lib/services/api.js
import { get } from 'svelte/store';
import { token, logout } from '$lib/stores/auth';

const API_URL = 'http://localhost:8000/api';

class ApiService {
	constructor(baseUrl = API_URL) {
		this.baseUrl = baseUrl;
	}

	async fetch(endpoint, options = {}) {
		try {
			const accessToken = get(token);

			const headers = {
				'Content-Type': 'application/json',
				...options.headers
			};

			if (accessToken) {
				headers['Authorization'] = `Bearer ${accessToken}`;
			}

			const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

			console.log('API Request:', {
				url,
				method: options.method || 'GET',
				headers: { ...headers, Authorization: headers.Authorization ? '****' : undefined }, // Mask token
				body: options.body ? JSON.parse(options.body) : undefined
			});

			const response = await fetch(url, {
				...options,
				headers
			});

			let responseData;
			let responseText = '';

			try {
				responseText = await response.text();
				responseData = responseText ? JSON.parse(responseText) : null;
			} catch (error) {
				console.error('Error parsing JSON response:', error, 'Response text:', responseText);
				responseData = { status: 'error', error: 'Invalid JSON response' };
			}

			console.log('API Response:', {
				status: response.status,
				data: responseData
			});

			if (!response.ok) {
				const errorMessage =
					responseData?.error?.message ||
					responseData?.error ||
					responseData?.detail ||
					'API request failed';
				throw new Error(errorMessage);
			}

			return responseData;
		} catch (error) {
			console.error(`API Error (${endpoint}):`, error);
			throw error;
		}
	}

	async get(endpoint, params = {}) {
		const queryParams = new URLSearchParams();
		for (const [key, value] of Object.entries(params)) {
			if (value !== undefined && value !== null) {
				queryParams.append(key, value);
			}
		}

		const queryString = queryParams.toString();
		const url = queryString ? `${endpoint}?${queryString}` : endpoint;

		return this.fetch(url, { method: 'GET' });
	}

	async post(endpoint, data = {}) {
		return this.fetch(endpoint, {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async put(endpoint, data = {}) {
		return this.fetch(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async patch(endpoint, data = {}) {
		return this.fetch(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(data)
		});
	}

	async delete(endpoint) {
		return this.fetch(endpoint, { method: 'DELETE' });
	}

	async uploadFile(endpoint, formData) {
		const accessToken = get(token);

		const headers = {};
		if (accessToken) {
			headers['Authorization'] = `Bearer ${accessToken}`;
		}

		try {
			const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;

			console.log('Uploading to:', url);
			console.log('Headers:', headers);
			// Log form data keys for debugging
			console.log('FormData contains keys:', [...formData.keys()]);

			const response = await fetch(url, {
				method: 'POST',
				headers,
				body: formData
			});

			let responseData;
			try {
				responseData = await response.json();
			} catch (error) {
				console.error('Error parsing JSON response:', error);
				responseData = null;
			}

			console.log('API Response:', {
				status: response.status,
				data: responseData
			});

			if (!response.ok) {
				const errorMessage =
					responseData?.error?.message || responseData?.error || 'API request failed';
				throw new Error(errorMessage);
			}

			return responseData;
		} catch (error) {
			console.error(`API Error (${endpoint}):`, error);
			throw error;
		}
	}
}

export const api = new ApiService();
export default api;
