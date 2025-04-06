<!-- src/lib/components/common/SearchBar.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let placeholder = 'بحث...';
	export let value = '';

	const dispatch = createEventDispatcher();

	let inputValue = value;

	// Update local value when parent changes value
	$: {
		if (value !== inputValue) {
			inputValue = value;
		}
	}

	// Handle search submit
	function handleSubmit(event) {
		event.preventDefault();
		dispatch('search', inputValue);
	}

	// Handle clear search
	function clearSearch() {
		inputValue = '';
		dispatch('search', '');
	}
</script>

<form on:submit={handleSubmit} class="relative w-full">
	<div class="relative">
		<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
			<svg
				class="h-5 w-5 text-gray-500 dark:text-gray-400"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
				aria-hidden="true"
			>
				<path
					fill-rule="evenodd"
					d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
					clip-rule="evenodd"
				/>
			</svg>
		</div>

		<input
			type="text"
			bind:value={inputValue}
			{placeholder}
			class="focus:border-primary-500 focus:ring-primary-500 block w-full rounded-lg border border-gray-300 bg-white p-3 pr-10 text-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-400"
		/>

		{#if inputValue}
			<button
				type="button"
				on:click={clearSearch}
				aria-label="مسح البحث"
				class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
			>
				<svg
					class="h-5 w-5"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					aria-hidden="true"
				>
					<path
						fill-rule="evenodd"
						d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<button type="submit" class="sr-only"> بحث </button>
</form>
