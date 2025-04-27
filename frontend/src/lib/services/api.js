// src/lib/services/api.js
import { get } from 'svelte/store';
import { token, logout } from '$lib/stores/auth';

const API_URL = 'http://localhost:8000/api';

const getStoredToken = () => {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

class ApiService {
  constructor(baseUrl = API_URL) {
    this.baseUrl = baseUrl;
  }


  async fetch(endpoint, options = {}) {
	try {
	  const accessToken = getStoredToken();
	  const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
	  const headers = {};
  
	  if (accessToken) {
		headers['Authorization'] = `Bearer ${accessToken}`;
	  }
  
	  // Only add Content-Type if not FormData
	  if (!(options.body instanceof FormData)) {
		headers['Content-Type'] = 'application/json';
		if (options.body && typeof options.body === 'object') {
		  options.body = JSON.stringify(options.body);
		}
	  }
  
	  const requestOptions = {
		...options,
		headers: {
		  ...headers,
		  ...options.headers
		}
	  };
  
	  const response = await fetch(url, requestOptions);
	  const data = await response.json();
  
	  // Log response for debugging
	  console.log('API Response:', {
		url,
		status: response.status,
		data
	  });
  
	  if (!response.ok) {
		throw new Error(data.error?.message || data.error || 'API request failed');
	  }
  
	  return {
		status: 'success',
		data: data.data || data
	  };
	} catch (error) {
	  console.error('API Request Error:', error);
	  return {
		status: 'error',
		error: error.message
	  };
	}
  }

  // Helper method for handling query parameters
  buildQueryString(params = {}) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(item => queryParams.append(`${key}[]`, item));
        } else {
          queryParams.append(key, value);
        }
      }
    });
    return queryParams.toString();
  }

  // Standard REST methods
  async get(endpoint, params = {}) {
    const queryString = this.buildQueryString(params);
    const url = `${endpoint}${queryString ? '?' + queryString : ''}`;
    return this.fetch(url, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'POST',
      body: data
    });
  }

  async put(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'PUT',
      body: data
    });
  }

  async patch(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'PATCH',
      body: data
    });
  }

  async delete(endpoint) {
    return this.fetch(endpoint, { method: 'DELETE' });
  }

  // File upload helper
  async uploadFile(endpoint, file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);

    return this.fetch(endpoint, {
      method: 'POST',
      body: formData,
      ...options
    });
  }

  // Batch upload helper
  async uploadFiles(endpoint, files, options = {}) {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file${index}`, file);
    });

    return this.fetch(endpoint, {
      method: 'POST',
      body: formData,
      ...options
    });
  }

  // Download helper
  async downloadFile(endpoint, params = {}) {
    const queryString = this.buildQueryString(params);
    const url = `${endpoint}${queryString ? '?' + queryString : ''}`;
    
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${getStoredToken()}`
      }
    });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    return response.blob();
  }
}

export const api = new ApiService();
export default api;