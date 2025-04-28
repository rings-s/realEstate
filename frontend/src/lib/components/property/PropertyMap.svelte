<!-- src/lib/components/property/PropertyMap.svelte -->
<script>
	import { onMount, onDestroy, tick, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';

	const dispatch = createEventDispatcher();
	export let latitude = 24.774265; // Default Riyadh
	export let longitude = 46.738586;
	export let editable = false;
	export let onLocationChange = (coords) => {}; // Provide default empty function

	let mapContainer;
	let map = null;
	let marker = null;
	let L = null;
	let loading = false;
	let error = '';
	let isMounted = false;

	async function initializeMap() {
		if (!browser || !mapContainer || map) return;

		try {
			// Dynamically import Leaflet only on the client-side
			if (!L) {
				L = (await import('leaflet')).default;
			}

			// Ensure the container is fully rendered
			await tick();

			if (!map) {
				// Make sure we have valid coordinates
				const validLat = typeof latitude === 'number' ? latitude : 24.774265;
				const validLng = typeof longitude === 'number' ? longitude : 46.738586;

				map = L.map(mapContainer, {
					center: [validLat, validLng],
					zoom: 13
				});

				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					attribution: '© OpenStreetMap contributors',
					maxZoom: 19
				}).addTo(map);

				// Add marker
				marker = L.marker([validLat, validLng], {
					draggable: editable
				}).addTo(map);

				if (editable) {
					marker.on('dragend', (e) => {
						const latlng = e.target.getLatLng();
						latitude = latlng.lat;
						longitude = latlng.lng;
						
						// Use dispatch function correctly
						dispatch('locationchange', { 
						lat: latlng.lat, 
						lng: latlng.lng 
						});
						
						console.log('Location updated:', latitude, longitude);
					});
				}

				await tick();
				map.invalidateSize();
				map.setView([validLat, validLng], 13);

				console.log('Leaflet map initialized successfully.');
			}
		} catch (err) {
			console.error('Failed to initialize Leaflet map:', err);
			error = 'حدث خطأ أثناء تحميل الخريطة.';
		}
	}

	onMount(() => {
		isMounted = true;
		initializeMap();

		return () => {
			isMounted = false;
			if (map) {
				map.remove();
				map = null;
				marker = null;
			}
		};
	});

	// Reactive statement to update marker position if props change externally
	$: if (browser && map && marker && isMounted) {
		// Check if latitude and longitude are valid numbers
		if (
			typeof latitude === 'number' &&
			!isNaN(latitude) &&
			typeof longitude === 'number' &&
			!isNaN(longitude)
		) {
			const currentLatLng = marker.getLatLng();
			if (currentLatLng.lat !== latitude || currentLatLng.lng !== longitude) {
				const newLatLng = L.latLng(latitude, longitude);
				marker.setLatLng(newLatLng);
			}
		}
	}

	async function getCurrentLocation() {
		if (!browser) return;

		loading = true;
		error = '';

		if (!navigator.geolocation) {
			error = 'المتصفح لا يدعم تحديد الموقع الجغرافي.';
			loading = false;
			return;
		}

		try {
			const position = await new Promise((resolve, reject) => {
				navigator.geolocation.getCurrentPosition(resolve, reject, {
					enableHighAccuracy: true,
					timeout: 10000,
					maximumAge: 0
				});
			});

			const { latitude: lat, longitude: lng } = position.coords;

			if (map && marker) {
				map.setView([lat, lng], 15);
				marker.setLatLng([lat, lng]);
			}

			latitude = lat;
			longitude = lng;
			onLocationChange({ latitude: lat, longitude: lng });
		} catch (err) {
			console.error('Geolocation error:', err);
			if (err.code === err.PERMISSION_DENIED) {
				error = 'تم رفض إذن تحديد الموقع.';
			} else if (err.code === err.POSITION_UNAVAILABLE) {
				error = 'معلومات الموقع غير متوفرة حالياً.';
			} else if (err.code === err.TIMEOUT) {
				error = 'انتهت مهلة طلب تحديد الموقع.';
			} else {
				error = 'فشل في تحديد الموقع الحالي.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

<div class="space-y-4">
	{#if editable}
		<div class="flex flex-col gap-3 sm:flex-row sm:gap-4">
			<button
				type="button"
				class="btn-secondary flex w-full items-center justify-center sm:flex-1"
				on:click={getCurrentLocation}
				disabled={loading}
			>
				{#if loading}
					<i class="fas fa-spinner fa-spin ml-2"></i>
					جاري التحديد...
				{:else}
					<i class="fas fa-map-marker-alt ml-2"></i> تحديد موقعي الحالي
				{/if}
			</button>

			<div class="grid w-full grid-cols-2 gap-2 sm:flex-1">
				<input
					type="number"
					step="any"
					bind:value={latitude}
					on:change={() => {
						if (
							browser &&
							map &&
							marker &&
							typeof latitude === 'number' &&
							typeof longitude === 'number'
						) {
							map.setView([latitude, longitude]);
							marker.setLatLng([latitude, longitude]);
							onLocationChange({ latitude, longitude });
						}
					}}
					placeholder="خط العرض"
					class="input w-full"
					aria-label="خط العرض"
				/>
				<input
					type="number"
					step="any"
					bind:value={longitude}
					on:change={() => {
						if (
							browser &&
							map &&
							marker &&
							typeof latitude === 'number' &&
							typeof longitude === 'number'
						) {
							map.setView([latitude, longitude]);
							marker.setLatLng([latitude, longitude]);
							onLocationChange({ latitude, longitude });
						}
					}}
					placeholder="خط الطول"
					class="input w-full"
					aria-label="خط الطول"
				/>
			</div>
		</div>
	{/if}

	{#if error}
		<div role="alert" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
			<i class="fas fa-exclamation-triangle ml-2"></i>
			{error}
		</div>
	{/if}

	<div
		class="relative h-[400px] w-full overflow-hidden rounded-lg border border-slate-200 shadow-sm"
	>
		{#if !browser}
			<div class="flex h-full items-center justify-center bg-slate-100 text-slate-500">
				جارٍ تحميل الخريطة...
			</div>
		{/if}
		<div bind:this={mapContainer} class="h-full w-full {browser ? '' : 'hidden'}"></div>
		{#if browser && !map && !error}
			<div class="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm">
				<i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
			</div>
		{/if}
	</div>
</div>

<style>
	:global(.leaflet-container) {
		font-family: inherit;
		background-color: #f8fafc;
	}

	:global(.leaflet-popup-content) {
		direction: rtl;
		text-align: right;
	}

	:global(.leaflet-marker-icon) {
		filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.3));
	}
</style>
