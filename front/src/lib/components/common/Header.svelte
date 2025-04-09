<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL, darkMode, toggleSidebar, uiStore } from '$lib/stores/ui';
	import { page } from '$app/stores';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';
	import { unreadCount as unreadNotifications } from '$lib/stores/notifications';
	import { fade } from 'svelte/transition';
	import {
		Menu,
		X,
		Home,
		Building,
		Gavel,
		User,
		Sun,
		Moon,
		Bell,
		Menu as MenuIcon
	} from 'lucide-svelte';
	import Avatar from './Avatar.svelte';
	import { onMount, afterUpdate } from 'svelte';
	import notificationsStore from '$lib/stores/notifications';
	import { browser } from '$app/environment';

	/**
	 * Props
	 */
	// Whether to show full header or simple version
	export let minimal = false;
	// Additional classes
	export let classes = '';
	// Logo path
	export let logoPath = '/placeholder.png';
	// Mobile breakpoint
	export let breakpoint = 'lg';

	// Local state
	let isMenuOpen = false;
	let isProfileOpen = false;
	let isScrolled = false;
	let stopPolling;

	// Toggle dark mode
	function toggleTheme() {
		darkMode.update((value) => {
			const newValue = !value;
			if (browser) {
				localStorage.setItem('darkMode', newValue ? 'true' : 'false');
				document.documentElement.classList.toggle('dark', newValue);
			}
			return newValue;
		});
	}

	// Toggle language between Arabic and English
	function toggleLanguage() {
		language.update((value) => {
			const newValue = value === 'ar' ? 'en' : 'ar';
			if (browser) {
				localStorage.setItem('language', newValue);
				document.documentElement.setAttribute('lang', newValue);

				// Set direction based on language
				const newDirection = newValue === 'ar' ? 'rtl' : 'ltr';
				document.documentElement.setAttribute('dir', newDirection);
				localStorage.setItem('direction', newDirection);
			}
			return newValue;
		});
	}

	// Toggle mobile menu
	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
	}

	// Toggle profile dropdown
	function toggleProfile() {
		isProfileOpen = !isProfileOpen;
		// Close menu when opening profile
		if (isProfileOpen) {
			isMenuOpen = false;
		}
	}

	// Close all menus
	function closeMenus() {
		isMenuOpen = false;
		isProfileOpen = false;
	}

	// Handle scroll event to add shadow to header
	function handleScroll() {
		isScrolled = window.scrollY > 10;
	}

	// Determine if a nav link is active
	$: getIsActive = (href) => {
		if (href === '/') {
			return $page.url.pathname === '/';
		}
		return $page.url.pathname.startsWith(href);
	};

	onMount(() => {
		// Add scroll listener
		window.addEventListener('scroll', handleScroll);

		// Start polling for notifications if authenticated
		if ($isAuthenticated) {
			stopPolling = notificationsStore.startPolling(30000);
			notificationsStore.getUnreadCount();
		}

		// Initial scroll check
		handleScroll();

		// Initialize dark mode from localStorage if available
		if (browser) {
			const savedDarkMode = localStorage.getItem('darkMode');
			if (savedDarkMode) {
				const isDark = savedDarkMode === 'true';
				darkMode.set(isDark);
				document.documentElement.classList.toggle('dark', isDark);
			}

			// Initialize language from localStorage if available
			const savedLanguage = localStorage.getItem('language');
			if (savedLanguage) {
				language.set(savedLanguage);
				document.documentElement.setAttribute('lang', savedLanguage);

				// Set direction based on language
				const direction = savedLanguage === 'ar' ? 'rtl' : 'ltr';
				document.documentElement.setAttribute('dir', direction);
			}
		}

		// Cleanup on unmount
		return () => {
			window.removeEventListener('scroll', handleScroll);
			if (stopPolling) stopPolling();
		};
	});

	// Update document when dark mode changes
	$: if (browser && $darkMode !== undefined) {
		document.documentElement.classList.toggle('dark', $darkMode);
	}

	// Update document when language changes
	$: if (browser && $language) {
		document.documentElement.setAttribute('lang', $language);
		// Update direction based on language
		const direction = $language === 'ar' ? 'rtl' : 'ltr';
		document.documentElement.setAttribute('dir', direction);
	}
</script>

<header
	class="sticky top-0 z-40 w-full {isScrolled
		? 'shadow-lg'
		: ''} bg-surface-100-800-token {classes}"
>
	<div class="container mx-auto p-4">
		<div class="flex items-center justify-between">
			<!-- Left section: Logo + Mobile menu toggle -->
			<div class="flex items-center">
				<!-- Mobile menu toggle -->
				<button
					class="btn btn-sm btn-icon {breakpoint}:hidden variant-ghost-surface mr-2"
					aria-label={t('menu', $language, { default: 'القائمة' })}
					on:click={toggleSidebar}
				>
					<MenuIcon class="w-5 h-5" />
				</button>

				<!-- Logo -->
				<a
					href="/"
					class="flex items-center gap-2"
					aria-label={t('app_name', $language, { default: 'منصة مزادات العقارات' })}
				>
					<img
						src={logoPath}
						alt={t('app_name', $language, { default: 'منصة مزادات العقارات' })}
						class="h-8"
						onError={(e) => {
							e.target.style.display = 'none';
						}}
					/>
					{#if !minimal}
						<span class="font-bold text-lg hidden sm:block">
							{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
						</span>
					{/if}
				</a>
			</div>

			<!-- Center section: Main navigation (desktop) -->
			{#if !minimal}
				<nav class="hidden {breakpoint}:flex items-center gap-2 {$isRTL ? 'mr-4' : 'ml-4'}">
					<a
						href="/"
						class="btn btn-sm {getIsActive('/')
							? 'variant-filled-primary'
							: 'variant-ghost-surface'}"
						aria-current={getIsActive('/') ? 'page' : undefined}
					>
						<Home class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
						<span>{t('home', $language, { default: 'الرئيسية' })}</span>
					</a>
					<a
						href="/properties"
						class="btn btn-sm {getIsActive('/properties')
							? 'variant-filled-primary'
							: 'variant-ghost-surface'}"
						aria-current={getIsActive('/properties') ? 'page' : undefined}
					>
						<Building class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
						<span>{t('properties', $language, { default: 'العقارات' })}</span>
					</a>
					<a
						href="/auctions"
						class="btn btn-sm {getIsActive('/auctions')
							? 'variant-filled-primary'
							: 'variant-ghost-surface'}"
						aria-current={getIsActive('/auctions') ? 'page' : undefined}
					>
						<Gavel class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
						<span>{t('auctions', $language, { default: 'المزادات' })}</span>
					</a>
				</nav>
			{/if}

			<!-- Right section: User menu, notifications, theme toggle, language toggle -->
			<div class="flex items-center gap-1 sm:gap-2">
				<!-- Theme toggle -->
				<button
					class="btn btn-sm btn-icon variant-ghost-surface"
					aria-label={$darkMode
						? t('light_mode', $language, { default: 'الوضع النهاري' })
						: t('dark_mode', $language, { default: 'الوضع الليلي' })}
					on:click={toggleTheme}
				>
					{#if $darkMode}
						<Sun class="w-5 h-5" />
					{:else}
						<Moon class="w-5 h-5" />
					{/if}
				</button>

				<!-- Language toggle -->
				<button
					class="btn btn-sm variant-ghost-surface"
					aria-label={$language === 'ar' ? 'English' : 'العربية'}
					on:click={toggleLanguage}
				>
					{$language === 'ar' ? 'EN' : 'عربي'}
				</button>

				<!-- Notifications (if authenticated) -->
				{#if $isAuthenticated}
					<a
						href="/notifications"
						class="btn btn-sm btn-icon variant-ghost-surface relative"
						aria-label={t('notifications', $language, { default: 'الإشعارات' })}
					>
						<Bell class="w-5 h-5" />
						{#if $unreadNotifications > 0}
							<span
								class="absolute -top-1 {$isRTL
									? 'left-0'
									: 'right-0'} badge-icon variant-filled-error"
								>{$unreadNotifications > 9 ? '9+' : $unreadNotifications}</span
							>
						{/if}
					</a>
				{/if}

				<!-- User menu (if authenticated) -->
				{#if $isAuthenticated}
					<div class="relative">
						<button
							class="btn btn-sm variant-ghost-surface flex items-center gap-2"
							aria-label={t('account', $language, { default: 'الحساب' })}
							aria-expanded={isProfileOpen}
							aria-controls="profile-menu"
							on:click={toggleProfile}
						>
							<Avatar user={$currentUser} size="xs" classes={$isRTL ? 'mr-0 ml-1' : 'ml-0 mr-1'} />
							<span class="hidden sm:inline">
								{$currentUser?.first_name || $currentUser?.email || ''}
							</span>
						</button>

						<!-- Profile dropdown -->
						{#if isProfileOpen}
							<div
								id="profile-menu"
								class="card absolute {$isRTL ? 'left-0' : 'right-0'} mt-2 p-2 w-48 z-50 shadow-xl"
								transition:fade={{ duration: 150 }}
							>
								<nav class="list-nav">
									<ul>
										<li>
											<a href="/dashboard" class="nav-item" on:click={closeMenus}>
												<span class="badge badge-sm variant-soft-primary"
													>{t($currentUser?.primary_role?.code || 'user', $language, {
														default: 'مستخدم'
													})}</span
												>
												<span>{t('dashboard', $language, { default: 'لوحة التحكم' })}</span>
											</a>
										</li>
										<li>
											<a href="/profile" class="nav-item" on:click={closeMenus}>
												<span>{t('profile', $language, { default: 'الملف الشخصي' })}</span>
											</a>
										</li>
										<li>
											<a href="/messages" class="nav-item" on:click={closeMenus}>
												<span>{t('messages', $language, { default: 'الرسائل' })}</span>
											</a>
										</li>
										<li>
											<a href="/favorites" class="nav-item" on:click={closeMenus}>
												<span>{t('favorites', $language, { default: 'المفضلة' })}</span>
											</a>
										</li>
										<li>
											<a href="/settings" class="nav-item" on:click={closeMenus}>
												<span>{t('settings', $language, { default: 'الإعدادات' })}</span>
											</a>
										</li>
										<li>
											<hr class="nav-divider" />
										</li>
										<li>
											<button
												class="nav-item text-error-500 w-full text-left"
												on:click={() => {
													closeMenus(); /* add logout logic */
												}}
											>
												<span>{t('logout', $language, { default: 'تسجيل الخروج' })}</span>
											</button>
										</li>
									</ul>
								</nav>
							</div>
						{/if}
					</div>
				{:else}
					<!-- Login/Register buttons if not authenticated -->
					<a href="/login" class="btn btn-sm variant-ghost">
						{t('login', $language, { default: 'تسجيل الدخول' })}
					</a>
					<a href="/register" class="btn btn-sm variant-filled-primary">
						{t('register', $language, { default: 'إنشاء حساب' })}
					</a>
				{/if}
			</div>
		</div>
	</div>

	<!-- Mobile navigation menu (when open) -->
	{#if isMenuOpen}
		<div
			class="block {breakpoint}:hidden bg-surface-100-800-token border-t border-surface-300-600-token"
			transition:fade={{ duration: 150 }}
		>
			<nav class="container mx-auto p-4">
				<ul class="space-y-2">
					<li>
						<a
							href="/"
							class="flex items-center p-2 rounded-token {getIsActive('/')
								? 'bg-primary-500 text-white'
								: 'hover:bg-surface-hover-token'}"
							on:click={closeMenus}
						>
							<Home class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('home', $language, { default: 'الرئيسية' })}</span>
						</a>
					</li>
					<li>
						<a
							href="/properties"
							class="flex items-center p-2 rounded-token {getIsActive('/properties')
								? 'bg-primary-500 text-white'
								: 'hover:bg-surface-hover-token'}"
							on:click={closeMenus}
						>
							<Building class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('properties', $language, { default: 'العقارات' })}</span>
						</a>
					</li>
					<li>
						<a
							href="/auctions"
							class="flex items-center p-2 rounded-token {getIsActive('/auctions')
								? 'bg-primary-500 text-white'
								: 'hover:bg-surface-hover-token'}"
							on:click={closeMenus}
						>
							<Gavel class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('auctions', $language, { default: 'المزادات' })}</span>
						</a>
					</li>
					<li>
						<a
							href="/about"
							class="flex items-center p-2 rounded-token {getIsActive('/about')
								? 'bg-primary-500 text-white'
								: 'hover:bg-surface-hover-token'}"
							on:click={closeMenus}
						>
							<User class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('about', $language, { default: 'من نحن' })}</span>
						</a>
					</li>
					<li>
						<a
							href="/contact"
							class="flex items-center p-2 rounded-token {getIsActive('/contact')
								? 'bg-primary-500 text-white'
								: 'hover:bg-surface-hover-token'}"
							on:click={closeMenus}
						>
							<Bell class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
							<span>{t('contact', $language, { default: 'اتصل بنا' })}</span>
						</a>
					</li>
				</ul>
			</nav>
		</div>
	{/if}
</header>

<!-- Click outside handler -->
{#if isProfileOpen || isMenuOpen}
	<div
		class="fixed inset-0 z-30 bg-transparent"
		on:click={closeMenus}
		on:keydown={(e) => e.key === 'Escape' && closeMenus()}
		role="button"
		tabindex="0"
		aria-label="Close menu"
	/>
{/if}
