// src/lib/stores/properties.js
import { writable, derived } from 'svelte/store';
import api from '$lib/services/api';

export const properties = writable([]);
export const currentProperty = writable(null);
export const propertiesCount = writable(0);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

export const hasProperties = derived(
	[properties, propertiesCount],
	([$properties, $propertiesCount]) => $properties.length > 0 || $propertiesCount > 0
);

export async function fetchProperties(params = {}) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.get('/properties/', params);

		properties.set(response.data.results || []);
		propertiesCount.set(response.data.count || 0);

		return response.data;
	} catch (error) {
		propertyError.set(error.message);
		properties.set([]);
		propertiesCount.set(0);
		throw error;
	} finally {
		loadingProperties.set(false);
	}
}

export async function fetchPropertyBySlug(slug) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.get(`/properties/${slug}/`);

		currentProperty.set(response.data);
		return response.data;
	} catch (error) {
		propertyError.set(error.message);
		currentProperty.set(null);
		throw error;
	} finally {
		loadingProperties.set(false);
	}
}

export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.post('/properties/', propertyData);

		// Refresh properties list
		fetchProperties();

		return { success: true, data: response.data };
	} catch (error) {
		propertyError.set(error.message);
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

export async function updateProperty(slug, propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		const response = await api.patch(`/properties/${slug}/`, propertyData);

		// Update current property if it matches
		currentProperty.update((prop) => {
			if (prop && prop.slug === slug) {
				return response.data;
			}
			return prop;
		});

		return { success: true, data: response.data };
	} catch (error) {
		propertyError.set(error.message);
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}

export async function deleteProperty(slug) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		await api.delete(`/properties/${slug}/`);

		// Remove from store
		properties.update((props) => props.filter((p) => p.slug !== slug));

		// If current property is deleted, reset
		currentProperty.update((prop) => {
			if (prop && prop.slug === slug) {
				return null;
			}
			return prop;
		});

		return { success: true };
	} catch (error) {
		propertyError.set(error.message);
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}
