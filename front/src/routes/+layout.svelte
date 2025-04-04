<script>
	import { onMount, setContext, afterUpdate, onDestroy } from 'svelte';
	import { writable } from 'svelte/store';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth, isAuthenticated, user, roles } from '$lib/stores/auth';
	import { uiStore, toasts, TOAST_TYPES } from '$lib/stores/ui';
	import { theme } from '$lib/stores/theme';
	import { browser } from '$app/environment';
	import api from '$lib/services/api';

	// Import layout components
	import Header from '$lib/components/layout/Header.svelte';
	import Navbar from '$lib/components/layout/Navbar.svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';
	import Toast from '$lib/components/common/Toast.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import '../app.css';

	// Local state
	let isLoading = true;
	let showMobileMenu = false;
	let sidebarOpen = false;
	let tokenVerified = false;
	let loadingTimeoutId; // For safety timeout

	// Create stores for layout components
	const headerStore = writable(null);
	const navbarStore = writable(null);
	const sidebarStore = writable(null);
	const footerStore = writable(null);

	// Make stores available to child components
	setContext('layout', {
		header: headerStore,
		navbar: navbarStore,
		sidebar: sidebarStore,
		footer: footerStore,
		sidebarOpen: writable(sidebarOpen)
	});

	// Navigation items (customize based on your needs)
	const navItems = [
		{ label: 'الرئيسية', href: '/' },
		{ label: 'المزادات', href: '/auctions' },
		{ label: 'العقارات', href: '/properties' },
		{ label: 'كيف يعمل', href: '/how-it-works' },
		{ label: 'من نحن', href: '/about' },
		{ label: 'اتصل بنا', href: '/contact' }
	];

	// Dashboard sidebar items
	const sidebarItems = [
		{
			label: 'لوحة التحكم',
			href: '/dashboard',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" /></svg>'
		},
		{
			label: 'المزادات',
			href: '/dashboard/auctions',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd" /></svg>',
			children: [
				{ label: 'المزادات النشطة', href: '/dashboard/auctions/active' },
				{ label: 'مزاداتي', href: '/dashboard/auctions/my-auctions' },
				{ label: 'إنشاء مزاد', href: '/dashboard/auctions/create' }
			]
		},
		{
			label: 'العقارات',
			href: '/dashboard/properties',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" /></svg>',
			children: [
				{ label: 'عقاراتي', href: '/dashboard/properties/my-properties' },
				{ label: 'إضافة عقار', href: '/dashboard/properties/create' }
			]
		},
		{
			label: 'المدفوعات',
			href: '/dashboard/payments',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" /><path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd" /></svg>'
		},
		{
			label: 'الملف الشخصي',
			href: '/profile',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" /></svg>'
		},
		{
			label: 'الإعدادات',
			href: '/settings',
			icon: '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" /></svg>'
		}
	];

	// Footer columns
	const footerColumns = [
		{
			title: 'المنصة',
			links: [
				{ label: 'الرئيسية', url: '/' },
				{ label: 'من نحن', url: '/about' },
				{ label: 'خدماتنا', url: '/services' },
				{ label: 'الأخبار', url: '/news' },
				{ label: 'تواصل معنا', url: '/contact' }
			]
		},
		{
			title: 'المزادات والعقارات',
			links: [
				{ label: 'جميع المزادات', url: '/auctions' },
				{ label: 'العقارات المميزة', url: '/properties/featured' },
				{ label: 'كيف يعمل المزاد', url: '/how-it-works' },
				{ label: 'الخدمات العقارية', url: '/services/real-estate' }
			]
		}
	];

	// Sample social links
	const socialLinks = [
		{
			name: 'تويتر',
			url: 'https://twitter.com',
			icon: '<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path></svg>'
		},
		{
			name: 'فيسبوك',
			url: 'https://facebook.com',
			icon: '<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clip-rule="evenodd"></path></svg>'
		},
		{
			name: 'انستجرام',
			url: 'https://instagram.com',
			icon: '<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772A4.902 4.902 0 015.45 2.525c.636-.247 1.363-.416 2.427-.465C8.901 2.013 9.256 2 11.685 2h.63zm-.081 1.802h-.468c-2.456 0-2.784.011-3.807.058-.975.045-1.504.207-1.857.344-.467.182-.8.398-1.15.748-.35.35-.566.683-.748 1.15-.137.353-.3.882-.344 1.857-.047 1.023-.058 1.351-.058 3.807v.468c0 2.456.011 2.784.058 3.807.045.975.207 1.504.344 1.857.182.466.399.8.748 1.15.35.35.683.566 1.15.748.353.137.882.3 1.857.344 1.054.048 1.37.058 4.041.058h.08c2.597 0 2.917-.01 3.96-.058.976-.045 1.505-.207 1.858-.344.466-.182.8-.398 1.15-.748.35-.35.566-.683.748-1.15.137-.353.3-.882.344-1.857.048-1.055.058-1.37.058-4.041v-.08c0-2.597-.01-2.917-.058-3.96-.045-.976-.207-1.505-.344-1.858a3.097 3.097 0 00-.748-1.15 3.098 3.098 0 00-1.15-.748c-.353-.137-.882-.3-1.857-.344-1.023-.047-1.351-.058-3.807-.058zM12 6.865a5.135 5.135 0 110 10.27 5.135 5.135 0 010-10.27zm0 1.802a3.333 3.333 0 100 6.666 3.333 3.333 0 000-6.666zm5.338-3.205a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z" clip-rule="evenodd"></path></svg>'
		},
		{
			name: 'لينكد إن',
			url: 'https://linkedin.com',
			icon: '<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fill-rule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clip-rule="evenodd"></path></svg>'
		}
	];

	// Mock notifications for demonstration
	const mockNotifications = [
		{
			id: 1,
			title: 'انتهاء المزاد',
			message: 'تم انتهاء المزاد على العقار #12345 بنجاح',
			time: 'منذ 30 دقيقة',
			read: false
		},
		{
			id: 2,
			title: 'عرض جديد',
			message: 'تم تقديم عرض جديد على العقار الخاص بك',
			time: 'منذ ساعتين',
			read: true
		},
		{
			id: 3,
			title: 'تحديث الحساب',
			message: 'تم تحديث معلومات حسابك بنجاح',
			time: 'منذ يوم واحد',
			read: true
		}
	];

	// Check if current route is an auth page
	$: isAuthPage =
		$page.url.pathname.startsWith('/login') ||
		$page.url.pathname.startsWith('/register') ||
		$page.url.pathname.startsWith('/password-reset') ||
		$page.url.pathname.startsWith('/email-verification');

	// Check if current route is a dashboard page
	$: isDashboardPage = $page.url.pathname.startsWith('/dashboard');

	// Protected routes that require authentication
	$: isProtectedRoute =
		$page.url.pathname.startsWith('/dashboard') ||
		$page.url.pathname.startsWith('/profile') ||
		$page.url.pathname.startsWith('/settings');

	// Handle navigation item click
	function handleNavItemClick() {
		showMobileMenu = false;
	}

	// Toggle mobile menu
	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
	}

	// Toggle sidebar
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	// Handle toast dismissal
	function handleToastDismiss(event) {
		const { id } = event.detail;
		if (id) {
			uiStore.removeToast(id);
		}
	}

	// Handle logout
	async function handleLogout() {
		// Get the refresh token before logging out
		const refreshToken = localStorage.getItem('refresh_token');

		try {
			if (refreshToken) {
				// Make the logout API call to invalidate the token on the server
				await api.post('/accounts/logout/', { refresh: refreshToken });
			}
		} catch (error) {
			console.error('Error during logout API call:', error);
		} finally {
			// Always clear local tokens regardless of API call success
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');

			// Update auth store state
			auth.logout().then(() => {
				uiStore.addToast('تم تسجيل الخروج بنجاح', TOAST_TYPES.SUCCESS);
				// Redirect to home page
				window.location.href = '/';
			});
		}
	}

	// Verify token validity with improved error handling
	async function verifyToken() {
		if (!browser || isAuthPage) {
			return true; // Skip verification for auth pages
		}

		const accessToken = localStorage.getItem('access_token');
		const refreshToken = localStorage.getItem('refresh_token');

		// If no tokens exist, no need to verify
		if (!accessToken || !refreshToken) {
			tokenVerified = true;

			// If on protected route, redirect to login
			if (isProtectedRoute) {
				uiStore.addToast('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', TOAST_TYPES.WARNING);
				goto('/login?redirect=' + encodeURIComponent($page.url.pathname));
			}
			return true;
		}

		try {
			// Verify token with backend
			await api.post('/accounts/token/verify/', {});
			tokenVerified = true;
			return true;
		} catch (error) {
			console.error('Token verification failed:', error);

			// Try to refresh the token
			try {
				const response = await api.post('/accounts/token/refresh/', { refresh: refreshToken });

				// Update the access token if refresh was successful
				if (response && response.access) {
					localStorage.setItem('access_token', response.access);
					tokenVerified = true;
					return true;
				} else {
					// If refresh failed, clear tokens and redirect to login
					localStorage.removeItem('access_token');
					localStorage.removeItem('refresh_token');

					if (isProtectedRoute) {
						uiStore.addToast('جلستك انتهت. يرجى إعادة تسجيل الدخول', TOAST_TYPES.WARNING);
						goto('/login?redirect=' + encodeURIComponent($page.url.pathname));
					}
					return false;
				}
			} catch (refreshError) {
				console.error('Token refresh failed:', refreshError);

				// Clear tokens and redirect if on protected route
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');

				if (isProtectedRoute) {
					uiStore.addToast('جلستك انتهت. يرجى إعادة تسجيل الدخول', TOAST_TYPES.WARNING);
					goto('/login?redirect=' + encodeURIComponent($page.url.pathname));
				}
				return false;
			}
		}
	}

	// Check authentication and redirect for protected routes
	afterUpdate(() => {
		if (browser && !isLoading && isProtectedRoute && !$isAuthenticated) {
			uiStore.addToast('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', TOAST_TYPES.WARNING);
			goto('/login?redirect=' + encodeURIComponent($page.url.pathname));
		}
	});

	// Cleanup resources on component destroy
	onDestroy(() => {
		if (loadingTimeoutId) {
			clearTimeout(loadingTimeoutId);
		}
	});

	// Initialize on mount with improved error handling
	onMount(async () => {
		if (browser) {
			// Set up a safety timeout to ensure loader doesn't run forever
			// This is a backup in case something goes wrong with the auth process
			loadingTimeoutId = setTimeout(() => {
				isLoading = false;
				console.warn('Loading timeout reached, forcing app to display');
				uiStore.addToast('تم تحميل التطبيق ببعض المشاكل', TOAST_TYPES.WARNING);
			}, 5000); // Reduced from 10000 to 5000 ms for faster fallback

			try {
				// Verify token in a safe way that doesn't get stuck
				const tokenPromise = verifyToken();
				const tokenTimeoutPromise = new Promise((_, reject) =>
					setTimeout(() => reject(new Error('Token verification timeout')), 2000)
				);

				// Use Promise.race to ensure we don't wait indefinitely for token verification
				await Promise.race([tokenPromise, tokenTimeoutPromise]).catch((err) => {
					console.warn("Token verification didn't complete in time:", err);
					// Continue anyway, verifyToken has already handled redirection if needed
				});

				// Initialize auth with timeout protection
				const authPromise = auth.initialize();
				const authTimeoutPromise = new Promise((_, reject) =>
					setTimeout(() => reject(new Error('Auth initialization timeout')), 2000)
				);

				await Promise.race([authPromise, authTimeoutPromise]).catch((err) => {
					console.warn("Auth initialization didn't complete in time:", err);
					// Continue anyway - the app should handle null user gracefully with our Header fixes
				});
			} catch (error) {
				console.error('App initialization error:', error);
				uiStore.addToast('حدث خطأ أثناء تحميل التطبيق', TOAST_TYPES.ERROR);
			} finally {
				// ALWAYS clear the safety timeout and end loading state
				if (loadingTimeoutId) {
					clearTimeout(loadingTimeoutId);
					loadingTimeoutId = null;
				}

				// Always set isLoading to false to remove the loader
				// Add a minimal delay for smoother transition
				setTimeout(() => {
					isLoading = false;
				}, 300);
			}
		}
	});
</script>

{#if isLoading}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-gray-900">
		<Loader size="large" color="auto" text="جاري التحميل..." timeout={10000} />
	</div>
{:else}
	<div
		class="flex min-h-screen flex-col {$theme === 'dark' ? 'dark' : ''} bg-gray-50 dark:bg-gray-900"
	>
		<!-- Header - Show on all pages except auth pages -->
		{#if !isAuthPage}
			<Header
				bind:this={$headerStore}
				{showMobileMenu}
				on:toggleMenu={toggleMobileMenu}
				user={$user}
				notifications={mockNotifications}
				transparent={$page.url.pathname === '/'}
				on:logout={handleLogout}
			>
				<svelte:fragment slot="navigation">
					{#each navItems as item}
						<a
							href={item.href}
							class="rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
							class:text-primary-600={$page.url.pathname === item.href}
							on:click={handleNavItemClick}
						>
							{item.label}
						</a>
					{/each}
				</svelte:fragment>

				<svelte:fragment slot="mobile-navigation">
					{#each navItems as item}
						<a
							href={item.href}
							class="block px-4 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
							class:text-primary-600={$page.url.pathname === item.href}
							on:click={handleNavItemClick}
						>
							{item.label}
						</a>
					{/each}
				</svelte:fragment>
			</Header>
		{/if}

		<!-- Main Content Area -->
		<div class="relative flex flex-1 flex-col md:flex-row">
			<!-- Sidebar for dashboard pages -->
			{#if isDashboardPage && $isAuthenticated}
				<Sidebar
					bind:this={$sidebarStore}
					bind:isOpen={sidebarOpen}
					items={sidebarItems}
					position="right"
					on:toggle={toggleSidebar}
					userInfo={$user
						? {
								name: $user.first_name + ' ' + $user.last_name,
								role: $user.primary_role?.name || '',
								avatar: $user.avatar
							}
						: undefined}
				/>
			{/if}

			<!-- Main content -->
			<main class="flex-1 {isDashboardPage ? 'bg-gray-50 p-4 lg:p-8 dark:bg-gray-900' : ''}">
				<!-- For auth pages, we render the slot directly -->
				{#if isAuthPage}
					<slot></slot>
					<!-- For dashboard pages, we handle the layout differently -->
				{:else if isDashboardPage}
					<div class="container mx-auto">
						<slot></slot>
					</div>
					<!-- For regular pages -->
				{:else}
					<slot></slot>
				{/if}
			</main>
		</div>

		<!-- Footer - Show on all pages except auth pages -->
		{#if !isAuthPage}
			<Footer bind:this={$footerStore} columns={footerColumns} {socialLinks} />
		{/if}

		<!-- Back to top button -->
		<button
			type="button"
			class="bg-primary-700 hover:bg-primary-800 focus:ring-primary-600 dark:bg-primary-600 dark:hover:bg-primary-500 fixed bottom-8 left-8 z-50 rounded-full p-3 text-white shadow-lg focus:ring-2 focus:ring-offset-2 focus:outline-none"
			on:click={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
			aria-label="العودة إلى الأعلى"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5"
				viewBox="0 0 20 20"
				fill="currentColor"
			>
				<path
					fill-rule="evenodd"
					d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
					clip-rule="evenodd"
				/>
			</svg>
		</button>

		<!-- Toast notifications -->
		{#if $toasts.length > 0}
			<div class="pointer-events-none fixed top-4 left-4 z-50 space-y-2">
				{#each $toasts as toast (toast.id)}
					<Toast
						id={toast.id}
						type={toast.type}
						message={toast.message}
						title={toast.title || ''}
						duration={toast.duration || 5000}
						dismissible={toast.dismissible !== false}
						on:dismiss={handleToastDismiss}
					/>
				{/each}
			</div>
		{/if}
	</div>
{/if}
