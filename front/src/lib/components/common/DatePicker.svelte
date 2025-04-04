<script>
	/**
	 * Date picker input component
	 * Arabic-friendly date picker for use in real estate application forms
	 * @component
	 */
	import { createEventDispatcher, onMount } from 'svelte';
	import { format, parse } from 'date-fns';
	import { ar } from 'date-fns/locale';

	// Props
	export let id = ''; // Input ID (required for accessibility)
	export let label = ''; // Input label
	export let value = ''; // Input value
	export let placeholder = ''; // Input placeholder
	export let disabled = false; // Is input disabled
	export let required = false; // Is input required
	export let helpText = ''; // Help text below input
	export let error = ''; // Error message
	export let min = ''; // Minimum date
	export let max = ''; // Maximum date
	export let name = id; // Input name (defaults to ID)
	export let readonly = false; // Is input readonly
	export let dateFormat = 'yyyy-MM-dd'; // Date format
	export let showCalendarIcon = true; // Show calendar icon
	export let size = 'default'; // Input size: small, default, large

	const dispatch = createEventDispatcher();

	// Local state
	let inputElement;
	let formatted = '';

	// Format the date for display
	function updateFormattedDate() {
		if (!value) {
			formatted = '';
			return;
		}

		try {
			// If it's already a string in yyyy-MM-dd format, convert to date then format
			const dateObj = typeof value === 'string' ? new Date(value) : value;

			if (isNaN(dateObj.getTime())) {
				formatted = '';
				return;
			}

			formatted = format(dateObj, dateFormat, { locale: ar });
		} catch (e) {
			console.error('Error formatting date:', e);
			formatted = '';
		}
	}

	// Update the value when input changes
	function handleChange(e) {
		value = e.target.value;
		updateFormattedDate();
		dispatch('change', { value });
	}

	// Handle calendar icon click
	function handleCalendarClick() {
		if (!disabled && !readonly) {
			inputElement.focus();
			inputElement.showPicker?.(); // Might not be supported in all browsers
		}
	}

	// Handle input focus
	function handleFocus() {
		dispatch('focus');
	}

	// Handle input blur
	function handleBlur() {
		dispatch('blur');
	}

	// Update formatted date when value changes
	$: {
		value; // reactive dependency
		updateFormattedDate();
	}

	// Get input size classes
	$: sizeClasses = (() => {
		switch (size) {
			case 'small':
				return 'py-1 px-2 text-sm';
			case 'large':
				return 'py-3 px-4 text-lg';
			default:
				return 'py-2 px-4';
		}
	})();

	// Get input states
	$: hasError = !!error;
	$: baseClasses = `
    w-full border rounded-md shadow-sm focus:outline-none focus:ring-2
    ${sizeClasses}
    ${showCalendarIcon ? 'pl-10' : ''}
    ${disabled ? 'bg-gray-100 text-gray-500 cursor-not-allowed dark:bg-gray-700 dark:text-gray-400' : 'bg-white dark:bg-gray-700 dark:text-white'}
    ${readonly ? 'bg-gray-50 cursor-default dark:bg-gray-800' : ''}
    ${
			hasError
				? 'border-red-300 focus:border-red-500 focus:ring-red-500 dark:border-red-700'
				: 'border-gray-300 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600'
		}
  `;

	onMount(() => {
		// Initialize formatted date on mount
		updateFormattedDate();
	});
</script>

<div class="w-full {$$props.class || ''}">
	{#if label}
		<label for={id} class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
			{label}
			{#if required}<span class="text-red-500">*</span>{/if}
		</label>
	{/if}

	<div class="relative">
		{#if showCalendarIcon}
			<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 text-gray-400 dark:text-gray-500"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
					/>
				</svg>
			</div>
		{/if}

		<input
			{id}
			{name}
			bind:this={inputElement}
			type="date"
			class={baseClasses}
			{placeholder}
			{disabled}
			{required}
			{readonly}
			{min}
			{max}
			{value}
			on:change={handleChange}
			on:focus={handleFocus}
			on:blur={handleBlur}
			on:input
			on:keydown
			on:keyup
			on:keypress
			aria-invalid={hasError}
			aria-describedby={hasError ? `${id}-error` : helpText ? `${id}-description` : undefined}
			dir="ltr"
		/>

		{#if showCalendarIcon && !disabled && !readonly}
			<button
				type="button"
				class="absolute top-0 left-0 h-full px-3 py-2 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400"
				on:click={handleCalendarClick}
				tabindex="-1"
			>
				<span class="sr-only">افتح التقويم</span>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
					/>
				</svg>
			</button>
		{/if}
	</div>

	{#if hasError}
		<p id="{id}-error" class="mt-1 text-sm text-red-600 dark:text-red-400">
			{error}
		</p>
	{:else if helpText}
		<p id="{id}-description" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			{helpText}
		</p>
	{/if}
</div>
