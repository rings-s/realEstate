<script>
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import AuctionTimer from './AuctionTimer.svelte';

	// Props
	export let auction;
	export let compact = false;
	export let showActions = true;

	// State
	let timeLeft = '';
	let isActive = false;
	let intervalId;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Format price with thousand separator
	function formatPrice(price) {
		return price?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
	}

	// Get auction status display name
	function getStatusDisplay(status) {
		switch (status) {
			case 'draft':
				return 'مسودة';
			case 'pending':
				return 'قيد الانتظار';
			case 'active':
				return 'مفتوح';
			case 'extended':
				return 'ممدد';
			case 'closed':
				return 'مغلق';
			case 'sold':
				return 'مُباع';
			case 'cancelled':
				return 'ملغي';
			default:
				return status || '';
		}
	}

	// Get status color class
	function getStatusColorClass(status) {
		switch (status) {
			case 'active':
			case 'extended':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
			case 'sold':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
			case 'closed':
				return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
			case 'pending':
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
			case 'cancelled':
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
			case 'draft':
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	// Format date
	function formatDate(dateString) {
		if (!dateString) return '';
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('ar-SA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(date);
	}

	// Handle auction click
	function handleAuctionClick() {
		if (auction.slug) {
			dispatch('select', { auction });
		}
	}

	// Place bid handler
	function handlePlaceBid(event) {
		event.stopPropagation();
		dispatch('bid', { auction });
	}

	// View details handler
	function handleViewDetails(event) {
		event.stopPropagation();
		dispatch('view', { auction });
	}

	// Calculate active state and time left on mount
	onMount(() => {
		updateAuctionStatus();

		// Update auction status every minute
		intervalId = setInterval(updateAuctionStatus, 60000);
	});

	onDestroy(() => {
		if (intervalId) clearInterval(intervalId);
	});

	function updateAuctionStatus() {
		const now = new Date();
		const startDate = new Date(auction.start_date);
		const endDate = new Date(auction.end_date);

		isActive = now >= startDate && now <= endDate;
	}

	// Get main image URL
	$: mainImage =
		auction.featured_image_url ||
		(auction.images &&
			(typeof auction.images === 'string'
				? JSON.parse(auction.images)[0]?.path
				: auction.images[0]?.path)) ||
		auction.related_property?.main_image_url ||
		'/images/placeholder-auction.jpg';

	// Get property title
	$: propertyTitle = auction.related_property?.title || '';

	// Check if auction is active
	$: isActiveAuction = auction.status === 'active' || auction.status === 'extended';
</script>

<div
	class="flex h-full flex-col overflow-hidden rounded-lg bg-white shadow-md transition-shadow duration-300 hover:shadow-lg dark:bg-gray-800"
	on:click={handleAuctionClick}
	on:keydown={(e) => e.key === 'Enter' && handleAuctionClick()}
	role="button"
	tabindex="0"
>
	<!-- Auction Image -->
	<div class="relative h-48 overflow-hidden">
		<img
			src={mainImage}
			alt={auction.title}
			class="h-full w-full object-cover transition-transform duration-500 hover:scale-110"
		/>

		<!-- Auction Status Badge -->
		<div
			class="absolute top-2 right-2 rounded px-2 py-1 text-xs font-semibold {getStatusColorClass(
				auction.status
			)}"
		>
			{getStatusDisplay(auction.status)}
		</div>

		<!-- Auction Type Badge -->
		<div class="bg-opacity-50 absolute top-2 left-2 rounded bg-black px-2 py-1 text-xs text-white">
			{auction.auction_type === 'public'
				? 'مزاد عام'
				: auction.auction_type === 'private'
					? 'مزاد خاص'
					: auction.auction_type === 'online'
						? 'مزاد إلكتروني'
						: auction.auction_type === 'onsite'
							? 'مزاد حضوري'
							: auction.auction_type === 'hybrid'
								? 'مزاد مختلط'
								: auction.auction_type}
		</div>

		<!-- Featured Badge -->
		{#if auction.is_featured}
			<div
				class="absolute right-2 bottom-2 rounded-full bg-amber-500 px-2 py-1 text-xs font-bold text-white"
			>
				مميز
			</div>
		{/if}
	</div>

	<!-- Auction Info -->
	<div class="flex flex-1 flex-col p-4">
		<!-- Title -->
		<h3 class="mb-1 line-clamp-1 text-lg font-semibold text-gray-900 dark:text-white">
			{auction.title}
		</h3>

		<!-- Property Reference -->
		{#if propertyTitle}
			<p class="mb-2 text-sm text-gray-600 dark:text-gray-400">
				العقار: {propertyTitle}
			</p>
		{/if}

		<!-- Current Bid -->
		<div class="mb-3 flex items-start justify-between">
			<span class="text-sm text-gray-600 dark:text-gray-400">المزايدة الحالية</span>
			<span class="font-bold text-green-600 dark:text-green-400"
				>{formatPrice(auction.current_bid || auction.starting_price)} ريال</span
			>
		</div>

		<!-- Starting Price -->
		<div class="mb-3 flex items-start justify-between">
			<span class="text-sm text-gray-600 dark:text-gray-400">سعر البداية</span>
			<span class="text-gray-700 dark:text-gray-300"
				>{formatPrice(auction.starting_price)} ريال</span
			>
		</div>

		<!-- Reserve Price (if applicable) -->
		{#if auction.reserve_price && !compact}
			<div class="mb-3 flex items-start justify-between">
				<span class="text-sm text-gray-600 dark:text-gray-400">السعر الاحتياطي</span>
				<span class="text-gray-700 dark:text-gray-300"
					>{formatPrice(auction.reserve_price)} ريال</span
				>
			</div>
		{/if}

		<!-- Bid Count -->
		{#if auction.bid_count !== undefined || auction.bids?.length !== undefined}
			<div class="mb-3 flex items-start justify-between">
				<span class="text-sm text-gray-600 dark:text-gray-400">عدد المزايدات</span>
				<span class="text-gray-700 dark:text-gray-300">
					{auction.bid_count !== undefined ? auction.bid_count : auction.bids?.length || 0}
				</span>
			</div>
		{/if}

		<!-- Timer section -->
		{#if !compact}
			<div class="mt-auto border-t border-gray-200 pt-3 dark:border-gray-700">
				{#if isActiveAuction}
					<div class="mb-2">
						<AuctionTimer endDate={auction.end_date} showDays={true} compact={true} />
					</div>
				{:else}
					<div class="mb-2 flex justify-between text-sm">
						<span class="text-gray-600 dark:text-gray-400">تاريخ البدء:</span>
						<span class="text-gray-700 dark:text-gray-300">{formatDate(auction.start_date)}</span>
					</div>
					<div class="flex justify-between text-sm">
						<span class="text-gray-600 dark:text-gray-400">تاريخ الانتهاء:</span>
						<span class="text-gray-700 dark:text-gray-300">{formatDate(auction.end_date)}</span>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Actions -->
		{#if showActions && !compact}
			<div
				class="mt-4 flex items-center justify-between border-t border-gray-200 pt-3 dark:border-gray-700"
			>
				<button
					class="rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition hover:bg-blue-700"
					on:click={handleViewDetails}
				>
					التفاصيل
				</button>

				{#if isActiveAuction}
					<button
						class="rounded-md bg-green-600 px-3 py-1 text-sm text-white transition hover:bg-green-700"
						on:click={handlePlaceBid}
					>
						مزايدة
					</button>
				{/if}
			</div>
		{/if}
	</div>
</div>
