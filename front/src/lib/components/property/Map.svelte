<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { Locate, MapPin, Search, Loader } from 'lucide-svelte';

	// Create event dispatcher for component events
	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Initial latitude (can be provided or will use default)
	export let latitude = null;
	// Initial longitude (can be provided or will use default)
	export let longitude = null;
	// Map height
	export let height = '400px';
	// Map width
	export let width = '100%';
	// Initial zoom level
	export let zoom = 13;
	// Whether to show a marker at the current location
	export let showMarker = true;
	// Whether the marker can be dragged to set position
	export let draggableMarker = true;
	// Whether to show the location detection button
	export let showLocationButton = true;
	// Whether the map is interactive
	export let interactive = true;
	// Popup text for marker (if any)
	export let markerPopup = '';
	// Additional classes for the map container
	export let classes = '';
	// Detect location on mount
	export let autoDetectLocation = false;

	// Local state
	let mapContainer;
	let map;
	let marker;
	let mapLoaded = false;
	let detectingLocation = false;
	let error = null;

	// Default coordinates if none provided (Riyadh, Saudi Arabia by default)
	let defaultLatitude = 24.774265;
	let defaultLongitude = 46.738586;

	// Initialize leaflet maps
	onMount(async () => {
		// Wait for leaflet library to load
		if (typeof window === 'undefined') return;

		try {
			// If no initial coordinates, use defaults
			if (latitude === null) latitude = defaultLatitude;
			if (longitude === null) longitude = defaultLongitude;

			// Create map when the component mounts
			await initializeMap();

			// Auto-detect location if enabled
			if (autoDetectLocation) {
				detectLocation();
			}
		} catch (err) {
			console.error('Error initializing map:', err);
			error = t('map_initialization_error', $language, {
				default: 'حدث خطأ أثناء تهيئة الخريطة'
			});
		}
	});

	// Initialize leaflet map
	async function initializeMap() {
		// Make sure we're running in the browser
		if (typeof window === 'undefined') return;

		// Dynamically import Leaflet
		if (!window.L) {
			// If we don't have the L namespace, Leaflet isn't loaded yet
			const leafletCSS = document.createElement('link');
			leafletCSS.rel = 'stylesheet';
			leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
			document.head.appendChild(leafletCSS);

			// Wait for the script to load
			await new Promise((resolve, reject) => {
				const leafletScript = document.createElement('script');
				leafletScript.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
				leafletScript.onload = resolve;
				leafletScript.onerror = reject;
				document.head.appendChild(leafletScript);
			});
		}

		// Create map instance
		map = window.L.map(mapContainer, {
			center: [latitude, longitude],
			zoom: zoom,
			zoomControl: interactive,
			dragging: interactive,
			touchZoom: interactive,
			doubleClickZoom: interactive,
			scrollWheelZoom: interactive,
			boxZoom: interactive,
			tap: interactive,
			zoomDelta: 1,
			zoomSnap: 1
		});

		// Add tile layer (OpenStreetMap)
		window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
			maxZoom: 19
		}).addTo(map);

		// Add marker if needed
		if (showMarker) {
			marker = window.L.marker([latitude, longitude], {
				draggable: draggableMarker
			}).addTo(map);

			// Add popup if text provided
			if (markerPopup) {
				marker.bindPopup(markerPopup).openPopup();
			}

			// Handle marker drag events
			if (draggableMarker) {
				marker.on('dragend', handleMarkerDrag);
			}
		}

		// Handle map click events if marker is draggable
		if (draggableMarker) {
			map.on('click', handleMapClick);
		}

		// Set map as loaded
		mapLoaded = true;
	}

	// Update marker position and dispatch location change event
	function updateMarkerPosition(lat, lng) {
		if (!map || !marker) return;

		// Update marker position
		marker.setLatLng([lat, lng]);

		// Update the map view
		map.setView([lat, lng], map.getZoom());

		// Update component props
		latitude = lat;
		longitude = lng;

		// Dispatch location change event
		dispatch('locationchange', { latitude: lat, longitude: lng });
	}

	// Handle map click to move marker
	function handleMapClick(e) {
		const { lat, lng } = e.latlng;
		updateMarkerPosition(lat, lng);
	}

	// Handle marker drag
	function handleMarkerDrag(e) {
		const { lat, lng } = e.target.getLatLng();
		updateMarkerPosition(lat, lng);
	}

	// Detect current location using browser geolocation API
	function detectLocation() {
		if (!navigator.geolocation) {
			error = t('geolocation_not_supported', $language, {
				default: 'خدمة تحديد الموقع الجغرافي غير متوفرة في متصفحك'
			});
			addToast(error, 'error');
			return;
		}

		detectingLocation = true;
		error = null;

		navigator.geolocation.getCurrentPosition(
			// Success callback
			(position) => {
				const lat = position.coords.latitude;
				const lng = position.coords.longitude;

				// Check for valid coordinates
				if (isNaN(lat) || isNaN(lng)) {
					error = t('invalid_coordinates', $language, {
						default: 'تم الحصول على إحداثيات غير صالحة'
					});
					detectingLocation = false;
					addToast(error, 'error');
					return;
				}

				// Update marker and map
				updateMarkerPosition(lat, lng);

				// Show success message
				addToast(
					t('location_detected', $language, {
						default: 'تم تحديد موقعك بنجاح'
					}),
					'success'
				);

				detectingLocation = false;
			},
			// Error callback
			(err) => {
				console.error('Error getting location:', err);

				let errorMessage;
				switch (err.code) {
					case err.PERMISSION_DENIED:
						errorMessage = t('location_permission_denied', $language, {
							default: 'تم رفض إذن الوصول إلى الموقع الجغرافي'
						});
						break;
					case err.POSITION_UNAVAILABLE:
						errorMessage = t('location_unavailable', $language, {
							default: 'معلومات الموقع الجغرافي غير متوفرة'
						});
						break;
					case err.TIMEOUT:
						errorMessage = t('location_timeout', $language, {
							default: 'انتهت مهلة طلب الموقع الجغرافي'
						});
						break;
					default:
						errorMessage = t('location_error', $language, {
							default: 'حدث خطأ أثناء تحديد الموقع الجغرافي'
						});
				}

				error = errorMessage;
				addToast(error, 'error');
				detectingLocation = false;
			},
			// Options
			{
				enableHighAccuracy: true,
				timeout: 10000,
				maximumAge: 0
			}
		);
	}

	// Search for a location by name
	async function searchLocation(query) {
		if (!query) return;

		try {
			// Use Nominatim API to search for locations
			const response = await fetch(
				`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`
			);

			if (!response.ok) {
				throw new Error('Failed to search location');
			}

			const data = await response.json();

			if (data && data.length > 0) {
				const location = data[0];
				updateMarkerPosition(parseFloat(location.lat), parseFloat(location.lon));

				// Show success message
				addToast(
					t('location_found', $language, {
						default: 'تم العثور على الموقع'
					}),
					'success'
				);
			} else {
				addToast(
					t('location_not_found', $language, {
						default: 'لم يتم العثور على الموقع'
					}),
					'warning'
				);
			}
		} catch (err) {
			console.error('Error searching for location:', err);
			addToast(
				t('location_search_error', $language, {
					default: 'حدث خطأ أثناء البحث عن الموقع'
				}),
				'error'
			);
		}
	}

	// Keep marker position updated when lat/lng props change
	$: if (map && marker && latitude !== null && longitude !== null) {
		const currentPos = marker.getLatLng();
		if (currentPos.lat !== latitude || currentPos.lng !== longitude) {
			marker.setLatLng([latitude, longitude]);
			map.setView([latitude, longitude], map.getZoom());
		}
	}
</script>

<!-- Map container with controls -->
<div class="map-wrapper relative {classes}">
	{#if error}
		<div class="bg-error-500 text-white p-2 text-sm rounded mb-2">
			{error}
		</div>
	{/if}

	<!-- Map container -->
	<div
		bind:this={mapContainer}
		class="map-container rounded-token border border-surface-300-600-token overflow-hidden"
		style="height: {height}; width: {width};"
	>
		{#if !mapLoaded}
			<div class="absolute inset-0 flex items-center justify-center bg-surface-200-700-token">
				<Loader class="w-8 h-8 animate-spin text-primary-500" />
			</div>
		{/if}
	</div>

	<!-- Map controls -->
	{#if showLocationButton && interactive}
		<div class="absolute {$isRTL ? 'left-4' : 'right-4'} top-4 flex flex-col gap-2">
			<button
				type="button"
				class="btn btn-sm variant-filled-primary rounded-full p-2"
				on:click={detectLocation}
				disabled={detectingLocation}
				title={t('detect_location', $language, { default: 'تحديد موقعي' })}
			>
				{#if detectingLocation}
					<Loader class="w-5 h-5 animate-spin" />
				{:else}
					<Locate class="w-5 h-5" />
				{/if}
			</button>
		</div>
	{/if}

	<!-- Coordinates display -->
	{#if latitude !== null && longitude !== null}
		<div class="mt-2 text-sm text-surface-700-200-token">
			<div class="flex flex-wrap gap-2">
				<div class="font-medium">
					{t('latitude', $language, { default: 'خط العرض' })}: {latitude.toFixed(6)}
				</div>
				<div class="font-medium">
					{t('longitude', $language, { default: 'خط الطول' })}: {longitude.toFixed(6)}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.map-wrapper {
		display: flex;
		flex-direction: column;
	}
</style>
