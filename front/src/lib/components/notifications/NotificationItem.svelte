<script>
	import { createEventDispatcher } from 'svelte';
	import { notificationsStore } from '$lib/stores/notifications';

	// Props
	export let notification;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Mark notification as read
	function markAsRead() {
		if (!notification.is_read) {
			notificationsStore.markAsRead(notification.id);
			dispatch('markAsRead', { id: notification.id });
		}
	}

	// Handle click
	function handleClick() {
		markAsRead();
		dispatch('click', { notification });

		// Navigate to relevant page if action_url exists
		if (notification.action_url) {
			dispatch('navigate', { url: notification.action_url });
		}
	}

	// Calculate time difference
	function getTimeDifference(timestamp) {
		const now = new Date();
		const notificationTime = new Date(timestamp);
		const diffMs = now - notificationTime;
		const diffSec = Math.floor(diffMs / 1000);
		const diffMin = Math.floor(diffSec / 60);
		const diffHour = Math.floor(diffMin / 60);
		const diffDay = Math.floor(diffHour / 24);

		if (diffDay > 0) {
			return diffDay === 1 ? 'منذ يوم واحد' : `منذ ${diffDay} أيام`;
		} else if (diffHour > 0) {
			return diffHour === 1 ? 'منذ ساعة واحدة' : `منذ ${diffHour} ساعات`;
		} else if (diffMin > 0) {
			return diffMin === 1 ? 'منذ دقيقة واحدة' : `منذ ${diffMin} دقائق`;
		} else {
			return 'الآن';
		}
	}

	// Get notification icon SVG based on type
	function getNotificationIconSvg(type) {
		switch (type) {
			case 'auction_start':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
			case 'auction_end':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`;
			case 'new_bid':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M19 21V8l-6-6H8v19h11z"></path><path d="M13 2v6h6"></path><path d="M10 12h3"></path><path d="M10 16h3"></path></svg>`;
			case 'outbid':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>`;
			case 'winning_bid':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>`;
			case 'payment':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>`;
			case 'property_listed':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 15l2 2 4-4"></path></svg>`;
			case 'property_status':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="9" y1="15" x2="15" y2="15"></line></svg>`;
			case 'message':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>`;
			case 'contract_status':
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.08V8l-6-6H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h6"></path><path d="M14 3v5h5M16 16l5 5M21 16l-5 5"></path></svg>`;
			case 'system':
			default:
				return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg>`;
		}
	}

	// Get notification color based on type
	function getNotificationColor(type) {
		switch (type) {
			case 'auction_start':
			case 'property_listed':
				return 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300';
			case 'new_bid':
			case 'winning_bid':
				return 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300';
			case 'outbid':
				return 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300';
			case 'auction_end':
			case 'auction_status':
				return 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-300';
			case 'payment':
				return 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300';
			case 'message':
				return 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-300';
			default:
				return 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	// Local variables
	const iconSvg = getNotificationIconSvg(notification.notification_type);
	const iconColorClass = getNotificationColor(notification.notification_type);
	const timeAgo = getTimeDifference(notification.created_at);
</script>

<div
	class="dark:hover:bg-gray-750 flex cursor-pointer border-b p-4 transition duration-150 ease-in-out hover:bg-gray-50 dark:border-gray-700 {notification.is_read
		? 'bg-white dark:bg-gray-800'
		: 'bg-blue-50 dark:bg-gray-700'}"
	on:click={handleClick}
>
	<!-- Notification Icon -->
	<div class="me-4 flex-shrink-0">
		<div class="{iconColorClass} flex items-center justify-center rounded-full p-2">
			{@html iconSvg}
		</div>
	</div>

	<!-- Notification Content -->
	<div class="min-w-0 flex-1">
		<div class="flex flex-wrap items-start justify-between">
			<h4 class="text-sm font-semibold text-gray-900 dark:text-white">{notification.title}</h4>
			<span class="mt-1 mr-auto inline-block text-xs text-gray-500 dark:text-gray-400"
				>{timeAgo}</span
			>
		</div>
		<p class="mt-1 line-clamp-2 text-sm text-gray-600 dark:text-gray-300">{notification.content}</p>

		<!-- Optional Action Button -->
		{#if notification.action_url && notification.is_actionable}
			<div class="mt-2 flex justify-end">
				<button
					class="text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
					on:click|stopPropagation={() => {
						markAsRead();
						dispatch('navigate', { url: notification.action_url });
					}}
				>
					{notification.action_text || 'عرض التفاصيل'}
				</button>
			</div>
		{/if}
	</div>
</div>
