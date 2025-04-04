<script>
	/**
	 * Advanced sidebar navigation component with nested items and responsiveness
	 * @component
	 */
	import { onMount, createEventDispatcher, tick } from 'svelte';
	import { writable } from 'svelte/store';
	import { slide, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import { theme } from '$lib/stores/theme';
	import { page } from '$app/stores';

	// Props
	export let isOpen = true; // Whether sidebar is open
	export let items = []; // Navigation items array
	export let collapsible = true; // Can sidebar be collapsed
	export let breakpoint = 'lg'; // Responsive breakpoint
	export let mini = true; // Show mini sidebar when collapsed
	export let position = 'fixed'; // fixed or static
	export let width = '280px'; // Full sidebar width
	export let miniWidth = '80px'; // Mini sidebar width
	export let logo = undefined; // Logo URL
	export let logoText = 'المزادات العقارية'; // Logo text
	export let showCloseButton = true; // Show close button on mobile
	export let userInfo = undefined; // User information
	export let sidebarStyle = {}; // Additional sidebar styles

	const dispatch = createEventDispatcher();

	// Local state
	const expandedItems = writable({});
	let mounted = false;
	let isMobile = false;

	// Set initial expanded state based on active item
	onMount(() => {
		const checkIfMobile = () => {
			switch (breakpoint) {
				case 'sm':
					isMobile = window.innerWidth < 640;
					break;
				case 'md':
					isMobile = window.innerWidth < 768;
					break;
				case 'lg':
					isMobile = window.innerWidth < 1024;
					break;
				case 'xl':
					isMobile = window.innerWidth < 1280;
					break;
				default:
					isMobile = window.innerWidth < 1024;
			}

			// Auto-close sidebar on mobile
			if (isMobile && isOpen) {
				isOpen = false;
				dispatch('toggle', { isOpen });
			}
		};

		// Set initial active and expanded items
		let pathToExpand = $page.url.pathname;

		items.forEach((item, index) => {
			if (item.children) {
				const hasActiveChild = item.children.some((child) => pathToExpand.startsWith(child.href));

				if (hasActiveChild) {
					$expandedItems[index] = true;
				}
			}
		});

		// Check responsive state
		checkIfMobile();
		window.addEventListener('resize', checkIfMobile);
		mounted = true;

		return () => {
			window.removeEventListener('resize', checkIfMobile);
		};
	});

	// Toggle sidebar
	function toggleSidebar() {
		isOpen = !isOpen;
		dispatch('toggle', { isOpen });
	}

	// Toggle a collapsible section
	function toggleSection(index) {
		$expandedItems[index] = !$expandedItems[index];
		$expandedItems = $expandedItems; // Trigger reactivity
	}

	// Check if an item is active
	function isActive(href) {
		return $page.url.pathname.startsWith(href);
	}

	// Compute sidebar width based on state
	$: sidebarWidth = isOpen ? width : mini ? miniWidth : '0px';

	// Compute sidebar classes
	$: sidebarClasses = [
		'h-screen overflow-y-auto bg-white dark:bg-gray-900 border-l dark:border-gray-800 shadow-lg z-40 transition-all duration-300 ease-in-out',
		position === 'fixed' ? 'fixed top-0 left-0' : 'relative',
		position === 'fixed' && !isOpen && !mini ? 'hidden' : '',
		$$props.class || ''
	].join(' ');
</script>

<!-- Backdrop for mobile -->
{#if isMobile && isOpen && position === 'fixed'}
	<div
		class="bg-opacity-50 fixed inset-0 z-30 bg-black"
		on:click={toggleSidebar}
		on:keydown={(e) => e.key === 'Escape' && toggleSidebar()}
		role="button"
		tabindex="0"
		aria-label="إغلاق القائمة الجانبية"
		transition:fade={{ duration: 150 }}
	></div>
{/if}

<!-- Sidebar container -->
<aside
	class={sidebarClasses}
	style="width: {sidebarWidth}; {Object.entries(sidebarStyle)
		.map(([key, value]) => `${key}: ${value};`)
		.join(' ')}"
	aria-hidden={!isOpen}
>
	<!-- Header with logo -->
	<div class="flex h-16 items-center justify-between border-b px-4 dark:border-gray-800">
		{#if isOpen}
			<div class="flex items-center space-x-3 space-x-reverse">
				{#if logo}
					<img src={logo} alt={logoText} class="h-8 w-auto" />
				{:else}
					<div
						class="bg-primary-600 flex h-8 w-8 items-center justify-center rounded-md text-white"
					>
						<span class="text-lg font-bold">{logoText.charAt(0)}</span>
					</div>
				{/if}

				<h1 class="truncate text-lg font-bold text-gray-900 dark:text-white">
					{logoText}
				</h1>
			</div>
		{:else if mini}
			<div class="mx-auto flex items-center justify-center">
				{#if logo}
					<img src={logo} alt={logoText} class="h-8 w-auto" />
				{:else}
					<div
						class="bg-primary-600 flex h-8 w-8 items-center justify-center rounded-md text-white"
					>
						<span class="text-lg font-bold">{logoText.charAt(0)}</span>
					</div>
				{/if}
			</div>
		{/if}

		{#if isMobile && showCloseButton}
			<button
				type="button"
				class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
				on:click={toggleSidebar}
				aria-label="إغلاق"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		{:else if collapsible && !isMobile}
			<button
				type="button"
				class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
				on:click={toggleSidebar}
				aria-label={isOpen ? 'طي القائمة' : 'فتح القائمة'}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 transform {isOpen ? 'rotate-180' : ''}"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<!-- User section if provided -->
	{#if userInfo && isOpen}
		<div class="border-b px-4 py-3 dark:border-gray-800">
			<div class="flex items-center">
				{#if userInfo.avatar}
					<img src={userInfo.avatar} alt={userInfo.name} class="h-10 w-10 rounded-full" />
				{:else}
					<div
						class="bg-primary-600 flex h-10 w-10 items-center justify-center rounded-full text-white"
					>
						<span class="text-sm font-medium">{userInfo.name.charAt(0)}</span>
					</div>
				{/if}

				<div class="mr-3">
					<p class="text-sm font-medium text-gray-900 dark:text-white">{userInfo.name}</p>
					<p class="text-xs text-gray-500 dark:text-gray-400">{userInfo.role}</p>
				</div>
			</div>
		</div>
	{:else if userInfo && !isOpen && mini}
		<div class="flex justify-center border-b px-2 py-3 dark:border-gray-800">
			{#if userInfo.avatar}
				<img src={userInfo.avatar} alt={userInfo.name} class="h-10 w-10 rounded-full" />
			{:else}
				<div
					class="bg-primary-600 flex h-10 w-10 items-center justify-center rounded-full text-white"
					title={userInfo.name}
				>
					<span class="text-sm font-medium">{userInfo.name.charAt(0)}</span>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Navigation menu -->
	<nav class="overflow-y-auto py-4">
		<ul class="space-y-1">
			{#each items as item, index}
				<li>
					{#if item.children && item.children.length > 0}
						<!-- Item with children - collapsible section -->
						<button
							type="button"
							class="flex w-full items-center justify-between rounded-md px-4 py-2.5 text-right text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 {$expandedItems[
								index
							]
								? 'bg-gray-100 dark:bg-gray-800'
								: ''}"
							on:click={() => toggleSection(index)}
							aria-expanded={$expandedItems[index] || false}
							aria-controls={`sidebar-section-${index}`}
						>
							<span class="flex items-center">
								{#if item.icon}
									<span
										class="ml-2 inline-flex h-5 w-5 items-center justify-center {isActive(item.href)
											? 'text-primary-600 dark:text-primary-400'
											: 'text-gray-500 dark:text-gray-400'}">{@html item.icon}</span
									>
								{/if}
								{#if isOpen}
									<span class="text-sm font-medium">{item.label}</span>
								{/if}
							</span>

							{#if isOpen}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 text-gray-500 transition-transform duration-200 dark:text-gray-400 {$expandedItems[
										index
									]
										? 'rotate-180 transform'
										: ''}"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
										clip-rule="evenodd"
									/>
								</svg>
							{/if}
						</button>

						<!-- Collapsible children -->
						{#if $expandedItems[index] && isOpen}
							<div
								id={`sidebar-section-${index}`}
								transition:slide={{ duration: 200, easing: quintOut }}
							>
								<ul class="mt-1 mr-2 space-y-1 border-r pr-2 dark:border-gray-700">
									{#each item.children as child}
										<li>
											<a
												href={child.href}
												class="flex items-center rounded-md px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 {isActive(
													child.href
												)
													? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'
													: ''}"
												aria-current={isActive(child.href) ? 'page' : undefined}
											>
												{#if child.icon}
													<span
														class="ml-2 inline-flex h-4 w-4 items-center justify-center {isActive(
															child.href
														)
															? 'text-primary-600 dark:text-primary-400'
															: 'text-gray-500 dark:text-gray-400'}">{@html child.icon}</span
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
											</a>
										</li>
									{/each}
								</ul>
							</div>
						{/if}
					{:else}
						<!-- Regular menu item -->
						<a
							href={item.href}
							class="flex items-center rounded-md px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 {isActive(
								item.href
							)
								? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:bg-opacity-30 dark:text-primary-400'
								: ''}"
							aria-current={isActive(item.href) ? 'page' : undefined}
						>
							{#if item.icon}
								<span
									class="ml-2 inline-flex h-5 w-5 items-center justify-center {isActive(item.href)
										? 'text-primary-600 dark:text-primary-400'
										: 'text-gray-500 dark:text-gray-400'}">{@html item.icon}</span
								>
							{/if}

							{#if isOpen}
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
							{:else if mini && item.badge}
								<span class="absolute top-1 left-1 flex h-3 w-3">
									<span
										class="bg-primary-400 absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
									></span>
									<span class="bg-primary-500 relative inline-flex h-3 w-3 rounded-full"></span>
								</span>
							{/if}
						</a>
					{/if}
				</li>
			{/each}
		</ul>
	</nav>

	<!-- Bottom actions -->
	{#if isOpen}
		<div class="mt-auto border-t p-4 dark:border-gray-800">
			<slot name="footer"></slot>

			{#if !$$slots.footer}
				<button
					type="button"
					class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 flex w-full items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-white focus:ring-2 focus:ring-offset-2 focus:outline-none"
					on:click={() => dispatch('help')}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-2 h-5 w-5"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
							clip-rule="evenodd"
						/>
					</svg>
					الدعم والمساعدة
				</button>
			{/if}
		</div>
	{:else if mini}
		<div class="mt-auto flex justify-center border-t p-2 dark:border-gray-800">
			<button
				type="button"
				class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300"
				on:click={() => dispatch('help')}
				aria-label="المساعدة"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		</div>
	{/if}
</aside>
