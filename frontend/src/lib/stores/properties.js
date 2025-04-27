// src/lib/stores/properties.js
import { writable, derived } from 'svelte/store';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';


export const properties = writable([]);
export const currentProperty = writable(null);
export const propertiesCount = writable(0);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

export const hasProperties = derived(
	[properties, propertiesCount],
	([$properties, $propertiesCount]) => $properties.length > 0 || $propertiesCount > 0
);

async function loadProperties() {
	try {
		const queryParams = {
			page: currentPage,
			page_size: pageSize
		};

		console.group('Property Fetch');
		console.log('Query Params:', queryParams);

		const result = await api.get('/properties/', queryParams);

		console.log('API Result:', result);
		console.groupEnd();

		if (result.status === 'success') {
			properties.set(result.data.results || []);
			propertiesCount.set(result.data.count || 0);
		} else {
			throw new Error(result.error || 'Unknown error');
		}
	} catch (error) {
		console.error('Properties Fetch Error:', error);
		addToast(error.message || 'Failed to load properties', 'error');
	}
}

export async function fetchProperties(params = {}) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		console.log('Loading properties with params:', params);
		const response = await api.get('/properties/', params);
		console.log('API response:', response);

		if (response.status === 'success') {
			const results = response.data.results || [];
			const count = response.data.count || 0;

			properties.set(results);
			propertiesCount.set(count);

			return { results, count };
		} else {
			console.error('API Error:', response.error);
			throw new Error(response.error || 'Failed to fetch properties');
		}
	} catch (error) {
		console.error('Error fetching properties:', error);
		propertyError.set(error.message);
		properties.set([]);
		propertiesCount.set(0);
		return { results: [], count: 0 };
	} finally {
		loadingProperties.set(false);
	}
}

export async function fetchPropertyBySlug(slug) {
	if (!slug) {
		propertyError.set('Invalid property ID');
		return null;
	}

	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.get(`/properties/${slug}/`);

		if (response.status === 'success') {
			currentProperty.set(response.data);
			return response.data;
		} else {
			throw new Error(response.error || 'Failed to fetch property');
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

export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);
  
	try {
	  // Create FormData for handling files
	  const formData = new FormData();
  
	  // Add all property data
	  Object.keys(propertyData).forEach(key => {
		if (key === 'media') {
		  // Handle media files
		  propertyData.media.forEach(file => {
			formData.append('media', file);
		  });
		} else if (typeof propertyData[key] === 'object' && propertyData[key] !== null) {
		  // Handle JSON fields
		  formData.append(key, JSON.stringify(propertyData[key]));
		} else if (propertyData[key] !== null && propertyData[key] !== undefined) {
		  formData.append(key, propertyData[key]);
		}
	  });
  
	  const response = await api.post('/properties/', formData);
  
	  if (response.status === 'success') {
		addToast('تم إضافة العقار بنجاح', 'success');
		return { success: true, data: response.data };
	  } else {
		throw new Error(response.error || 'Failed to create property');
	  }
	} catch (error) {
	  console.error('Error creating property:', error);
	  propertyError.set(error.message);
	  addToast(error.message || 'فشل في إضافة العقار', 'error');
	  return { success: false, error: error.message };
	} finally {
	  loadingProperties.set(false);
	}
  }
  
export async function updateProperty(slug, propertyData) {
	if (!slug) {
		return { success: false, error: 'Invalid property ID' };
	}

	loadingProperties.set(true);
	propertyError.set(null);

	try {
		// Create a FormData object
		const formData = new FormData();

		// Add all property data to FormData
		for (const [key, value] of Object.entries(propertyData)) {
			if (value !== null && value !== undefined) {
				if (Array.isArray(value)) {
					value.forEach((item) => {
						formData.append(`${key}[]`, item);
					});
				} else if (value instanceof File) {
					formData.append(key, value);
				} else if (typeof value === 'object') {
					formData.append(key, JSON.stringify(value));
				} else {
					formData.append(key, value);
				}
			}
		}

		const response = await api.patch(`/properties/${slug}/`, formData);

		if (response.status === 'success') {
			// Update current property if it matches
			currentProperty.update((prop) => {
				if (prop && prop.slug === slug) {
					return response.data;
				}
				return prop;
			});

			addToast('تم تحديث العقار بنجاح', 'success');
			return { success: true, data: response.data };
		} else {
			throw new Error(response.error || 'Failed to update property');
		}
	} catch (error) {
		console.error('Error updating property:', error);
		propertyError.set(error.message);
		addToast(error.message || 'فشل في تحديث العقار', 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}
