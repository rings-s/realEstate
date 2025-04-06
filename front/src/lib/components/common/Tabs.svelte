<script>
	/**
	 * مكون التبويبات باستخدام Tailwind CSS
	 */
	export let tabs = [];
	export let activeTab = 0;
	export let variant = 'underline'; // underline, pills, minimal
	export let fullWidth = false;
	export let disabled = false;

	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();

	function selectTab(index) {
		if (!disabled && index !== activeTab) {
			activeTab = index;
			dispatch('change', { index, tab: tabs[index] });
		}
	}

	// تحديد أنماط التبويبات بناءً على النوع المختار
	$: tabStyles = {
		underline: {
			container: 'border-b border-gray-200',
			tab: 'px-4 py-2 border-b-2 border-transparent',
			active: 'border-primary-500 text-primary-600 font-medium',
			inactive: 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
		},
		pills: {
			container: 'flex gap-2',
			tab: 'px-3 py-2 rounded-md',
			active: 'bg-primary-100 text-primary-700 font-medium',
			inactive: 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
		},
		minimal: {
			container: '',
			tab: 'px-3 py-2',
			active: 'text-primary-700 font-medium',
			inactive: 'text-gray-500 hover:text-gray-700'
		}
	}[variant];
</script>

<div class="w-full {$$props.class || ''}" dir="rtl">
	<div
		class="flex {tabStyles.container} {fullWidth ? 'w-full' : ''} overflow-x-auto"
		role="tablist"
	>
		{#each tabs as tab, i}
			<button
				class="{tabStyles.tab} {activeTab === i
					? tabStyles.active
					: tabStyles.inactive} transition-colors {fullWidth
					? 'flex-1 justify-center text-center'
					: ''} {tab.disabled || disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}"
				on:click={() => selectTab(i)}
				disabled={disabled || tab.disabled}
				aria-selected={activeTab === i}
				id="tab-{i}"
				aria-controls="panel-{i}"
				role="tab"
			>
				{#if tab.icon}
					<span class="inline-block ltr:mr-2 rtl:ml-2">
						{@html tab.icon}
					</span>
				{/if}
				<span>{tab.label}</span>
			</button>
		{/each}
	</div>

	<div class="mt-4">
		<!-- Fixed approach: Use component rendering only -->
		{#each tabs as tab, i}
			<div
				class={activeTab === i ? 'block' : 'hidden'}
				id="panel-{i}"
				aria-labelledby="tab-{i}"
				role="tabpanel"
				tabindex={activeTab === i ? 0 : -1}
			>
				{#if activeTab === i}
					{#if tab.component}
						<svelte:component this={tab.component} {...tab.props || {}} />
					{:else}
						<!-- Pass content with slot props instead of dynamic named slots -->
						<slot {activeTab} index={i} />
					{/if}
				{/if}
			</div>
		{/each}
	</div>
</div>
