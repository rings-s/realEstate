// src/lib/stores/properties.js
import { writable, derived } from 'svelte/store';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';

// Initialize stores
export const properties = writable([]);
export const currentProperty = writable(null);
export const propertiesCount = writable(0);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

// Derived stores
export const hasProperties = derived(
	[properties, propertiesCount],
	([$properties, $propertiesCount]) => $properties.length > 0 || $propertiesCount > 0
);

export const isLoading = derived(loadingProperties, ($loading) => $loading);

// Helper functions
function isValidPropertyData(data) {
	return data && typeof data === 'object' && 'id' in data && 'title' in data;
}

// Main store functions
export async function fetchProperties(params = {}) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const cleanParams = {};
		Object.entries(params).forEach(([key, value]) => {
			if (value !== null && value !== undefined && value !== '') {
				cleanParams[key] = value;
			}
		});

		const response = await api.get('/properties/', cleanParams);

		if (response.status === 'success' && response.data) {
			const results = response.data.results || [];
			const count = response.data.count || 0;

			properties.set(results);
			propertiesCount.set(count);

			return { results, count };
		} else {
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

		if (response.status === 'success' && isValidPropertyData(response.data)) {
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

		// Process each field
		Object.entries(propertyData).forEach(([key, value]) => {
			if (value === null || value === undefined) return;

			if (jsonFields.includes(key)) {
				// JSON fields
				const jsonValue = JSON.stringify(value || (Array.isArray(value) ? [] : {}));
				formData.append(key, jsonValue);
			} else if (key === 'media' && Array.isArray(value)) {
				// Media files
				value.forEach((file) => {
					if (file instanceof File) {
						formData.append('media', file);
					}
				});
			} else {
				// Regular fields
				formData.append(key, value);
			}
		});

		const response = await api.post('/properties/', formData);

		if (response.status === 'success' && response.data) {
			// Update stores
			properties.update((props) => [...props, response.data]);
			addToast('تم إضافة العقار بنجاح', 'success');
			return { success: true, data: response.data };
		} else {
			throw new Error(response.error || 'Failed to create property');
		}
	} catch (error) {
		console.error('Property creation error:', error);
		propertyError.set(error.message);
		addToast(error.message, 'error');
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
			// Update stores
			properties.update((props) => props.map((p) => (p.slug === slug ? response.data : p)));
			currentProperty.set(response.data);
			addToast('تم تحديث العقار بنجاح', 'success');
			return { success: true, data: response.data };
		} else {
			throw new Error(response.error || 'Failed to update property');
		}
	} catch (error) {
		console.error('Property update error:', error);
		propertyError.set(error.message);
		addToast(error.message, 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

export async function deleteProperty(slug) {
	if (!slug) {
		return { success: false, error: 'Invalid property ID' };
	}

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
		console.error('Property deletion error:', error);
		propertyError.set(error.message);
		addToast(error.message, 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

export async function togglePropertyFavorite(propertyId) {
	try {
		const response = await api.post(`/properties/${propertyId}/toggle-favorite/`);

		if (response.status === 'success') {
			properties.update((props) =>
				props.map((p) => (p.id === propertyId ? { ...p, is_favorite: !p.is_favorite } : p))
			);
			currentProperty.update((prop) => {
				if (prop?.id === propertyId) {
					return { ...prop, is_favorite: !prop.is_favorite };
				}
				return prop; // Return unchanged prop otherwise
			});
			return { success: true, isFavorite: response.data?.is_favorite };
		} else {
			throw new Error(response.error || 'Failed to update favorite status');
		}
	} catch (error) {
		console.error('Error toggling favorite:', error);
		return { success: false, error: error.message };
	}
}

// Cleanup function
export function cleanup() {
	properties.set([]);
	currentProperty.set(null);
	propertiesCount.set(0);
	loadingProperties.set(false);
	propertyError.set(null);
}

// Export default object with all functions
export default {
	fetchProperties,
	fetchPropertyBySlug,
	createProperty,
	updateProperty,
	deleteProperty,
	togglePropertyFavorite,
	cleanup,
	properties,
	currentProperty,
	propertiesCount,
	loadingProperties,
	propertyError,
	hasProperties,
	isLoading
};
