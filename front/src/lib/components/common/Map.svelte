<!--
  Enhanced Map Component
  Reusable Leaflet map component with marker support and location detection
-->
<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	export let latitude = 24.774265; // Default to Riyadh, Saudi Arabia
	export let longitude = 46.738586;
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

	let mapContainer;
	let map;
	let marker;
	let isLocating = false;
	let locationError = null;

	// Dynamically import Leaflet only on the client side
	let L;
	onMount(async () => {
		if (typeof window !== 'undefined') {
			L = await import('leaflet');
			initializeMap();
		}
	});

	async function initializeMap() {
		if (!mapContainer || typeof window === 'undefined') return;

		try {
			map = L.map(mapContainer, {
				center: [latitude || 24.774265, longitude || 46.738586],
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

			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(map);

			if (showMarker && latitude && longitude) {
				addMarker(latitude, longitude);
			}

			if (interactive) {
				map.on('click', handleMapClick);
				if (draggableMarker && marker) {
					marker.on('dragend', handleMarkerDrag);
				}
			}

			dispatch('ready', { map, L });
		} catch (error) {
			console.error('Error initializing Leaflet map:', error);
		}
	}

	function addMarker(lat, lng) {
		if (!map || !L) return;

		if (marker) {
			marker.remove();
		}

		let icon = null;
		if (markerIcon) {
			icon = L.icon({
				iconUrl: markerIcon,
				iconSize: [32, 32],
				iconAnchor: [16, 32]
			});
		}

		marker = L.marker([lat, lng], {
			draggable: draggableMarker,
			icon: icon || undefined
		}).addTo(map);

		if (markerPopup) {
			marker.bindPopup(markerPopup).openPopup();
		}

		latitude = lat;
		longitude = lng;

		dispatch('locationchange', { latitude, longitude });
	}

	function handleMapClick(e) {
		if (!draggableMarker) {
			addMarker(e.latlng.lat, e.latlng.lng);
		}
	}

	function handleMarkerDrag(e) {
		const latlng = e.target.getLatLng();
		latitude = latlng.lat;
		longitude = latlng.lng;

		dispatch('locationchange', { latitude, longitude });
	}

	$: if (map && L) {
		// Handle changes to latitude/longitude from outside component
		if (latitude && longitude) {
			// If we already have a marker, update its position
			if (marker) {
				marker.setLatLng([latitude, longitude]);
			} else if (showMarker) {
				// If we don't have a marker yet but should show one, add it
				addMarker(latitude, longitude);
			}

			// Update map view
			map.setView([latitude, longitude], map.getZoom());
		}
	}

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

			if (map) {
				map.setView([lat, lng], 16); // Zoom in closer when using current location

				if (showMarker) {
					addMarker(lat, lng);
				}
			}

			latitude = lat;
			longitude = lng;

			// Show success message
			addToast(
				t('location_detected', $language, { default: 'تم تحديد موقعك الحالي بنجاح' }),
				'success'
			);

			dispatch('locationdetect', { latitude: lat, longitude: lng });
		} catch (error) {
			console.error('Error getting location:', error);

			// Provide more specific error messages
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

	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});
</script>

<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

<div class="leaflet-map-container w-full {classes}">
	<div bind:this={mapContainer} style="width: {width}; height: {height};" class="rounded-lg"></div>

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

	{#if locationError}
		<div class="mt-2 text-error-500 text-sm bg-error-500/20 p-2 rounded-token">
			{locationError}
		</div>
	{/if}

	<!-- Coordinates display -->
	{#if latitude && longitude}
		<div class="mt-2 text-sm text-surface-600-300-token">
			<span class="font-medium">
				{t('coordinates', $language, { default: 'الإحداثيات' })}:
			</span>
			{latitude.toFixed(6)}, {longitude.toFixed(6)}
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

	:global(.leaflet-map-container .leaflet-container) {
		position: relative;
		z-index: 1;
	}
</style>
