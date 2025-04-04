/**
 * Geocoding utilities for the Real Estate Auction Platform
 *
 * Provides functions to convert addresses to coordinates and
 * handle location data compatible with both frontend and backend.
 */

/**
 * Convert a human-readable address into geographic coordinates
 *
 * @param {string} address - Full address string (e.g., "District, City, Saudi Arabia")
 * @param {object} options - Optional configuration
 * @param {boolean} options.fullResponse - Return full response instead of just coordinates
 * @param {string} options.apiKey - Optional API key for premium geocoding services
 * @returns {Promise<object>} - Object with latitude and longitude
 */
export const getLocationFromAddress = async (address, options = {}) => {
	try {
		// Check if address is empty
		if (!address || !address.trim()) {
			throw new Error('Empty address provided');
		}

		// Choose geocoding provider
		// We'll use Nominatim (OpenStreetMap) as it doesn't require API key by default
		// For production, consider using a premium service with API key
		const useNominatim = !options.apiKey;

		if (useNominatim) {
			return await getNominatimLocation(address, options);
		} else {
			// If API key is provided, use premium service (implementation depends on chosen provider)
			return await getPremiumLocation(address, options);
		}
	} catch (error) {
		console.error(`Geocoding error for address "${address}":`, error);
		throw new Error(`Failed to get coordinates: ${error.message}`);
	}
};

/**
 * Get location using OpenStreetMap Nominatim API
 * Note: For production use, respect usage policy by:
 * - Caching results
 * - Adding delay between requests
 * - Using a User-Agent header identifying your application
 *
 * @param {string} address - Address string
 * @param {object} options - Options
 * @returns {Promise<object>} - Location object
 */
const getNominatimLocation = async (address, options = {}) => {
	// Encode the address for URL
	const encodedAddress = encodeURIComponent(address);

	// Build the Nominatim API URL
	// Add countrycodes=sa to limit results to Saudi Arabia
	const url = `https://nominatim.openstreetmap.org/search?q=${encodedAddress}&countrycodes=sa&format=json&limit=1`;

	// Add a delay to respect Nominatim usage policy (max 1 request per second)
	await new Promise((resolve) => setTimeout(resolve, 1000));

	// Make the request
	const response = await fetch(url, {
		method: 'GET',
		headers: {
			'User-Agent': 'RealEstateAuctionPlatform/1.0',
			Accept: 'application/json'
		}
	});

	if (!response.ok) {
		throw new Error(`Geocoding request failed with status ${response.status}`);
	}

	const data = await response.json();

	// Check if results were found
	if (!data || data.length === 0) {
		throw new Error('No results found for this address');
	}

	const result = data[0];

	// Return full response or just coordinates
	if (options.fullResponse) {
		return {
			latitude: parseFloat(result.lat),
			longitude: parseFloat(result.lon),
			displayName: result.display_name,
			boundingBox: result.boundingbox,
			placeId: result.place_id,
			osmId: result.osm_id,
			osmType: result.osm_type,
			type: result.type,
			class: result.class
		};
	}

	// Return only coordinates in format compatible with backend
	return {
		latitude: parseFloat(result.lat),
		longitude: parseFloat(result.lon)
	};
};

/**
 * Get location using a premium geocoding service
 * Implement with your preferred provider (Google Maps, Mapbox, HERE, etc.)
 *
 * @param {string} address - Address string
 * @param {object} options - Options including API key
 * @returns {Promise<object>} - Location object
 */
const getPremiumLocation = async (address, options = {}) => {
	// Implementation will depend on which service you choose
	// This is a placeholder for a premium geocoding service

	// For Google Maps Geocoding API example:
	// const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${options.apiKey}`;

	// For now, we'll throw an error since this requires configuration
	throw new Error('Premium geocoding not configured');
};

/**
 * Validate if coordinates are valid
 *
 * @param {number} latitude - Latitude to validate
 * @param {number} longitude - Longitude to validate
 * @returns {boolean} - True if coordinates are valid
 */
export const validateCoordinates = (latitude, longitude) => {
	// Check if values are numbers
	if (typeof latitude !== 'number' || typeof longitude !== 'number') {
		return false;
	}

	// Check if values are within valid ranges
	if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
		return false;
	}

	return true;
};

/**
 * Format coordinates to fixed precision
 *
 * @param {object} location - Location object with latitude and longitude
 * @param {number} precision - Decimal places (default: 6)
 * @returns {object} - Location with formatted coordinates
 */
export const formatCoordinates = (location, precision = 6) => {
	if (!location || typeof location !== 'object') {
		return null;
	}

	const { latitude, longitude } = location;

	if (!validateCoordinates(latitude, longitude)) {
		return null;
	}

	return {
		latitude: parseFloat(latitude.toFixed(precision)),
		longitude: parseFloat(longitude.toFixed(precision))
	};
};

/**
 * Get the center coordinates for Saudi Arabia
 * Useful as a default location for maps
 *
 * @returns {object} - Default coordinates for Saudi Arabia
 */
export const getSaudiArabiaCenter = () => {
	return {
		latitude: 24.7136, // Approximate center of Saudi Arabia
		longitude: 46.6753 // (Riyadh coordinates)
	};
};

/**
 * Convert backend location format to frontend format
 *
 * @param {string|object} locationData - Location from backend (JSON string or object)
 * @returns {object} - Parsed location object
 */
export const parseLocationData = (locationData) => {
	if (!locationData) {
		return getSaudiArabiaCenter();
	}

	try {
		// If it's a string (from backend), parse it
		if (typeof locationData === 'string') {
			const parsed = JSON.parse(locationData);
			return {
				latitude: parseFloat(parsed.latitude),
				longitude: parseFloat(parsed.longitude)
			};
		}

		// If it's already an object
		if (locationData.latitude && locationData.longitude) {
			return {
				latitude: parseFloat(locationData.latitude),
				longitude: parseFloat(locationData.longitude)
			};
		}
	} catch (error) {
		console.error('Failed to parse location data:', error);
	}

	// Return default if parsing fails
	return getSaudiArabiaCenter();
};

export default {
	getLocationFromAddress,
	validateCoordinates,
	formatCoordinates,
	getSaudiArabiaCenter,
	parseLocationData
};
