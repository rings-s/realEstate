<!-- src/lib/components/property/PropertyMap.svelte -->
<script>
	import { onMount, onDestroy } from 'svelte';

	export let latitude = 24.774265; // Default to Riyadh coordinates
	export let longitude = 46.738586;
	export let editable = false;
	export let onLocationChange = () => {};

	let mapContainer;
	let map;
	let marker;
	let loading = false;
	let error = '';

	onMount(async () => {
		try {
			// Wait for Leaflet script to load
			if (typeof L === 'undefined') {
				const script = document.createElement('script');
				script.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
				script.integrity =
					'sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==';
				script.crossorigin = '';
				document.head.appendChild(script);

				await new Promise((resolve) => (script.onload = resolve));
			}

			// Initialize map
			map = L.map(mapContainer).setView([latitude, longitude], 13);

			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution: '© OpenStreetMap contributors'
			}).addTo(map);

			// Add marker
			marker = L.marker([latitude, longitude], {
				draggable: editable
			}).addTo(map);

			if (editable) {
				// Update coordinates when marker is dragged
				marker.on('dragend', (e) => {
					const { lat, lng } = e.target.getLatLng();
					latitude = lat;
					longitude = lng;
					onLocationChange({ latitude: lat, longitude: lng });
				});

				// Update coordinates when map is clicked
				map.on('click', (e) => {
					const { lat, lng } = e.latlng;
					marker.setLatLng([lat, lng]);
					latitude = lat;
					longitude = lng;
					onLocationChange({ latitude: lat, longitude: lng });
				});
			}
		} catch (err) {
			error = 'Failed to load map';
			console.error(err);
		}
	});

	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});

	async function getCurrentLocation() {
		loading = true;
		error = '';

		try {
			const position = await new Promise((resolve, reject) => {
				navigator.geolocation.getCurrentPosition(resolve, reject);
			});

			const { latitude: lat, longitude: lng } = position.coords;
			map.setView([lat, lng], 15);
			marker.setLatLng([lat, lng]);
			latitude = lat;
			longitude = lng;
			onLocationChange({ latitude: lat, longitude: lng });
		} catch (err) {
			error = 'فشل في تحديد الموقع الحالي';
		} finally {
			loading = false;
		}
	}
</script>

<div class="space-y-4">
	{#if editable}
		<div class="flex gap-4">
			<button
				type="button"
				class="btn-secondary flex-1"
				on:click={getCurrentLocation}
				disabled={loading}
			>
				{#if loading}
					<i class="fas fa-spinner fa-spin ml-2"></i>
					جاري التحديد...
				{:else}
					<i class="fas fa-location-arrow ml-2"></i>
					تحديد موقعي الحالي
				{/if}
			</button>

			<div class="grid flex-1 grid-cols-2 gap-2">
				<input
					type="number"
					step="any"
					bind:value={latitude}
					on:change={() => marker?.setLatLng([latitude, longitude])}
					placeholder="خط العرض"
					class="input"
				/>
				<input
					type="number"
					step="any"
					bind:value={longitude}
					on:change={() => marker?.setLatLng([latitude, longitude])}
					placeholder="خط الطول"
					class="input"
				/>
			</div>
		</div>
	{/if}

	{#if error}
		<div class="rounded-lg bg-red-50 p-4 text-red-700">
			<i class="fas fa-exclamation-circle ml-2"></i>
			{error}
		</div>
	{/if}

	<div
		bind:this={mapContainer}
		class="h-[400px] w-full overflow-hidden rounded-lg border border-slate-200"
	></div>
</div>

<style>
	/* Ensure the map container has dimensions */
	div[bind\:this] {
		min-height: 400px;
		width: 100%;
	}

	/* Override Leaflet styles for better Arabic support */
	:global(.leaflet-container) {
		font-family: inherit;
	}

	:global(.leaflet-popup-content) {
		direction: rtl;
		text-align: right;
	}
</style>
