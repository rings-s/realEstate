<script>
	/**
	 * Input component with better dark mode support
	 * @component
	 */
	export let id = undefined;
	export let name = undefined;
	export let label = undefined;
	export let placeholder = '';
	export let value = '';
	export let type = 'text';
	export let error = '';
	export let hint = '';
	export let required = false;
	export let disabled = false;
	export let readonly = false;
	export let rounded = 'md'; // none, sm, md, lg
	export let size = 'base'; // sm, base, lg
	export let fullWidth = true;
	export let dir = 'rtl'; // rtl, ltr, auto
	export let icon = null; // icon component
	export let iconPosition = 'start'; // start, end

	// Generate ID if not provided
	$: inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;

	// Size classes
	const sizeClasses = {
		sm: 'py-1.5 px-3 text-sm',
		base: 'py-2 px-4 text-base',
		lg: 'py-3 px-6 text-lg'
	};

	// Rounded classes
	const roundedClasses = {
		none: 'rounded-none',
		sm: 'rounded-sm',
		md: 'rounded-md',
		lg: 'rounded-lg'
	};

	// Icon padding classes
	const iconPaddingClasses = {
		start: 'pr-4 pl-10',
		end: 'pl-4 pr-10'
	};

	// Compute input classes with improved dark mode support
	$: inputClasses = [
		'block border bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-gray-100',
		sizeClasses[size],
		roundedClasses[rounded],
		error
			? 'border-red-500 focus:ring-red-500 focus:border-red-500 dark:border-red-600 dark:focus:ring-red-500 dark:focus:border-red-600'
			: 'border-gray-300 focus:ring-primary-500 focus:border-primary-500 dark:border-gray-600 dark:focus:ring-primary-500 dark:focus:border-primary-500',
		icon ? iconPaddingClasses[iconPosition] : 'px-4',
		fullWidth ? 'w-full' : '',
		disabled ? 'bg-gray-100 cursor-not-allowed opacity-75 dark:bg-gray-800 dark:opacity-75' : '',
		$$props.class || ''
	].join(' ');
</script>

<div class={`flex flex-col gap-1.5 ${fullWidth ? 'w-full' : ''}`}>
	{#if label}
		<label for={inputId} class="block text-sm font-medium text-gray-900 dark:text-gray-200">
			{label}
			{#if required}<span class="text-red-500 dark:text-red-400">*</span>{/if}
		</label>
	{/if}

	<div class="relative">
		{#if icon && iconPosition === 'start'}
			<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
				<svelte:component this={icon} class="h-5 w-5 text-gray-400 dark:text-gray-500" />
			</div>
		{/if}

		<input
			id={inputId}
			{name}
			{type}
			{placeholder}
			bind:value
			{disabled}
			{readonly}
			{required}
			{dir}
			aria-invalid={!!error}
			aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
			class={inputClasses}
			on:focus
			on:blur
			on:input
			on:change
			{...$$restProps}
		/>

		{#if icon && iconPosition === 'end'}
			<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
				<svelte:component this={icon} class="h-5 w-5 text-gray-400 dark:text-gray-500" />
			</div>
		{/if}
	</div>

	{#if error}
		<p id="{inputId}-error" class="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
	{:else if hint}
		<p id="{inputId}-hint" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{hint}</p>
	{/if}
</div>
