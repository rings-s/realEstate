<script>
	/**
	 * Advanced horizontal navigation component with skeleton-ui design principles
	 * Includes dropdowns, mobile responsiveness, and scroll effects
	 * @component
	 */
	import { onMount, createEventDispatcher, tick } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { quintOut, cubicOut } from 'svelte/easing';
	import { tweened } from 'svelte/motion';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { clickOutside } from '$lib/actions/clickOutside';
	import { browser } from '$app/environment';

	// Component props
	export let items = []; // Navigation items array
	export let variant = 'default'; // default, primary, minimal, transparent, bordered
	export let position = 'sticky'; // sticky, fixed, static, relative
	export let hideOnScroll = false; // Hide navbar when scrolling down
	export let colorOnScroll = false; // Add background color on scroll
	export let showMobileMenu = false; // Mobile menu state
	export let activeClass = ''; // Custom active class
	export let activeItemIndicator = true; // Show indicator for active item
	export let indicatorTransition = true; // Animate the active indicator
	export let containerClass = ''; // Additional classes for container
	export let elevated = false; // Add elevation shadow
	export let blur = false; // Glassmorphism effect
	export let appearance = 'light'; // light, dark, or auto (follows theme)
	export let dense = false; // Compact navbar
	export let border = false; // Show border
	export let logo = null; // Logo component or URL
	export let logoText = 'منصة المزادات العقارية'; // Logo text
	export let breakpoint = 'lg'; // Breakpoint for mobile menu: sm, md, lg, xl

	// Create event dispatcher
	const dispatch = createEventDispatcher();

	// Local state
	let navElement;
	let activeItemRect = null;
	let navItems = [];
	let dropdownOpen = null;
	let prevScrollY = 0;
	let currentScrollY = 0;
	let scrollingDown = false;
	let scrollingUp = false;
	let hasScrolled = false;
	let heightTransition = tweened(0, { duration: 300, easing: cubicOut });
	let indicatorStyles = {};
	let hideNav = false;
	let showMenuButton = false;
	let menuButtonElement;

	// Scroll direction tracker
	$: {
		scrollingDown = currentScrollY > prevScrollY;
		scrollingUp = currentScrollY < prevScrollY;
		hasScrolled = currentScrollY > 10;

		if (hideOnScroll) {
			hideNav = scrollingDown && currentScrollY > 100;
		}
	}

	// Calculate breakpoint width
	function getBreakpointWidth() {
		switch (breakpoint) {
			case 'sm':
				return 640;
			case 'md':
				return 768;
			case 'lg':
				return 1024;
			case 'xl':
				return 1280;
			case '2xl':
				return 1536;
			default:
				return 1024;
		}
	}

	// Handle window scroll events
	function handleScroll() {
		if (!browser) return;

		prevScrollY = currentScrollY;
		currentScrollY = window.scrollY;
	}

	// Handle window resize events
	function handleResize() {
		if (!browser) return;

		showMenuButton = window.innerWidth < getBreakpointWidth();

		// Update indicator position on resize
		updateActiveIndicator();
	}

	// Toggle mobile menu
	function toggleMobileMenu() {
		showMobileMenu = !showMobileMenu;
		dispatch('toggleMenu', { open: showMobileMenu });
	}

	// Toggle dropdown menu
	function toggleDropdown(index, event) {
		// Don't toggle if clicking on a link
		if (event?.target?.tagName === 'A') return;

		// Only one dropdown can be open at a time
		if (dropdownOpen === index) {
			dropdownOpen = null;
		} else {
			dropdownOpen = index;
		}
	}

	// Close dropdown when clicking outside
	function closeDropdown() {
		dropdownOpen = null;
	}

	// Set up intersection observer for navbar items
	function observeNavItems() {
		if (!browser || !navElement) return;

		// Get all nav items
		navItems = Array.from(navElement.querySelectorAll('[data-nav-item]'));

		// Update the active indicator position
		updateActiveIndicator();
	}

	// Update the active indicator position and dimensions
	function updateActiveIndicator() {
		if (!activeItemIndicator || !navItems.length) return;

		// Find the active item
		const activeItemElement = navItems.find((el) => el.getAttribute('aria-current') === 'page');

		if (activeItemElement) {
			const rect = activeItemElement.getBoundingClientRect();
			const navRect = navElement.getBoundingClientRect();

			// Calculate position relative to navbar
			activeItemRect = {
				left: rect.left - navRect.left,
				top: rect.top - navRect.top + navRect.height - 2,
				width: rect.width
			};

			// Update indicator styles
			indicatorStyles = {
				left: `${activeItemRect.left}px`,
				width: `${activeItemRect.width}px`,
				transition: indicatorTransition ? 'all 0.2s ease-out' : 'none'
			};
		} else {
			activeItemRect = null;
		}
	}

	// Check if an item is active based on URL
	function isActive(href) {
		if (!href) return false;
		if (href === '/') return $page.url.pathname === '/';
		return $page.url.pathname.startsWith(href);
	}

	// Set up component when mounted
	onMount(() => {
		if (browser) {
			// Handle initial resize
			handleResize();

			// Add event listeners
			window.addEventListener('scroll', handleScroll, { passive: true });
			window.addEventListener('resize', handleResize, { passive: true });

			// Set up intersections
			observeNavItems();

			// Clean up
			return () => {
				window.removeEventListener('scroll', handleScroll);
				window.removeEventListener('resize', handleResize);
			};
		}
	});

	// Update the active indicator when page changes
	$: if ($page && browser && navElement) {
		tick().then(updateActiveIndicator);
	}

	// Variant-specific classes
	const variantClasses = {
		default: 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200',
		primary: 'bg-primary-600 text-white',
		minimal: 'bg-transparent text-gray-800 dark:text-gray-200',
		transparent: 'bg-transparent text-gray-800 dark:text-white',
		bordered:
			'bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 text-gray-800 dark:text-gray-200'
	};

	// Position classes
	const positionClasses = {
		sticky: 'sticky top-0 z-40',
		fixed: 'fixed top-0 left-0 right-0 z-40',
		static: 'relative',
		relative: 'relative'
	};

	// Get default active class based on variant
	function getDefaultActiveClass() {
		switch (variant) {
			case 'primary':
				return 'bg-primary-700 text-white';
			case 'minimal':
			case 'transparent':
				return 'font-medium text-primary-600 dark:text-primary-400';
			default:
				return 'font-medium text-primary-600 dark:text-primary-400';
		}
	}

	// Computed classes for navbar
	$: navbarClasses = [
		// Base classes
		'transition-all duration-300',
		// Variant classes - override with transparent on scroll settings
		variant === 'transparent' && hasScrolled && colorOnScroll
			? 'bg-white/90 dark:bg-gray-900/90 text-gray-800 dark:text-gray-200 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800'
			: variantClasses[variant],
		// Position classes
		positionClasses[position],
		// Appearance-based classes
		appearance === 'dark' ? 'text-white' : appearance === 'auto' ? '' : 'text-gray-800',
		// Conditional classes
		elevated ? 'shadow-md' : '',
		blur ? 'backdrop-blur-md bg-opacity-80 dark:bg-opacity-80' : '',
		border && !variantClasses[variant].includes('border')
			? 'border-b border-gray-200 dark:border-gray-800'
			: '',
		hideNav ? '-translate-y-full' : 'translate-y-0',
		containerClass || '',
		dense ? 'py-1' : 'py-3'
	].join(' ');

	// Computed active class
	$: computedActiveClass = activeClass || getDefaultActiveClass();
</script>

<svelte:window on:scroll={handleScroll} on:resize={handleResize} />

<nav
	bind:this={navElement}
	class={navbarClasses}
	data-variant={variant}
	data-position={position}
	aria-label="قائمة التنقل الرئيسية"
>
	<div class="container mx-auto px-4 lg:px-6">
		<div class={`flex items-center justify-between ${dense ? 'h-12' : 'h-16'}`}>
			<!-- Logo section -->
			<div class="flex flex-shrink-0 items-center">
				{#if logo}
					<a href="/" class="flex items-center">
						{#if typeof logo === 'string'}
							<img src={logo} alt={logoText} class="h-8 w-auto" />
						{:else}
							<svelte:component this={logo} />
						{/if}
						<span class="mr-3 text-lg font-bold">{logoText}</span>
					</a>
				{:else}
					<a href="/" class="flex items-center">
						<div
							class="bg-primary-600 flex h-8 w-8 items-center justify-center rounded-md text-white"
						>
							<span class="text-sm font-bold">{logoText.charAt(0)}</span>
						</div>
						<span class="mr-3 text-lg font-bold">{logoText}</span>
					</a>
				{/if}
			</div>

			<!-- Main navigation - desktop -->
			<div
				class={`hidden ${breakpoint}:flex ${breakpoint}:items-center ${breakpoint}:space-x-4 ${breakpoint}:space-x-reverse`}
			>
				{#each items as item, index}
					{#if item.children && item.children.length > 0}
						<!-- Item with dropdown -->
						<div class="relative" use:clickOutside={closeDropdown}>
							<button
								type="button"
								class={`hover:bg-opacity-10 flex items-center rounded-md px-3 py-2.5 transition-colors hover:bg-gray-700 ${isActive(item.href) ? computedActiveClass : ''}`}
								on:click={(e) => toggleDropdown(index, e)}
								aria-expanded={dropdownOpen === index}
								aria-haspopup="true"
								data-nav-item
								aria-current={isActive(item.href) ? 'page' : undefined}
							>
								{#if item.icon}
									<span class="ml-2 inline-flex items-center justify-center">{@html item.icon}</span
									>
								{/if}
								<span>{item.label}</span>
								<svg
									class={`mr-1 h-4 w-4 transition-transform duration-200 ${dropdownOpen === index ? 'rotate-180 transform' : ''}`}
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									aria-hidden="true"
								>
									<path
										fill-rule="evenodd"
										d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>

							<!-- Dropdown menu -->
							{#if dropdownOpen === index}
								<div
									class="ring-opacity-5 absolute left-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black focus:outline-none dark:bg-gray-800"
									role="menu"
									aria-orientation="vertical"
									in:fly={{ y: 5, duration: 150, easing: quintOut }}
									out:fade={{ duration: 100 }}
								>
									<div class="py-1" role="none">
										{#each item.children as child}
											<a
												href={child.href}
												class={`block px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${isActive(child.href) ? computedActiveClass : 'text-gray-700 dark:text-gray-300'}`}
												role="menuitem"
												on:click={() => {
													dropdownOpen = null;
												}}
											>
												<div class="flex items-center">
													{#if child.icon}
														<span class="ml-2 inline-flex items-center justify-center"
															>{@html child.icon}</span
														>
													{/if}
													<span>{child.label}</span>

													{#if child.badge}
														<span
															class="mr-auto inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium {child
																.badge.color ||
																'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'}"
														>
															{child.badge.text}
														</span>
													{/if}
												</div>
											</a>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{:else}
						<!-- Regular item -->
						<a
							href={item.href}
							class={`hover:bg-opacity-10 rounded-md px-3 py-2.5 transition-colors hover:bg-gray-700 ${isActive(item.href) ? computedActiveClass : ''}`}
							data-nav-item
							aria-current={isActive(item.href) ? 'page' : undefined}
						>
							{#if item.icon}
								<span class="ml-2 inline-flex items-center justify-center">{@html item.icon}</span>
							{/if}
							<span>{item.label}</span>

							{#if item.badge}
								<span
									class="mr-1 inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium {item
										.badge.color ||
										'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'}"
								>
									{item.badge.text}
								</span>
							{/if}
						</a>
					{/if}
				{/each}

				<!-- Extra items slot -->
				<slot name="extra-items"></slot>
			</div>

			<!-- Mobile menu button -->
			<div class={`${breakpoint}:hidden`}>
				<button
					bind:this={menuButtonElement}
					type="button"
					class="hover:bg-opacity-10 focus:ring-primary-500 inline-flex items-center justify-center rounded-md p-2 text-current hover:bg-gray-700 focus:ring-2 focus:ring-offset-2 focus:outline-none"
					aria-expanded={showMobileMenu}
					aria-controls="mobile-menu"
					on:click={toggleMobileMenu}
				>
					<span class="sr-only">{showMobileMenu ? 'إغلاق القائمة' : 'فتح القائمة'}</span>
					{#if showMobileMenu}
						<svg
							class="h-6 w-6"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							aria-hidden="true"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					{:else}
						<svg
							class="h-6 w-6"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							aria-hidden="true"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 6h16M4 12h16M4 18h16"
							/>
						</svg>
					{/if}
				</button>
			</div>

			<!-- Right section -->
			<div class={`hidden ${breakpoint}:flex items-center`}>
				<slot name="right"></slot>
			</div>
		</div>
	</div>

	<!-- Active item indicator -->
	{#if activeItemIndicator && activeItemRect}
		<div
			class="bg-primary-600 dark:bg-primary-400 absolute h-0.5 -translate-y-full transform rounded-full transition-all"
			style={Object.entries(indicatorStyles)
				.map(([key, value]) => `${key}: ${value}`)
				.join(';')}
		></div>
	{/if}

	<!-- Mobile menu -->
	{#if showMobileMenu}
		<div
			id="mobile-menu"
			class={`${breakpoint}:hidden border-t bg-white dark:border-gray-800 dark:bg-gray-900`}
			transition:slide={{ duration: 200, easing: cubicOut }}
		>
			<div class="space-y-1 px-2 pt-2 pb-3">
				{#each items as item, index}
					{#if item.children && item.children.length > 0}
						<!-- Mobile dropdown item -->
						<div>
							<button
								type="button"
								class={`flex w-full items-center justify-between rounded-md px-3 py-2.5 text-right ${isActive(item.href) ? computedActiveClass : 'text-gray-700 dark:text-gray-300'} hover:bg-gray-100 dark:hover:bg-gray-800`}
								on:click={(e) => toggleDropdown(index, e)}
								aria-expanded={dropdownOpen === index}
							>
								<div class="flex items-center">
									{#if item.icon}
										<span class="ml-2 inline-flex items-center justify-center"
											>{@html item.icon}</span
										>
									{/if}
									<span>{item.label}</span>

									{#if item.badge}
										<span
											class="mr-2 inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium {item
												.badge.color ||
												'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'}"
										>
											{item.badge.text}
										</span>
									{/if}
								</div>
								<svg
									class={`h-5 w-5 transition-transform duration-200 ${dropdownOpen === index ? 'rotate-180 transform' : ''}`}
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
										clip-rule="evenodd"
									/>
								</svg>
							</button>

							<!-- Mobile dropdown children -->
							{#if dropdownOpen === index}
								<div transition:slide={{ duration: 200 }}>
									<div
										class="mt-2 mr-3.5 space-y-1 border-r border-gray-300 pr-4 dark:border-gray-700"
									>
										{#each item.children as child}
											<a
												href={child.href}
												class={`block rounded-md px-3 py-2 ${isActive(child.href) ? computedActiveClass : 'text-gray-700 dark:text-gray-300'} hover:bg-gray-100 dark:hover:bg-gray-800`}
												on:click={() => {
													showMobileMenu = false;
													dropdownOpen = null;
												}}
											>
												<div class="flex items-center">
													{#if child.icon}
														<span class="ml-2 inline-flex items-center justify-center"
															>{@html child.icon}</span
														>
													{/if}
													<span>{child.label}</span>

													{#if child.badge}
														<span
															class="mr-auto inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium {child
																.badge.color ||
																'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'}"
														>
															{child.badge.text}
														</span>
													{/if}
												</div>
											</a>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{:else}
						<!-- Mobile regular item -->
						<a
							href={item.href}
							class={`block rounded-md px-3 py-2.5 ${isActive(item.href) ? computedActiveClass : 'text-gray-700 dark:text-gray-300'} hover:bg-gray-100 dark:hover:bg-gray-800`}
							on:click={() => {
								showMobileMenu = false;
							}}
						>
							<div class="flex items-center">
								{#if item.icon}
									<span class="ml-2 inline-flex items-center justify-center">{@html item.icon}</span
									>
								{/if}
								<span>{item.label}</span>

								{#if item.badge}
									<span
										class="mr-auto inline-flex items-center justify-center rounded-full px-2 py-0.5 text-xs font-medium {item
											.badge.color ||
											'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'}"
									>
										{item.badge.text}
									</span>
								{/if}
							</div>
						</a>
					{/if}
				{/each}

				<!-- Mobile extra items slot -->
				<slot name="mobile-extra-items"></slot>
			</div>

			<!-- Mobile right section -->
			<div class="border-t border-gray-200 px-4 py-3 dark:border-gray-700">
				<slot name="mobile-right"></slot>
			</div>
		</div>
	{/if}
</nav>
