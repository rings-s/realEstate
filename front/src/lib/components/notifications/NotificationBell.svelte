<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import { unreadNotificationsCount, notificationsStore } from '$lib/stores/notifications';
	import NotificationCenter from './NotificationCenter.svelte';

	// Props
	export let size = 20;
	export let showCount = true;
	export let maxCount = 99;

	// State
	let isOpen = false;
	let bellElement;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Toggle notification center
	function toggleNotificationCenter() {
		isOpen = !isOpen;
		dispatch('toggle', { isOpen });
	}

	// Close notification center
	function closeNotificationCenter() {
		isOpen = false;
		dispatch('toggle', { isOpen });
	}

	// Handle clicks outside the notification center
	function handleClickOutside(event) {
		if (bellElement && !bellElement.contains(event.target) && isOpen) {
			closeNotificationCenter();
		}
	}

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
		};
	});
</script>

<div class="relative" bind:this={bellElement}>
	<!-- Bell Button -->
	<button
		type="button"
		class="relative rounded-full p-2 transition duration-150 ease-in-out hover:bg-gray-100 focus:outline-none dark:hover:bg-gray-700"
		on:click|stopPropagation={toggleNotificationCenter}
		aria-label={$unreadNotificationsCount > 0
			? `${$unreadNotificationsCount} إشعارات غير مقروءة`
			: 'لا توجد إشعارات جديدة'}
	>
		<!-- Bell Icon (inline SVG) -->
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="text-gray-700 dark:text-gray-200"
			width={size}
			height={size}
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		>
			<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path>
			<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path>
		</svg>

		<!-- Badge -->
		{#if showCount && $unreadNotificationsCount > 0}
			<span
				class="absolute end-0 top-0 inline-flex h-5 min-w-[1.25rem] translate-x-1/2 -translate-y-1/2 transform items-center justify-center rounded-full bg-red-600 px-2 py-1 text-xs leading-none font-bold text-white"
			>
				{$unreadNotificationsCount > maxCount ? `${maxCount}+` : $unreadNotificationsCount}
			</span>
		{/if}
	</button>

	<!-- Notification Center Dropdown -->
	{#if isOpen}
		<div
			class="absolute left-0 z-50 mt-2 w-screen origin-top-right rounded-md bg-white shadow-lg sm:w-96 md:right-0 md:left-auto dark:bg-gray-800"
			style="max-height: calc(100vh - 150px);"
		>
			<!-- Close button for mobile -->
			<button
				class="absolute top-3 left-3 rounded-full p-2 hover:bg-gray-100 focus:outline-none md:hidden dark:hover:bg-gray-700"
				on:click={closeNotificationCenter}
			>
				<!-- X Icon (inline SVG) -->
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="18"
					height="18"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="text-gray-500 dark:text-gray-400"
				>
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>

			<NotificationCenter on:markAsRead={() => {}} on:close={closeNotificationCenter} />
		</div>
	{/if}
</div>
