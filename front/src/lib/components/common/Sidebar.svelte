<script>
	import {
		Home,
		LayoutDashboard,
		Building,
		Gavel,
		FileText,
		MessageSquare,
		Settings,
		Users,
		X,
		ChevronRight,
		LogOut
	} from 'lucide-svelte';
	import { page } from '$app/stores';
	import { isSidebarOpen, toggleSidebar, isRTL, textClass, language } from '$lib/stores/ui';
	import { isAuthenticated, currentUser, userRoles, logout } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { ROLES } from '$lib/utils/permissions';
	import { goto } from '$app/navigation';
	import { fade, fly } from 'svelte/transition';

	// Props
	export let dashboard = false; // Whether this sidebar is used in dashboard

	// Current route
	$: currentPath = $page.url.pathname;

	// Icon size
	const iconSize = 18;

	// Navigation items for dashboard
	const dashboardNav = [
		{
			label: 'dashboard',
			url: '/dashboard',
			icon: LayoutDashboard,
			matchExact: true,
			roles: [] // Empty means all roles can access
		},
		{
			label: 'properties',
			url: '/dashboard/properties',
			icon: Building,
			roles: [ROLES.ADMIN, ROLES.SELLER, ROLES.AGENT, ROLES.INSPECTOR]
		},
		{
			label: 'auctions',
			url: '/dashboard/auctions',
			icon: Gavel,
			roles: [ROLES.ADMIN, ROLES.SELLER, ROLES.BUYER, ROLES.AGENT]
		},
		{
			label: 'contracts',
			url: '/dashboard/contracts',
			icon: FileText,
			roles: [ROLES.ADMIN, ROLES.SELLER, ROLES.BUYER, ROLES.LEGAL]
		},
		{
			label: 'messages',
			url: '/dashboard/messages',
			icon: MessageSquare,
			roles: [] // All users can access messages
		},
		{
			label: 'profile',
			url: '/dashboard/profile',
			icon: Settings,
			roles: [] // All users can access their profile
		},
		{
			label: 'users',
			url: '/dashboard/users',
			icon: Users,
			roles: [ROLES.ADMIN] // Only admin can access user management
		}
	];

	// Navigation items for main site
	const mainNav = [
		{ label: 'home', url: '/', icon: Home, matchExact: true },
		{ label: 'properties', url: '/properties', icon: Building },
		{ label: 'auctions', url: '/auctions', icon: Gavel }
	];

	// Get navigation based on context
	$: navigation = dashboard ? dashboardNav : mainNav;

	// Filter navigation items based on user roles
	$: filteredNavigation = navigation.filter((item) => {
		// If no roles specified, allow all
		if (!item.roles || item.roles.length === 0) return true;

		// Check if user has any of the required roles
		return $userRoles.some((role) => item.roles.includes(role));
	});

	// Check if a path is active
	function isActive(path, matchExact = false) {
		if (matchExact) {
			return currentPath === path;
		}
		return currentPath.startsWith(path);
	}

	// Handle logout
	async function handleLogout() {
		await logout();
		goto('/auth/login');
	}
</script>

<!-- Sidebar backdrop for mobile (shown when sidebar is open) -->
{#if $isSidebarOpen}
	<div
		class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
		on:click={() => toggleSidebar(false)}
		transition:fade={{ duration: 150 }}
		aria-hidden="true"
	></div>
{/if}

<!-- Sidebar component -->
<aside
	class="
    fixed inset-y-0 {$isRTL ? 'right-0' : 'left-0'} z-50
    w-64 bg-surface-100-800-token border-{$isRTL ? 'l' : 'r'} border-surface-300-600-token
    transform transition-transform duration-200 ease-in-out
    {$isSidebarOpen ? 'translate-x-0' : $isRTL ? 'translate-x-64' : '-translate-x-64'}
    lg:relative lg:translate-x-0
    {dashboard ? 'lg:block' : 'lg:hidden'}
    flex flex-col
  "
>
	<!-- Sidebar header -->
	<div class="h-14 flex items-center justify-between px-4 border-b border-surface-300-600-token">
		<h2 class="text-lg font-semibold {$textClass}">
			{dashboard
				? t('dashboard', $language, { default: 'لوحة التحكم' })
				: t('menu', $language, { default: 'القائمة' })}
		</h2>

		<!-- Close button for mobile -->
		<button
			class="btn btn-sm btn-icon variant-ghost h-8 w-8 lg:hidden"
			on:click={() => toggleSidebar(false)}
		>
			<X size={18} />
		</button>
	</div>

	<!-- Sidebar body with navigation -->
	<div class="flex-1 py-3 overflow-y-auto">
		{#if dashboard && $isAuthenticated}
			<!-- User info card in dashboard -->
			<div class="px-3 mb-3">
				<div class="p-3 rounded-lg bg-primary-500/10 {$textClass}">
					<div class="flex items-center gap-3 mb-2">
						<div class="avatar w-8 h-8 rounded-full overflow-hidden bg-primary-500/20">
							{#if $currentUser?.avatar}
								<img src={$currentUser.avatar} alt={$currentUser.first_name} />
							{:else}
								<span class="text-xs uppercase flex justify-center items-center h-full">
									{($currentUser?.first_name?.[0] || '') + ($currentUser?.last_name?.[0] || '')}
								</span>
							{/if}
						</div>
						<div>
							<p class="font-medium text-sm">
								{$currentUser?.first_name}
								{$currentUser?.last_name}
							</p>
							<p class="text-xs opacity-80">{$currentUser?.email}</p>
						</div>
					</div>
					{#if $currentUser?.primary_role}
						<span class="badge variant-soft-primary text-xs">
							{$currentUser.primary_role.name}
						</span>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Navigation -->
		<nav class="px-2">
			<ul class="space-y-px">
				{#each filteredNavigation as item}
					<li>
						<a
							href={item.url}
							class="
                flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                {isActive(item.url, item.matchExact)
								? 'bg-primary-500 text-white'
								: 'hover:bg-primary-500/10'}
                {$textClass}
              "
							on:click={() => {
								if (!dashboard) toggleSidebar(false);
							}}
						>
							<svelte:component this={item.icon} size={iconSize} />
							<span>{t(item.label, $language)}</span>
							{#if isActive(item.url, item.matchExact)}
								<span class="ml-auto text-white">
									<ChevronRight size={14} class={$isRTL ? 'rotate-180' : ''} />
								</span>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	</div>

	{#if dashboard && $isAuthenticated}
		<!-- Bottom section with logout -->
		<div class="p-3 border-t border-surface-300-600-token">
			<button
				class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm hover:bg-primary-500/10 {$textClass} text-error-500"
				on:click={handleLogout}
			>
				<LogOut size={iconSize} />
				<span>{t('logout', $language)}</span>
			</button>
		</div>
	{/if}
</aside>
