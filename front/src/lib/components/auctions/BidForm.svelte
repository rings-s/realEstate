<script>
	import { createEventDispatcher } from 'svelte';
	import AuctionTimer from './AuctionTimer.svelte';

	// Props
	export let auction;
	export let isSubmitting = false;
	export let error = null;
	export let myLastBid = null;
	export let highestBid = null;
	export let isAuthenticated = true;

	// Local state
	let bidAmount = '';
	let maxAutoBidAmount = '';
	let enableAutoBid = false;
	let showAutoBidForm = false;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Calculate minimum bid amount
	$: minBidAmount = calculateMinBidAmount();

	// Check if bid is valid
	$: isBidValid = bidAmount && !isNaN(bidAmount) && parseFloat(bidAmount) >= minBidAmount;

	// Check if auto bid is valid
	$: isAutoBidValid =
		enableAutoBid &&
		maxAutoBidAmount &&
		!isNaN(maxAutoBidAmount) &&
		parseFloat(maxAutoBidAmount) > parseFloat(bidAmount || 0);

	// Get minimum bid increment
	$: minBidIncrement = auction?.min_bid_increment || 100;

	// Get current highest bid (from auction or provided prop)
	$: currentHighestBid = highestBid || auction?.current_bid || auction?.starting_price || 0;

	// Check if auction is active
	$: isActive = auction && (auction.status === 'active' || auction.status === 'extended');

	// Calculate the minimum bid amount
	function calculateMinBidAmount() {
		if (!auction) return 0;

		// If no bids yet, use starting price
		if (!auction.current_bid) {
			return auction.starting_price;
		}

		// Otherwise, current highest bid + min increment
		return parseFloat(currentHighestBid) + parseFloat(minBidIncrement);
	}

	// Format price with thousand separator
	function formatPrice(price) {
		return price?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
	}

	// Handle bid submission
	function handleSubmit() {
		if (!isBidValid) return;

		const bid = {
			auction_id: auction.id,
			bid_amount: parseFloat(bidAmount),
			max_bid_amount: enableAutoBid ? parseFloat(maxAutoBidAmount) : null,
			is_auto_bid: enableAutoBid
		};

		dispatch('submit', bid);
	}

	// Increment bid amount
	function incrementBid() {
		if (!bidAmount) {
			bidAmount = minBidAmount.toString();
		} else {
			const newAmount = parseFloat(bidAmount) + parseFloat(minBidIncrement);
			bidAmount = newAmount.toString();
		}
	}

	// Decrement bid amount
	function decrementBid() {
		if (bidAmount) {
			const newAmount = Math.max(minBidAmount, parseFloat(bidAmount) - parseFloat(minBidIncrement));
			bidAmount = newAmount.toString();
		} else {
			bidAmount = minBidAmount.toString();
		}
	}

	// Toggle auto bid form
	function toggleAutoBidForm() {
		showAutoBidForm = !showAutoBidForm;
		if (!showAutoBidForm) {
			enableAutoBid = false;
		}
	}
</script>

<div class="overflow-hidden rounded-lg bg-white p-4 shadow-md dark:bg-gray-800">
	<h3 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">تقديم عرض</h3>

	{#if !isAuthenticated}
		<div
			class="mb-4 rounded-md bg-yellow-50 p-4 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
		>
			<p>يرجى تسجيل الدخول أولاً لتتمكن من المزايدة على هذا العقار.</p>
			<button
				class="mt-2 rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
				on:click={() => dispatch('login')}
			>
				تسجيل الدخول
			</button>
		</div>
	{:else if !isActive}
		<div class="mb-4 rounded-md bg-red-50 p-4 text-red-800 dark:bg-red-900 dark:text-red-200">
			<p>هذا المزاد غير متاح للمزايدة حالياً.</p>
			<p class="mt-1 text-sm">
				{auction?.status === 'closed' || auction?.status === 'sold'
					? 'المزاد مغلق'
					: 'المزاد غير نشط'}
			</p>
		</div>
	{:else}
		<!-- Countdown timer -->
		<div class="mb-6">
			<AuctionTimer
				endDate={auction.end_date}
				showDays={true}
				showHours={true}
				showMinutes={true}
				showSeconds={true}
				compact={false}
				on:expired={() => dispatch('auctionEnded')}
			/>
		</div>

		<!-- Current bid information -->
		<div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
			<div class="rounded-md bg-gray-50 p-3 dark:bg-gray-700">
				<span class="mb-1 block text-sm text-gray-600 dark:text-gray-400">المزايدة الحالية</span>
				<span class="text-lg font-bold text-blue-600 dark:text-blue-400"
					>{formatPrice(currentHighestBid)} ريال</span
				>
			</div>

			<div class="rounded-md bg-gray-50 p-3 dark:bg-gray-700">
				<span class="mb-1 block text-sm text-gray-600 dark:text-gray-400">الحد الأدنى للمزايدة</span
				>
				<span class="text-lg font-bold text-green-600 dark:text-green-400"
					>{formatPrice(minBidAmount)} ريال</span
				>
			</div>
		</div>

		{#if myLastBid}
			<div class="mb-4 rounded-md bg-blue-50 p-3 dark:bg-blue-900">
				<span class="mb-1 block text-sm text-blue-800 dark:text-blue-200">آخر مزايدة قمت بها</span>
				<span class="text-lg font-bold text-blue-800 dark:text-blue-200"
					>{formatPrice(myLastBid.bid_amount)} ريال</span
				>
				{#if myLastBid.is_auto_bid}
					<div class="mt-1 text-xs text-blue-700 dark:text-blue-300">
						<span>المزايدة التلقائية حتى: {formatPrice(myLastBid.max_bid_amount)} ريال</span>
					</div>
				{/if}
			</div>
		{/if}

		{#if error}
			<div class="mb-4 rounded-md bg-red-50 p-3 text-red-800 dark:bg-red-900 dark:text-red-200">
				{error}
			</div>
		{/if}

		<!-- Bid Form -->
		<form on:submit|preventDefault={handleSubmit} class="space-y-4">
			<!-- Bid amount input -->
			<div>
				<label
					for="bidAmount"
					class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>
					قيمة المزايدة (ريال) <span class="text-red-500">*</span>
				</label>
				<div class="flex rounded-md">
					<button
						type="button"
						class="rounded-l-md rounded-r-none border-r border-gray-300 bg-gray-200 px-3 py-2 text-gray-700 transition hover:bg-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
						on:click={decrementBid}
						disabled={bidAmount && parseFloat(bidAmount) <= minBidAmount}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
					<input
						type="number"
						id="bidAmount"
						class="flex-1 rounded-none border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
						bind:value={bidAmount}
						min={minBidAmount}
						step={minBidIncrement}
						required
						placeholder={`أدخل قيمة لا تقل عن ${formatPrice(minBidAmount)} ريال`}
					/>
					<button
						type="button"
						class="rounded-l-none rounded-r-md border-l border-gray-300 bg-gray-200 px-3 py-2 text-gray-700 transition hover:bg-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
						on:click={incrementBid}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				</div>
				{#if bidAmount && !isBidValid}
					<p class="mt-1 text-sm text-red-600 dark:text-red-400">
						يجب أن تكون قيمة المزايدة {formatPrice(minBidAmount)} ريال أو أكثر
					</p>
				{/if}
			</div>

			<!-- Auto bid toggle -->
			<div class="flex items-center justify-between">
				<div class="flex items-center">
					<button
						type="button"
						class="text-sm text-blue-600 hover:underline dark:text-blue-400"
						on:click={toggleAutoBidForm}
					>
						{showAutoBidForm ? 'إخفاء المزايدة التلقائية' : 'تفعيل المزايدة التلقائية'}
					</button>

					<button
						type="button"
						class="mr-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
						title="المزايدة التلقائية تتيح لك تحديد الحد الأقصى الذي ترغب في الوصول إليه، وسيتم رفع مزايدتك تلقائياً"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				</div>
			</div>

			<!-- Auto bid form -->
			{#if showAutoBidForm}
				<div class="rounded-md bg-blue-50 p-4 dark:bg-blue-900">
					<div class="mb-3 flex items-center">
						<input
							type="checkbox"
							id="enableAutoBid"
							class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:text-blue-500"
							bind:checked={enableAutoBid}
						/>
						<label
							for="enableAutoBid"
							class="mr-2 text-sm font-medium text-blue-800 dark:text-blue-200"
						>
							تفعيل المزايدة التلقائية
						</label>
					</div>

					{#if enableAutoBid}
						<div>
							<label
								for="maxAutoBidAmount"
								class="mb-1 block text-sm font-medium text-blue-800 dark:text-blue-200"
							>
								الحد الأقصى للمزايدة التلقائية (ريال)
							</label>
							<input
								type="number"
								id="maxAutoBidAmount"
								class="w-full rounded-md border border-blue-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-blue-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={maxAutoBidAmount}
								min={parseFloat(bidAmount || minBidAmount) + parseFloat(minBidIncrement)}
								placeholder={`أدخل قيمة أكبر من ${formatPrice(parseFloat(bidAmount || minBidAmount))} ريال`}
							/>
							{#if enableAutoBid && maxAutoBidAmount && !isAutoBidValid}
								<p class="mt-1 text-sm text-red-600 dark:text-red-400">
									يجب أن يكون الحد الأقصى أكبر من قيمة المزايدة الحالية
								</p>
							{/if}
							<p class="mt-2 text-xs text-blue-700 dark:text-blue-300">
								سيتم رفع مزايدتك تلقائياً بالحد الأدنى المطلوب عند تجاوز مزايدتك حتى الوصول للحد
								الأقصى المحدد
							</p>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Deposit warning -->
			{#if auction.deposit_required}
				<div
					class="rounded-md bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
				>
					<strong>ملاحظة:</strong> هذا المزاد يتطلب دفع تأمين بقيمة {formatPrice(
						auction.deposit_amount
					)} ريال قبل المشاركة في المزايدة.
				</div>
			{/if}

			<!-- Submit button -->
			<div>
				<button
					type="submit"
					class="flex w-full items-center justify-center gap-2 rounded-md bg-green-600 px-4 py-3 font-medium text-white transition hover:bg-green-700"
					disabled={!isBidValid || (enableAutoBid && !isAutoBidValid) || isSubmitting}
				>
					{#if isSubmitting}
						<div
							class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"
						></div>
					{/if}
					تقديم المزايدة
				</button>
			</div>
		</form>
	{/if}
</div>
