<script>
	import { onMount, onDestroy, tick } from 'svelte';
	import { browser } from '$app/environment'; // Import browser check

	export let latitude = 24.774265; // Default Riyadh
	export let longitude = 46.738586;
	export let editable = false;
	export let onLocationChange = (coords) => {}; // Provide default empty function

	let mapContainer;
	let map = null; // Initialize map variable to null
	let marker = null; // Initialize marker variable to null
	let L = null; // To store the Leaflet instance
	let loading = false;
	let error = '';
	let isMounted = false; // Track mount state

	async function initializeMap() {
		if (!browser || !mapContainer || map) return; // Guard: Run only in browser, if container exists, and map not already initialized

		try {
			// Dynamically import Leaflet only on the client-side
			// This replaces the manual script loading
			if (!L) {
				L = (await import('leaflet')).default; // Use dynamic import
			}

			// Ensure the container is fully rendered
			await tick();

			if (!map) {
				// Double-check map isn't initialized by a rapid re-render
				map = L.map(mapContainer, {
					center: [latitude, longitude],
					zoom: 13
				});

				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					attribution: '© OpenStreetMap contributors',
					maxZoom: 19 // Good default maxZoom
				}).addTo(map);

				// Add marker
				marker = L.marker([latitude, longitude], {
					draggable: editable
				}).addTo(map);

				if (editable) {
					marker.on('dragend', (e) => {
						const { lat, lng } = e.target.getLatLng();
						// Update props directly (if needed) or rely on parent handling via onLocationChange
						latitude = lat;
						longitude = lng;
						onLocationChange({ latitude: lat, longitude: lng });
					});
				}

				// Invalidate size after a short delay to ensure CSS is applied
				await tick(); // Wait another tick just in case
				map.invalidateSize();
				map.setView([latitude, longitude], 13); // Explicitly set view again after invalidation

				console.log('Leaflet map initialized successfully.'); // Add log for debugging
			}
		} catch (err) {
			console.error('Failed to initialize Leaflet map:', err);
			error = 'حدث خطأ أثناء تحميل الخريطة.'; // Map loading error message
		}
	}

	onMount(() => {
		isMounted = true;
		initializeMap(); // Attempt initialization on mount

		// Optional: Re-initialize if coordinates change significantly after mount
		// Be cautious with this to avoid excessive re-renders/initializations
		const unsubscribe = () => {}; // Placeholder if needed later

		return () => {
			unsubscribe();
			isMounted = false;
			if (map) {
				map.remove();
				map = null; // Clean up map instance
				marker = null; // Clean up marker instance
				console.log('Leaflet map destroyed.'); // Add log for debugging
			}
		};
	});

	// Reactive statement to update marker position if props change externally
	$: if (browser && map && marker && isMounted) {
		// Check if the map/marker internal state differs from props
		const currentLatLng = marker.getLatLng();
		if (currentLatLng.lat !== latitude || currentLatLng.lng !== longitude) {
			const newLatLng = L.latLng(latitude, longitude);
			marker.setLatLng(newLatLng);
			// Optionally center map on new coordinates if they change significantly
			// map.setView(newLatLng);
		}
	}

	async function getCurrentLocation() {
		if (!browser) return; // Guard for browser env

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
					enableHighAccuracy: true, // Request higher accuracy
					timeout: 10000, // Set timeout (10 seconds)
					maximumAge: 0 // Don't use cached position
				});
			});

			const { latitude: lat, longitude: lng } = position.coords;

			if (map && marker) {
				map.setView([lat, lng], 15); // Zoom in closer for current location
				marker.setLatLng([lat, lng]);
			}
			// Update props reactively
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
						if (browser && map && marker) {
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
						if (browser && map && marker) {
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
	/* Ensure the map container has dimensions - already handled by Tailwind classes */

	/* Override Leaflet styles if needed */
	:global(.leaflet-container) {
		font-family: inherit; /* Use the font from the rest of your app */
		background-color: #f8fafc; /* bg-slate-50 - Prevents white flash before tiles load */
	}

	:global(.leaflet-popup-content) {
		direction: rtl;
		text-align: right;
	}

	/* Improve marker visibility */
	:global(.leaflet-marker-icon) {
		filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.3));
	}
</style>
