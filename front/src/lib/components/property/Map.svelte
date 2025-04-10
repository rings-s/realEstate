<script>
	import { onMount } from 'svelte';
	import Map from '$lib/components/property/Map.svelte';

	// Default coordinates (e.g., Riyadh)
	let latitude = 24.774265;
	let longitude = 46.738586;
	let addressInfo = null;

	// Called when the Map component emits a locationchange event.
	function handleLocationChange(event) {
		// Destructure coordinates from the event detail.
		const { latitude: lat, longitude: lng } = event.detail;
		latitude = lat;
		longitude = lng;
		console.log(`New location from map: ${latitude}, ${longitude}`);
		fetchAddressInfo(latitude, longitude);
	}

	// Trigger browser geolocation to detect the user's location.
	function detectLocation() {
		if (navigator.geolocation) {
			navigator.geolocation.getCurrentPosition(
				(position) => {
					latitude = position.coords.latitude;
					longitude = position.coords.longitude;
					console.log(`Detected location: ${latitude}, ${longitude}`);
					fetchAddressInfo(latitude, longitude);
				},
				(error) => {
					console.error('Error detecting location:', error);
				}
			);
		} else {
			console.error('Geolocation is not supported by this browser.');
		}
	}

	// Fetch address information using Nominatim's reverse geocoding API.
	async function fetchAddressInfo(lat, lng) {
		try {
			if (!lat || !lng) {
				addressInfo = null;
				return;
			}
			// Set a loading state
			addressInfo = { loading: true };

			const response = await fetch(
				`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
			);

			if (!response.ok) {
				throw new Error('Failed to fetch address information');
			}

			const data = await response.json();

			// Update the address information state.
			addressInfo = {
				loading: false,
				display: data.display_name,
				details: data.address || {}
			};
		} catch (error) {
			console.error('Error fetching address:', error);
			addressInfo = { loading: false, error: 'Failed to fetch address information' };
		}
	}

	// Fetch initial address information when the component is mounted.
	onMount(() => {
		fetchAddressInfo(latitude, longitude);
	});
</script>

<div class="container">
	<h1>Real Estate Map Demo</h1>

	<!-- Detect Location Button -->
	<button on:click={detectLocation}> Detect My Location </button>

	<!-- Map Component -->
	<div class="map-container">
		<Map
			bind:latitude
			bind:longitude
			height="500px"
			width="100%"
			zoom={13}
			showMarker={true}
			draggableMarker={true}
			showLocationButton={true}
			on:locationchange={handleLocationChange}
		/>
	</div>

	<!-- Display Selected Coordinates -->
	<div class="info">
		<h2>Selected Coordinates</h2>
		<p>
			<strong>Latitude:</strong>
			{latitude} &nbsp; | &nbsp;
			<strong>Longitude:</strong>
			{longitude}
		</p>
	</div>

	<!-- Display Address Information -->
	<div class="info">
		<h2>Address Information</h2>
		{#if addressInfo}
			{#if addressInfo.loading}
				<p>Loading address information...</p>
			{:else if addressInfo.error}
				<p style="color: red;">{addressInfo.error}</p>
			{:else}
				<p>{addressInfo.display}</p>
				<ul>
					{#if addressInfo.details.city}
						<li><strong>City:</strong> {addressInfo.details.city}</li>
					{/if}
					{#if addressInfo.details.state}
						<li><strong>State:</strong> {addressInfo.details.state}</li>
					{/if}
					{#if addressInfo.details.country}
						<li><strong>Country:</strong> {addressInfo.details.country}</li>
					{/if}
					{#if addressInfo.details.postcode}
						<li><strong>Postal Code:</strong> {addressInfo.details.postcode}</li>
					{/if}
					{#if addressInfo.details.road}
						<li><strong>Street:</strong> {addressInfo.details.road}</li>
					{/if}
				</ul>
			{/if}
		{:else}
			<p>No address information available.</p>
		{/if}
	</div>
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 1rem;
	}
	.map-container {
		margin-bottom: 1rem;
	}
	button {
		padding: 0.5rem 1rem;
		margin-bottom: 1rem;
		font-size: 1rem;
	}
	.info {
		margin-top: 1rem;
	}
</style>
