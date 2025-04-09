<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL, isSidebarOpen, toggleSidebar } from '$lib/stores/ui';
	import { page } from '$app/stores';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import {
		Home,
		Building,
		Gavel,
		User,
		Users,
		FileText,
		Settings,
		LogOut,
		ChevronRight,
		ChevronLeft,
		ChevronDown,
		X,
		LayoutDashboard
	} from 'lucide-svelte';
	import Avatar from './Avatar.svelte';

	/**
	 * Props
	 */
	// Whether the sidebar is for dashboard or main layout
	export let dashboard = false;
	// Breakpoint for mobile/desktop
	export let breakpoint = 'lg';
	// Additional classes
	export let classes = '';
	// Width (for desktop)
	export let width = 'w-64';
	// Mobile breakpoint width
	$: mobileBreakpointClass = `${breakpoint}:hidden`;
	// Desktop breakpoint width
	$: desktopBreakpointClass = `hidden ${breakpoint}:block`;

	// Local state
	let activeSubmenu = null;

	// Determine if a nav link is active
	$: getIsActive = (href) => {
		if (href === '/') {
			return $page.url.pathname === '/';
		}
		return $page.url.pathname.startsWith(href);
	};

	// Toggle submenu
	function toggleSubmenu(id) {
		activeSubmenu = activeSubmenu === id ? null : id;
	}

	// Close sidebar on mobile when clicking a link
	function handleLinkClick() {
		if (window.innerWidth < 1024) {
			// Adjust breakpoint as needed
			isSidebarOpen.set(false);
		}
	}

	// Navigation items for main sidebar
	const mainNavItems = [
		{ id: 'home', href: '/', label: 'home', icon: Home },
		{ id: 'properties', href: '/properties', label: 'properties', icon: Building },
		{ id: 'auctions', href: '/auctions', label: 'auctions', icon: Gavel },
		{ id: 'about', href: '/about', label: 'about', icon: Users },
		{ id: 'contact', href: '/contact', label: 'contact', icon: FileText }
	];

	// Navigation items for dashboard sidebar
	const dashboardNavItems = [
		{ id: 'dashboard', href: '/dashboard', label: 'dashboard', icon: LayoutDashboard },
		{
			id: 'properties',
			href: '/dashboard/properties',
			label: 'properties',
			icon: Building,
			children: [
				{ id: 'my-properties', href: '/dashboard/properties', label: 'my_properties' },
				{ id: 'add-property', href: '/dashboard/properties/add', label: 'add_property' }
			]
		},
		{
			id: 'auctions',
			href: '/dashboard/auctions',
			label: 'auctions',
			icon: Gavel,
			children: [
				{ id: 'my-auctions', href: '/dashboard/auctions', label: 'my_auctions' },
				{ id: 'active-auctions', href: '/dashboard/auctions/active', label: 'active_auctions' },
				{ id: 'create-auction', href: '/dashboard/auctions/create', label: 'create_auction' }
			]
		},
		{ id: 'bids', href: '/dashboard/bids', label: 'my_bids', icon: Gavel },
		{ id: 'contracts', href: '/dashboard/contracts', label: 'contracts', icon: FileText },
		{ id: 'messages', href: '/dashboard/messages', label: 'messages', icon: FileText },
		{ id: 'profile', href: '/dashboard/profile', label: 'profile', icon: User },
		{ id: 'settings', href: '/dashboard/settings', label: 'settings', icon: Settings }
	];

	// Get navigation items based on sidebar type
	$: navItems = dashboard ? dashboardNavItems : mainNavItems;

	// Get sidebar content based on user authentication
	$: navContent = $isAuthenticated ? navItems : mainNavItems;

	// Handle escape key to close mobile sidebar
	function handleKeydown(event) {
		if (event.key === 'Escape' && $isSidebarOpen) {
			isSidebarOpen.set(false);
		}
	}

	onMount(() => {
		document.addEventListener('keydown', handleKeydown);
		return () => {
			document.removeEventListener('keydown', handleKeydown);
		};
	});

	// Get the appropriate chevron icon based on direction
	$: ChevronIcon = $isRTL ? ChevronLeft : ChevronRight;
</script>

<!-- Mobile sidebar backdrop -->
{#if $isSidebarOpen}
	<div
		class="fixed inset-0 z-30 bg-black bg-opacity-50 {desktopBreakpointClass}"
		transition:fade={{ duration: 200 }}
		on:click={() => isSidebarOpen.set(false)}
		aria-hidden="true"
	></div>
{/if}

<!-- Mobile sidebar -->
{#if $isSidebarOpen}
	<aside
		class="fixed top-0 {$isRTL
			? 'right-0'
			: 'left-0'} z-40 h-full w-64 overflow-y-auto {mobileBreakpointClass} {classes}"
		transition:fly={{ x: $isRTL ? 300 : -300, duration: 300 }}
		aria-label={t('navigation', $language, { default: 'التنقل' })}
	>
		<div
			class="h-full flex flex-col bg-surface-100-800-token border-{$isRTL
				? 'l'
				: 'r'} border-surface-300-600-token shadow-lg"
		>
			<!-- Header with close button -->
			<div class="p-4 border-b border-surface-300-600-token flex items-center justify-between">
				<div class="flex items-center gap-2">
					{#if dashboard && $currentUser}
						<!-- User avatar and info for dashboard -->
						<Avatar user={$currentUser} size="sm" />
						<div class={$isRTL ? 'text-right' : 'text-left'}>
							<p class="font-medium">{$currentUser.first_name} {$currentUser.last_name}</p>
							<p class="text-xs text-surface-500-400-token">
								{t($currentUser?.primary_role?.code || 'user', $language)}
							</p>
						</div>
					{:else}
						<!-- App title for main sidebar -->
						<span class="font-bold text-lg">
							{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
						</span>
					{/if}
				</div>

				<button
					class="btn btn-sm btn-icon variant-ghost-surface"
					aria-label={t('close_menu', $language, { default: 'إغلاق القائمة' })}
					on:click={() => isSidebarOpen.set(false)}
				>
					<X class="w-5 h-5" />
				</button>
			</div>

			<!-- Navigation -->
			<nav class="flex-1 p-4">
				<ul class="space-y-1">
					{#each navContent as item}
						<li>
							{#if item.children}
								<!-- Item with submenu -->
								<button
									class="w-full flex items-center justify-between p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
										item.href
									)
										? 'bg-primary-500 text-white'
										: ''}"
									on:click={() => toggleSubmenu(item.id)}
									aria-expanded={activeSubmenu === item.id}
								>
									<div class="flex items-center">
										<svelte:component this={item.icon} class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
										<span>{t(item.label, $language)}</span>
									</div>
									<ChevronDown
										class="w-4 h-4 {activeSubmenu === item.id ? 'transform rotate-180' : ''}"
									/>
								</button>

								{#if activeSubmenu === item.id}
									<ul class="pl-8 mt-1 space-y-1" transition:fade={{ duration: 150 }}>
										{#each item.children as child}
											<li>
												<a
													href={child.href}
													class="flex items-center p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
														child.href
													)
														? 'bg-primary-500 text-white'
														: ''}"
													on:click={handleLinkClick}
													aria-current={getIsActive(child.href) ? 'page' : undefined}
												>
													<span>{t(child.label, $language)}</span>
												</a>
											</li>
										{/each}
									</ul>
								{/if}
							{:else}
								<!-- Regular item -->
								<a
									href={item.href}
									class="flex items-center p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
										item.href
									)
										? 'bg-primary-500 text-white'
										: ''}"
									on:click={handleLinkClick}
									aria-current={getIsActive(item.href) ? 'page' : undefined}
								>
									<svelte:component this={item.icon} class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
									<span>{t(item.label, $language)}</span>
								</a>
							{/if}
						</li>
					{/each}

					{#if $isAuthenticated}
						<!-- Logout button -->
						<li class="mt-4">
							<button
								class="w-full flex items-center p-2 rounded-token hover:bg-surface-hover-token text-error-500"
								on:click={() => {
									/* add logout logic */
								}}
							>
								<LogOut class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
								<span>{t('logout', $language, { default: 'تسجيل الخروج' })}</span>
							</button>
						</li>
					{/if}
				</ul>
			</nav>
		</div>
	</aside>
{/if}

<!-- Desktop sidebar -->
<aside
	class="{desktopBreakpointClass} {width} h-screen sticky top-0 overflow-y-auto {classes}"
	aria-label={t('navigation', $language, { default: 'التنقل' })}
>
	<div
		class="h-full flex flex-col bg-surface-100-800-token border-{$isRTL
			? 'l'
			: 'r'} border-surface-300-600-token"
	>
		<!-- Header -->
		<div class="p-4 border-b border-surface-300-600-token">
			{#if dashboard && $currentUser}
				<!-- User avatar and info for dashboard -->
				<div class="flex items-center gap-3 mb-2">
					<Avatar user={$currentUser} size="md" />
					<div class={$isRTL ? 'text-right' : 'text-left'}>
						<p class="font-medium">{$currentUser.first_name} {$currentUser.last_name}</p>
						<p class="text-sm text-surface-500-400-token">
							{t($currentUser?.primary_role?.code || 'user', $language)}
						</p>
					</div>
				</div>
			{:else}
				<!-- App title for main sidebar -->
				<div class="flex items-center justify-center">
					<span class="font-bold text-lg">
						{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
					</span>
				</div>
			{/if}
		</div>

		<!-- Navigation -->
		<nav class="flex-1 p-4">
			<ul class="space-y-1">
				{#each navContent as item}
					<li>
						{#if item.children}
							<!-- Item with submenu -->
							<button
								class="w-full flex items-center justify-between p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
									item.href
								)
									? 'bg-primary-500 text-white'
									: ''}"
								on:click={() => toggleSubmenu(item.id)}
								aria-expanded={activeSubmenu === item.id}
							>
								<div class="flex items-center">
									<svelte:component this={item.icon} class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
									<span>{t(item.label, $language)}</span>
								</div>
								<ChevronDown
									class="w-4 h-4 {activeSubmenu === item.id ? 'transform rotate-180' : ''}"
								/>
							</button>

							{#if activeSubmenu === item.id}
								<ul class="pl-8 mt-1 space-y-1" transition:fade={{ duration: 150 }}>
									{#each item.children as child}
										<li>
											<a
												href={child.href}
												class="flex items-center p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
													child.href
												)
													? 'bg-primary-500 text-white'
													: ''}"
												aria-current={getIsActive(child.href) ? 'page' : undefined}
											>
												<span>{t(child.label, $language)}</span>
											</a>
										</li>
									{/each}
								</ul>
							{/if}
						{:else}
							<!-- Regular item -->
							<a
								href={item.href}
								class="flex items-center p-2 rounded-token hover:bg-surface-hover-token {getIsActive(
									item.href
								)
									? 'bg-primary-500 text-white'
									: ''}"
								aria-current={getIsActive(item.href) ? 'page' : undefined}
							>
								<svelte:component this={item.icon} class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
								<span>{t(item.label, $language)}</span>
							</a>
						{/if}
					</li>
				{/each}

				{#if $isAuthenticated}
					<!-- Logout button -->
					<li class="mt-4">
						<button
							class="w-full flex items-center p-2 rounded-token hover:bg-surface-hover-token text-error-500"
							on:click={() => {
								/* add logout logic */
							}}
						>
							<LogOut class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('logout', $language, { default: 'تسجيل الخروج' })}</span>
						</button>
					</li>
				{/if}
			</ul>
		</nav>
	</div>
</aside>
