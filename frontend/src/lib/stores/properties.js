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

// src/lib/stores/properties.js

// Alternative implementation for createProperty in properties.js
export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);

	try {
		// Create direct request
		const requestData = {
			title: propertyData.title || '',
			property_type: propertyData.property_type || 'residential',
			description: propertyData.description || '',
			address: propertyData.address || '',
			city: propertyData.city || '',
			state: propertyData.state || '',
			postal_code: propertyData.postal_code || '',
			country: propertyData.country || 'المملكة العربية السعودية',
			is_published: true
		};

		// Add optional fields if they exist
		if (propertyData.size_sqm) requestData.size_sqm = Number(propertyData.size_sqm);
		if (propertyData.bedrooms) requestData.bedrooms = Number(propertyData.bedrooms);
		if (propertyData.bathrooms) requestData.bathrooms = Number(propertyData.bathrooms);
		if (propertyData.floors) requestData.floors = Number(propertyData.floors);
		if (propertyData.market_value) requestData.market_value = Number(propertyData.market_value);
		if (propertyData.minimum_bid) requestData.minimum_bid = Number(propertyData.minimum_bid);

		// Make the POST request
		const accessToken = get(token);

		const response = await fetch(`${API_URL}/properties/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			},
			body: JSON.stringify(requestData)
		});

		// Get the response
		const text = await response.text();
		const result = text ? JSON.parse(text) : {};

		if (!response.ok) {
			throw new Error(result.error || result.detail || 'Failed to create property');
		}

		addToast('تم إنشاء العقار بنجاح', 'success');
		return { success: true, data: result };
	} catch (error) {
		console.error('Error creating property:', error);
		propertyError.set(error.message);
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
