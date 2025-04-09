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
				return 'variant-filled-success';
			case 'scheduled':
				return 'variant-filled-primary';
			case 'ended':
				return 'variant-filled-warning';
			case 'completed':
				return 'variant-filled-tertiary';
			case 'cancelled':
				return 'variant-filled-error';
			default:
				return 'variant-filled-surface';
		}
	}
</script>

<a
	href="/auctions/{auction.slug}"
	class="card card-hover overflow-hidden h-full transition-all duration-200 hover:shadow-xl"
>
	<!-- Auction Image -->
	<header class="relative">
		<img
			src={auction.cover_image_url ||
				auction.property_details?.cover_image_url ||
				'/placeholder-auction.jpg'}
			alt={auction.title}
			class="aspect-video w-full object-cover"
		/>

		<!-- Type Badge -->
		<span class="badge variant-filled-primary absolute top-2 {$isRTL ? 'right-2' : 'left-2'}">
			{t(auction.auction_type, $language, { default: auction.auction_type })}
		</span>

		<!-- Status Badge -->
		<span class="badge {statusClass} absolute top-2 {$isRTL ? 'left-2' : 'right-2'}">
			{t(auction.status, $language, { default: auction.status })}
		</span>
	</header>

	<!-- Auction Details -->
	<div class="p-4">
		<!-- Title and Current Bid -->
		<div class="flex justify-between items-start gap-2 mb-2">
			<h3 class="text-lg font-semibold {$textClass} flex-1">{auction.title}</h3>
			<div class="text-right">
				<div class="text-xs">{t('current_bid', $language)}:</div>
				<span class="text-lg font-bold text-primary-500 whitespace-nowrap">
					{formatCurrency(auction.current_bid || auction.starting_bid || 0, 'SAR')}
				</span>
			</div>
		</div>

		<!-- Location (if property details available) -->
		{#if auction.property_details || auction.related_property}
			<div class="flex items-center text-sm text-surface-600-300-token mb-3">
				<MapPin class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
				<span class={$textClass}>
					{auction.property_details?.city || ''}
					{auction.property_details?.state ? `, ${auction.property_details.state}` : ''}
				</span>
			</div>
		{/if}

		<!-- Additional details if not compact -->
		{#if !compact}
			<div class="grid grid-cols-2 gap-4 mt-4 text-sm">
				<!-- Starting Bid -->
				<div>
					<div class="text-xs text-surface-600-300-token">{t('starting_bid', $language)}:</div>
					<div class="font-semibold">{formatCurrency(auction.starting_bid || 0, 'SAR')}</div>
				</div>

				<!-- Minimum Increment -->
				<div>
					<div class="text-xs text-surface-600-300-token">{t('minimum_increment', $language)}:</div>
					<div class="font-semibold">{formatCurrency(auction.minimum_increment || 0, 'SAR')}</div>
				</div>

				<!-- Start Date -->
				<div>
					<div class="text-xs text-surface-600-300-token">{t('start_date', $language)}:</div>
					<div class="font-semibold">{formatDateTime(auction.start_date)}</div>
				</div>

				<!-- End Date -->
				<div>
					<div class="text-xs text-surface-600-300-token">{t('end_date', $language)}:</div>
					<div class="font-semibold">{formatDateTime(auction.end_date)}</div>
				</div>
			</div>

			<!-- Stats (Bids, Views) -->
			<div class="flex justify-between mt-4 text-sm">
				<div class="flex items-center">
					<Tag class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
					<span>{auction.bid_count || 0} {t('bids', $language)}</span>
				</div>

				<div class="flex items-center">
					<Users class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
					<span>{auction.view_count || 0} {t('views', $language)}</span>
				</div>
			</div>
		{/if}

		<!-- Time Remaining (for live auctions) -->
		{#if auction.status === 'live' && endDate}
			<div class="mt-4 p-2 rounded bg-surface-200 dark:bg-surface-700 {$textClass}">
				<div class="flex items-center justify-between">
					<div class="flex items-center text-sm">
						<Clock class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
						<span>{t('time_remaining', $language)}:</span>
					</div>

					<div class="font-mono font-bold">
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
