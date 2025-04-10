<!--
  Reusable Tabs Component
  A flexible and accessible tabs component for Skeleton UI v2
-->
<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import { isRTL } from '$lib/stores/ui';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// The ID for the tabs component (used for a11y)
	export let id = 'tabs';
	// Array of tab objects: [{ id: 'tab1', label: 'Tab 1', icon: Component }]
	export let tabs = [];
	// ID of the active tab
	export let activeTab = '';
	// Optional CSS classes to apply to the tabs container
	export let classes = '';
	// Tab variant (ghost, ghost-hover, filled, or soft)
	export let variant = 'ghost';
	// Whether tabs should take full width
	export let block = false;
	// Whether tabs should be centered
	export let center = false;
	// Whether to enable transition animation
	export let transition = true;
	// Whether tabs are disabled
	export let disabled = false;
	// Whether to show pill style tabs
	export let pill = false;
	// Border style (border-t, border-b, border-x, border-none)
	export let border = 'border-b';
	// Tab content visibility (auto, visible, manual)
	export let contentVisibility = 'auto';

	// Set initial active tab if not provided
	onMount(() => {
		if (!activeTab && tabs.length > 0) {
			activeTab = tabs[0].id;
			dispatch('change', { id: activeTab });
		}

		// Handle URL hash for tab activation
		if (typeof window !== 'undefined') {
			const hash = window.location.hash.replace('#', '');
			if (hash && tabs.some((tab) => tab.id === hash)) {
				activeTab = hash;
				dispatch('change', { id: activeTab });
			}
		}
	});

	// Handle tab click
	function handleTabClick(tabId) {
		if (disabled) return;
		activeTab = tabId;
		dispatch('change', { id: tabId });

		// Update URL hash for bookmarking
		if (typeof window !== 'undefined') {
			window.history.replaceState(null, null, `#${tabId}`);
		}
	}

	// Build the tabs variant class
	$: variantClass = (() => {
		switch (variant) {
			case 'filled':
				return 'variant-filled';
			case 'soft':
				return 'variant-soft';
			case 'ghost-hover':
				return 'variant-ghost-hover';
			case 'ghost':
			default:
				return 'variant-ghost';
		}
	})();

	// Build border class
	$: borderClass = (() => {
		if (border === 'none') return '';
		return border;
	})();

	// Build the tab button class
	$: tabButtonClass = `tab ${variantClass} ${pill ? 'rounded-token' : ''} ${block ? 'flex-auto' : ''} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`;

	// Access first and last tab for keyboard navigation
	$: firstTab = tabs[0]?.id;
	$: lastTab = tabs[tabs.length - 1]?.id;

	// Handle keyboard navigation
	function handleKeyDown(event, currentTabId) {
		if (disabled) return;

		const currentIndex = tabs.findIndex((tab) => tab.id === currentTabId);

		// Handle keyboard navigation
		switch (event.key) {
			case 'ArrowRight':
				// If RTL, move left (previous tab), else move right (next tab)
				if ($isRTL) {
					if (currentIndex > 0) {
						activeTab = tabs[currentIndex - 1].id;
					} else {
						activeTab = lastTab;
					}
				} else {
					if (currentIndex < tabs.length - 1) {
						activeTab = tabs[currentIndex + 1].id;
					} else {
						activeTab = firstTab;
					}
				}
				dispatch('change', { id: activeTab });
				event.preventDefault();
				break;

			case 'ArrowLeft':
				// If RTL, move right (next tab), else move left (previous tab)
				if ($isRTL) {
					if (currentIndex < tabs.length - 1) {
						activeTab = tabs[currentIndex + 1].id;
					} else {
						activeTab = firstTab;
					}
				} else {
					if (currentIndex > 0) {
						activeTab = tabs[currentIndex - 1].id;
					} else {
						activeTab = lastTab;
					}
				}
				dispatch('change', { id: activeTab });
				event.preventDefault();
				break;

			case 'Home':
				// Move to first tab
				activeTab = firstTab;
				dispatch('change', { id: activeTab });
				event.preventDefault();
				break;

			case 'End':
				// Move to last tab
				activeTab = lastTab;
				dispatch('change', { id: activeTab });
				event.preventDefault();
				break;
		}
	}
</script>

<div class="tabs-container {classes}" {id}>
	<!-- Tab Navigation -->
	<div
		class="tabs {border ? borderClass + ' border-surface-300-600-token' : ''} {center
			? 'flex justify-center'
			: ''} {block ? 'grid grid-cols-' + tabs.length : ''}"
		role="tablist"
		aria-orientation="horizontal"
	>
		{#each tabs as tab, i}
			<button
				class="{tabButtonClass} {activeTab === tab.id ? 'tab-active' : ''}"
				on:click={() => handleTabClick(tab.id)}
				on:keydown={(e) => handleKeyDown(e, tab.id)}
				{disabled}
				aria-selected={activeTab === tab.id}
				id="{id}-tab-{tab.id}"
				aria-controls="{id}-panel-{tab.id}"
				tabindex={activeTab === tab.id ? 0 : -1}
				role="tab"
			>
				{#if tab.icon}
					<div class={$isRTL ? 'ml-2' : 'mr-2'}>
						<svelte:component this={tab.icon} class="w-4 h-4" />
					</div>
				{/if}
				<span>{tab.label}</span>
			</button>
		{/each}
	</div>

	<!-- Tab Content -->
	<div class="tab-content" role="tabpanel">
		{#if contentVisibility === 'auto'}
			<!-- Auto mode: show the selected tab content -->
			<div
				id="{id}-panel-{activeTab}"
				role="tabpanel"
				aria-labelledby="{id}-tab-{activeTab}"
				tabindex="0"
				class="tab-panel"
				class:pt-4={border === 'border-b'}
				class:pb-4={border === 'border-t'}
				class:transition-all={transition}
				class:duration-200={transition}
			>
				<slot />
			</div>
		{:else if contentVisibility === 'visible'}
			<!-- Visible mode: always show tab content -->
			<div class:pt-4={border === 'border-b'} class:pb-4={border === 'border-t'}>
				<slot />
			</div>
		{:else}
			<!-- Manual mode: parent controls visibility through slot -->
			<slot />
		{/if}
	</div>
</div>

<style>
	.tabs-container {
		width: 100%;
	}

	.tab-content {
		position: relative;
	}

	.tab-panel {
		outline: none;
	}

	/* Adjust for RTL layout */
	:global([dir='rtl']) .tab-panel {
		text-align: right;
	}
</style>
