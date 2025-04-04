<script>
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import {
		notifications,
		unreadNotifications,
		notificationsLoading,
		notificationsError,
		notificationsStore
	} from '$lib/stores/notifications';
	import NotificationItem from './NotificationItem.svelte';

	// Props
	export let maxHeight = '600px';
	export let showTabs = true;
	export let defaultTab = 'all'; // 'all' or 'unread'

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Local state
	let activeTab = defaultTab;
	let pollingInterval;
	let notificationsToShow;

	$: {
		notificationsToShow = activeTab === 'unread' ? $unreadNotifications : $notifications;
	}

	// Handle tab change
	function setActiveTab(tab) {
		activeTab = tab;
	}

	// Mark all notifications as read
	function markAllAsRead() {
		notificationsStore.markAllAsRead();
		dispatch('markAllAsRead');
	}

	// Handle notification click
	function handleNotificationClick(event) {
		dispatch('notificationClick', event.detail);
	}

	// Handle navigation
	function handleNavigate(event) {
		dispatch('navigate', event.detail);
		dispatch('close');
	}

	// Handle mark as read
	function handleMarkAsRead(event) {
		dispatch('markAsRead', event.detail);
	}

	// Load notifications on mount
	onMount(() => {
		// Initial load
		notificationsStore.loadNotifications();

		// Set up polling for new notifications (every 30 seconds)
		pollingInterval = setInterval(() => {
			notificationsStore.loadNotifications();
		}, 30000);

		return () => {
			if (pollingInterval) clearInterval(pollingInterval);
		};
	});

	onDestroy(() => {
		if (pollingInterval) clearInterval(pollingInterval);
	});
</script>

<div class="overflow-hidden rounded-md bg-white shadow-lg dark:bg-gray-800">
	<!-- Header -->
	<div
		class="flex items-center justify-between border-b border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900"
	>
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">الإشعارات</h3>

		{#if $unreadNotifications.length > 0}
			<button
				class="flex items-center gap-1 text-sm text-blue-600 transition hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
				on:click={markAllAsRead}
			>
				<!-- Check Icon (inline SVG) -->
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<polyline points="20 6 9 17 4 12"></polyline>
				</svg>
				<span>قراءة الكل</span>
			</button>
		{/if}
	</div>

	<!-- Tabs -->
	{#if showTabs}
		<div class="flex border-b border-gray-200 dark:border-gray-700">
			<button
				class="flex-1 py-3 text-center text-sm font-medium {activeTab === 'all'
					? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
					: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				on:click={() => setActiveTab('all')}
			>
				الكل
			</button>
			<button
				class="flex-1 py-3 text-center text-sm font-medium {activeTab === 'unread'
					? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
					: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				on:click={() => setActiveTab('unread')}
			>
				غير مقروءة
				{#if $unreadNotifications.length > 0}
					<span
						class="mr-1 inline-flex items-center justify-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800 dark:bg-blue-900 dark:text-blue-200"
					>
						{$unreadNotifications.length}
					</span>
				{/if}
			</button>
		</div>
	{/if}

	<!-- Content -->
	<div
		class="scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 overflow-x-hidden overflow-y-auto"
		style="max-height: {maxHeight};"
	>
		{#if $notificationsLoading && $notifications.length === 0}
			<!-- Loading state -->
			<div
				class="flex flex-col items-center justify-center px-4 py-12 text-gray-500 dark:text-gray-400"
			>
				<!-- Loading Spinner (inline SVG) -->
				<svg
					class="mb-3 h-8 w-8 animate-spin"
					xmlns="http://www.w3.org/2000/svg"
					width="32"
					height="32"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="12" y1="2" x2="12" y2="6"></line>
					<line x1="12" y1="18" x2="12" y2="22"></line>
					<line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
					<line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
					<line x1="2" y1="12" x2="6" y2="12"></line>
					<line x1="18" y1="12" x2="22" y2="12"></line>
					<line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
					<line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
				</svg>
				<p>جاري تحميل الإشعارات...</p>
			</div>
		{:else if $notificationsError}
			<!-- Error state -->
			<div
				class="flex flex-col items-center justify-center px-4 py-12 text-red-500 dark:text-red-400"
			>
				<p class="mb-2">حدث خطأ أثناء تحميل الإشعارات</p>
				<button
					class="mt-2 rounded-md bg-red-100 px-4 py-2 text-red-700 transition hover:bg-red-200 dark:bg-red-900 dark:text-red-300 dark:hover:bg-red-800"
					on:click={() => notificationsStore.loadNotifications()}
				>
					إعادة المحاولة
				</button>
			</div>
		{:else if notificationsToShow.length === 0}
			<!-- Empty state -->
			<div
				class="flex flex-col items-center justify-center px-4 py-12 text-gray-500 dark:text-gray-400"
			>
				<div class="mb-3 rounded-full bg-gray-100 p-3 dark:bg-gray-700">
					{#if activeTab === 'unread'}
						<!-- Check Icon (inline SVG) -->
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="32"
							height="32"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<polyline points="20 6 9 17 4 12"></polyline>
						</svg>
					{:else}
						<!-- Bell Icon (inline SVG) -->
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="32"
							height="32"
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
					{/if}
				</div>
				{#if activeTab === 'unread'}
					<p>ليس لديك إشعارات غير مقروءة</p>
				{:else}
					<p>ليس لديك إشعارات حتى الآن</p>
				{/if}
			</div>
		{:else}
			<!-- Notification list -->
			<div class="divide-y divide-gray-200 dark:divide-gray-700">
				{#each notificationsToShow as notification (notification.id)}
					<NotificationItem
						{notification}
						on:click={handleNotificationClick}
						on:navigate={handleNavigate}
						on:markAsRead={handleMarkAsRead}
					/>
				{/each}
			</div>

			<!-- Show all notifications link -->
			{#if activeTab === 'unread' && $unreadNotifications.length < $notifications.length}
				<div class="border-t border-gray-200 p-4 text-center dark:border-gray-700">
					<button
						class="flex w-full items-center justify-center gap-1 text-sm text-blue-600 transition hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
						on:click={() => setActiveTab('all')}
					>
						<span>عرض جميع الإشعارات</span>
						<!-- Chevron Left Icon (inline SVG) -->
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<polyline points="15 18 9 12 15 6"></polyline>
						</svg>
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>
