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
			const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
			const headers = {};

			if (accessToken) {
				headers['Authorization'] = `Bearer ${accessToken}`;
			}

			// Only add Content-Type if not FormData
			if (!(options.body instanceof FormData)) {
				headers['Content-Type'] = 'application/json';
			}

			const requestOptions = {
				...options,
				headers: {
					...headers,
					...options.headers
				}
			};

			console.log('Making request to:', url, {
				method: requestOptions.method,
				headers: {
					...requestOptions.headers,
					Authorization: requestOptions.headers.Authorization ? '[HIDDEN]' : undefined
				},
				bodyType: options.body ? options.body.constructor.name : 'none'
			});

			const response = await fetch(url, requestOptions);
			let data;

			const contentType = response.headers.get('content-type');
			if (contentType?.includes('application/json')) {
				const text = await response.text();
				try {
					data = text ? JSON.parse(text) : null;
				} catch (e) {
					console.error('Failed to parse JSON response:', text);
					throw new Error('Invalid JSON response from server');
				}
			} else {
				data = await response.text();
			}

			if (!response.ok) {
				let errorMessage = 'API request failed';
				if (data) {
					if (data.error?.message) errorMessage = data.error.message;
					else if (data.error) errorMessage = data.error;
					else if (data.detail) errorMessage = data.detail;
				}
				throw new Error(errorMessage);
			}

			return data;
		} catch (error) {
			if (error.message.includes('401')) {
				logout();
			}
			throw error;
		}
	}

	async createProperty(propertyData, mediaFiles) {
		try {
			const formData = new FormData();

			// Handle regular fields
			Object.entries(propertyData).forEach(([key, value]) => {
				if (value !== null && value !== undefined) {
					// JSON stringify objects
					if (typeof value === 'object') {
						formData.append(key, JSON.stringify(value));
					} else {
						formData.append(key, value);
					}
				}
			});

			// Handle media files
			if (mediaFiles?.length) {
				mediaFiles.forEach((file, index) => {
					formData.append('media', file);
				});
			}

			// Log FormData contents for debugging
			console.log(
				'FormData contents:',
				[...formData.entries()].map(([key, value]) => {
					return `${key}: ${value instanceof File ? value.name : value}`;
				})
			);

			return this.fetch('/properties/', {
				method: 'POST',
				body: formData
			});
		} catch (error) {
			console.error('Property creation error:', error);
			throw error;
		}
	}

	// Standard REST methods
	async get(endpoint, params = {}) {
		const queryParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== null && value !== undefined) {
				queryParams.append(key, value);
			}
		});

		const url = `${endpoint}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
		return this.fetch(url, { method: 'GET' });
	}

	async post(endpoint, data) {
		return this.fetch(endpoint, {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async put(endpoint, data) {
		return this.fetch(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async patch(endpoint, data) {
		return this.fetch(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(data)
		});
	}

	async delete(endpoint) {
		return this.fetch(endpoint, { method: 'DELETE' });
	}
}

export const api = new ApiService();
export default api;
