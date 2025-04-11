<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import { isRTL } from '$lib/stores/ui';

	const dispatch = createEventDispatcher();

	// Props
	export let id = 'tabs';
	export let tabs = [];
	export let activeTab = tabs[0]?.id || '';
	export let classes = '';
	export let variant = 'ghost';
	export let border = 'border-b';
	export let showValidationErrors = true;

	// Set initial active tab if not provided
	onMount(() => {
		if (!activeTab && tabs.length > 0) {
			activeTab = tabs[0].id;
			dispatch('change', { id: activeTab });
		}
	});

	// Handle tab change with validation
	function handleTabChange(tab) {
		// If tab has a validation function
		if (tab.isValid && !tab.isValid()) {
			// Dispatch validation error if validation fails
			if (showValidationErrors) {
				dispatch('validation-error', { tab });
			}
			return;
		}

		// Change active tab
		activeTab = tab.id;
		dispatch('change', { id: tab.id });
	}

	// Determine tab button classes
	function getTabClasses(tab) {
		const baseClasses = 'px-4 py-2 flex items-center transition-all duration-200 ease-in-out';
		const activeClasses =
			tab.id === activeTab
				? 'font-semibold text-primary-600 dark:text-primary-400'
				: 'text-surface-600 dark:text-surface-300 hover:text-primary-500';

		// Variant-specific classes
		let variantClasses = '';
		switch (variant) {
			case 'filled':
				variantClasses =
					tab.id === activeTab ? 'bg-primary-500 text-white' : 'hover:bg-surface-100/50';
				break;
			case 'soft':
				variantClasses = tab.id === activeTab ? 'bg-primary-500/10' : 'hover:bg-surface-100/50';
				break;
			case 'ghost-hover':
				variantClasses =
					tab.id === activeTab
						? 'bg-primary-500/10 rounded-token'
						: 'hover:bg-surface-100/50 rounded-token';
				break;
			case 'underline':
				variantClasses =
					tab.id === activeTab
						? 'border-b-2 border-primary-500'
						: 'border-b-2 border-transparent hover:border-surface-500/30';
				break;
			default: // 'ghost'
				variantClasses = tab.id === activeTab ? 'bg-surface-100/50' : 'hover:bg-surface-100/50';
		}

		return `${baseClasses} ${activeClasses} ${variantClasses}`;
	}

	// Keyboard navigation
	function handleKeyDown(event, currentTabId) {
		const currentIndex = tabs.findIndex((tab) => tab.id === currentTabId);

		switch (event.key) {
			case 'ArrowRight':
				if ($isRTL) {
					// Move to previous tab in RTL
					const prevIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
					handleTabChange(tabs[prevIndex]);
				} else {
					// Move to next tab in LTR
					const nextIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
					handleTabChange(tabs[nextIndex]);
				}
				event.preventDefault();
				break;

			case 'ArrowLeft':
				if ($isRTL) {
					// Move to next tab in RTL
					const nextIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
					handleTabChange(tabs[nextIndex]);
				} else {
					// Move to previous tab in LTR
					const prevIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
					handleTabChange(tabs[prevIndex]);
				}
				event.preventDefault();
				break;

			case 'Home':
				handleTabChange(tabs[0]);
				event.preventDefault();
				break;

			case 'End':
				handleTabChange(tabs[tabs.length - 1]);
				event.preventDefault();
				break;
		}
	}
</script>

<div class="tabs-container {classes}" {id}>
	<!-- Tab Navigation -->
	<div
		class="tabs {border === 'border-b' ? 'border-b border-surface-300-600-token' : ''} flex"
		role="tablist"
		aria-orientation="horizontal"
	>
		{#each tabs as tab}
			<button
				type="button"
				class={getTabClasses(tab)}
				on:click={() => handleTabChange(tab)}
				on:keydown={(e) => handleKeyDown(e, tab.id)}
				aria-selected={activeTab === tab.id}
				role="tab"
			>
				{#if tab.icon}
					<svelte:component this={tab.icon} class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
				{/if}
				<span>{tab.label}</span>

				<!-- Validation error indicator -->
				{#if showValidationErrors && tab.isValid && !tab.isValid()}
					<span
						class="w-2 h-2 rounded-full bg-error-500 {$isRTL ? 'mr-2' : 'ml-2'}"
						title="This tab requires attention"
					></span>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Tab Content -->
	<div class="tab-content pt-4" role="tabpanel">
		<slot />
	</div>
</div>

<style>
	.tabs-container {
		width: 100%;
	}

	.tabs {
		overflow-x: auto;
		white-space: nowrap;
	}

	.tab-content {
		position: relative;
		outline: none;
	}

	/* Adjust for RTL layout */
	:global([dir='rtl']) .tab-content {
		text-align: right;
	}
</style>
