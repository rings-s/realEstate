// src/lib/services/properties.js
import api from '$lib/services/api';
import {
	properties,
	currentProperty,
	loadingProperties,
	propertyError
} from '$lib/stores/properties';
import { addToast } from '$lib/stores/ui';

/**
 * Fetch properties with filters
 */
export async function fetchProperties(params = {}) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const queryParams = new URLSearchParams();
		for (const [key, value] of Object.entries(params)) {
			if (value !== undefined && value !== null && value !== '') {
				queryParams.append(key, value);
			}
		}

		const endpoint = `/properties/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
		const response = await api.get(endpoint);

		if (response.status === 'success' && response.data) {
			properties.set(response.data.results || []);
			return {
				results: response.data.results || [],
				count: response.data.count || 0
			};
		} else {
			throw new Error(response.error || 'Failed to fetch properties');
		}
	} catch (error) {
		console.error('Error fetching properties:', error);
		propertyError.set(error.message);
		properties.set([]);
		return { results: [], count: 0 };
	} finally {
		loadingProperties.set(false);
	}
}

/**
 * Fetch single property
 */
export async function fetchPropertyBySlug(slug) {
	if (!slug) return null;

	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.get(`/properties/${slug}/`);

		if (response.status === 'success' && response.data) {
			currentProperty.set(response.data);
			return response.data;
		} else {
			throw new Error('Failed to fetch property details');
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
 * Create new property
 */

// src/lib/services/properties.js

// src/lib/services/properties.js 
export async function createProperty(formData) {
	try {
	  // Log what we're sending to the API
	  console.log("Sending FormData to API:");
	  for (let [key, value] of formData.entries()) {
		console.log(key, ':', value);
	  }
  
	  const response = await api.post('/properties/', formData);
  
	  if (response.status === 'success' && response.data) {
		return { success: true, data: response.data };
	  }
  
	  throw new Error(response.error || 'Failed to create property');
	} catch (error) {
	  console.error('Property creation error:', error);
	  return { success: false, error: error.message };
	}
}

/**
 * Update property
 */
export async function updateProperty(slug, propertyData) {
	if (!slug) return { success: false, error: 'Invalid property ID' };

	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const formData = new FormData();
		const jsonFields = [
			'location',
			'features',
			'amenities',
			'rooms',
			'specifications',
			'pricing_details',
			'highQualityStreets'
		];

		Object.entries(propertyData).forEach(([key, value]) => {
			if (value === null || value === undefined) return;

			if (jsonFields.includes(key)) {
				formData.append(key, JSON.stringify(value));
			} else if (key === 'media' && Array.isArray(value)) {
				value.forEach((file) => {
					if (file instanceof File) {
						formData.append('media', file);
					}
				});
			} else {
				formData.append(key, value);
			}
		});

		const response = await api.patch(`/properties/${slug}/`, formData);

		if (response.status === 'success' && response.data) {
			properties.update((props) => props.map((p) => (p.slug === slug ? response.data : p)));
			currentProperty.set(response.data);
			addToast('تم تحديث العقار بنجاح', 'success');
			return { success: true, data: response.data };
		} else {
			throw new Error(response.error || 'Failed to update property');
		}
	} catch (error) {
		console.error('Error updating property:', error);
		propertyError.set(error.message);
		addToast(error.message, 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

/**
 * Delete property
 */
export async function deleteProperty(slug) {
	if (!slug) return { success: false, error: 'Invalid property ID' };

	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.delete(`/properties/${slug}/`);

		if (response.status === 'success') {
			properties.update((props) => props.filter((p) => p.slug !== slug));
			currentProperty.update((prop) => (prop?.slug === slug ? null : prop));
			addToast('تم حذف العقار بنجاح', 'success');
			return { success: true };
		} else {
			throw new Error(response.error || 'Failed to delete property');
		}
	} catch (error) {
		console.error('Error deleting property:', error);
		propertyError.set(error.message);
		addToast(error.message, 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

export default {
	fetchProperties,
	fetchPropertyBySlug,
	createProperty,
	updateProperty,
	deleteProperty
};
