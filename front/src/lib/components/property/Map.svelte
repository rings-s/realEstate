<!--
  Enhanced Map Component
  A reliable Leaflet map component with marker support and location detection
-->
<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	export let latitude = null; // Initial latitude
	export let longitude = null; // Initial longitude
	export let height = '400px';
	export let width = '100%';
	export let zoom = 13;
	export let interactive = true;
	export let showMarker = true;
	export let draggableMarker = false;
	export let showLocationButton = false;
	export let markerIcon = null;
	export let markerPopup = '';
	export let classes = '';

	// Internal state
	let mapContainer;
	let map;
	let marker;
	let isLocating = false;
	let locationError = null;

	// Make sure we have default coordinates if none provided
	$: initialLatitude = latitude !== null ? latitude : 24.774265; // Default to Riyadh, Saudi Arabia
	$: initialLongitude = longitude !== null ? longitude : 46.738586;

	// We'll store Leaflet as a module-level variable to avoid re-importing
	let L;
	let leafletLoaded = false;

	onMount(async () => {
		try {
			// Only import Leaflet in the browser
			if (typeof window !== 'undefined') {
				// Dynamic import for Leaflet
				const leafletModule = await import('leaflet');
				L = leafletModule.default;

				// Wait a tick to ensure the DOM is ready
				await new Promise((resolve) => setTimeout(resolve, 0));

				// Initialize the map
				initializeMap();
				leafletLoaded = true;
			}
		} catch (error) {
			console.error('Error loading Leaflet:', error);
		}
	});

	async function initializeMap() {
		if (!mapContainer || !L) return;

		try {
			// Create map with the provided options
			map = L.map(mapContainer, {
				center: [initialLatitude, initialLongitude],
				zoom: zoom,
				dragging: interactive,
				touchZoom: interactive,
				scrollWheelZoom: interactive,
				doubleClickZoom: interactive,
				boxZoom: interactive,
				keyboard: interactive,
				tap: interactive,
				zoomControl: interactive
			});

			// Add the OpenStreetMap tile layer
			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
				maxZoom: 19
			}).addTo(map);

			// Add marker if coordinates are provided
			if (showMarker && latitude && longitude) {
				addMarker(latitude, longitude);
			}

			// Add click handler for interactive maps
			if (interactive) {
				map.on('click', handleMapClick);
			}

			// Dispatch the ready event
			dispatch('ready', { map });
		} catch (error) {
			console.error('Error initializing map:', error);
		}
	}

	// Add or update marker on the map
	function addMarker(lat, lng) {
		if (!map || !L) return;

		// Remove existing marker if any
		if (marker) {
			marker.remove();
		}

		// Custom icon if provided
		let icon = null;
		if (markerIcon) {
			icon = L.icon({
				iconUrl: markerIcon,
				iconSize: [32, 32],
				iconAnchor: [16, 32]
			});
		}

		// Create and add the marker
		marker = L.marker([lat, lng], {
			draggable: draggableMarker,
			icon: icon || undefined
		}).addTo(map);

		// Add popup if provided
		if (markerPopup) {
			marker.bindPopup(markerPopup).openPopup();
		}

		// Add drag end event for draggable markers
		if (draggableMarker) {
			marker.on('dragend', handleMarkerDrag);
		}

		// Update the component state
		latitude = lat;
		longitude = lng;

		// Dispatch the location change event
		dispatch('locationchange', { latitude, longitude });
	}

	// Handle map click event
	function handleMapClick(e) {
		// Add or update marker
		addMarker(e.latlng.lat, e.latlng.lng);

		// Pan to the new location
		map.panTo(e.latlng);

		// Clear any previous errors
		locationError = null;
	}

	// Handle marker drag event
	function handleMarkerDrag(e) {
		const latlng = e.target.getLatLng();

		// Update the component state
		latitude = latlng.lat;
		longitude = latlng.lng;

		// Dispatch the location change event
		dispatch('locationchange', { latitude, longitude });

		// Clear any previous errors
		locationError = null;
	}

	// When props change, update the map
	$: if (map && L && leafletLoaded) {
		// Update marker if latitude/longitude change
		if (latitude !== null && longitude !== null) {
			if (marker) {
				// Update existing marker position
				marker.setLatLng([latitude, longitude]);
			} else if (showMarker) {
				// Create new marker if needed
				addMarker(latitude, longitude);
			}

			// Center map on new coordinates
			map.setView([latitude, longitude], map.getZoom());
		}
	}

	// Detect user's current location
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
			// Get current position with a timeout
			const position = await new Promise((resolve, reject) => {
				navigator.geolocation.getCurrentPosition(resolve, reject, {
					enableHighAccuracy: true,
					timeout: 10000,
					maximumAge: 0
				});
			});

			const { latitude: lat, longitude: lng } = position.coords;

			// Update map and marker
			if (map) {
				map.setView([lat, lng], 16); // Zoom in closer for current location

				if (showMarker) {
					addMarker(lat, lng);
				}
			}

			// Update component state
			latitude = lat;
			longitude = lng;

			// Show success message
			addToast(
				t('location_detected', $language, { default: 'تم تحديد موقعك الحالي بنجاح' }),
				'success'
			);

			// Dispatch the location detection event
			dispatch('locationdetect', { latitude: lat, longitude: lng });
			dispatch('locationchange', { latitude: lat, longitude: lng });
		} catch (error) {
			console.error('Error getting location:', error);

			// Provide specific error messages
			let errorMessage;

			switch (error.code) {
				case 1: // PERMISSION_DENIED
					errorMessage = t('geolocation_permission_denied', $language, {
						default:
							'تم رفض إذن الوصول إلى الموقع. يرجى السماح للموقع بالوصول إلى موقعك من إعدادات المتصفح.'
					});
					break;
				case 2: // POSITION_UNAVAILABLE
					errorMessage = t('geolocation_unavailable', $language, {
						default: 'معلومات الموقع غير متوفرة حالياً. حاول مرة أخرى لاحقاً.'
					});
					break;
				case 3: // TIMEOUT
					errorMessage = t('geolocation_timeout', $language, {
						default: 'انتهت مهلة طلب تحديد الموقع. تحقق من اتصالك بالإنترنت وحاول مرة أخرى.'
					});
					break;
				default:
					errorMessage = t('geolocation_error', $language, {
						default: 'فشل في تحديد موقعك. يرجى التأكد من السماح بالوصول إلى الموقع'
					});
			}

			locationError = errorMessage;

			// Show error toast
			addToast(errorMessage, 'error');
		} finally {
			isLocating = false;
		}
	}

	// Clean up map when component is destroyed
	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});
</script>

<!-- Include Leaflet CSS in the component -->
<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

<div class="map-container w-full {classes}">
	<!-- Map container element -->
	<div bind:this={mapContainer} style="width: {width}; height: {height};" class="rounded-lg"></div>

	<!-- Location detection button -->
	{#if showLocationButton}
		<div class="mt-2">
			<button
				class="btn btn-sm variant-filled-primary"
				on:click={detectLocation}
				disabled={isLocating}
			>
				{#if isLocating}
					<div class="spinner-icon {$isRTL ? 'ml-2' : 'mr-2'}"></div>
				{:else}
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

	<!-- Location error message -->
	{#if locationError}
		<div class="mt-2 text-error-500 text-sm bg-error-500/20 p-2 rounded-token">
			{locationError}
		</div>
	{/if}

	<!-- Display coordinates if available -->
	{#if latitude !== null && longitude !== null}
		<div class="mt-2 text-sm text-surface-600-300-token">
			<span class="font-medium">
				{t('coordinates', $language, { default: 'الإحداثيات' })}:
			</span>
			{latitude.toFixed(6)}, {longitude.toFixed(6)}
		</div>
	{/if}
</div>

<style>
	/* Loading spinner animation */
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

	/* Fix z-index issues with Leaflet controls */
	:global(.map-container .leaflet-container) {
		z-index: 1;
	}
</style>
