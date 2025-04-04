// front/src/lib/services/api.js

// Base API URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Base fetch API wrapper with authentication and error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} - API response
 */
async function apiFetch(endpoint, options = {}) {
	// Make sure endpoint doesn't start with a slash when concatenating with base URL
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
	const url = `${API_BASE_URL}/${cleanEndpoint}`;

	// Default headers
	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	// Add auth token if available
	const token = localStorage.getItem('access_token');
	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}

	// Merge options
	const fetchOptions = {
		...options,
		headers
	};

	try {
		console.log(
			`API Request: ${fetchOptions.method || 'GET'} ${url}`,
			fetchOptions.body ? JSON.parse(fetchOptions.body) : ''
		);

		const response = await fetch(url, fetchOptions);

		// Handle 401 Unauthorized (token expired)
		if (response.status === 401) {
			const refreshed = await refreshToken();
			if (refreshed) {
				// Retry request with new token
				headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
				return apiFetch(endpoint, options);
			} else {
				// Redirect to login if refresh failed
				window.location.href = '/login';
				throw new Error('Authentication failed');
			}
		}

		// Parse JSON response if possible
		let data;
		const contentType = response.headers.get('content-type');
		if (contentType && contentType.includes('application/json')) {
			data = await response.json();
		} else {
			data = await response.text();
		}

		// Log response for debugging
		console.log(`API Response: ${response.status}`, data);

		// Handle error responses
		if (!response.ok) {
			throw {
				status: response.status,
				data,
				message: data.error || 'حدث خطأ في الخادم'
			};
		}

		return data;
	} catch (error) {
		console.error('API request failed:', error);
		throw error;
	}
}

/**
 * Refresh the access token using refresh token
 * @returns {Promise<boolean>} Success status
 */
async function refreshToken() {
	const refreshToken = localStorage.getItem('refresh_token');
	if (!refreshToken) return false;

	try {
		const response = await fetch(`${API_BASE_URL}/accounts/token/refresh/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh: refreshToken })
		});

		if (!response.ok) return false;

		const data = await response.json();
		localStorage.setItem('access_token', data.access);
		return true;
	} catch (error) {
		console.error('Token refresh failed:', error);
		return false;
	}
}

/**
 * Handle API errors in a consistent way
 * @param {Object} error - Error object
 * @returns {string} User-friendly error message
 */
export function handleApiError(error) {
	if (error.data?.error_code) {
		// Handle specific error codes
		switch (error.data.error_code) {
			case 'validation_error':
				return Object.values(error.data.error).flat().join('\n');
			case 'invalid_credentials':
				return 'بيانات الدخول غير صحيحة';
			case 'email_not_verified':
				return 'البريد الإلكتروني غير مفعل، الرجاء التحقق من بريدك';
			default:
				return error.data.error || 'حدث خطأ غير متوقع';
		}
	}

	return error.message || 'حدث خطأ في الاتصال بالخادم';
}

// Create the API service object
const apiService = {
	get: (endpoint) => apiFetch(endpoint, { method: 'GET' }),
	post: (endpoint, data) =>
		apiFetch(endpoint, {
			method: 'POST',
			body: JSON.stringify(data)
		}),
	put: (endpoint, data) =>
		apiFetch(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data)
		}),
	patch: (endpoint, data) =>
		apiFetch(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(data)
		}),
	delete: (endpoint) => apiFetch(endpoint, { method: 'DELETE' }),
	upload: (endpoint, formData) =>
		apiFetch(endpoint, {
			method: 'POST',
			headers: {}, // Let browser set content-type with boundary
			body: formData
		})
};

// Use named and default exports to ensure compatibility
export { apiService };
export default apiService;
