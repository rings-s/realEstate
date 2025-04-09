<!--
  LeafletMap Component
  Reusable Leaflet map component with marker support and location detection
-->
<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { Browser } from 'leaflet';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Initial latitude
	export let latitude = 24.774265; // Default to Riyadh, Saudi Arabia
	// Initial longitude
	export let longitude = 46.738586;
	// Map height
	export let height = '400px';
	// Map width (default 100%)
	export let width = '100%';
	// Zoom level
	export let zoom = 13;
	// Whether the map is interactive (can be moved/zoomed)
	export let interactive = true;
	// Whether to show a marker at the specified coordinates
	export let showMarker = true;
	// Whether the marker is draggable
	export let draggableMarker = false;
	// Whether to show a "detect my location" button
	export let showLocationButton = false;
	// Custom marker icon URL
	export let markerIcon = null;
	// Custom marker popup content
	export let markerPopup = '';
	// Additional classes
	export let classes = '';

	// Local state
	let mapContainer;
	let map;
	let marker;
	let isLocating = false;
	let locationError = null;

	// Dynamically import Leaflet (due to SSR)
	async function initializeMap() {
		try {
			// Import Leaflet on the client side
			const L = await import('leaflet');

			// Create the map instance
			map = L.map(mapContainer, {
				center: [latitude, longitude],
				zoom: zoom,
				dragging: interactive,
				touchZoom: interactive,
				scrollWheelZoom: interactive,
				doubleClickZoom: interactive,
				boxZoom: interactive,
				keyboard: interactive,
				tap: interactive && L.Browser.mobile,
				zoomControl: interactive
			});

			// Add tile layer (OSM default)
			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(map);

			// Add marker if requested
			if (showMarker) {
				addMarker(latitude, longitude);
			}

			// Set up event listeners
			if (interactive) {
				map.on('click', handleMapClick);
				if (draggableMarker && marker) {
					marker.on('dragend', handleMarkerDrag);
				}
			}

			// Dispatch event that map is initialized
			dispatch('ready', { map, L });
		} catch (error) {
			console.error('Error initializing Leaflet map:', error);
		}
	}

	// Add or update marker
	function addMarker(lat, lng) {
		if (!map) return;

		// Get Leaflet from the map instance
		const L = map.L || window.L;
		if (!L) return;

		// Remove existing marker
		if (marker) {
			marker.remove();
		}

		// Create custom icon if specified
		let icon = null;
		if (markerIcon) {
			icon = L.icon({
				iconUrl: markerIcon,
				iconSize: [32, 32],
				iconAnchor: [16, 32]
			});
		}

		// Create marker
		marker = L.marker([lat, lng], {
			draggable: draggableMarker,
			icon: icon || undefined
		}).addTo(map);

		// Add popup if specified
		if (markerPopup) {
			marker.bindPopup(markerPopup).openPopup();
		}

		// Update coordinates
		latitude = lat;
		longitude = lng;

		// Dispatch event with new coordinates
		dispatch('locationchange', { latitude, longitude });
	}

	// Handle map click event
	function handleMapClick(e) {
		if (!draggableMarker) {
			addMarker(e.latlng.lat, e.latlng.lng);
		}
	}

	// Handle marker drag event
	function handleMarkerDrag(e) {
		const latlng = e.target.getLatLng();
		latitude = latlng.lat;
		longitude = latlng.lng;

		// Dispatch event with new coordinates
		dispatch('locationchange', { latitude, longitude });
	}

	// Handle manual coordinate updates
	$: if (
		map &&
		marker &&
		(marker.getLatLng().lat !== latitude || marker.getLatLng().lng !== longitude)
	) {
		marker.setLatLng([latitude, longitude]);
		map.setView([latitude, longitude], map.getZoom());
	}

	// Get current location
	async function detectLocation() {
		if (!navigator.geolocation) {
			locationError = t('geolocation_not_supported', $language, {
				default: 'الموقع الجغرافي غير مدعوم في متصفحك'
			});
			return;
		}

		isLocating = true;
		locationError = null;

		try {
			const position = await new Promise((resolve, reject) => {
				navigator.geolocation.getCurrentPosition(resolve, reject, {
					enableHighAccuracy: true,
					timeout: 10000,
					maximumAge: 0
				});
			});

			const { latitude: lat, longitude: lng } = position.coords;

			// Update the map and marker
			if (map) {
				map.setView([lat, lng], 16);
				addMarker(lat, lng);
			}

			// Update props
			latitude = lat;
			longitude = lng;

			// Dispatch event
			dispatch('locationdetect', { latitude: lat, longitude: lng });
		} catch (error) {
			console.error('Error getting location:', error);
			locationError = t('geolocation_error', $language, {
				default: 'فشل في تحديد موقعك. يرجى التأكد من السماح بالوصول إلى الموقع'
			});
		} finally {
			isLocating = false;
		}
	}

	// Update map when coordinates change
	$: if (map && marker) {
		marker.setLatLng([latitude, longitude]);
	}

	// Set up map on mount
	onMount(() => {
		if (typeof window !== 'undefined') {
			initializeMap();
		}
	});

	// Clean up on component destroy
	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});
</script>

<!-- Leaflet CSS -->
<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

<div class="leaflet-map-container w-full {classes}">
	<!-- Map Container -->
	<div bind:this={mapContainer} style="width: {width}; height: {height};" class="rounded-lg"></div>

	<!-- Location Button -->
	{#if showLocationButton}
		<div class="mt-2">
			<button
				class="btn btn-sm variant-ghost-primary"
				on:click={detectLocation}
				disabled={isLocating}
			>
				{#if isLocating}
					<div class="spinner-icon {$isRTL ? 'ml-2' : 'mr-2'}"></div>
				{:else}
					<!-- Location icon -->
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2"
						class={$isRTL ? 'ml-2' : 'mr-2'}
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
						/>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
						/>
					</svg>
				{/if}
				{t('detect_location', $language, { default: 'تحديد موقعي الحالي' })}
			</button>
		</div>
	{/if}

	<!-- Location Error -->
	{#if locationError}
		<div class="mt-2 text-error-500 text-sm">
			{locationError}
		</div>
	{/if}
</div>

<style>
	.spinner-icon {
		border: 2px solid #f3f3f3;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		width: 1em;
		height: 1em;
		animation: spin 1s linear infinite;
		display: inline-block;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	/* Make sure Leaflet container has position relative for proper rendering */
	:global(.leaflet-map-container .leaflet-container) {
		position: relative;
		z-index: 1;
	}
</style>
