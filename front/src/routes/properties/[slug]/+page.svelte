<!-- src/routes/properties/[slug]/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { propertiesStore, currentProperty } from '$lib/stores/properties';
	import { isAuthenticated, hasRole, user } from '$lib/stores/auth';
	import { theme } from '$lib/stores/theme';
	import { uiStore } from '$lib/stores/ui';
	import PropertyDetails from '$lib/components/properties/PropertyDetails.svelte';
	import PropertyMap from '$lib/components/properties/PropertyMap.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { formatCurrency } from '$lib/utils/formatting';

	export let data; // SvelteKit data object containing the slug

	let isLoading = true;
	let error = null;

	// Fetch property data on mount using the by-slug endpoint from backend urls.py
	onMount(async () => {
		try {
			uiStore.startLoading('جاري تحميل بيانات العقار...');

			// Use the property service to call the retrieve_by_slug endpoint
			await propertiesStore.loadPropertyBySlug(data.params.slug);

			isLoading = false;
			uiStore.stopLoading();
		} catch (err) {
			error = err;
			isLoading = false;
			uiStore.stopLoading();

			// Show error toast
			uiStore.addToast('حدث خطأ أثناء تحميل بيانات العقار. يرجى المحاولة مرة أخرى.', 'error');
		}
	});

	// Handle auction creation - requires IsSellerPermission or IsAgentPermission on backend
	function handleCreateAuction() {
		// Navigate to create auction page with property pre-selected
		window.location.href = `/auctions/add?property=${$currentProperty.id}`;
	}

	// Check if current user is property owner - mimics the IsPropertyOwner permission
	$: isOwner = $currentProperty?.owner === $user?.id;

	// Check if user can create auction - reflects backend permission logic
	$: canCreateAuction = isOwner || $hasRole('agent') || $hasRole('admin');

	// Parse JSON fields - necessary because backend stores as strings
	$: propertyImages = $currentProperty?.images
		? typeof $currentProperty.images === 'string'
			? JSON.parse($currentProperty.images)
			: $currentProperty.images
		: [];

	$: propertyFeatures = $currentProperty?.features
		? typeof $currentProperty.features === 'string'
			? JSON.parse($currentProperty.features)
			: $currentProperty.features
		: [];

	$: propertyAmenities = $currentProperty?.amenities
		? typeof $currentProperty.amenities === 'string'
			? JSON.parse($currentProperty.amenities)
			: $currentProperty.amenities
		: [];

	// Safely parse location for the map
	$: propertyLocation = getLocationData($currentProperty);

	// Function to safely get location data for the map
	function getLocationData(property) {
		if (!property) return { lat: 24.7136, lng: 46.6753 }; // Default to Riyadh coordinates

		// Try to get from location_coordinates first
		if (property.location_coordinates) {
			return property.location_coordinates;
		}

		// Then try from location as JSON string
		if (property.location) {
			if (typeof property.location === 'string') {
				try {
					return JSON.parse(property.location);
				} catch (err) {
					console.error('Error parsing location JSON:', err);
				}
			} else if (typeof property.location === 'object') {
				return property.location;
			}
		}

		// Fallback to default coordinates
		return { lat: 24.7136, lng: 46.6753 }; // Riyadh coordinates
	}

	// Helper function to safely parse JSON with error handling
	function safeJsonParse(jsonString, defaultValue = {}) {
		if (!jsonString) return defaultValue;
		if (typeof jsonString !== 'string') return jsonString;

		try {
			return JSON.parse(jsonString);
		} catch (err) {
			console.error('Error parsing JSON:', err);
			return defaultValue;
		}
	}

	// Parse street details safely
	$: parsedStreetDetails = $currentProperty?.street_details
		? safeJsonParse($currentProperty.street_details, {})
		: {};
</script>

<svelte:head>
	<title>{$currentProperty?.title || 'تفاصيل العقار'} | نظام المزادات العقارية</title>
	<meta name="description" content={$currentProperty?.description || 'تفاصيل العقار'} />
</svelte:head>

<div class="container mx-auto px-4 py-8">
	{#if isLoading}
		<div class="flex min-h-[50vh] items-center justify-center">
			<Loader size="lg" />
		</div>
	{:else if error}
		<Alert
			type="error"
			title="خطأ في تحميل بيانات العقار"
			message={error.message || 'حدث خطأ أثناء تحميل بيانات العقار. يرجى المحاولة مرة أخرى.'}
		/>
	{:else if $currentProperty}
		<!-- Property Header with Actions -->
		<div class="mb-8">
			<div class="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900 dark:text-white">{$currentProperty.title}</h1>
					<p class="mt-2 text-gray-600 dark:text-gray-300">
						{$currentProperty.district}, {$currentProperty.city}
					</p>
				</div>

				<div class="flex flex-col items-start gap-2 sm:items-end">
					<div class="text-2xl font-bold text-green-600 dark:text-green-400">
						{formatCurrency($currentProperty.estimated_value, 'SAR')}
					</div>

					<div class="flex flex-wrap gap-2">
						<!-- Edit button - requires IsPropertyOwner permission -->
						{#if isOwner}
							<Button
								href={`/properties/edit/${$currentProperty.slug}`}
								variant="outline"
								color="primary"
							>
								تعديل
							</Button>
						{/if}

						<!-- Create auction button - requires proper permissions -->
						{#if canCreateAuction && !$currentProperty.has_auction}
							<Button on:click={handleCreateAuction} variant="solid" color="primary">
								إنشاء مزاد
							</Button>
						{/if}

						<!-- View auction button if exists -->
						{#if $currentProperty.has_auction}
							<Button
								href={`/auctions/${$currentProperty.active_auction_id}`}
								variant="solid"
								color="accent"
							>
								عرض المزاد
							</Button>
						{/if}
					</div>
				</div>
			</div>

			<!-- Status Badges -->
			<div class="mb-4 flex flex-wrap gap-3">
				<!-- Property status -->
				<span
					class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium
					{$currentProperty.status === 'active'
						? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
						: $currentProperty.status === 'sold'
							? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
							: $currentProperty.status === 'pending_approval'
								? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
								: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'}"
				>
					{$currentProperty.status === 'active'
						? 'نشط'
						: $currentProperty.status === 'sold'
							? 'مباع'
							: $currentProperty.status === 'pending_approval'
								? 'قيد الموافقة'
								: $currentProperty.status === 'under_contract'
									? 'تحت التعاقد'
									: $currentProperty.status === 'inactive'
										? 'غير نشط'
										: $currentProperty.status === 'rejected'
											? 'مرفوض'
											: $currentProperty.status}
				</span>

				<!-- Property type -->
				<span
					class="inline-flex items-center rounded-full bg-purple-100 px-3 py-1 text-sm font-medium text-purple-800 dark:bg-purple-900 dark:text-purple-200"
				>
					{$currentProperty.property_type === 'apartment'
						? 'شقة'
						: $currentProperty.property_type === 'villa'
							? 'فيلا'
							: $currentProperty.property_type === 'land'
								? 'أرض'
								: $currentProperty.property_type === 'commercial'
									? 'تجاري'
									: $currentProperty.property_type === 'building'
										? 'مبنى'
										: $currentProperty.property_type === 'farm'
											? 'مزرعة'
											: $currentProperty.property_type === 'industrial'
												? 'صناعي'
												: $currentProperty.property_type === 'office'
													? 'مكتب'
													: $currentProperty.property_type === 'retail'
														? 'محل تجاري'
														: $currentProperty.property_type === 'mixed_use'
															? 'متعدد الاستخدامات'
															: $currentProperty.property_type}
				</span>

				<!-- Verification badge -->
				{#if $currentProperty.is_verified}
					<span
						class="inline-flex items-center rounded-full bg-teal-100 px-3 py-1 text-sm font-medium text-teal-800 dark:bg-teal-900 dark:text-teal-200"
					>
						موثق
					</span>
				{/if}
			</div>
		</div>

		<!-- Main Property Details Section -->
		<PropertyDetails
			property={{
				...$currentProperty,
				images: propertyImages,
				features: propertyFeatures,
				amenities: propertyAmenities
			}}
			loading={false}
		/>

		<!-- Property Location Map -->
		<div class="mt-8 rounded-lg bg-white p-6 shadow dark:bg-gray-800">
			<h2 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">الموقع</h2>
			<div class="h-96 overflow-hidden rounded-lg">
				<PropertyMap
					location={propertyLocation}
					height="400px"
					interactive={false}
					showControls={true}
				/>
			</div>

			<div class="mt-4 text-gray-700 dark:text-gray-300">
				<p>
					<strong>العنوان:</strong>
					{$currentProperty.address || `${$currentProperty.district}، ${$currentProperty.city}`}
				</p>

				<!-- Street details from JSON field -->
				{#if $currentProperty.street_details}
					{#each Object.entries(parsedStreetDetails) as [key, value]}
						<p>
							<strong
								>{key === 'street_width'
									? 'عرض الشارع'
									: key === 'street_type'
										? 'نوع الشارع'
										: key}:</strong
							>
							{value}
						</p>
					{/each}
				{/if}
			</div>
		</div>

		<!-- Documents Section - based on backend structure -->
		{#if $currentProperty.documents_count > 0}
			<div class="mt-8 rounded-lg bg-white p-6 shadow dark:bg-gray-800">
				<h2 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
					المستندات
					<span class="mr-2 text-base font-normal text-gray-500 dark:text-gray-400"
						>({$currentProperty.documents_count})</span
					>
				</h2>

				{#if $isAuthenticated}
					<Button
						href={`/documents?property=${$currentProperty.id}`}
						variant="outline"
						color="primary"
					>
						عرض المستندات
					</Button>
				{:else}
					<p class="mb-4 text-gray-600 dark:text-gray-400">
						يحتوي هذا العقار على مستندات متاحة. يرجى
						<a href="/login" class="text-blue-600 hover:underline dark:text-blue-400">
							تسجيل الدخول
						</a>
						لعرض المستندات.
					</p>
				{/if}
			</div>
		{/if}
	{:else}
		<Alert
			type="info"
			title="العقار غير موجود"
			message="لم يتم العثور على العقار المطلوب. يرجى التحقق من الرابط والمحاولة مرة أخرى."
		/>
	{/if}
</div>
