<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let bids = [];
	export let auctionId = null;
	export let loading = false;
	export let currentUser = null;
	export let isAdminOrAuctioneer = false;
	export let winningBid = null;

	// State
	let sortedBids = [];

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Sort and process bids whenever they change
	$: {
		if (bids && bids.length > 0) {
			// Sort by amount (highest first) and then by date (newest first)
			sortedBids = [...bids].sort((a, b) => {
				if (b.bid_amount !== a.bid_amount) {
					return b.bid_amount - a.bid_amount;
				}
				return new Date(b.bid_time || b.created_at) - new Date(a.bid_time || a.created_at);
			});
		} else {
			sortedBids = [];
		}
	}

	// Format price with thousand separator
	function formatPrice(price) {
		return price?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
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
			minute: '2-digit',
			second: '2-digit'
		}).format(date);
	}

	// Handle bidder click
	function handleBidderClick(bidder) {
		dispatch('bidderClick', { bidder });
	}

	// Mark bid as winning
	function markAsWinning(bid) {
		dispatch('markWinning', { bid });
	}

	// Check if user is the current bidder
	function isCurrentUser(bid) {
		return currentUser && bid.bidder && bid.bidder.id === currentUser.id;
	}
</script>

<div class="overflow-hidden rounded-lg bg-white shadow-md dark:bg-gray-800">
	<div class="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700">
		<h3 class="text-xl font-semibold text-gray-900 dark:text-white">سجل المزايدات</h3>
		<div class="text-sm text-gray-600 dark:text-gray-400">
			{bids.length} مزايدة
		</div>
	</div>

	{#if loading}
		<!-- Loading state -->
		<div class="flex flex-col items-center justify-center p-8">
			<div
				class="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"
			></div>
			<p class="text-gray-600 dark:text-gray-300">جاري تحميل سجل المزايدات...</p>
		</div>
	{:else if sortedBids.length === 0}
		<!-- Empty state -->
		<div class="p-8 text-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mx-auto mb-4 h-12 w-12 text-gray-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
				/>
			</svg>
			<p class="text-gray-600 dark:text-gray-300">لا توجد مزايدات حتى الآن.</p>
			<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
				كن أول من يقدم مزايدة على هذا العقار!
			</p>
		</div>
	{:else}
		<!-- Bid list -->
		<div class="overflow-x-auto">
			<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
				<thead class="bg-gray-50 dark:bg-gray-900">
					<tr>
						<th
							scope="col"
							class="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
						>
							المزايد
						</th>
						<th
							scope="col"
							class="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
						>
							قيمة المزايدة
						</th>
						<th
							scope="col"
							class="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
						>
							وقت المزايدة
						</th>
						<th
							scope="col"
							class="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
						>
							الحالة
						</th>
						{#if isAdminOrAuctioneer}
							<th
								scope="col"
								class="px-4 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								الإجراءات
							</th>
						{/if}
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
					{#each sortedBids as bid (bid.id)}
						<tr class={isCurrentUser(bid) ? 'bg-blue-50 dark:bg-blue-900' : ''}>
							<!-- Bidder -->
							<td class="px-4 py-4 whitespace-nowrap">
								<div class="flex items-center">
									{#if bid.bidder?.avatar}
										<img
											class="mr-2 h-8 w-8 rounded-full"
											src={bid.bidder.avatar}
											alt={bid.bidder.name}
										/>
									{:else}
										<div
											class="mr-2 flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 dark:bg-gray-700"
										>
											<span class="text-sm font-medium text-gray-600 dark:text-gray-300">
												{bid.bidder?.first_name?.charAt(0) || bid.bidder?.name?.charAt(0) || 'م'}
											</span>
										</div>
									{/if}
									<div>
										<button
											class="text-sm font-medium text-gray-900 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
											on:click={() => handleBidderClick(bid.bidder)}
										>
											{bid.bidder?.name ||
												bid.bidder?.first_name + ' ' + bid.bidder?.last_name ||
												'مزايد مجهول'}
										</button>
										{#if isCurrentUser(bid)}
											<span class="block text-xs text-blue-600 dark:text-blue-400">أنت</span>
										{/if}
									</div>
								</div>
							</td>

							<!-- Bid Amount -->
							<td class="px-4 py-4 whitespace-nowrap">
								<div class="text-sm font-medium text-gray-900 dark:text-white">
									{formatPrice(bid.bid_amount)} ريال
								</div>
								{#if bid.is_auto_bid}
									<span class="text-xs text-gray-500 dark:text-gray-400">
										مزايدة تلقائية
										{#if isCurrentUser(bid) && bid.max_bid_amount}
											(حتى {formatPrice(bid.max_bid_amount)} ريال)
										{/if}
									</span>
								{/if}
							</td>

							<!-- Bid Time -->
							<td class="px-4 py-4 whitespace-nowrap">
								<div class="text-sm text-gray-500 dark:text-gray-400">
									{formatDate(bid.bid_time || bid.created_at)}
								</div>
							</td>

							<!-- Status -->
							<td class="px-4 py-4 whitespace-nowrap">
								{#if winningBid && bid.id === winningBid.id}
									<span
										class="inline-flex rounded-full bg-green-100 px-2 text-xs leading-5 font-semibold text-green-800 dark:bg-green-900 dark:text-green-200"
									>
										فائز
									</span>
								{:else if bid.status === 'winning'}
									<span
										class="inline-flex rounded-full bg-green-100 px-2 text-xs leading-5 font-semibold text-green-800 dark:bg-green-900 dark:text-green-200"
									>
										فائز
									</span>
								{:else if bid.status === 'outbid'}
									<span
										class="inline-flex rounded-full bg-red-100 px-2 text-xs leading-5 font-semibold text-red-800 dark:bg-red-900 dark:text-red-200"
									>
										تم تجاوزه
									</span>
								{:else if bid.status === 'accepted'}
									<span
										class="inline-flex rounded-full bg-blue-100 px-2 text-xs leading-5 font-semibold text-blue-800 dark:bg-blue-900 dark:text-blue-200"
									>
										مقبول
									</span>
								{:else if bid.status === 'rejected'}
									<span
										class="inline-flex rounded-full bg-red-100 px-2 text-xs leading-5 font-semibold text-red-800 dark:bg-red-900 dark:text-red-200"
									>
										مرفوض
									</span>
								{:else}
									<span
										class="inline-flex rounded-full bg-gray-100 px-2 text-xs leading-5 font-semibold text-gray-800 dark:bg-gray-900 dark:text-gray-200"
									>
										معلق
									</span>
								{/if}
							</td>

							<!-- Actions (Admin/Auctioneer only) -->
							{#if isAdminOrAuctioneer}
								<td class="px-4 py-4 text-sm font-medium whitespace-nowrap">
									{#if winningBid && bid.id === winningBid.id}
										<span class="text-green-600 dark:text-green-400">فائز</span>
									{:else if bid.status !== 'winning'}
										<button
											class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
											on:click={() => markAsWinning(bid)}
										>
											تعيين كفائز
										</button>
									{/if}
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
