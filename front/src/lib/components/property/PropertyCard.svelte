<!--
  AuctionCard Component
  Reusable card for displaying auction information with RTL support
-->
<script>
	import { MapPin, Clock, Coins, Users, Tag } from 'lucide-svelte';
	import { language, isRTL, textClass } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { formatCurrency, formatDateTime } from '$lib/utils/formatters';

	// Auction data passed from parent
	export let auction = {};
	export let compact = false; // Compact mode for smaller cards

	// Compute time remaining
	$: endDate = auction.end_date ? new Date(auction.end_date) : null;
	$: timeRemaining = getTimeRemaining(endDate);
	$: statusClass = getStatusClass(auction.status);

	// Calculate time remaining
	function getTimeRemaining(endDate) {
		if (!endDate) return { days: 0, hours: 0, minutes: 0, seconds: 0 };

		const now = new Date();
		if (endDate <= now) return { days: 0, hours: 0, minutes: 0, seconds: 0 };

		const diff = endDate - now;
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));
		const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
		const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
		const seconds = Math.floor((diff % (1000 * 60)) / 1000);

		return { days, hours, minutes, seconds };
	}

	// Get status class
	function getStatusClass(status) {
		switch (status) {
			case 'live':
				return 'variant-soft-success';
			case 'scheduled':
				return 'variant-soft-primary';
			case 'ended':
				return 'variant-soft-warning';
			case 'completed':
				return 'variant-soft-tertiary';
			case 'cancelled':
				return 'variant-soft-error';
			default:
				return 'variant-soft-surface';
		}
	}
</script>

<a
	href="/auctions/{auction.slug}"
	class="card overflow-hidden h-full transition-all duration-200 hover:shadow-lg"
>
	<!-- Auction Image -->
	<header class="relative">
		<img
			src={auction.cover_image_url ||
				auction.property_details?.cover_image_url ||
				'/placeholder-auction.jpg'}
			alt={auction.title}
			class="aspect-video w-full object-cover h-44"
		/>

		<!-- Type Badge -->
		<span class="badge variant-soft-primary text-xs absolute top-2 {$isRTL ? 'right-2' : 'left-2'}">
			{t(auction.auction_type, $language, { default: auction.auction_type })}
		</span>

		<!-- Status Badge -->
		<span class="badge {statusClass} text-xs absolute top-2 {$isRTL ? 'left-2' : 'right-2'}">
			{t(auction.status, $language, { default: auction.status })}
		</span>

		<!-- Current Bid -->
		<span
			class="badge variant-filled text-xs absolute bottom-2 {$isRTL
				? 'right-2'
				: 'left-2'} font-bold"
		>
			{formatCurrency(auction.current_bid || auction.starting_bid || 0, 'SAR')}
		</span>
	</header>

	<!-- Auction Details -->
	<div class="p-3">
		<!-- Title -->
		<h3 class="text-base font-semibold {$textClass} line-clamp-1">{auction.title}</h3>

		<!-- Location (if property details available) -->
		{#if auction.property_details || auction.related_property}
			<div class="flex items-center text-xs text-surface-600-300-token mt-1 mb-2">
				<MapPin class="w-3.5 h-3.5 {$isRTL ? 'ml-1' : 'mr-1'} flex-shrink-0" />
				<span class={$textClass}>
					{auction.property_details?.city || ''}
					{auction.property_details?.state ? `, ${auction.property_details.state}` : ''}
				</span>
			</div>
		{/if}

		<!-- Additional details if not compact -->
		{#if !compact}
			<div class="grid grid-cols-2 gap-2 mt-3 text-xs">
				<!-- Starting Bid -->
				<div>
					<div class="text-xs text-surface-600-300-token mb-0.5">
						{t('starting_bid', $language)}:
					</div>
					<div class="font-medium">{formatCurrency(auction.starting_bid || 0, 'SAR')}</div>
				</div>

				<!-- Minimum Increment -->
				<div>
					<div class="text-xs text-surface-600-300-token mb-0.5">
						{t('minimum_increment', $language)}:
					</div>
					<div class="font-medium">{formatCurrency(auction.minimum_increment || 0, 'SAR')}</div>
				</div>

				<!-- Start Date -->
				<div>
					<div class="text-xs text-surface-600-300-token mb-0.5">{t('start_date', $language)}:</div>
					<div class="font-medium">{formatDateTime(auction.start_date)}</div>
				</div>

				<!-- End Date -->
				<div>
					<div class="text-xs text-surface-600-300-token mb-0.5">{t('end_date', $language)}:</div>
					<div class="font-medium">{formatDateTime(auction.end_date)}</div>
				</div>
			</div>

			<!-- Stats (Bids, Views) -->
			<div class="flex justify-between mt-3 text-xs">
				<div class="flex items-center">
					<Tag class="w-3.5 h-3.5 {$isRTL ? 'ml-1' : 'mr-1'} flex-shrink-0" />
					<span>{auction.bid_count || 0} {t('bids', $language)}</span>
				</div>

				<div class="flex items-center">
					<Users class="w-3.5 h-3.5 {$isRTL ? 'ml-1' : 'mr-1'} flex-shrink-0" />
					<span>{auction.view_count || 0} {t('views', $language)}</span>
				</div>
			</div>
		{/if}

		<!-- Time Remaining (for live auctions) -->
		{#if auction.status === 'live' && endDate}
			<div class="mt-3 p-2 rounded bg-surface-200-700-token {$textClass}">
				<div class="flex items-center justify-between">
					<div class="flex items-center text-xs">
						<Clock class="w-3.5 h-3.5 {$isRTL ? 'ml-1' : 'mr-1'} flex-shrink-0" />
						<span>{t('time_remaining', $language)}:</span>
					</div>

					<div class="font-mono font-bold text-xs">
						{#if timeRemaining.days > 0}
							{timeRemaining.days}{t('d', $language)} {timeRemaining.hours}{t('h', $language)}
						{:else}
							{timeRemaining.hours.toString().padStart(2, '0')}:{timeRemaining.minutes
								.toString()
								.padStart(2, '0')}:{timeRemaining.seconds.toString().padStart(2, '0')}
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</a>
