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

			const response = await fetch(url, {
				...options,
				headers
			});

			// Check for authentication errors
			if (response.status === 401) {
				// Token expired or invalid
				logout();
				throw new Error('انتهت صلاحية الجلسة. يرجى إعادة تسجيل الدخول.');
			}

			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error?.message || data.error || 'حدث خطأ أثناء جلب البيانات');
			}

			return data;
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

		return this.fetch(endpoint, {
			method: 'POST',
			headers,
			body: formData
		});
	}
}

export const api = new ApiService();
export default api;
