<script>
	/**
	 * Select component with better dark mode support
	 * @component
	 */
	export let id = undefined;
	export let name = undefined;
	export let label = undefined;
	export let options = []; // Array of { value, label } objects
	export let value = '';
	export let placeholder = 'اختر...';
	export let error = '';
	export let hint = '';
	export let required = false;
	export let disabled = false;
	export let rounded = 'md'; // none, sm, md, lg
	export let size = 'base'; // sm, base, lg
	export let fullWidth = true;
	export let dir = 'rtl'; // rtl, ltr, auto

	// Note: multiple is removed as a prop
	// Instead, create two different select elements based on static multiple state

	// Generate ID if not provided
	$: selectId = id || `select-${Math.random().toString(36).substring(2, 9)}`;

	// Size classes
	const sizeClasses = {
		sm: 'py-1.5 pr-3 pl-10 text-sm',
		base: 'py-2 pr-4 pl-10 text-base',
		lg: 'py-3 pr-6 pl-10 text-lg'
	};

	// Rounded classes
	const roundedClasses = {
		none: 'rounded-none',
		sm: 'rounded-sm',
		md: 'rounded-md',
		lg: 'rounded-lg'
	};

	// Compute select classes with better dark mode support
	$: selectClasses = [
		'block border bg-white text-gray-900 shadow-sm appearance-none dark:bg-gray-700 dark:text-gray-100',
		sizeClasses[size],
		roundedClasses[rounded],
		error
			? 'border-red-500 focus:ring-red-500 focus:border-red-500 dark:border-red-600 dark:focus:ring-red-500 dark:focus:border-red-600'
			: 'border-gray-300 focus:ring-primary-500 focus:border-primary-500 dark:border-gray-600 dark:focus:ring-primary-500 dark:focus:border-primary-500',
		fullWidth ? 'w-full' : '',
		disabled ? 'bg-gray-100 cursor-not-allowed opacity-75 dark:bg-gray-800 dark:opacity-75' : '',
		$$props.class || ''
	].join(' ');

	// Create a custom change event dispatcher
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();

	function handleChange(event) {
		dispatch('change', { value: event.target.value });
	}
</script>

<div class={`flex flex-col gap-1.5 ${fullWidth ? 'w-full' : ''}`}>
	{#if label}
		<label for={selectId} class="block text-sm font-medium text-gray-900 dark:text-gray-200">
			{label}
			{#if required}<span class="text-red-500 dark:text-red-400">*</span>{/if}
		</label>
	{/if}

	<div class="relative">
		<!-- Only single select -->
		<select
			id={selectId}
			{name}
			bind:value
			{disabled}
			{required}
			{dir}
			aria-invalid={!!error}
			aria-describedby={error ? `${selectId}-error` : hint ? `${selectId}-hint` : undefined}
			class={selectClasses}
			on:focus
			on:blur
			on:change={handleChange}
			{...$$restProps}
		>
			{#if placeholder}
				<option value="" disabled selected>{placeholder}</option>
			{/if}

			{#each options as option}
				<option value={option.value}>{option.label}</option>
			{/each}
		</select>

		<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 text-gray-400 dark:text-gray-500"
				viewBox="0 0 20 20"
				fill="currentColor"
			>
				<path
					fill-rule="evenodd"
					d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
					clip-rule="evenodd"
				/>
			</svg>
		</div>
	</div>

	{#if error}
		<p id="{selectId}-error" class="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
	{:else if hint}
		<p id="{selectId}-hint" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{hint}</p>
	{/if}
</div>
