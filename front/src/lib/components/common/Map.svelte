<!--
  LeafletMap Component
  Reusable Leaflet map component with marker support and location detection
-->
<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';

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

			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(map);

			if (showMarker) {
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

	$: if (map && marker && L) {
		marker.setLatLng([latitude, longitude]);
		map.setView([latitude, longitude], map.getZoom());
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
				map.setView([lat, lng], 16);
				addMarker(lat, lng);
			}

			latitude = lat;
			longitude = lng;

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
				class="btn btn-sm variant-ghost-primary"
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

	:global(.leaflet-map-container .leaflet-container) {
		position: relative;
		z-index: 1;
	}
</style>
