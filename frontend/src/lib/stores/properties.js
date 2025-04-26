// src/lib/stores/properties.js
import { writable, derived } from 'svelte/store';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';
import { get } from 'svelte/store';
import { token } from '$lib/stores/auth';

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
		console.log('Loading properties with params:', params);
		const response = await api.get('/properties/', params);
		console.log('API response:', response);

		// Check if response has the expected structure
		if (response?.status === 'success' && response?.data) {
			const results = response.data.results || [];
			const count = response.data.count || 0;

			properties.set(results);
			propertiesCount.set(count);

			return { results, count };
		} else {
			console.error('Unexpected API response format:', response);
			throw new Error('Invalid response format from server');
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

		// Check if response has the expected structure
		if (response && response.data) {
			currentProperty.set(response.data);
			return response.data;
		} else {
			throw new Error('Invalid response format from server');
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
	try {
		// Separate files from data
		const { mediaFiles, ...propertyFields } = propertyData;

		// Ensure numeric fields are numbers
		const numericFields = [
			'size_sqm',
			'bedrooms',
			'bathrooms',
			'floors',
			'parking_spaces',
			'market_value',
			'minimum_bid'
		];

		numericFields.forEach((field) => {
			if (propertyFields[field]) {
				propertyFields[field] = Number(propertyFields[field]);
			}
		});

		const response = await api.createProperty('/properties/', propertyFields, mediaFiles);

		if (response.status === 'success') {
			return { success: true, data: response.data };
		}

		throw new Error(response.error || 'Failed to create property');
	} catch (error) {
		console.error('Error creating property:', error);
		return { success: false, error: error.message };
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
