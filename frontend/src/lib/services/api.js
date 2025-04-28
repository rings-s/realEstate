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

  // Helper method for handling query parameters
  buildQueryString(params = {}) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(item => queryParams.append(`${key}[]`, item));
        } else {
          queryParams.append(key, value);
        }
      }
    });
    return queryParams.toString();
  }

  async fetch(endpoint, options = {}) {
    try {
      const accessToken = getStoredToken();
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
      const headers = {};

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      // Don't set Content-Type for FormData - browser will set this with correct boundary
      const isFormData = options.body instanceof FormData;
      if (!isFormData) {
        headers['Content-Type'] = 'application/json';
        if (options.body && typeof options.body === 'object') {
          options.body = JSON.stringify(options.body);
        }
      } else {
        console.log(`Sending FormData to ${url}`);
      }

      const requestOptions = {
        ...options,
        headers: {
          ...headers,
          ...options.headers
        }
      };

      console.log(`Request to ${url}, method: ${options.method}`);
      const response = await fetch(url, requestOptions);
      const contentType = response.headers.get('content-type');
      
      let data;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
        try {
          data = JSON.parse(data);
        } catch (e) {
          // Keep as text if not valid JSON
        }
      }

      if (!response.ok) {
        console.error('API Error Response:', data);
        
        // Handle validation errors (usually 400 status)
        if (response.status === 400 && data) {
          if (data.errors) {
            // Django REST framework detailed validation errors
            const errorMessages = [];
            for (const [field, messages] of Object.entries(data.errors)) {
              errorMessages.push(`${field}: ${messages.join(', ')}`);
            }
            throw new Error(`Validation errors: ${errorMessages.join('; ')}`);
          } else if (data.error) {
            // Simple error message
            throw new Error(data.error);
          } else if (data.detail) {
            // DRF default detail field
            throw new Error(data.detail);
          } else if (typeof data === 'object') {
            // Try to extract any field-level errors
            const errorFields = Object.keys(data).filter(k => 
              Array.isArray(data[k]) || typeof data[k] === 'string');
            
            if (errorFields.length > 0) {
              const errorMessages = errorFields.map(field => 
                `${field}: ${Array.isArray(data[field]) ? data[field].join(', ') : data[field]}`);
              throw new Error(`Validation errors: ${errorMessages.join('; ')}`);
            }
          }
        }
        
        // Default error handling
        const error = data.error || data.detail || `API request failed with status ${response.status}`;
        throw new Error(error);
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