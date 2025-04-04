<script>
	/**
	 * Advanced layout component combining header, footer, sidebar, and content
	 * @component
	 */
	import { onMount, setContext } from 'svelte';
	import { writable } from 'svelte/store';
	import { fly } from 'svelte/transition';
	import Header from './Header.svelte';
	import Footer from './Footer.svelte';
	import Sidebar from './Sidebar.svelte';
	import Navbar from './Navbar.svelte';
	import { theme, toggleTheme } from '$lib/stores/theme';

	// Props
	export let title = ''; // Page title
	export let showHeader = true;
	export let showFooter = true;
	export let showSidebar = false;
	export let sidebarOpen = true;
	export let showNavbar = false;
	export let layout = 'default'; // default, sidebar, blank, dashboard, landing
	export let mainClass = ''; // Additional classes for main content
	export let containerClass = ''; // Additional classes for container
	export let sidebarWidth = '280px';
	export let sidebarMiniWidth = '80px';
	export let collapsible = true;
	export let sidebarPosition = 'right'; // left, right
	export let fullWidth = false; // Remove container padding
	export let bleedTop = false; // Content bleeds to top (no padding-top)
	export let bleedBottom = false; // Content bleeds to bottom (no padding-bottom)
	export let mobileMenuOpen = false;
	export let headerProps = {};
	export let sidebarProps = {};
	export let navbarProps = {};
	export let footerProps = {};

	// Create stores for layout components
	const headerStore = writable(null);
	const sidebarStore = writable(null);
	const navbarStore = writable(null);
	const footerStore = writable(null);

	// Make these stores available to child components
	setContext('layout', {
		header: headerStore,
		sidebar: sidebarStore,
		navbar: navbarStore,
		footer: footerStore,
		sidebarOpen: writable(sidebarOpen)
	});

	// Local state
	let mounted = false;
	let pageWidth = 0;
	let isMobile = false;

	// Set initial state for sidebar
	$: if (mounted && isMobile && sidebarOpen) {
		sidebarOpen = false;
	}

	// Check responsive breakpoints
	function checkResponsive() {
		isMobile = window.innerWidth < 1024;
		pageWidth = window.innerWidth;
	}

	// Handle sidebar toggle
	function toggleSidebar(event) {
		if (event && event.detail && typeof event.detail.isOpen !== 'undefined') {
			sidebarOpen = event.detail.isOpen;
		} else {
			sidebarOpen = !sidebarOpen;
		}
	}

	// Handle mobile menu toggle
	function toggleMobileMenu(event) {
		if (event && event.detail && typeof event.detail.open !== 'undefined') {
			mobileMenuOpen = event.detail.open;
		} else {
			mobileMenuOpen = !mobileMenuOpen;
		}
	}

	// Update title
	$: if (title && typeof document !== 'undefined') {
		document.title = title;
	}

	// Set direction based on language
	onMount(() => {
		// Set RTL direction
		document.documentElement.dir = 'rtl';

		// Check responsive breakpoints
		checkResponsive();
		window.addEventListener('resize', checkResponsive);

		// Now we're mounted
		mounted = true;

		return () => {
			window.removeEventListener('resize', checkResponsive);
		};
	});

	// Compute content padding based on sidebar
	$: contentPadding =
		layout === 'sidebar' && !isMobile && sidebarPosition === 'right'
			? { paddingRight: sidebarOpen ? sidebarWidth : collapsible ? sidebarMiniWidth : '0px' }
			: layout === 'sidebar' && !isMobile && sidebarPosition === 'left'
				? { paddingLeft: sidebarOpen ? sidebarWidth : collapsible ? sidebarMiniWidth : '0px' }
				: {};

	// Container classes
	$: computedContainerClass = [
		!fullWidth ? 'container mx-auto px-4 sm:px-6 lg:px-8' : 'w-full',
		containerClass
	].join(' ');

	// Main content classes with explicit dark mode styling
	$: computedMainClass = [
		'flex-1',
		layout === 'dashboard' ? 'bg-gray-50 dark:bg-gray-900' : 'bg-white dark:bg-gray-900',
		'text-gray-900 dark:text-white',
		bleedTop ? '' : layout === 'dashboard' ? 'pt-6' : 'pt-8',
		bleedBottom ? '' : layout === 'dashboard' ? 'pb-12' : 'pb-16',
		mainClass
	].join(' ');
</script>

<svelte:head>
	{#if title}
		<title>{title}</title>
	{/if}
</svelte:head>

<div class="flex min-h-screen flex-col bg-white text-gray-900 dark:bg-gray-900 dark:text-white">
	<!-- Header Component -->
	{#if showHeader}
		<Header
			{...headerProps}
			bind:this={$headerStore}
			showMobileMenu={mobileMenuOpen}
			on:toggleMenu={toggleMobileMenu}
		>
			<svelte:fragment slot="navigation">
				<slot name="header-navigation"></slot>
			</svelte:fragment>

			<svelte:fragment slot="mobile-navigation">
				<slot name="header-mobile-navigation"></slot>
			</svelte:fragment>
		</Header>
	{/if}

	<!-- Main Content Area -->
	<div class="relative flex flex-1 flex-col bg-white md:flex-row dark:bg-gray-900">
		<!-- Sidebar Component -->
		{#if showSidebar && layout === 'sidebar'}
			<Sidebar
				{...sidebarProps}
				bind:this={$sidebarStore}
				bind:isOpen={sidebarOpen}
				position={sidebarPosition === 'right' ? 'left' : 'right'}
				width={sidebarWidth}
				miniWidth={sidebarMiniWidth}
				on:toggle={toggleSidebar}
			/>
		{/if}

		<!-- Main content -->
		<main
			class={computedMainClass}
			style={Object.entries(contentPadding)
				.map(([key, value]) => `${key}: ${value};`)
				.join(' ')}
		>
			<!-- Navbar Component (if enabled) -->
			{#if showNavbar}
				<Navbar
					{...navbarProps}
					bind:this={$navbarStore}
					bind:showMobileMenu={mobileMenuOpen}
					on:toggleMenu={toggleMobileMenu}
				>
					<svelte:fragment slot="logo">
						<slot name="navbar-logo"></slot>
					</svelte:fragment>

					<svelte:fragment slot="right">
						<slot name="navbar-right"></slot>
					</svelte:fragment>

					<svelte:fragment slot="extra-items">
						<slot name="navbar-extra-items"></slot>
					</svelte:fragment>

					<svelte:fragment slot="mobile-extra-items">
						<slot name="navbar-mobile-extra-items"></slot>
					</svelte:fragment>
				</Navbar>
			{/if}

			<!-- Page Content Container -->
			<div class={computedContainerClass}>
				<!-- Title section -->
				{#if $$slots.title}
					<div class="mt-2 mb-6">
						<slot name="title"></slot>
					</div>
				{/if}

				<!-- Main content -->
				<slot></slot>

				<!-- Bottom section -->
				{#if $$slots.bottom}
					<div class="mt-8">
						<slot name="bottom"></slot>
					</div>
				{/if}
			</div>
		</main>
	</div>

	<!-- Footer Component -->
	{#if showFooter}
		<Footer {...footerProps} bind:this={$footerStore}>
			<svelte:fragment slot="description">
				<slot name="footer-description"></slot>
			</svelte:fragment>
		</Footer>
	{/if}

	<!-- Back to top button -->
	<div class="fixed bottom-8 left-8 z-50">
		<slot name="floating-actions">
			<button
				type="button"
				class="bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 focus:ring-primary-600 rounded-full p-3 text-white shadow-lg focus:ring-2 focus:ring-offset-2 focus:outline-none"
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
		</slot>
	</div>

	<!-- Toast notifications slot -->
	<div class="pointer-events-none fixed inset-0 z-50 flex flex-col items-center space-y-2">
		<div class="fixed right-4 bottom-4 flex flex-col items-end space-y-2">
			<slot name="toasts"></slot>
		</div>
	</div>

	<!-- Modals slot -->
	<slot name="modals"></slot>
</div>
