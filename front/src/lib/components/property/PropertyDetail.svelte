<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { formatCurrency, formatDate } from '$lib/config/constants';
	import { onMount } from 'svelte';
	import {
		Home,
		MapPin,
		Calendar,
		DollarSign,
		Ruler,
		Bed,
		Bath,
		Car,
		CheckCircle,
		User,
		Heart,
		Share2,
		Flag
	} from 'lucide-svelte';
	import PropertyImages from './PropertyImages.svelte';
	import Avatar from '../common/Avatar.svelte';
	import Alert from '../common/Alert.svelte';
	import Map from '../common/Map.svelte';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Property data
	export let property = null;
	// Loading state
	export let loading = false;
	// Error state
	export let error = null;
	// Show property info only (without actions, contact, etc.)
	export let minimal = false;
	// User can favorite the property
	export let canFavorite = true;
	// Property is favorited by current user
	export let isFavorited = false;
	// User can contact the owner
	export let canContact = true;
	// Current user can edit the property
	export let canEdit = false;
	// Show auction info if property is in auction
	export let showAuction = true;
	// Related auction data
	export let auction = null;

	// Local state
	let selectedTab = 'details';
	let mapLoaded = false;

	// Property coordinates from location data
	$: latitude = property?.location?.latitude || null;
	$: longitude = property?.location?.longitude || null;

	// Whether we have valid coordinates for the map
	$: hasValidCoordinates = latitude && longitude;

	// Tabs for property information
	const tabs = [
		{ id: 'details', label: 'details' },
		{ id: 'features', label: 'features' },
		{ id: 'location', label: 'location' }
	];

	// Handle tab change
	function changeTab(tabId) {
		selectedTab = tabId;

		// Load map if location tab is selected
		if (tabId === 'location') {
			mapLoaded = true;
		}
	}

	// Handle favorite action
	function toggleFavorite() {
		dispatch('favorite', { property, isFavorited: !isFavorited });
	}

	// Handle contact owner
	function contactOwner() {
		dispatch('contact', { property, owner: property.owner_details });
	}

	// Handle report property
	function reportProperty() {
		dispatch('report', { property });
	}

	// Handle share property
	function shareProperty() {
		if (navigator.share) {
			navigator
				.share({
					title: property.title,
					text: property.description?.substring(0, 100),
					url: window.location.href
				})
				.catch((err) => {
					console.error('Error sharing:', err);
				});
		} else {
			// Fallback copy to clipboard
			navigator.clipboard
				.writeText(window.location.href)
				.then(() => {
					dispatch('notification', {
						message: t('link_copied', $language, { default: 'تم نسخ الرابط إلى الحافظة' }),
						type: 'success'
					});
				})
				.catch((err) => {
					console.error('Error copying link:', err);
				});
		}
	}

	// Handle view auction
	function viewAuction() {
		if (auction) {
			dispatch('viewAuction', { auction });
		}
	}

	// Handle location change from Map component
	function handleLocationChange(event) {
		const { latitude: newLat, longitude: newLng } = event.detail;
		console.log(`Location updated: ${newLat}, ${newLng}`);
		// In a real application, you might want to update the property or take other actions
	}

	// Format features as array
	$: features = Array.isArray(property?.features)
		? property.features
		: Object.entries(property?.features || {}).map(([key, value]) => value);

	// Format amenities as array
	$: amenities = Array.isArray(property?.amenities)
		? property.amenities
		: Object.entries(property?.amenities || {}).map(([key, value]) => value);

	onMount(() => {
		// No need to manually load map, we'll use the Map component
	});
</script>

{#if loading}
	<div class="card p-4">
		<div class="placeholder animate-pulse w-full h-80 rounded-lg mb-4"></div>
		<div class="placeholder animate-pulse w-2/3 h-8 mb-4"></div>
		<div class="placeholder animate-pulse w-full h-32 mb-4"></div>
		<div class="flex flex-wrap gap-3">
			<div class="placeholder animate-pulse w-24 h-6"></div>
			<div class="placeholder animate-pulse w-32 h-6"></div>
			<div class="placeholder animate-pulse w-28 h-6"></div>
		</div>
	</div>
{:else if error}
	<Alert type="error" message={error} />
{:else if property}
	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<!-- Left column: property images and details -->
		<div class="lg:col-span-2">
			<!-- Property Images Gallery -->
			<PropertyImages
				images={property.images || []}
				coverImage={property.cover_image_url}
				altText={property.title}
			/>

			<!-- Property Info Tabs -->
			<div class="mt-6">
				<div class="tabs">
					{#each tabs as tab}
						<button
							class="tab {selectedTab === tab.id ? 'variant-filled-primary' : 'variant-ghost'}"
							on:click={() => changeTab(tab.id)}
							aria-selected={selectedTab === tab.id}
						>
							{t(tab.label, $language, { default: tab.id })}
						</button>
					{/each}
				</div>

				<div
					class="p-4 border border-surface-300-600-token rounded-b-lg {$isRTL
						? 'text-right'
						: 'text-left'} bg-surface-100-800-token"
				>
					{#if selectedTab === 'details'}
						<!-- Property Details Tab -->
						<div class="space-y-6">
							<h2 class="h3">{t('property_details', $language, { default: 'تفاصيل العقار' })}</h2>

							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<!-- Property Specs -->
								<div class="space-y-3">
									<div class="flex items-center gap-2">
										<Home class="w-5 h-5 text-primary-500" />
										<span class="font-medium"
											>{t('property_type', $language, { default: 'نوع العقار' })}:</span
										>
										<span>{property.property_type_display}</span>
									</div>

									<div class="flex items-center gap-2">
										<Ruler class="w-5 h-5 text-primary-500" />
										<span class="font-medium">{t('size', $language, { default: 'المساحة' })}:</span>
										<span>{property.size_sqm} {t('sqm', $language, { default: 'متر مربع' })}</span>
									</div>

									{#if property.bedrooms !== null && property.bedrooms !== undefined}
										<div class="flex items-center gap-2">
											<Bed class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('bedrooms', $language, { default: 'غرف النوم' })}:</span
											>
											<span>{property.bedrooms}</span>
										</div>
									{/if}

									{#if property.bathrooms !== null && property.bathrooms !== undefined}
										<div class="flex items-center gap-2">
											<Bath class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('bathrooms', $language, { default: 'الحمامات' })}:</span
											>
											<span>{property.bathrooms}</span>
										</div>
									{/if}

									{#if property.parking_spaces !== null && property.parking_spaces !== undefined}
										<div class="flex items-center gap-2">
											<Car class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('parking', $language, { default: 'مواقف السيارات' })}:</span
											>
											<span>{property.parking_spaces}</span>
										</div>
									{/if}

									{#if property.year_built !== null && property.year_built !== undefined}
										<div class="flex items-center gap-2">
											<Calendar class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('year_built', $language, { default: 'سنة البناء' })}:</span
											>
											<span>{property.year_built}</span>
										</div>
									{/if}
								</div>

								<!-- Financial and Status Info -->
								<div class="space-y-3">
									<div class="flex items-center gap-2">
										<DollarSign class="w-5 h-5 text-primary-500" />
										<span class="font-medium"
											>{t('market_value', $language, { default: 'القيمة السوقية' })}:</span
										>
										<span>{formatCurrency(property.market_value)}</span>
									</div>

									{#if property.minimum_bid !== null && property.minimum_bid !== undefined}
										<div class="flex items-center gap-2">
											<DollarSign class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('minimum_bid', $language, { default: 'الحد الأدنى للمزايدة' })}:</span
											>
											<span>{formatCurrency(property.minimum_bid)}</span>
										</div>
									{/if}

									<div class="flex items-center gap-2">
										<CheckCircle class="w-5 h-5 text-primary-500" />
										<span class="font-medium">{t('status', $language, { default: 'الحالة' })}:</span
										>
										<span
											class="badge {property.status === 'available'
												? 'variant-filled-success'
												: property.status === 'auction'
													? 'variant-filled-warning'
													: 'variant-filled-surface'}"
										>
											{property.status_display}
										</span>
									</div>

									<div class="flex items-center gap-2">
										<MapPin class="w-5 h-5 text-primary-500" />
										<span class="font-medium"
											>{t('location', $language, { default: 'الموقع' })}:</span
										>
										<span>{property.city}, {property.state}</span>
									</div>

									{#if property.owner_details}
										<div class="flex items-center gap-2">
											<User class="w-5 h-5 text-primary-500" />
											<span class="font-medium"
												>{t('owner', $language, { default: 'المالك' })}:</span
											>
											<span
												>{property.owner_details.full_name ||
													`${property.owner_details.first_name} ${property.owner_details.last_name}`}</span
											>
										</div>
									{/if}
								</div>
							</div>

							<!-- Description -->
							<div>
								<h3 class="h4 mb-2">{t('description', $language, { default: 'الوصف' })}</h3>
								<p class="whitespace-pre-line">{property.description}</p>
							</div>

							<!-- Additional Details -->
							{#if property.specifications && Object.keys(property.specifications).length > 0}
								<div>
									<h3 class="h4 mb-2">
										{t('specifications', $language, { default: 'المواصفات' })}
									</h3>
									<ul class="list-disc {$isRTL ? 'pr-6' : 'pl-6'} space-y-1">
										{#each Object.entries(property.specifications) as [key, value]}
											<li><strong>{key}:</strong> {value}</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					{:else if selectedTab === 'features'}
						<!-- Features and Amenities Tab -->
						<div class="space-y-6">
							<!-- Features -->
							<div>
								<h2 class="h3 mb-4">{t('features', $language, { default: 'المميزات' })}</h2>
								{#if features.length > 0}
									<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
										{#each features as feature}
											<div class="flex items-center gap-2">
												<CheckCircle class="w-5 h-5 text-success-500" />
												<span>{feature}</span>
											</div>
										{/each}
									</div>
								{:else}
									<p class="text-surface-600-300-token">
										{t('no_features', $language, { default: 'لا توجد ميزات محددة' })}
									</p>
								{/if}
							</div>

							<!-- Amenities -->
							<div>
								<h3 class="h3 mb-4">{t('amenities', $language, { default: 'المرافق' })}</h3>
								{#if amenities.length > 0}
									<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
										{#each amenities as amenity}
											<div class="flex items-center gap-2">
												<CheckCircle class="w-5 h-5 text-success-500" />
												<span>{amenity}</span>
											</div>
										{/each}
									</div>
								{:else}
									<p class="text-surface-600-300-token">
										{t('no_amenities', $language, { default: 'لا توجد مرافق محددة' })}
									</p>
								{/if}
							</div>

							<!-- Room Details -->
							{#if property.rooms && property.rooms.length > 0}
								<div>
									<h3 class="h3 mb-4">{t('rooms', $language, { default: 'الغرف' })}</h3>
									<div class="overflow-x-auto">
										<table class="table">
											<thead>
												<tr>
													<th>{t('room_type', $language, { default: 'نوع الغرفة' })}</th>
													<th>{t('size', $language, { default: 'المساحة' })}</th>
													<th>{t('features', $language, { default: 'المميزات' })}</th>
												</tr>
											</thead>
											<tbody>
												{#each property.rooms as room}
													<tr>
														<td>{room.type}</td>
														<td>{room.size} {t('sqm', $language, { default: 'متر مربع' })}</td>
														<td>
															{#if room.features && room.features.length > 0}
																<div class="flex flex-wrap gap-1">
																	{#each room.features as feature}
																		<span class="badge variant-soft">{feature}</span>
																	{/each}
																</div>
															{:else}
																-
															{/if}
														</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							{/if}
						</div>
					{:else if selectedTab === 'location'}
						<!-- Location Tab -->
						<div class="space-y-4">
							<h2 class="h3">{t('location', $language, { default: 'الموقع' })}</h2>

							<!-- Location Details -->
							<div class="mb-4">
								<div class="flex items-start gap-2">
									<MapPin class="w-5 h-5 text-primary-500 mt-1" />
									<div>
										<p class="font-medium">{property.address}</p>
										<p>{property.city}, {property.state} {property.postal_code}</p>
										<p>{property.country}</p>
									</div>
								</div>
							</div>

							<!-- Map Component -->
							{#if mapLoaded}
								{#if hasValidCoordinates}
									<Map
										{latitude}
										{longitude}
										height="400px"
										width="100%"
										showMarker={true}
										showLocationButton={false}
										interactive={true}
										markerPopup={property.title}
										on:locationchange={handleLocationChange}
									/>
								{:else}
									<div
										class="w-full h-96 bg-surface-200-700-token rounded-lg flex items-center justify-center"
									>
										<p class="text-surface-600-300-token">
											{t('no_location_data', $language, { default: 'لا توجد بيانات موقع متاحة' })}
										</p>
									</div>
								{/if}
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Right column: property actions, contact, and related info -->
		{#if !minimal}
			<div class="lg:col-span-1">
				<!-- Property Actions Card -->
				<div class="card p-4 mb-6">
					<h3 class="h3 mb-4">{t('property_actions', $language, { default: 'إجراءات العقار' })}</h3>

					<div class="space-y-3">
						{#if property.status === 'auction' && auction && showAuction}
							<!-- Auction Info -->
							<div class="card variant-soft-warning p-3">
								<h4 class="font-medium">{t('in_auction', $language, { default: 'في المزاد' })}</h4>
								<p class="mb-2 text-sm">
									{t('current_bid', $language, { default: 'المزايدة الحالية' })}: {formatCurrency(
										auction.current_bid || auction.starting_bid
									)}
								</p>
								<p class="text-sm mb-4">
									{t('ends_at', $language, { default: 'ينتهي في' })}: {formatDate(auction.end_date)}
								</p>
								<button class="btn variant-filled-warning w-full" on:click={viewAuction}>
									{t('view_auction', $language, { default: 'عرض المزاد' })}
								</button>
							</div>
						{/if}

						<!-- Action Buttons -->
						<div class="grid grid-cols-2 gap-2">
							{#if canFavorite}
								<button
									class="btn {isFavorited ? 'variant-soft-primary' : 'variant-ghost'}"
									on:click={toggleFavorite}
								>
									<Heart
										class="w-5 h-5 {isFavorited ? 'fill-current' : ''} {$isRTL ? 'ml-2' : 'mr-2'}"
									/>
									{isFavorited
										? t('favorited', $language, { default: 'في المفضلة' })
										: t('favorite', $language, { default: 'المفضلة' })}
								</button>
							{/if}

							<button class="btn variant-ghost" on:click={shareProperty}>
								<Share2 class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
								{t('share', $language, { default: 'مشاركة' })}
							</button>
						</div>

						{#if canContact && property.owner_details}
							<button class="btn variant-filled-primary w-full" on:click={contactOwner}>
								{t('contact_owner', $language, { default: 'التواصل مع المالك' })}
							</button>
						{/if}

						{#if canEdit}
							<a href="/properties/{property.id}/edit" class="btn variant-ghost w-full">
								{t('edit_property', $language, { default: 'تعديل العقار' })}
							</a>
						{/if}

						<button class="btn variant-ghost-error w-full" on:click={reportProperty}>
							<Flag class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							{t('report_property', $language, { default: 'الإبلاغ عن مشكلة' })}
						</button>
					</div>
				</div>

				<!-- Owner Info Card -->
				{#if property.owner_details && !minimal}
					<div class="card p-4 mb-6">
						<h3 class="h3 mb-4">{t('owner_info', $language, { default: 'معلومات المالك' })}</h3>

						<div class="flex items-center gap-4 mb-4">
							<Avatar user={property.owner_details} size="lg" />
							<div>
								<p class="font-medium">
									{property.owner_details.full_name ||
										`${property.owner_details.first_name} ${property.owner_details.last_name}`}
								</p>
								{#if property.owner_details.primary_role}
									<span class="badge variant-soft-primary"
										>{t(property.owner_details.primary_role.code, $language)}</span
									>
								{/if}
							</div>
						</div>

						{#if canContact}
							<button class="btn variant-filled-primary w-full" on:click={contactOwner}>
								{t('contact_owner', $language, { default: 'التواصل مع المالك' })}
							</button>
						{/if}
					</div>
				{/if}

				<!-- Property Details Card (For Mobile Quick View) -->
				<div class="card p-4 lg:hidden">
					<h3 class="h3 mb-4">{t('quick_details', $language, { default: 'تفاصيل سريعة' })}</h3>

					<div class="grid grid-cols-2 gap-4">
						<div class="flex flex-col items-center p-2 rounded-token bg-surface-hover-token">
							<Ruler class="w-6 h-6 text-primary-500 mb-1" />
							<span class="text-xs text-surface-600-300-token"
								>{t('size', $language, { default: 'المساحة' })}</span
							>
							<span class="font-medium"
								>{property.size_sqm} {t('sqm', $language, { default: 'متر مربع' })}</span
							>
						</div>

						{#if property.bedrooms !== null && property.bedrooms !== undefined}
							<div class="flex flex-col items-center p-2 rounded-token bg-surface-hover-token">
								<Bed class="w-6 h-6 text-primary-500 mb-1" />
								<span class="text-xs text-surface-600-300-token"
									>{t('bedrooms', $language, { default: 'غرف النوم' })}</span
								>
								<span class="font-medium">{property.bedrooms}</span>
							</div>
						{/if}

						{#if property.bathrooms !== null && property.bathrooms !== undefined}
							<div class="flex flex-col items-center p-2 rounded-token bg-surface-hover-token">
								<Bath class="w-6 h-6 text-primary-500 mb-1" />
								<span class="text-xs text-surface-600-300-token"
									>{t('bathrooms', $language, { default: 'الحمامات' })}</span
								>
								<span class="font-medium">{property.bathrooms}</span>
							</div>
						{/if}

						<div class="flex flex-col items-center p-2 rounded-token bg-surface-hover-token">
							<DollarSign class="w-6 h-6 text-primary-500 mb-1" />
							<span class="text-xs text-surface-600-300-token"
								>{t('price', $language, { default: 'السعر' })}</span
							>
							<span class="font-medium">{formatCurrency(property.market_value)}</span>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
{:else}
	<Alert
		type="warning"
		message={t('no_property_found', $language, { default: 'لم يتم العثور على العقار' })}
	/>
{/if}
