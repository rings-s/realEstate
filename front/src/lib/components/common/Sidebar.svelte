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
		X
	} from 'lucide-svelte';
	import { page } from '$app/stores';
	import { isSidebarOpen, toggleSidebar, isRTL, textClass, language } from '$lib/stores/ui';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { ROLES } from '$lib/utils/permissions';

	// Props
	export let dashboard = false; // Whether this sidebar is used in dashboard

	// Current route
	$: currentPath = $page.url.pathname;

	// Icon size
	const iconSize = 20;

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
</script>

<!-- Sidebar backdrop for mobile (shown when sidebar is open) -->
{#if $isSidebarOpen}
	<div
		class="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
		on:click={() => toggleSidebar(false)}
		transition:fade={{ duration: 150 }}
	></div>
{/if}

<!-- Sidebar component -->
<aside
	class="
    fixed inset-y-0 {$isRTL ? 'right-0' : 'left-0'} z-50
    w-64 bg-surface-100-800-token border-{$isRTL ? 'l' : 'r'} border-surface-300-600-token
    transform transition-transform duration-300 ease-in-out
    {$isSidebarOpen ? 'translate-x-0' : $isRTL ? 'translate-x-64' : '-translate-x-64'}
    lg:relative lg:translate-x-0
    {dashboard ? 'lg:block' : 'lg:hidden'}
  "
>
	<!-- Sidebar header -->
	<div class="h-16 flex items-center justify-between px-4 border-b border-surface-300-600-token">
		<h2 class="text-xl font-bold {$textClass}">
			{dashboard
				? t('dashboard', $language, { default: 'لوحة التحكم' })
				: t('menu', $language, { default: 'القائمة' })}
		</h2>

		<!-- Close button for mobile -->
		<button
			class="btn btn-sm btn-icon variant-ghost lg:hidden"
			on:click={() => toggleSidebar(false)}
		>
			<X size={18} />
		</button>
	</div>

	<!-- Sidebar body with navigation -->
	<div class="py-4">
		{#if dashboard && $isAuthenticated}
			<!-- User info in dashboard -->
			<div class="px-4 mb-4">
				<div class="p-3 rounded-lg bg-primary-500/10 {$textClass}">
					<p class="font-medium">{$currentUser?.first_name} {$currentUser?.last_name}</p>
					<p class="text-sm opacity-80">{$currentUser?.email}</p>
					{#if $currentUser?.primary_role}
						<span class="badge variant-filled-primary mt-2">
							{$currentUser.primary_role.name}
						</span>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Navigation -->
		<nav class="px-2">
			<ul class="space-y-1">
				{#each filteredNavigation as item}
					<li>
						<a
							href={item.url}
							class="
                flex items-center gap-3 px-3 py-2.5 rounded-lg
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
						</a>
					</li>
				{/each}
			</ul>
		</nav>

		{#if dashboard && $isAuthenticated}
			<!-- Bottom section with logout -->
			<div class="absolute bottom-0 w-full p-4 border-t border-surface-300-600-token">
				<a
					href="/auth/logout"
					class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-primary-500/10 {$textClass}"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width={iconSize}
						height={iconSize}
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
						<polyline points="16 17 21 12 16 7"></polyline>
						<line x1="21" y1="12" x2="9" y2="12"></line>
					</svg>
					<span>{t('logout', $language)}</span>
				</a>
			</div>
		{/if}
	</div>
</aside>
