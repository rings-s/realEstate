<!-- src/lib/components/properties/PropertyMap.svelte -->
<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import {
		parseLocationData,
		validateCoordinates,
		formatCoordinates,
		getSaudiArabiaCenter
	} from '$lib/utils/geocoding';

	// Props
	export let location = null; // JSON location object
	export let height = '400px';
	export let width = '100%';
	export let interactive = false; // If true, allow marker placement
	export let zoom = 15;
	export let showControls = true;
	export let enableSearch = false; // For address search functionality

	// Default location from geocoding utility
	const defaultLocation = getSaudiArabiaCenter();

	// Local state
	let mapContainer;
	let map;
	let marker;
	let L; // Leaflet instance
	let locationData = parseLocationData(location) || defaultLocation;
	let searchAddress = ''; // For search functionality
	let isLocating = false; // Track geolocation status
	let locationError = null; // Track geolocation errors

	// Handle location changes from prop
	$: {
		if (location) {
			const parsedLocation = parseLocationData(location);
			if (
				parsedLocation &&
				validateCoordinates(parsedLocation.latitude, parsedLocation.longitude)
			) {
				locationData = parsedLocation;
			}
		}
	}

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Initialize map
	async function initMap() {
		if (!browser || !mapContainer) return;

		// Dynamically import Leaflet (only in browser)
		try {
			// We're using dynamic import to avoid SSR issues
			L = await import('leaflet');

			// Create map
			map = L.map(mapContainer, {
				center: [locationData.latitude, locationData.longitude],
				zoom: zoom,
				zoomControl: showControls,
				scrollWheelZoom: interactive
			});

			// Add tile layer
			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(map);

			// Add marker
			marker = L.marker([locationData.latitude, locationData.longitude], {
				draggable: interactive
			}).addTo(map);

			// Handle marker drag events if interactive
			if (interactive) {
				marker.on('dragend', handleMarkerDrag);

				// Also handle map click for marker placement
				map.on('click', handleMapClick);
			}

			// Dispatch map ready event
			dispatch('mapready', { map, marker });
		} catch (error) {
			console.error('Failed to load Leaflet:', error);
		}
	}

	// Handle marker drag event
	function handleMarkerDrag(e) {
		const latLng = marker.getLatLng();
		locationData = {
			latitude: latLng.lat,
			longitude: latLng.lng
		};

		// Format coordinates to fixed precision using utility
		const formattedLocation = formatCoordinates(locationData);

		// Dispatch change event with formatted coordinates
		dispatch('locationchange', formattedLocation);
	}

	// Handle map click for marker placement
	function handleMapClick(e) {
		const latLng = e.latlng;
		locationData = {
			latitude: latLng.lat,
			longitude: latLng.lng
		};

		// Format coordinates to fixed precision using utility
		const formattedLocation = formatCoordinates(locationData);

		// Move marker to new position
		marker.setLatLng([locationData.latitude, locationData.longitude]);

		// Dispatch change event with formatted coordinates
		dispatch('locationchange', formattedLocation);
	}

	// Function to get current user location
	function getCurrentLocation() {
		if (!browser || !navigator.geolocation) {
			locationError = 'خدمة تحديد الموقع غير متوفرة في متصفحك';
			return;
		}

		isLocating = true;
		locationError = null;

		navigator.geolocation.getCurrentPosition(
			(position) => {
				// Success - update location data
				locationData = {
					latitude: position.coords.latitude,
					longitude: position.coords.longitude
				};

				// Format coordinates to fixed precision using utility
				const formattedLocation = formatCoordinates(locationData);

				// Update marker and map view
				if (marker && map) {
					marker.setLatLng([locationData.latitude, locationData.longitude]);
					map.setView([locationData.latitude, locationData.longitude], zoom);
				}

				// Dispatch event with formatted coordinates
				dispatch('locationchange', formattedLocation);
				isLocating = false;
			},
			(error) => {
				// Error handling
				switch (error.code) {
					case error.PERMISSION_DENIED:
						locationError = 'تم رفض طلب تحديد الموقع';
						break;
					case error.POSITION_UNAVAILABLE:
						locationError = 'معلومات الموقع غير متوفرة';
						break;
					case error.TIMEOUT:
						locationError = 'انتهت مهلة طلب تحديد الموقع';
						break;
					case error.UNKNOWN_ERROR:
						locationError = 'حدث خطأ غير معروف';
						break;
				}
				isLocating = false;
			},
			{
				enableHighAccuracy: true,
				timeout: 10000,
				maximumAge: 0
			}
		);
	}

	// Function to search for location by address using geocoding utility
	async function searchLocation() {
		if (!searchAddress.trim() || !browser) return;

		try {
			// Import the geocoding function dynamically to avoid SSR issues
			const { getLocationFromAddress } = await import('$lib/utils/geocoding');

			isLocating = true;
			locationError = null;

			// Use the utility function to get coordinates
			const searchResult = await getLocationFromAddress(searchAddress);

			if (searchResult) {
				locationData = {
					latitude: searchResult.latitude,
					longitude: searchResult.longitude
				};

				// Update map and marker
				if (map && marker) {
					marker.setLatLng([locationData.latitude, locationData.longitude]);
					map.setView([locationData.latitude, locationData.longitude], zoom);
				}

				// Dispatch event with coordinates
				dispatch('locationchange', locationData);

				// Clear search field after successful search
				searchAddress = '';
			}
		} catch (error) {
			console.error('Error searching for location:', error);
			locationError = error.message || 'حدث خطأ أثناء البحث عن الموقع';
		} finally {
			isLocating = false;
		}
	}

	// Update map when location changes from external source
	$: if (map && marker && locationData) {
		marker.setLatLng([locationData.latitude, locationData.longitude]);
		map.setView([locationData.latitude, locationData.longitude], zoom);
	}

	// Initialize on mount
	onMount(() => {
		initMap();

		// Add Leaflet CSS
		if (browser) {
			const link = document.createElement('link');
			link.rel = 'stylesheet';
			link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
			link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
			link.crossOrigin = '';
			document.head.appendChild(link);
		}
	});

	// Cleanup on destroy
	onDestroy(() => {
		if (map) {
			map.remove();
			map = null;
		}
	});
</script>

<div
	bind:this={mapContainer}
	class="relative overflow-hidden rounded-lg"
	style="height: {height}; width: {width};"
	role="application"
	aria-label="خريطة العقار"
>
	{#if !browser}
		<div class="absolute inset-0 flex items-center justify-center bg-gray-200 dark:bg-gray-700">
			<span class="text-gray-500 dark:text-gray-400">جاري تحميل الخريطة...</span>
		</div>
	{/if}

	<!-- Interactive mode instructions -->
	{#if interactive && browser}
		<div
			class="bg-opacity-90 dark:bg-opacity-90 absolute top-3 right-0 left-0 z-[1000] mx-auto w-max rounded-md bg-white px-4 py-2 text-sm text-gray-800 shadow-md dark:bg-gray-800 dark:text-gray-200"
		>
			انقر على الخريطة لتحديد موقع العقار أو اسحب العلامة
		</div>
	{/if}

	<!-- Detect My Location button -->
	{#if interactive && browser}
		<div
			class="bg-opacity-90 dark:bg-opacity-90 absolute top-16 left-2 z-[1000] rounded-md bg-white p-2 shadow-md dark:bg-gray-800"
		>
			<button
				on:click={getCurrentLocation}
				class="flex items-center gap-1 rounded-md bg-blue-600 px-2 py-1 text-sm text-white hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
				disabled={isLocating}
			>
				{#if isLocating}
					<span
						class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"
					></span>
					جاري التحديد...
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
						/>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
						/>
					</svg>
					تحديد موقعي الحالي
				{/if}
			</button>
			{#if locationError}
				<div class="mt-1 text-xs text-red-500">
					{locationError}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Search control (if enabled) -->
	{#if enableSearch && interactive && browser}
		<div
			class="bg-opacity-90 dark:bg-opacity-90 absolute top-16 right-0 left-0 z-[1000] mx-auto w-64 rounded-md bg-white p-2 shadow-md dark:bg-gray-800"
		>
			<div class="flex">
				<input
					type="text"
					bind:value={searchAddress}
					placeholder="ابحث عن عنوان..."
					class="flex-1 rounded-l-md border border-gray-300 px-2 py-1 text-sm text-gray-800 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
					on:keydown={(e) => e.key === 'Enter' && searchLocation()}
				/>
				<button
					on:click={searchLocation}
					class="rounded-r-md bg-blue-600 px-2 py-1 text-sm text-white hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
				>
					بحث
				</button>
			</div>
		</div>
	{/if}

	<!-- Coordinates display -->
	{#if interactive && locationData && browser}
		<div
			class="bg-opacity-90 dark:bg-opacity-90 absolute right-0 bottom-3 left-0 z-[1000] mx-auto w-max rounded-md bg-white px-3 py-1 text-xs text-gray-800 shadow-md dark:bg-gray-800 dark:text-gray-200"
		>
			{locationData.latitude.toFixed(6)}, {locationData.longitude.toFixed(6)}
		</div>
	{/if}
</div>
