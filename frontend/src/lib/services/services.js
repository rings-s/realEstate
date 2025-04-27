// src/lib/services/services.js
import { get } from 'svelte/store';
import { token } from './auth';
import api from './api';

const API_URL = 'http://localhost:8000/api';

export async function fetchProperties(params = {}) {
  try {
    // Clean params - remove empty values
    const cleanParams = {};
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        cleanParams[key] = value;
      }
    });
    
    const response = await api.get('/properties/', cleanParams);
    
    if (response.status === 'success') {
      return {
        results: response.data.results || [],
        count: response.data.count || 0
      };
    }
    
    return { results: [], count: 0 };
  } catch (error) {
    console.error('Error in fetchProperties service:', error);
    return { results: [], count: 0 };
  }
}

export async function fetchPropertyBySlug(slug) {
  try {
    if (!slug) return null;
    
    const response = await api.get(`/properties/${slug}/`);
    
    if (response.status === 'success') {
      return response.data;
    }
    
    return null;
  } catch (error) {
    console.error('Error in fetchPropertyBySlug service:', error);
    return null;
  }
}

export async function createProperty(propertyData) {
  try {
    // Create FormData for file uploads
    const formData = new FormData();
    
    // Handle property data
    Object.entries(propertyData).forEach(([key, value]) => {
      if (value === null || value === undefined) return;
      
      if (key === 'media' && Array.isArray(value)) {
        // Handle media files
        value.forEach(file => {
          if (file instanceof File) {
            formData.append('media', file);
          }
        });
      } else if (typeof value === 'object') {
        // Convert objects to JSON strings
        formData.append(key, JSON.stringify(value));
      } else {
        // Handle primitive values
        formData.append(key, value);
      }
    });
    
    const response = await api.post('/properties/', formData);
    
    if (response.status === 'success') {
      return { 
        success: true, 
        data: response.data 
      };
    }
    
    return { 
      success: false, 
      error: response.error || 'Failed to create property' 
    };
  } catch (error) {
    console.error('Error in createProperty service:', error);
    return { 
      success: false, 
      error: error.message || 'An unexpected error occurred' 
    };
  }
}

export async function updateProperty(slug, propertyData) {
  try {
    if (!slug) {
      return { success: false, error: 'Property slug is required' };
    }
    
    // Create FormData for file uploads
    const formData = new FormData();
    
    // Handle property data
    Object.entries(propertyData).forEach(([key, value]) => {
      if (value === null || value === undefined) return;
      
      if (key === 'media' && Array.isArray(value)) {
        // Handle media files
        value.forEach(file => {
          if (file instanceof File) {
            formData.append('media', file);
          }
        });
      } else if (typeof value === 'object') {
        // Convert objects to JSON strings
        formData.append(key, JSON.stringify(value));
      } else {
        // Handle primitive values
        formData.append(key, value);
      }
    });
    
    const response = await api.patch(`/properties/${slug}/`, formData);
    
    if (response.status === 'success') {
      return { 
        success: true, 
        data: response.data 
      };
    }
    
    return { 
      success: false, 
      error: response.error || 'Failed to update property' 
    };
  } catch (error) {
    console.error('Error in updateProperty service:', error);
    return { 
      success: false, 
      error: error.message || 'An unexpected error occurred' 
    };
  }
}

export async function deleteProperty(slug) {
  try {
    if (!slug) {
      return { success: false, error: 'Property slug is required' };
    }
    
    const response = await api.delete(`/properties/${slug}/`);
    
    if (response.status === 'success') {
      return { success: true };
    }
    
    return { 
      success: false, 
      error: response.error || 'Failed to delete property' 
    };
  } catch (error) {
    console.error('Error in deleteProperty service:', error);
    return { 
      success: false, 
      error: error.message || 'An unexpected error occurred' 
    };
  }
}

// Helper functions
export function formatPrice(price) {
  if (!price) return 'السعر عند الطلب';
  
  return new Intl.NumberFormat('ar-SA', {
    style: 'decimal',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
}

export function formatDate(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ar-SA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date);
}

export default {
  fetchProperties,
  fetchPropertyBySlug,
  createProperty,
  updateProperty,
  deleteProperty,
  formatPrice,
  formatDate
};