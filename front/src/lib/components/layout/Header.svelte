<script>
	/**
	 * Advanced header component with responsive navigation, search and user menu
	 * Updated with improved dark mode support
	 * @component
	 */
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { page } from '$app/stores';
	import { clickOutside } from '$lib/actions/clickOutside';
	import { theme, toggleTheme } from '$lib/stores/theme';

	// Props
	export let siteTitle = 'منصة المزادات العقارية';
	export let logo = undefined; // URL to logo image
	export let user = undefined; // User object for authenticated user
	export let notifications = []; // Array of notifications
	export let searchEnabled = true;
	export let transparent = false; // Transparent header (for hero sections)
	export let sticky = true; // Sticky header
	export let showMobileMenu = false; // Control mobile menu state from parent
	export let avatarFallback = ''; // Fallback text for avatar

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Local state
	let isScrolled = false;
	let searchOpen = false;
	let dropdownOpen = false;
	let notificationsOpen = false;
	let searchQuery = '';
	let isLoading = false;
	let headerElement;
	let searchInputElement;

	// Calculate unread notifications count
	$: unreadCount = notifications.filter((n) => !n.read).length;

	// Handle header scroll effect
	onMount(() => {
		const handleScroll = () => {
			isScrolled = window.scrollY > 10;
		};

		window.addEventListener('scroll', handleScroll);
		handleScroll(); // Initial check

		return () => {
			window.removeEventListener('scroll', handleScroll);
		};
	});

	// Toggle mobile menu
	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
		dispatch('toggleMenu', { open: showMobileMenu });
	}

	// Toggle search
	function toggleSearch() {
		searchOpen = !searchOpen;
		if (searchOpen) {
			// Focus search input after it's rendered
			setTimeout(() => {
				searchInputElement?.focus();
			}, 50);
		}
	}

	// Handle search submit
	function handleSearch(e) {
		e.preventDefault();
		if (!searchQuery) return;

		isLoading = true;
		dispatch('search', { query: searchQuery });

		// Simulate API call
		setTimeout(() => {
			isLoading = false;
			searchOpen = false;
		}, 500);
	}

	// Handle notification click
	function handleNotificationClick(notification) {
		dispatch('notificationClick', { notification });

		// Mark as read if not already
		if (!notification.read) {
			dispatch('markAsRead', { id: notification.id });
		}
	}

	// Close notification panel
	function closeNotifications() {
		notificationsOpen = false;
	}

	// Mark all notifications as read
	function markAllAsRead() {
		dispatch('markAllAsRead');
		closeNotifications();
	}

	// Determine header classes based on scroll and transparency with improved dark mode support
	$: headerClasses = [
		'w-full transition-all duration-200 z-50 px-4 lg:px-8',
		sticky ? 'sticky top-0' : '',
		isScrolled || !transparent || showMobileMenu
			? 'bg-white dark:bg-gray-900 shadow-md'
			: transparent
				? 'bg-transparent dark:bg-transparent'
				: 'bg-white dark:bg-gray-900',
		isScrolled ? 'py-2' : 'py-4',
		'text-gray-900 dark:text-white',
		$$props.class || ''
	].join(' ');
</script>

<header bind:this={headerElement} class={headerClasses}>
	<div class="mx-auto flex max-w-7xl items-center justify-between">
		<!-- Logo and Site Title -->
		<div class="flex items-center space-x-0 space-x-reverse">
			<!-- Mobile menu button -->
			<button
				type="button"
				class="focus:ring-primary-500 inline-flex items-center justify-center rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 focus:ring-2 focus:outline-none lg:hidden dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
				aria-controls="mobile-menu"
				aria-expanded={showMobileMenu ? 'true' : 'false'}
				on:click={toggleMobileMenu}
			>
				<span class="sr-only">{showMobileMenu ? 'إغلاق القائمة' : 'فتح القائمة'}</span>
				<!-- Icon when menu is closed -->
				{#if !showMobileMenu}
					<svg
						class="block h-6 w-6"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 12h16M4 18h16"
						/>
					</svg>
				{:else}
					<!-- Icon when menu is open -->
					<svg
						class="block h-6 w-6"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				{/if}
			</button>

			<!-- Logo -->
			<a href="/" class="ml-4 flex items-center">
				{#if logo}
					<img src={logo} alt={siteTitle} class="h-8 w-auto lg:h-10" />
				{:else}
					<div
						class="bg-primary-600 flex h-10 w-10 items-center justify-center rounded-md text-white"
					>
						<span class="text-lg font-bold">{siteTitle.charAt(0)}</span>
					</div>
				{/if}
				<span class="mr-3 text-xl font-bold whitespace-nowrap text-gray-900 dark:text-white">
					{siteTitle}
				</span>
			</a>
		</div>

		<!-- Main navigation - Hidden on mobile -->
		<nav class="hidden lg:flex lg:items-center lg:space-x-6 lg:space-x-reverse">
			<slot name="navigation"></slot>
		</nav>

		<!-- Search and user actions -->
		<div class="mr-2 flex items-center space-x-3 space-x-reverse">
			<!-- Search button -->
			{#if searchEnabled}
				<button
					type="button"
					class="focus:ring-primary-600 rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 focus:ring-2 focus:outline-none dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
					aria-label="بحث"
					on:click={toggleSearch}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</button>
			{/if}

			<!-- Theme toggle -->
			<button
				type="button"
				class="focus:ring-primary-600 rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 focus:ring-2 focus:outline-none dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
				aria-label={$theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}
				on:click={toggleTheme}
			>
				{#if $theme === 'dark'}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
						/>
					</svg>
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
						/>
					</svg>
				{/if}
			</button>

			<!-- Notifications -->
			{#if user && notifications}
				<div class="relative">
					<button
						type="button"
						class="focus:ring-primary-600 relative rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 focus:ring-2 focus:outline-none dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
						aria-label="الإشعارات"
						on:click={() => (notificationsOpen = !notificationsOpen)}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
							/>
						</svg>

						{#if unreadCount > 0}
							<span
								class="absolute top-0 left-0 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white"
							>
								{unreadCount > 9 ? '9+' : unreadCount}
							</span>
						{/if}
					</button>

					<!-- Notification panel -->
					{#if notificationsOpen}
						<div
							class="absolute left-0 mt-2 w-80 overflow-hidden rounded-md bg-white shadow-lg sm:w-96 dark:bg-gray-800"
							transition:fly={{ y: 10, duration: 200, easing: cubicOut }}
							use:clickOutside={() => (notificationsOpen = false)}
						>
							<div class="flex items-center justify-between border-b p-4 dark:border-gray-700">
								<h3 class="text-lg font-medium text-gray-900 dark:text-white">الإشعارات</h3>
								{#if unreadCount > 0}
									<button
										type="button"
										class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300 text-sm"
										on:click={markAllAsRead}
									>
										تحديد الكل كمقروء
									</button>
								{/if}
							</div>

							<div class="max-h-80 overflow-y-auto">
								{#if notifications.length > 0}
									{#each notifications as notification}
										<div
											class="cursor-pointer border-b p-4 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700 {notification.read
												? ''
												: 'dark:bg-opacity-20 bg-blue-50 dark:bg-blue-900'}"
											on:click={() => handleNotificationClick(notification)}
											on:keydown={(e) => e.key === 'Enter' && handleNotificationClick(notification)}
											on:keypress={(e) =>
												e.key === 'Enter' && handleNotificationClick(notification)}
											tabindex="0"
											role="button"
											aria-label="عرض الإشعار: {notification.title}"
										>
											<div class="flex items-start">
												<!-- Notification icon -->
												<div
													class="mt-0.5 flex-shrink-0 p-1 {notification.read
														? 'text-gray-400 dark:text-gray-500'
														: 'text-primary-500 dark:text-primary-400'}"
												>
													<svg
														xmlns="http://www.w3.org/2000/svg"
														class="h-5 w-5"
														viewBox="0 0 20 20"
														fill="currentColor"
													>
														<path
															fill-rule="evenodd"
															d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
															clip-rule="evenodd"
														/>
													</svg>
												</div>

												<!-- Notification content -->
												<div class="mr-3 flex-1">
													<p class="text-sm font-medium text-gray-900 dark:text-white">
														{notification.title}
													</p>
													<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
														{notification.message}
													</p>
													<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
														{notification.time}
													</p>
												</div>

												<!-- Unread indicator -->
												{#if !notification.read}
													<div class="flex-shrink-0">
														<div class="bg-primary-500 h-2 w-2 rounded-full"></div>
													</div>
												{/if}
											</div>
										</div>
									{/each}
								{:else}
									<div class="p-6 text-center text-gray-500 dark:text-gray-400">
										لا توجد إشعارات
									</div>
								{/if}
							</div>

							{#if notifications.length > 0}
								<div class="border-t p-4 text-center dark:border-gray-700">
									<a
										href="/notifications"
										class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium"
									>
										عرض كل الإشعارات
									</a>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/if}

			<!-- User dropdown or login button -->
			{#if user}
				<div class="relative">
					<button
						type="button"
						class="focus:ring-primary-600 flex rounded-full bg-gray-200 text-sm focus:ring-2 focus:outline-none dark:bg-gray-700"
						id="user-menu-button"
						aria-expanded={dropdownOpen ? 'true' : 'false'}
						aria-haspopup="true"
						on:click={() => (dropdownOpen = !dropdownOpen)}
					>
						<span class="sr-only">فتح قائمة المستخدم</span>
						{#if user.avatar}
							<img class="h-8 w-8 rounded-full object-cover" src={user.avatar} alt={user?.name || "المستخدم"} />
						{:else}
							<div
								class="bg-primary-600 flex h-8 w-8 items-center justify-center rounded-full text-white"
							>
								<!-- FIX: Added null check for user.name -->
								<span class="text-sm font-medium">{avatarFallback || (user?.name ? user.name.charAt(0) : 'م')}</span>
							</div>
						{/if}
					</button>

					<!-- Dropdown menu -->
					{#if dropdownOpen}
						<div
							class="absolute left-0 z-10 mt-2 w-48 origin-top-left divide-y divide-gray-100 rounded-md bg-white shadow-lg focus:outline-none dark:divide-gray-700 dark:bg-gray-800"
							role="menu"
							aria-orientation="vertical"
							aria-labelledby="user-menu-button"
							tabindex="-1"
							transition:fly={{ y: 8, duration: 150, easing: cubicOut }}
							use:clickOutside={() => (dropdownOpen = false)}
						>
							<div class="py-1" role="none">
								<div class="px-4 py-2 text-sm text-gray-900 dark:text-white">
									<!-- FIX: Added null check for user.name and user.email -->
									<div class="font-medium">{user?.name || 'المستخدم'}</div>
									<div class="truncate text-xs text-gray-500 dark:text-gray-400">{user?.email || ''}</div>
								</div>
							</div>

							<div class="py-1" role="none">
								<a
									href="/profile"
									class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
									role="menuitem"
									tabindex="-1"
								>
									الملف الشخصي
								</a>
								<a
									href="/account/settings"
									class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
									role="menuitem"
									tabindex="-1"
								>
									الإعدادات
								</a>
								{#if user?.role === 'seller'}
									<a
										href="/dashboard/seller"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
										role="menuitem"
										tabindex="-1"
									>
										لوحة التحكم
									</a>
								{:else if user?.role === 'buyer'}
									<a
										href="/dashboard/buyer"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
										role="menuitem"
										tabindex="-1"
									>
										لوحة التحكم
									</a>
								{:else if user?.role === 'admin'}
									<a
										href="/admin"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
										role="menuitem"
										tabindex="-1"
									>
										لوحة الإدارة
									</a>
								{/if}
							</div>

							<div class="py-1" role="none">
								<button
									type="button"
									class="block w-full px-4 py-2 text-right text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
									role="menuitem"
									tabindex="-1"
									on:click={() => dispatch('logout')}
								>
									تسجيل الخروج
								</button>
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<div>
					<a
						href="/login"
						class="bg-primary-700 hover:bg-primary-800 focus:ring-primary-600 dark:bg-primary-600 dark:hover:bg-primary-500 rounded-md px-4 py-2 text-sm font-medium text-white focus:ring-2 focus:outline-none"
					>
						تسجيل الدخول
					</a>
				</div>
			{/if}
		</div>
	</div>

	<!-- Search overlay -->
	{#if searchOpen}
		<div
			class="fixed inset-0 z-50 overflow-y-auto"
			aria-labelledby="search-overlay-title"
			role="dialog"
			aria-modal="true"
			transition:fade={{ duration: 150 }}
		>
			<div
				class="flex min-h-screen items-start justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0"
			>
				<div
					class="bg-opacity-50 dark:bg-opacity-75 fixed inset-0 bg-gray-500 transition-opacity dark:bg-gray-900"
					on:click={toggleSearch}
					on:keydown={(e) => e.key === 'Escape' && toggleSearch()}
					role="button"
					tabindex="0"
					aria-label="إغلاق البحث"
				></div>

				<!-- Search content -->
				<div
					class="inline-block transform rounded-lg bg-white p-6 text-right shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg dark:bg-gray-800"
					transition:fly={{ y: -30, duration: 200, easing: cubicOut }}
				>
					<div class="relative">
						<form on:submit={handleSearch}>
							<label for="search-input" class="sr-only">بحث</label>
							<div class="flex items-center border-b-2 border-gray-300 py-2 dark:border-gray-600">
								<input
									id="search-input"
									bind:this={searchInputElement}
									bind:value={searchQuery}
									type="text"
									placeholder="ابحث عن عقارات، مزادات..."
									class="w-full border-none bg-transparent text-lg text-gray-900 focus:outline-none dark:text-white"
									autocomplete="off"
								/>
								<button
									type="submit"
									class="ml-3 text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300"
									disabled={isLoading}
									aria-label="بحث"
								>
									{#if isLoading}
										<svg
											class="h-5 w-5 animate-spin"
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
										>
											<circle
												class="opacity-25"
												cx="12"
												cy="12"
												r="10"
												stroke="currentColor"
												stroke-width="4"
											></circle>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
											></path>
										</svg>
									{:else}
										<svg
											class="h-5 w-5"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
											></path>
										</svg>
									{/if}
								</button>
								<button
									type="button"
									class="ml-2 text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300"
									on:click={toggleSearch}
									aria-label="إغلاق البحث"
								>
									<svg
										class="h-5 w-5"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M6 18L18 6M6 6l12 12"
										></path>
									</svg>
								</button>
							</div>
						</form>

						<!-- Quick search suggestions -->
						<div class="mt-4 border-t border-gray-200 pt-4 dark:border-gray-700">
							<h3 class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">
								اقتراحات البحث
							</h3>
							<div class="flex flex-wrap gap-2">
								<button
									class="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
									on:click={() => {
										searchQuery = 'فلل للبيع';
										handleSearch(new Event('click'));
									}}
								>
									فلل للبيع
								</button>
								<button
									class="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
									on:click={() => {
										searchQuery = 'شقق';
										handleSearch(new Event('click'));
									}}
								>
									شقق
								</button>
								<button
									class="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
									on:click={() => {
										searchQuery = 'أراضي استثمارية';
										handleSearch(new Event('click'));
									}}
								>
									أراضي استثمارية
								</button>
								<button
									class="rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
									on:click={() => {
										searchQuery = 'مكاتب تجارية';
										handleSearch(new Event('click'));
									}}
								>
									مكاتب تجارية
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</header>

<!-- Mobile menu when visible -->
{#if showMobileMenu}
	<div
		id="mobile-menu"
		class="fixed inset-0 z-40 flex flex-col bg-white text-gray-900 lg:hidden dark:bg-gray-900 dark:text-white"
		transition:slide={{ duration: 300, easing: cubicOut }}
	>
		<div class="flex items-center justify-between border-b p-4 dark:border-gray-800">
			{#if logo}
				<img src={logo} alt={siteTitle} class="h-8 w-auto" />
			{:else}
				<div
					class="bg-primary-600 flex h-10 w-10 items-center justify-center rounded-md text-white"
				>
					<span class="text-lg font-bold">{siteTitle.charAt(0)}</span>
				</div>
			{/if}

			<button
				type="button"
				class="focus:ring-primary-600 rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 focus:ring-2 focus:outline-none dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
				on:click={toggleMobileMenu}
				aria-label="إغلاق القائمة"
			>
				<span class="sr-only">إغلاق القائمة</span>
				<svg
					class="h-6 w-6"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					aria-hidden="true"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>
		</div>

		<div class="flex-1 overflow-y-auto p-4">
			<nav class="flex flex-col space-y-4">
				<slot name="mobile-navigation"></slot>
			</nav>
		</div>

		<!-- User section for mobile -->
		{#if user}
			<div class="border-t p-4 dark:border-gray-800">
				<div class="flex items-center">
					{#if user.avatar}
						<img class="h-12 w-12 rounded-full object-cover" src={user.avatar} alt={user?.name || "المستخدم"} />
					{:else}
						<div
							class="bg-primary-600 flex h-12 w-12 items-center justify-center rounded-full text-white"
						>
							<!-- FIX: Added null check for user.name -->
							<span class="text-lg font-medium">{avatarFallback || (user?.name ? user.name.charAt(0) : 'م')}</span>
						</div>
					{/if}
					<div class="mr-3">
						<!-- FIX: Added null check for user.name and user.email -->
						<p class="text-sm font-medium text-gray-900 dark:text-white">{user?.name || 'المستخدم'}</p>
						<p class="text-xs text-gray-500 dark:text-gray-400">{user?.email || ''}</p>
					</div>
				</div>

				<div class="mt-4 grid grid-cols-2 gap-4">
					<a
						href="/profile"
						class="w-full rounded-md bg-gray-100 px-4 py-2 text-center text-sm font-medium text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-700"
					>
						الملف الشخصي
					</a>
					<button
						type="button"
						class="bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 dark:hover:bg-primary-500 w-full rounded-md px-4 py-2 text-center text-sm font-medium text-white"
						on:click={() => dispatch('logout')}
					>
						تسجيل الخروج
					</button>
				</div>
			</div>
		{:else}
			<div class="border-t p-4 dark:border-gray-800">
				<div class="grid grid-cols-2 gap-4">
					<a
						href="/login"
						class="bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 dark:hover:bg-primary-500 w-full rounded-md px-4 py-2 text-center text-sm font-medium text-white"
					>
						تسجيل الدخول
					</a>
					<a
						href="/register"
						class="w-full rounded-md bg-gray-100 px-4 py-2 text-center text-sm font-medium text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-700"
					>
						إنشاء حساب
					</a>
				</div>
			</div>
		{/if}
	</div>
{/if}
