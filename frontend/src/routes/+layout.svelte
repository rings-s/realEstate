<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { user, isAuthenticated, logout } from '$lib/stores/auth';
	import { fade, fly } from 'svelte/transition';
	import Toast from '$lib/components/Toast.svelte';
	import '../app.css';

	// Props or data passed from +layout.js if needed
	// export let data;

	let sidebarExpanded = true;
	let sidebarMobileOpen = false;
	let userMenuOpen = false;

	// Refs for click outside logic
	let userMenuRef; // Ref for the dropdown menu itself
	let userMenuButtonRef; // Ref for the button that opens the user menu

	// Navigation structure (remains the same)
	const navigation = [
		{
			label: 'الرئيسية',
			items: [
				{ name: 'لوحة التحكم', href: '/', icon: 'fas fa-home' },
				{ name: 'العقارات', href: '/properties', icon: 'fas fa-building', count: 12 },
				{ name: 'المزادات', href: '/auctions', icon: 'fas fa-gavel', count: 8 }
			]
		},
		{
			label: 'التواصل',
			items: [
				{
					name: 'الرسائل',
					href: '/messages',
					icon: 'fas fa-envelope',
					count: 3,
					notification: true
				},
				{
					name: 'الإشعارات',
					href: '/notifications',
					icon: 'fas fa-bell',
					count: 5,
					notification: true
				}
			]
		}
	];

	// Improved Click Outside Logic
	function handleClickOutside(event) {
		if (
			userMenuOpen &&
			userMenuRef &&
			!userMenuRef.contains(event.target) &&
			userMenuButtonRef &&
			!userMenuButtonRef.contains(event.target)
		) {
			userMenuOpen = false;
		}
	}

	onMount(() => {
		document.addEventListener('click', handleClickOutside, true);
		return () => {
			document.removeEventListener('click', handleClickOutside, true);
		};
	});

	// Close menus on page navigation
	$: $page.url.pathname,
		(() => {
			sidebarMobileOpen = false;
			userMenuOpen = false;
		})();

	async function handleLogout() {
		try {
			await logout();
		} catch (error) {
			console.error('Logout failed:', error);
		}
	}

	// Toggle functions
	const toggleMobileSidebar = () => (sidebarMobileOpen = !sidebarMobileOpen);
	const closeMobileSidebar = () => (sidebarMobileOpen = false);
	const toggleUserMenu = () => (userMenuOpen = !userMenuOpen);
	const toggleDesktopSidebar = () => (sidebarExpanded = !sidebarExpanded);
</script>

<div class="flex min-h-screen bg-gray-50" dir="rtl">
	<button
		class="fixed top-4 right-4 z-50 flex h-12 w-12 items-center justify-center rounded-xl
               bg-white text-gray-600 shadow-lg transition-all hover:text-gray-900 focus:outline-none
               focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 lg:hidden"
		on:click={toggleMobileSidebar}
		aria-label={sidebarMobileOpen ? 'إغلاق القائمة' : 'فتح القائمة'}
		aria-controls="mobile-sidebar"
		aria-expanded={sidebarMobileOpen}
	>
		{#key sidebarMobileOpen}
			<i
				class="fas {sidebarMobileOpen ? 'fa-times' : 'fa-bars'} text-xl"
				in:fly={{ y: -5, duration: 200, delay: 100 }}
				out:fly={{ y: -5, duration: 200 }}
			/>
		{/key}
	</button>

	{#if sidebarMobileOpen}
		<div
			class="fixed inset-0 z-30 bg-gray-900/50 backdrop-blur-sm lg:hidden"
			transition:fade={{ duration: 200 }}
			on:click={closeMobileSidebar}
			aria-hidden="true"
		/>
	{/if}

	<aside
		id="mobile-sidebar"
		class="fixed inset-y-0 right-0 z-40 flex w-[280px] flex-col bg-white shadow-xl transition-transform duration-300 ease-in-out
               {sidebarMobileOpen ? 'translate-x-0' : 'translate-x-full'}
               lg:translate-x-0 lg:border-l lg:border-gray-200 lg:shadow-none
               {sidebarExpanded ? 'lg:w-[280px]' : 'lg:w-[80px]'}"
		aria-label="القائمة الجانبية الرئيسية"
	>
		<div class="relative flex h-16 shrink-0 items-center border-b border-gray-200 px-4">
			<div class="flex flex-grow items-center gap-3 overflow-hidden">
				<a
					href="/"
					aria-label="الصفحة الرئيسية للمنصة"
					class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
				>
					<img src="/logo.svg" alt="" class="h-6 w-6" />
				</a>
				{#if sidebarExpanded}
					<span
						class="text-lg font-semibold whitespace-nowrap text-gray-900 transition-opacity duration-200 ease-in-out"
						in:fade={{ duration: 150, delay: 150 }}
						out:fade={{ duration: 100 }}
					>
						منصة المزادات
					</span>
				{/if}
			</div>

			<button
				class="absolute top-1/2 -left-4 hidden h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full
                       border bg-white text-gray-500 shadow-sm transition-all hover:bg-gray-50 hover:text-gray-700 focus:outline-none
                       focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 focus-visible:ring-offset-white lg:flex"
				on:click={toggleDesktopSidebar}
				aria-label={sidebarExpanded ? 'تصغير القائمة الجانبية' : 'توسيع القائمة الجانبية'}
			>
				<i
					class="fas fa-angle-right transition-transform duration-300"
					class:rotate-180={sidebarExpanded}
				></i>
			</button>
		</div>

		<nav class="flex-1 space-y-1 overflow-y-auto p-4" aria-label="التنقل الرئيسي">
			{#each navigation as section, i (section.label || i)}
				<div class="py-3">
					{#if section.label}
						<h3
							class="mb-2 px-3 text-xs font-semibold tracking-wider text-gray-500 uppercase transition-opacity duration-200
                                   {sidebarExpanded
								? 'opacity-100'
								: 'lg:invisible lg:h-0 lg:opacity-0'}"
							aria-hidden={!sidebarExpanded &&
								typeof window !== 'undefined' &&
								window.innerWidth >= 1024}
						>
							{section.label}
						</h3>
					{/if}

					<ul class="space-y-1" role="list">
						{#each section.items as item (item.href)}
							<li role="listitem">
								<a
									href={item.href}
									class="group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150 ease-in-out
                                           {$page.url.pathname === item.href
										? 'bg-blue-50 text-blue-600'
										: 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'}
                                           focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset"
									aria-current={$page.url.pathname === item.href ? 'page' : undefined}
								>
									<span
										class="flex h-6 w-6 shrink-0 items-center justify-center"
										aria-hidden="true"
									>
										<i class="{item.icon} text-base lg:text-lg" />
									</span>

									<span
										class="mr-3 flex-1 whitespace-nowrap transition-opacity duration-200
                                               {sidebarExpanded
											? 'opacity-100 delay-100'
											: 'lg:invisible lg:opacity-0'}"
										aria-hidden={!sidebarExpanded &&
											typeof window !== 'undefined' &&
											window.innerWidth >= 1024}
									>
										{item.name}
									</span>

									{#if item.count}
										<span
											class="ml-auto transition-opacity duration-200
                                                   {sidebarExpanded
												? 'opacity-100 delay-100'
												: 'lg:invisible lg:opacity-0'}"
											aria-hidden={!sidebarExpanded &&
												typeof window !== 'undefined' &&
												window.innerWidth >= 1024}
										>
											<span
												class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-xs font-medium
                                                       {item.notification
													? 'bg-red-100 text-red-600'
													: 'bg-gray-100 text-gray-600'}"
											>
												{item.count}
												{#if item.notification}
													<span class="sr-only">غير مقروء</span>
												{/if}
											</span>
										</span>
									{/if}
								</a>
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</nav>

		<div class="relative mt-auto border-t border-gray-200 p-4">
			{#if $isAuthenticated && $user}
				<div class="relative">
					<button
						bind:this={userMenuButtonRef}
						class="group flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors duration-150 ease-in-out hover:bg-gray-50
                               focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset"
						on:click={toggleUserMenu}
						aria-haspopup="true"
						aria-expanded={userMenuOpen}
						aria-controls="user-menu-dropdown"
						aria-label="قائمة المستخدم"
					>
						<div class="relative shrink-0">
							<img
								src={$user.avatar_url || '/default-avatar.jpg'}
								alt="الصورة الرمزية للمستخدم"
								class="h-10 w-10 rounded-full object-cover ring-2 ring-gray-300 ring-offset-1 ring-offset-white"
								width="40"
								height="40"
							/>
							<span
								class="absolute right-0 bottom-0 h-3 w-3 rounded-full border-2 border-white bg-green-400"
								aria-label="متصل"
							/>
						</div>

						{#if sidebarExpanded}
							<div
								class="flex-1 overflow-hidden whitespace-nowrap transition-opacity duration-200 ease-in-out"
								in:fade={{ duration: 150, delay: 150 }}
								out:fade={{ duration: 100 }}
							>
								<p class="truncate text-sm font-medium text-gray-900">
									{$user.name || $user.email}
								</p>
								<p class="truncate text-xs text-gray-500">{$user.email}</p>
							</div>
						{/if}

						{#if sidebarExpanded}
							<i
								class="fas fa-chevron-down text-gray-400 transition-transform duration-200"
								class:rotate-180={userMenuOpen}
								in:fade={{ duration: 150, delay: 150 }}
								out:fade={{ duration: 100 }}
								aria-hidden="true"
							></i>
						{/if}
					</button>

					{#if userMenuOpen}
						<div
							bind:this={userMenuRef}
							id="user-menu-dropdown"
							class="absolute bottom-full mb-2 {sidebarExpanded
								? 'right-0 w-56'
								: 'right-0 lg:right-auto lg:left-0 lg:w-56'} z-50 rounded-lg bg-white py-2 shadow-xl ring-1 ring-black/5 focus:outline-none"
							transition:fade={{ duration: 150 }}
							role="menu"
							aria-orientation="vertical"
							aria-labelledby="user-menu-button"
						>
							<a
								href="/profile"
								class="flex items-center px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100
                                       focus:bg-gray-100 focus:text-gray-900 focus:outline-none"
								role="menuitem"
							>
								<i class="fas fa-user ml-3 w-5 text-gray-400" aria-hidden="true" />
								الملف الشخصي
							</a>
							<a
								href="/settings"
								class="flex items-center px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100
                                       focus:bg-gray-100 focus:text-gray-900 focus:outline-none"
								role="menuitem"
							>
								<i class="fas fa-cog ml-3 w-5 text-gray-400" aria-hidden="true" />
								الإعدادات
							</a>
							<div class="my-1 border-t border-gray-100" role="separator" />
							<button
								class="flex w-full items-center px-4 py-2 text-sm text-red-600 transition-colors hover:bg-red-50
                                       focus:bg-red-50 focus:outline-none"
								on:click={handleLogout}
								role="menuitem"
							>
								<i class="fas fa-sign-out-alt ml-3 w-5 text-red-400" aria-hidden="true" />
								تسجيل الخروج
							</button>
						</div>
					{/if}
				</div>
			{:else}
				<div class="border-t border-gray-200 pt-4">
					<a
						href="/login"
						class="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm
                               font-medium text-white transition-colors hover:bg-blue-700
                               focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
					>
						<i class="fas fa-sign-in-alt ml-2"></i>
						تسجيل الدخول
					</a>
				</div>
			{/if}
		</div>
	</aside>

	<main
		class="flex-1 transition-all duration-300 ease-in-out
               {sidebarExpanded ? 'lg:mr-[280px]' : 'lg:mr-[80px]'}"
	>
		<div class="min-h-screen p-6 pt-20 lg:p-8 lg:pt-8">
			<slot />
		</div>
	</main>
</div>

<Toast />

<style>
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: rgba(203, 213, 225, 1) transparent; /* Tailwind slate-300 */
	}

	.overflow-y-auto::-webkit-scrollbar {
		width: 6px;
	}

	.overflow-y-auto::-webkit-scrollbar-track {
		background: transparent;
		margin-top: 16px; /* p-4 */
		margin-bottom: 16px; /* p-4 */
	}

	.overflow-y-auto::-webkit-scrollbar-thumb {
		background-color: rgba(203, 213, 225, 0.7); /* Lighter slate-300 */
		border-radius: 6px;
		border: 1px solid transparent;
		background-clip: content-box;
	}
	.overflow-y-auto::-webkit-scrollbar-thumb:hover {
		background-color: rgba(156, 163, 175, 0.8); /* gray-400 */
	}

	.overflow-y-auto {
		scrollbar-gutter: stable both-edges;
	}

	/* Add subtle transition to main content margin */
	main {
		transition: margin-right 0.3s ease-in-out;
	}
</style>
