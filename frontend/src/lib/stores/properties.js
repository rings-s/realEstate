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

// In your properties store or page
async function loadProperties() {
	try {
		const queryParams = {
			page: currentPage,
			page_size: pageSize
			// other filters...
		};

		console.group('Property Fetch');
		console.log('Query Params:', queryParams);

		const result = await api.get('/properties/', queryParams);

		console.log('API Result:', result);
		console.groupEnd();

		if (result.status === 'success') {
			properties.set(result.results || []);
			propertiesCount.set(result.count || 0);
		} else {
			throw new Error(result.message || 'Unknown error');
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
		console.log('Fetching properties with params:', params);

		const response = await api.get('/properties/', params);

		console.log('API Response:', response);

		if (response.data && response.data.results) {
			properties.set(response.data.results);
			propertiesCount.set(response.data.count || 0);
			return {
				results: response.data.results,
				count: response.data.count || 0
			};
		} else {
			console.warn('Unexpected response structure:', response);
			properties.set([]);
			propertiesCount.set(0);
			return { results: [], count: 0 };
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

		if (response.data) {
			currentProperty.set(response.data);
			return response.data;
		}

		throw new Error('Failed to fetch property details');
	} catch (error) {
		console.error('Error fetching property:', error);
		propertyError.set(error.message);
		currentProperty.set(null);
		addToast(error.message || 'Failed to load property details', 'error');
		return null;
	} finally {
		loadingProperties.set(false);
	}
}

export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		// Make a deep copy to avoid modifying the original
		const dataToSend = JSON.parse(JSON.stringify(propertyData));

		// Format data if needed
		if (dataToSend.rooms && Array.isArray(dataToSend.rooms)) {
			// Ensure rooms are properly formatted
			dataToSend.rooms = dataToSend.rooms.map((room) => ({
				name: room.name,
				type: room.type,
				floor: room.floor,
				size: room.size ? parseFloat(room.size) : null,
				features: room.features || []
			}));
		}

		const response = await api.post('/properties/', dataToSend);

		if (response.data) {
			addToast('Property created successfully', 'success');
			return { success: true, data: response.data };
		}

		throw new Error('Failed to create property');
	} catch (error) {
		console.error('Error creating property:', error);
		propertyError.set(error.message);
		addToast(error.message || 'Failed to create property', 'error');
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
		// Make a deep copy to avoid modifying the original
		const dataToSend = JSON.parse(JSON.stringify(propertyData));

		// Format data if needed
		if (dataToSend.rooms && Array.isArray(dataToSend.rooms)) {
			// Ensure rooms are properly formatted
			dataToSend.rooms = dataToSend.rooms.map((room) => ({
				name: room.name,
				type: room.type,
				floor: room.floor,
				size: room.size ? parseFloat(room.size) : null,
				features: room.features || []
			}));
		}

		const response = await api.patch(`/properties/${slug}/`, dataToSend);

		if (response.data) {
			// Update current property if it matches
			currentProperty.update((prop) => {
				if (prop && prop.slug === slug) {
					return response.data;
				}
				return prop;
			});

			addToast('Property updated successfully', 'success');
			return { success: true, data: response.data };
		}

		throw new Error('Failed to update property');
	} catch (error) {
		console.error('Error updating property:', error);
		propertyError.set(error.message);
		addToast(error.message || 'Failed to update property', 'error');
		return { success: false, error: error.message };
	} finally {
		loadingProperties.set(false);
	}
}
