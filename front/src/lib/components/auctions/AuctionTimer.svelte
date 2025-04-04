<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';

	// Props
	export let endDate; // Can be a string or Date object
	export let startDate = null; // Optional start date (string or Date object)
	export let showDays = true;
	export let showHours = true;
	export let showMinutes = true;
	export let showSeconds = true;
	export let compact = false;
	export let largeFormat = false;
	export let autoRefresh = 1000; // Refresh interval in ms, set to 0 to disable auto-refresh

	// State
	let timeLeft = {
		days: 0,
		hours: 0,
		minutes: 0,
		seconds: 0,
		total: 0,
		expired: false,
		notStarted: false
	};
	let intervalId;
	let hasStarted = false;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Calculate time left
	function calculateTimeLeft() {
		const now = new Date().getTime();
		const end = new Date(endDate).getTime();
		const start = startDate ? new Date(startDate).getTime() : null;

		// Check if auction hasn't started yet
		if (start && now < start) {
			timeLeft = {
				days: 0,
				hours: 0,
				minutes: 0,
				seconds: 0,
				total: 0,
				expired: false,
				notStarted: true
			};
			return;
		}

		// Auction has started
		hasStarted = true;

		// Calculate time difference
		const difference = end - now;

		if (difference <= 0) {
			// Auction has ended
			timeLeft = {
				days: 0,
				hours: 0,
				minutes: 0,
				seconds: 0,
				total: 0,
				expired: true,
				notStarted: false
			};

			// Stop interval when time expires
			if (intervalId) {
				clearInterval(intervalId);
				intervalId = null;
			}

			// Dispatch event when time expires
			dispatch('expired');
		} else {
			// Auction is active, calculate time units
			const days = Math.floor(difference / (1000 * 60 * 60 * 24));
			const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
			const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
			const seconds = Math.floor((difference % (1000 * 60)) / 1000);

			timeLeft = {
				days,
				hours,
				minutes,
				seconds,
				total: difference,
				expired: false,
				notStarted: false
			};

			// Dispatch event when time is updated
			dispatch('update', timeLeft);
		}
	}

	// Initialize timer on mount
	onMount(() => {
		calculateTimeLeft();

		// Set up interval for auto-refresh if enabled
		if (autoRefresh > 0) {
			intervalId = setInterval(calculateTimeLeft, autoRefresh);
		}

		return () => {
			if (intervalId) {
				clearInterval(intervalId);
			}
		};
	});

	onDestroy(() => {
		if (intervalId) {
			clearInterval(intervalId);
		}
	});

	// Pad numbers with leading zero
	function padNumber(num) {
		return num.toString().padStart(2, '0');
	}
</script>

{#if timeLeft.notStarted}
	<div class="text-center {compact ? 'text-sm' : ''} {largeFormat ? 'text-xl' : ''}">
		<span class="font-medium text-blue-600 dark:text-blue-400">المزاد لم يبدأ بعد</span>
	</div>
{:else if timeLeft.expired}
	<div class="text-center {compact ? 'text-sm' : ''} {largeFormat ? 'text-xl' : ''}">
		<span class="font-medium text-red-600 dark:text-red-400">انتهى المزاد</span>
	</div>
{:else if compact}
	<!-- Compact timer display -->
	<div class="text-center">
		<div class="mb-1 text-xs text-gray-600 dark:text-gray-400">الوقت المتبقي</div>
		<div class="flex items-center justify-center gap-1">
			{#if showDays && timeLeft.days > 0}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="font-medium text-blue-800 dark:text-blue-200">{timeLeft.days}د</span>
				</div>
				<span class="text-gray-400">:</span>
			{/if}

			{#if showHours}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.hours)}س</span
					>
				</div>
				<span class="text-gray-400">:</span>
			{/if}

			{#if showMinutes}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.minutes)}د</span
					>
				</div>
				<span class="text-gray-400">:</span>
			{/if}

			{#if showSeconds}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.seconds)}ث</span
					>
				</div>
			{/if}
		</div>
	</div>
{:else if largeFormat}
	<!-- Large format timer -->
	<div class="text-center">
		<div class="mb-2 text-sm text-gray-600 dark:text-gray-400">الوقت المتبقي للمزاد</div>
		<div class="flex items-center justify-center gap-2">
			{#if showDays}
				<div class="flex flex-col items-center">
					<div class="min-w-[4rem] rounded-lg bg-blue-100 px-3 py-2 dark:bg-blue-900">
						<span class="text-3xl font-bold text-blue-800 dark:text-blue-200">{timeLeft.days}</span>
					</div>
					<span class="mt-1 text-xs text-gray-600 dark:text-gray-400">أيام</span>
				</div>
				<div class="mt-[-1rem] text-2xl text-gray-400">:</div>
			{/if}

			{#if showHours}
				<div class="flex flex-col items-center">
					<div class="min-w-[4rem] rounded-lg bg-blue-100 px-3 py-2 dark:bg-blue-900">
						<span class="text-3xl font-bold text-blue-800 dark:text-blue-200"
							>{padNumber(timeLeft.hours)}</span
						>
					</div>
					<span class="mt-1 text-xs text-gray-600 dark:text-gray-400">ساعات</span>
				</div>
				<div class="mt-[-1rem] text-2xl text-gray-400">:</div>
			{/if}

			{#if showMinutes}
				<div class="flex flex-col items-center">
					<div class="min-w-[4rem] rounded-lg bg-blue-100 px-3 py-2 dark:bg-blue-900">
						<span class="text-3xl font-bold text-blue-800 dark:text-blue-200"
							>{padNumber(timeLeft.minutes)}</span
						>
					</div>
					<span class="mt-1 text-xs text-gray-600 dark:text-gray-400">دقائق</span>
				</div>
				<div class="mt-[-1rem] text-2xl text-gray-400">:</div>
			{/if}

			{#if showSeconds}
				<div class="flex flex-col items-center">
					<div class="min-w-[4rem] rounded-lg bg-blue-100 px-3 py-2 dark:bg-blue-900">
						<span class="text-3xl font-bold text-blue-800 dark:text-blue-200"
							>{padNumber(timeLeft.seconds)}</span
						>
					</div>
					<span class="mt-1 text-xs text-gray-600 dark:text-gray-400">ثواني</span>
				</div>
			{/if}
		</div>
	</div>
{:else}
	<!-- Default timer display -->
	<div class="text-center">
		<div class="mb-2 text-sm text-gray-600 dark:text-gray-400">الوقت المتبقي</div>
		<div class="flex items-center justify-center gap-2">
			{#if showDays && timeLeft.days > 0}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="text-lg font-medium text-blue-800 dark:text-blue-200">{timeLeft.days}</span>
				</div>
				<span class="ml-1 text-sm text-gray-600 dark:text-gray-400">أيام</span>
			{/if}

			{#if showHours}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="text-lg font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.hours)}</span
					>
				</div>
				<span class="ml-1 text-sm text-gray-600 dark:text-gray-400">س</span>
			{/if}

			{#if showMinutes}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="text-lg font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.minutes)}</span
					>
				</div>
				<span class="ml-1 text-sm text-gray-600 dark:text-gray-400">د</span>
			{/if}

			{#if showSeconds}
				<div class="rounded bg-blue-100 px-2 py-1 dark:bg-blue-900">
					<span class="text-lg font-medium text-blue-800 dark:text-blue-200"
						>{padNumber(timeLeft.seconds)}</span
					>
				</div>
				<span class="ml-1 text-sm text-gray-600 dark:text-gray-400">ث</span>
			{/if}
		</div>
	</div>
{/if}
