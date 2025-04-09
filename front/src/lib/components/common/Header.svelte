<script>
	import { Moon, Sun, Globe, Menu, User, Bell, LogOut } from 'lucide-svelte';
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

	// Prop to control header display (minimal for dashboard)
	export let minimal = false;

	// Dropdown states
	let profileDropdownOpen = false;
	let notificationsDropdownOpen = false;

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
	}
</script>

<svelte:window on:click={handleClickOutside} />

<header class="navbar bg-surface-100-800-token border-b border-surface-300-600-token">
	<div class="navbar-start">
		{#if !minimal}
			<a href="/" class="text-xl font-bold tracking-tight {$textClass}">
				{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
			</a>
		{:else}
			<button class="btn btn-sm {$isRTL ? 'ms-2' : 'me-2'}" on:click={() => toggleSidebar()}>
				<Menu />
			</button>
			<span class="text-base font-bold {$textClass}">
				{t('dashboard', $language, { default: 'لوحة التحكم' })}
			</span>
		{/if}
	</div>

	{#if !minimal}
		<div class="navbar-center hidden md:flex">
			<nav class="flex items-center gap-4">
				<a href="/" class="btn btn-sm variant-ghost-surface">{t('home', $language)}</a>
				<a href="/properties" class="btn btn-sm variant-ghost-surface"
					>{t('properties', $language)}</a
				>
				<a href="/auctions" class="btn btn-sm variant-ghost-surface">{t('auctions', $language)}</a>
				{#if $isAuthenticated}
					<a href="/dashboard" class="btn btn-sm variant-ghost-surface"
						>{t('dashboard', $language)}</a
					>
				{/if}
			</nav>
		</div>
	{/if}

	<div class="navbar-end">
		<div class="flex items-center gap-2">
			<!-- Theme Toggle -->
			<button
				class="btn btn-sm btn-icon variant-ghost-surface"
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
				class="btn btn-sm btn-icon variant-ghost-surface"
				on:click={toggleLanguage}
				aria-label={$language === 'ar' ? 'English' : 'العربية'}
			>
				<Globe size={18} />
				<span class="ms-1 hidden sm:inline">{$language === 'ar' ? 'EN' : 'عربي'}</span>
			</button>

			{#if $isAuthenticated}
				<!-- Notifications Dropdown -->
				<div class="relative" id="notifications-dropdown">
					<button
						class="btn btn-sm btn-icon variant-ghost-surface"
						on:click={toggleNotificationsDropdown}
						aria-label={t('notifications', $language)}
					>
						<Bell size={18} />
						<span
							class="badge-icon bg-primary-500 absolute top-0 {$isRTL
								? 'left-0'
								: 'right-0'} h-2 w-2 rounded-full"
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
						class="btn btn-sm variant-ghost-surface {$isRTL ? 'me-2' : 'ms-2'}"
						on:click={toggleProfileDropdown}
					>
						<User size={18} class={$isRTL ? 'ms-1' : 'me-1'} />
						<span class="hidden sm:inline {$textClass}">
							{$currentUser?.first_name || t('profile', $language)}
						</span>
					</button>

					{#if profileDropdownOpen}
						<div
							class="card absolute top-10 {$isRTL ? 'left-0' : 'right-0'} w-48 z-50 shadow-xl"
							transition:fly={{ y: -5, duration: 200 }}
						>
							<nav class="list-nav p-2">
								<ul>
									<li>
										<a href="/dashboard" class="flex items-center gap-2 {$textClass}">
											<span class="badge bg-primary-500"
												>{$currentUser?.primary_role?.name || ''}</span
											>
											<span>{t('dashboard', $language)}</span>
										</a>
									</li>
									<li>
										<a href="/dashboard/profile" class="flex items-center gap-2 {$textClass}">
											<User size={16} />
											<span>{t('profile', $language)}</span>
										</a>
									</li>
									<li>
										<hr class="my-2" />
									</li>
									<li>
										<button
											class="w-full flex items-center gap-2 text-error-500 {$textClass}"
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
				<a href="/auth/login" class="btn btn-sm variant-ghost-surface">
					{t('login', $language)}
				</a>
				<a href="/auth/register" class="btn btn-sm variant-filled-primary hidden sm:flex">
					{t('register', $language)}
				</a>
			{/if}
		</div>
	</div>
</header>
