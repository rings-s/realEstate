<!--
  PropertyCard Component
  Reusable card for displaying property information with RTL support
-->
<script>
	import { MapPin, Home, Bed, Bath, Car } from 'lucide-svelte';
	import { language, isRTL, textClass } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { formatCurrency } from '$lib/utils/formatters';

	// Property data passed from parent
	export let property = {};
	export let compact = false; // Compact mode for smaller cards
</script>

<a
	href="/properties/{property.slug}"
	class="card card-hover overflow-hidden h-full transition-all duration-200 hover:shadow-xl"
>
	<!-- Property Image -->
	<header class="relative">
		<img
			src={property.cover_image_url || '/placeholder-property.jpg'}
			alt={property.title}
			class="aspect-video w-full object-cover"
		/>

		<!-- Type Badge -->
		<span class="badge variant-filled-primary absolute top-2 {$isRTL ? 'right-2' : 'left-2'}">
			{t(property.property_type, $language)}
		</span>

		<!-- Featured Badge (if applicable) -->
		{#if property.is_featured}
			<span class="badge variant-filled-secondary absolute top-2 {$isRTL ? 'left-2' : 'right-2'}">
				{t('featured', $language)}
			</span>
		{/if}
	</header>

	<!-- Property Details -->
	<div class="p-4">
		<!-- Title and Price -->
		<div class="flex justify-between items-start gap-2 mb-2">
			<h3 class="text-lg font-semibold {$textClass} flex-1">{property.title}</h3>
			<span class="text-lg font-bold text-primary-500 whitespace-nowrap">
				{formatCurrency(property.market_value || property.minimum_bid || 0, 'SAR')}
			</span>
		</div>

		<!-- Location -->
		<div class="flex items-center text-sm text-surface-600-300-token mb-3">
			<MapPin class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
			<span class={$textClass}>{property.city}{property.state ? `, ${property.state}` : ''}</span>
		</div>

		<!-- Property details if not compact -->
		{#if !compact}
			<div class="flex flex-wrap justify-between mt-4 gap-y-2 text-sm">
				<!-- Size -->
				<div class="flex items-center {$isRTL ? 'ml-3' : 'mr-3'}">
					<Home class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
					<span>{property.size_sqm || 0} {t('sqm', $language)}</span>
				</div>

				<!-- Bedrooms -->
				{#if property.bedrooms !== null && property.bedrooms !== undefined}
					<div class="flex items-center {$isRTL ? 'ml-3' : 'mr-3'}">
						<Bed class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
						<span>{property.bedrooms} {t('bedrooms', $language)}</span>
					</div>
				{/if}

				<!-- Bathrooms -->
				{#if property.bathrooms !== null && property.bathrooms !== undefined}
					<div class="flex items-center {$isRTL ? 'ml-3' : 'mr-3'}">
						<Bath class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
						<span>{property.bathrooms} {t('bathrooms', $language)}</span>
					</div>
				{/if}

				<!-- Parking -->
				{#if property.parking_spaces !== null && property.parking_spaces !== undefined}
					<div class="flex items-center">
						<Car class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
						<span>{property.parking_spaces} {t('parking', $language)}</span>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Status Badge -->
		<div class="mt-4 flex {$isRTL ? 'justify-start' : 'justify-end'}">
			{#if property.status === 'available'}
				<span class="badge variant-soft-success">{t('available', $language)}</span>
			{:else if property.status === 'under_contract'}
				<span class="badge variant-soft-warning">{t('under_contract', $language)}</span>
			{:else if property.status === 'sold'}
				<span class="badge variant-soft-error">{t('sold', $language)}</span>
			{:else if property.status === 'auction'}
				<span class="badge variant-soft-primary">{t('in_auction', $language)}</span>
			{:else}
				<span class="badge variant-soft-surface"
					>{t(property.status, $language, { default: property.status })}</span
				>
			{/if}
		</div>
	</div>
</a>
