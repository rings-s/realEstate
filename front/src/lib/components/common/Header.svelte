<script>
	import { Moon, Sun, Globe, Menu, User, Bell, LogOut, ChevronDown } from 'lucide-svelte';
	import {
		theme,
		language,
		isRTL,
		toggleTheme,
		toggleLanguage,
		toggleSidebar,
		textClass
	} from '$lib/stores/ui';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { isAuthenticated, currentUser, logout } from '$lib/stores/auth';
	import { browser } from '$app/environment';

	// Prop to control header display (minimal for dashboard)
	export let minimal = false;

	// Dropdown states
	let profileDropdownOpen = false;
	let notificationsDropdownOpen = false;
	let mobileMenuOpen = false;

	// Toggle profile dropdown
	function toggleProfileDropdown() {
		profileDropdownOpen = !profileDropdownOpen;
		if (profileDropdownOpen) notificationsDropdownOpen = false;
	}

	// Toggle notifications dropdown
	function toggleNotificationsDropdown() {
		notificationsDropdownOpen = !notificationsDropdownOpen;
		if (notificationsDropdownOpen) profileDropdownOpen = false;
	}

	// Toggle mobile menu
	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	// Handle logout
	async function handleLogout() {
		await logout();
		goto('/auth/login');
	}

	// Close dropdowns when clicking outside
	function handleClickOutside(event) {
		if (profileDropdownOpen && !event.target.closest('#profile-dropdown')) {
			profileDropdownOpen = false;
		}
		if (notificationsDropdownOpen && !event.target.closest('#notifications-dropdown')) {
			notificationsDropdownOpen = false;
		}
		if (
			mobileMenuOpen &&
			!event.target.closest('#mobile-menu') &&
			!event.target.closest('#mobile-menu-button')
		) {
			mobileMenuOpen = false;
		}
	}

	// Navigation items
	const navItems = [
		{ label: 'home', path: '/' },
		{ label: 'properties', path: '/properties' },
		{ label: 'auctions', path: '/auctions' }
	];
</script>

<svelte:window on:click={handleClickOutside} />

<!-- Modern compact header with better mobile support -->
<header class="bg-surface-100-800-token border-b border-surface-300-600-token sticky top-0 z-40">
	<div class="container mx-auto px-4">
		<div class="flex h-14 justify-between items-center">
			<!-- Left section: Logo/Title and sidebar toggle for dashboard -->
			<div class="flex items-center gap-2">
				{#if minimal}
					<button
						class="btn btn-sm btn-icon variant-ghost h-9 w-9 aspect-square lg:hidden"
						on:click={() => toggleSidebar()}
						id="mobile-menu-button"
						aria-label={t('toggle_menu', $language, { default: 'القائمة' })}
					>
						<Menu size={18} />
					</button>
					<span class="font-semibold tracking-tight {$textClass} text-base">
						{t('dashboard', $language, { default: 'لوحة التحكم' })}
					</span>
				{:else}
					<a href="/" class="font-semibold tracking-tight {$textClass} text-xl hidden md:block">
						{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
					</a>
					<a href="/" class="font-semibold tracking-tight {$textClass} text-base md:hidden">
						{t('app_short_name', $language, { default: 'مزادات العقارات' })}
					</a>
					<!-- Mobile menu button -->
					<button
						class="btn btn-sm btn-icon variant-ghost h-9 w-9 aspect-square md:hidden {$isRTL
							? 'mr-2'
							: 'ml-2'}"
						on:click={toggleMobileMenu}
						id="mobile-menu-button"
						aria-label={t('toggle_menu', $language, { default: 'القائمة' })}
					>
						<Menu size={18} />
					</button>
				{/if}
			</div>

			<!-- Center section: Main navigation (desktop only) -->
			{#if !minimal}
				<nav class="hidden md:flex items-center gap-1">
					{#each navItems as item}
						<a href={item.path} class="btn btn-sm variant-ghost h-9">
							{t(item.label, $language)}
						</a>
					{/each}
					{#if $isAuthenticated}
						<a href="/dashboard" class="btn btn-sm variant-ghost h-9">
							{t('dashboard', $language)}
						</a>
					{/if}
				</nav>
			{/if}

			<!-- Right section: Theme/Language toggles, notifications, profile -->
			<div class="flex items-center gap-1">
				<!-- Theme Toggle -->
				<button
					class="btn btn-sm btn-icon variant-ghost h-9 w-9 aspect-square"
					on:click={toggleTheme}
					aria-label={$theme === 'dark' ? t('light_mode', $language) : t('dark_mode', $language)}
				>
					{#if $theme === 'dark'}
						<Sun size={18} />
					{:else}
						<Moon size={18} />
					{/if}
				</button>

				<!-- Language Toggle -->
				<button
					class="btn btn-sm btn-icon variant-ghost h-9 w-9 aspect-square"
					on:click={toggleLanguage}
					aria-label={$language === 'ar' ? 'English' : 'العربية'}
				>
					<Globe size={18} />
				</button>

				{#if $isAuthenticated}
					<!-- Notifications Dropdown -->
					<div class="relative" id="notifications-dropdown">
						<button
							class="btn btn-sm btn-icon variant-ghost h-9 w-9 aspect-square"
							on:click={toggleNotificationsDropdown}
							aria-label={t('notifications', $language)}
						>
							<Bell size={18} />
							<span
								class="badge-icon bg-primary-500 absolute top-1 {$isRTL
									? 'left-1'
									: 'right-1'} h-2 w-2 rounded-full"
							></span>
						</button>

						{#if notificationsDropdownOpen}
							<div
								class="card absolute top-10 {$isRTL
									? 'left-0'
									: 'right-0'} w-64 sm:w-80 z-50 overflow-hidden shadow-xl"
								transition:fly={{ y: -5, duration: 200 }}
							>
								<header class="card-header p-2 {$textClass}">
									<h3 class="h4">{t('notifications', $language)}</h3>
								</header>
								<div class="p-2 max-h-96 overflow-auto">
									<p class="p-2 {$textClass}">
										{t('no_notifications', $language, { default: 'لا توجد إشعارات' })}
									</p>
								</div>
								<footer class="card-footer p-2 flex justify-center">
									<a href="/notifications" class="anchor"
										>{t('view_all', $language, { default: 'عرض الكل' })}</a
									>
								</footer>
							</div>
						{/if}
					</div>

					<!-- Profile Dropdown -->
					<div class="relative" id="profile-dropdown">
						<button
							class="btn btn-sm variant-ghost h-9 flex items-center gap-1 pr-2"
							on:click={toggleProfileDropdown}
							aria-label={t('profile', $language)}
						>
							<div class="avatar w-7 h-7 rounded-full overflow-hidden bg-primary-500/20">
								{#if $currentUser?.avatar}
									<img
										src={$currentUser.avatar}
										alt={$currentUser.first_name || t('profile', $language)}
									/>
								{:else}
									<span class="text-xs uppercase flex justify-center items-center h-full">
										{($currentUser?.first_name?.[0] || '') + ($currentUser?.last_name?.[0] || '')}
									</span>
								{/if}
							</div>
							<span class="hidden sm:inline text-sm">
								{$currentUser?.first_name || t('profile', $language)}
							</span>
							<ChevronDown size={14} class="hidden sm:inline" />
						</button>

						{#if profileDropdownOpen}
							<div
								class="card absolute top-10 {$isRTL ? 'left-0' : 'right-0'} w-56 z-50 shadow-xl"
								transition:fly={{ y: -5, duration: 200 }}
							>
								<div class="p-3 border-b border-surface-300-600-token">
									<div class="font-semibold text-sm">
										{$currentUser?.first_name}
										{$currentUser?.last_name}
									</div>
									<div class="text-xs text-surface-500-400-token break-all">
										{$currentUser?.email}
									</div>
									{#if $currentUser?.primary_role}
										<span class="badge variant-soft-primary text-xs mt-1">
											{$currentUser.primary_role.name}
										</span>
									{/if}
								</div>
								<nav class="list-nav p-2">
									<ul>
										<li>
											<a href="/dashboard" class="!py-2 text-sm">
												{t('dashboard', $language)}
											</a>
										</li>
										<li>
											<a href="/dashboard/profile" class="!py-2 text-sm">
												{t('profile', $language)}
											</a>
										</li>
										<li>
											<hr class="!my-2" />
										</li>
										<li>
											<button
												class="w-full flex items-center gap-2 text-error-500 !py-2 text-sm"
												on:click={handleLogout}
											>
												<LogOut size={16} />
												<span>{t('logout', $language)}</span>
											</button>
										</li>
									</ul>
								</nav>
							</div>
						{/if}
					</div>
				{:else}
					<div class="flex items-center gap-1">
						<a href="/auth/login" class="btn btn-sm variant-ghost h-9">
							{t('login', $language)}
						</a>
						<a href="/auth/register" class="btn btn-sm variant-filled-primary h-9 hidden sm:flex">
							{t('register', $language)}
						</a>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Mobile menu (visible when toggled) -->
	{#if mobileMenuOpen && !minimal}
		<div
			id="mobile-menu"
			class="md:hidden bg-surface-100-800-token border-t border-surface-300-600-token"
			transition:fly={{ y: -5, duration: 150 }}
		>
			<nav class="container mx-auto p-3 flex flex-col gap-1 {$textClass}">
				{#each navItems as item}
					<a
						href={item.path}
						class="btn btn-sm variant-ghost justify-start h-9"
						on:click={() => (mobileMenuOpen = false)}
					>
						{t(item.label, $language)}
					</a>
				{/each}
				{#if $isAuthenticated}
					<a
						href="/dashboard"
						class="btn btn-sm variant-ghost justify-start h-9"
						on:click={() => (mobileMenuOpen = false)}
					>
						{t('dashboard', $language)}
					</a>
				{/if}
				{#if !$isAuthenticated}
					<a
						href="/auth/register"
						class="btn btn-sm variant-ghost justify-start h-9 sm:hidden"
						on:click={() => (mobileMenuOpen = false)}
					>
						{t('register', $language)}
					</a>
				{/if}
			</nav>
		</div>
	{/if}
</header>
