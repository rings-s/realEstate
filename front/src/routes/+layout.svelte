<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { fly, fade } from 'svelte/transition';

	// Import UI stores and components
	import {
		language,
		isRTL,
		darkMode,
		isSidebarOpen,
		pageLoading,
		toast,
		uiStore
	} from '$lib/stores/ui';
	import Header from '$lib/components/common/Header.svelte';
	import Footer from '$lib/components/common/Footer.svelte';
	import Sidebar from '$lib/components/common/Sidebar.svelte';
	import Alert from '$lib/components/common/Alert.svelte';

	// Import auth store
	import {
		isAuthenticated,
		refreshToken,
		validateToken,
		logout,
		currentUser
	} from '$lib/stores/auth';

	// Import utils
	import { t } from '$lib/config/translations';
	import { TOKEN_KEY, REFRESH_TOKEN_KEY, TOKEN_EXPIRY_KEY } from '$lib/config/constants';
	import '../app.postcss'; // Adjust path if needed - might be app.css in your setup

	// Determine if page is in dashboard layout
	$: isDashboard = $page.url.pathname.startsWith('/dashboard');

	// Paths that don't require authentication
	const publicPaths = [
		'/',
		'/login',
		'/register',
		'/properties',
		'/auctions',
		'/about',
		'/contact',
		'/verify-email',
		'/reset-password',
		'/forgot-password'
	];

	// Handle token refresh
	let refreshTokenInterval;
	let tokenCheckInterval;

	// Check token expiration
	function checkTokenExpiration() {
		if (!browser) return;

		const tokenExpiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

		if (!tokenExpiry) return;

		const expiryDate = new Date(tokenExpiry);
		const now = new Date();

		// If token expires in less than 5 minutes, refresh it
		const fiveMinutes = 5 * 60 * 1000;
		if (expiryDate.getTime() - now.getTime() < fiveMinutes) {
			doRefreshToken();
		}
	}

	// Refresh token function
	async function doRefreshToken() {
		try {
			const refreshed = await refreshToken();
			if (!refreshed) {
				// If refresh fails, redirect to login for protected routes
				if (!isPublicPath($page.url.pathname)) {
					goto('/login');
				}
			}
		} catch (error) {
			console.error('Failed to refresh token:', error);
			// Handle failed token refresh by logging out
			if (!isPublicPath($page.url.pathname)) {
				await logout();
				goto('/login');
			}
		}
	}

	// Check if a path is public
	function isPublicPath(path) {
		return publicPaths.some((publicPath) => {
			// Exact match
			if (publicPath === path) return true;
			// Root path '/' should match exactly
			if (publicPath === '/' && path !== '/') return false;
			// Other paths should match by prefix
			return path.startsWith(publicPath) && publicPath !== '/';
		});
	}

	// Initialize the UI settings
	function initUI() {
		if (browser) {
			// Initialize language from localStorage
			const savedLanguage = localStorage.getItem('language') || 'ar';
			language.set(savedLanguage);
			document.documentElement.setAttribute('lang', savedLanguage);

			// Initialize direction based on language
			const direction = savedLanguage === 'ar' ? 'rtl' : 'ltr';
			isRTL.set(direction === 'rtl');
			document.documentElement.setAttribute('dir', direction);

			// Initialize dark mode from localStorage
			const savedDarkMode = localStorage.getItem('darkMode') === 'true';
			darkMode.set(savedDarkMode);
			document.documentElement.classList.toggle('dark', savedDarkMode);
		}
	}

	// Handle auth validation on mount
	onMount(async () => {
		if (browser) {
			// Initialize UI settings
			initUI();

			pageLoading.set(true);

			// Check for token and validate
			const token = localStorage.getItem(TOKEN_KEY);
			const refreshTokenValue = localStorage.getItem(REFRESH_TOKEN_KEY);

			if (token) {
				try {
					// Try to validate token
					const isValid = await validateToken();

					if (!isValid && refreshTokenValue) {
						// Try to refresh token if validation fails
						await doRefreshToken();
					}

					// If still not authenticated and on protected route, redirect to login
					if (!$isAuthenticated && !isPublicPath($page.url.pathname)) {
						goto('/login');
					}
				} catch (error) {
					console.error('Error validating auth:', error);

					// Clear auth if validation completely fails
					localStorage.removeItem(TOKEN_KEY);
					localStorage.removeItem(REFRESH_TOKEN_KEY);
					localStorage.removeItem(TOKEN_EXPIRY_KEY);
					isAuthenticated.set(false);

					// Redirect to login if on protected route
					if (!isPublicPath($page.url.pathname)) {
						goto('/login');
					}
				}
			} else if (!isPublicPath($page.url.pathname)) {
				// No token and on protected route, redirect to login
				goto('/login');
			}

			// Set up token refresh interval (check every minute)
			tokenCheckInterval = setInterval(checkTokenExpiration, 60000);

			// Set up full token refresh (every 20 minutes to be safe)
			refreshTokenInterval = setInterval(doRefreshToken, 20 * 60 * 1000);

			pageLoading.set(false);
		}
	});

	// Clean up intervals on destroy
	onDestroy(() => {
		if (tokenCheckInterval) clearInterval(tokenCheckInterval);
		if (refreshTokenInterval) clearInterval(refreshTokenInterval);
	});

	// Apply theme changes when darkMode or language changes
	$: if (browser) {
		document.documentElement.classList.toggle('dark', $darkMode);
		document.documentElement.setAttribute('lang', $language);
		document.documentElement.setAttribute('dir', $isRTL ? 'rtl' : 'ltr');
	}
</script>

<!-- Apply directional styles if RTL -->
<svelte:head>
	{#if $isRTL}
		<style>
			/* Adjust paddings and margins for RTL */
			[dir='rtl'] .ml-4 {
				margin-right: 1rem;
				margin-left: 0;
			}
			[dir='rtl'] .mr-4 {
				margin-left: 1rem;
				margin-right: 0;
			}
			[dir='rtl'] .pl-4 {
				padding-right: 1rem;
				padding-left: 0;
			}
			[dir='rtl'] .pr-4 {
				padding-left: 1rem;
				padding-right: 0;
			}
		</style>
	{/if}
</svelte:head>

{#if $pageLoading}
	<!-- Loading overlay -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-surface-900/50 backdrop-blur-sm"
	>
		<div class="card p-8 shadow-xl">
			<div class="flex flex-col items-center gap-4">
				<div class="spinner-circle-secondary w-12 h-12"></div>
				<p>{t('loading', $language, { default: 'جاري التحميل...' })}</p>
			</div>
		</div>
	</div>
{:else}
	<!-- Main layout -->
	<div class="flex h-screen overflow-hidden bg-surface-50-900-token">
		<!-- Sidebar (visible based on isSidebarOpen for mobile, always visible on desktop for dashboard) -->
		<Sidebar dashboard={isDashboard} />

		<!-- Main content -->
		<div class="flex flex-col flex-1 w-full overflow-hidden">
			<!-- Header -->
			<Header minimal={isDashboard} />

			<!-- Content area -->
			<main class="flex-1 overflow-y-auto">
				<!-- Page content -->
				<div class="container mx-auto p-4 mb-auto min-h-[calc(100vh-10rem)]">
					<slot />
				</div>

				<!-- Footer -->
				<Footer minimal={isDashboard} />
			</main>
		</div>
	</div>

	<!-- Toast notification -->
	{#if $toast.isVisible}
		<div class="toast" class:toast-end={!$isRTL} class:toast-start={$isRTL}>
			<div
				class="alert {$toast.type === 'error'
					? 'variant-filled-error'
					: $toast.type === 'success'
						? 'variant-filled-success'
						: $toast.type === 'warning'
							? 'variant-filled-warning'
							: 'variant-filled-primary'}"
				transition:fly={{ y: 50, duration: 200 }}
			>
				<div class="flex items-center gap-4">
					{#if $toast.type === 'error'}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"
							></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg
						>
					{:else if $toast.type === 'success'}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline
								points="22 4 12 14.01 9 11.01"
							></polyline></svg
						>
					{:else if $toast.type === 'warning'}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><path
								d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
							></path><line x1="12" y1="9" x2="12" y2="13"></line><line
								x1="12"
								y1="17"
								x2="12.01"
								y2="17"
							></line></svg
						>
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"
							></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg
						>
					{/if}
					<div class="flex-1 {$isRTL ? 'text-right' : 'text-left'}">
						<p>{$toast.message}</p>
					</div>
					<button class="btn btn-sm btn-icon variant-ghost" on:click={() => uiStore.hideToast()}>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="20"
							height="20"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"
							></line></svg
						>
					</button>
				</div>
			</div>
		</div>
	{/if}
{/if}
