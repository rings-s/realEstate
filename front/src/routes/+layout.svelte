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
		theme,
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
	import { isAuthenticated, currentUser } from '$lib/stores/auth';

	// Import token manager
	import {
		isTokenExpired,
		getAccessToken,
		getRefreshToken,
		clearTokens
	} from '$lib/utils/tokenManager';

	// Import utils
	import { t } from '$lib/config/translations';
	import '../app.postcss'; // Adjust path if needed - might be app.css in your setup

	// Determine if page is in dashboard layout
	$: isDashboard = $page.url.pathname.startsWith('/dashboard');

	// Paths that don't require authentication
	const publicPaths = [
		'/',
		'/auth/login',
		'/auth/register',
		'/properties',
		'/auctions',
		'/about',
		'/contact',
		'/auth/verify-email',
		'/auth/reset-password',
		'/auth/forgot-password'
	];

	// Handle token refresh
	let refreshTokenInterval;
	let tokenCheckInterval;

	// Check token expiration
	function checkTokenExpiration() {
		if (!browser) return;

		if (isTokenExpired()) {
			// If token expires, try to refresh it
			doRefreshToken();
		}
	}

	// Refresh token function
	async function doRefreshToken() {
		try {
			const refreshToken = getRefreshToken();

			if (!refreshToken) {
				handleAuthFailure();
				return false;
			}

			const response = await fetch(`/api/accounts/token/refresh/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ refresh: refreshToken })
			});

			if (!response.ok) {
				handleAuthFailure();
				return false;
			}

			const data = await response.json();

			// Store new tokens
			localStorage.setItem('access_token', data.access);

			// Calculate token expiry (1 hour from now)
			const expiry = new Date();
			expiry.setHours(expiry.getHours() + 1);
			localStorage.setItem('token_expiry', expiry.toISOString());

			return true;
		} catch (error) {
			console.error('Failed to refresh token:', error);
			handleAuthFailure();
			return false;
		}
	}

	// Handle authentication failure
	function handleAuthFailure() {
		clearTokens();
		isAuthenticated.set(false);
		currentUser.set(null);

		// Redirect to login if on protected route
		if (!isPublicPath($page.url.pathname)) {
			goto('/auth/login');
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

			// Initialize theme from localStorage - Skeleton UI v2 uses data-theme attribute
			const savedTheme = localStorage.getItem('theme') || 'light';
			theme.set(savedTheme);
			document.documentElement.setAttribute('data-theme', savedTheme);
		}
	}

	// Handle auth validation on mount
	onMount(async () => {
		if (browser) {
			// Initialize UI settings
			initUI();

			pageLoading.set(true);

			// Check for token and validate
			const token = getAccessToken();

			if (token) {
				// Check if token is expired
				if (isTokenExpired()) {
					// Try to refresh token
					const refreshed = await doRefreshToken();

					if (!refreshed && !isPublicPath($page.url.pathname)) {
						goto('/auth/login');
					}
				} else {
					// Token is valid, set authenticated state
					isAuthenticated.set(true);
				}
			} else if (!isPublicPath($page.url.pathname)) {
				// No token and on protected route, redirect to login
				goto('/auth/login');
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

	// Apply theme changes when theme or language changes
	$: if (browser) {
		document.documentElement.setAttribute('data-theme', $theme);
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
