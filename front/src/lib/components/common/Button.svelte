<!-- src/lib/components/common/Button.svelte -->
<script>
	/**
	 * Button component with light background in dark mode
	 * @component
	 */
	export let type = 'button';
	export let variant = 'primary';
	export let size = 'base';
	export let fullWidth = false;
	export let disabled = false;
	export let loading = false;
	export let icon = null;
	export let iconPosition = 'start';
	export let rounded = 'md';
	export let href = '';

	// Size definitions
	const sizeClasses = {
		sm: 'py-1.5 px-3 text-sm',
		base: 'py-2 px-4 text-base',
		lg: 'py-3 px-6 text-lg'
	};

	// Border radius
	const roundedClasses = {
		none: 'rounded-none',
		sm: 'rounded-sm',
		md: 'rounded-md',
		lg: 'rounded-lg',
		full: 'rounded-full'
	};

	// Get the base style classes
	function getBaseClasses() {
		let classes = [
			'inline-flex items-center justify-center font-medium transition-colors duration-200',
			'focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800',
			sizeClasses[size] || sizeClasses.base,
			roundedClasses[rounded] || roundedClasses.md
		];

		if (fullWidth) {
			classes.push('w-full');
		}

		if (disabled || loading) {
			classes.push('opacity-60 cursor-not-allowed');
		}

		if ($$props.class) {
			classes.push($$props.class);
		}

		return classes;
	}

	// Get the variant-specific classes with inverted dark mode
	function getVariantClasses() {
		// Default primary style
		if (variant === 'primary' || variant === 'solid') {
			return 'bg-blue-600 hover:bg-blue-700 text-white border border-transparent dark:bg-blue-200 dark:hover:bg-blue-300 dark:text-blue-900 shadow-sm focus:ring-blue-500';
		}

		// Secondary style
		if (variant === 'secondary') {
			return 'bg-green-600 hover:bg-green-700 text-white border border-transparent dark:bg-green-200 dark:hover:bg-green-300 dark:text-green-900 shadow-sm focus:ring-green-500';
		}

		// Outline style
		if (variant === 'outline') {
			return 'bg-transparent border-2 border-blue-600 text-blue-700 hover:bg-blue-50 dark:border-blue-300 dark:text-blue-300 dark:hover:bg-blue-900/20 focus:ring-blue-500';
		}

		// Ghost style
		if (variant === 'ghost') {
			return 'bg-transparent hover:bg-gray-100 text-gray-800 border border-transparent dark:text-gray-300 dark:hover:bg-gray-800 focus:ring-gray-500';
		}

		// Danger/Error style
		if (variant === 'danger' || variant === 'error') {
			return 'bg-red-600 hover:bg-red-700 text-white border border-transparent dark:bg-red-200 dark:hover:bg-red-300 dark:text-red-900 focus:ring-red-500';
		}

		// Success style
		if (variant === 'success') {
			return 'bg-green-600 hover:bg-green-700 text-white border border-transparent dark:bg-green-200 dark:hover:bg-green-300 dark:text-green-900 focus:ring-green-500';
		}

		// Warning style
		if (variant === 'warning') {
			return 'bg-yellow-600 hover:bg-yellow-700 text-white border border-transparent dark:bg-yellow-200 dark:hover:bg-yellow-300 dark:text-yellow-900 focus:ring-yellow-500';
		}

		// Info style
		if (variant === 'info') {
			return 'bg-blue-500 hover:bg-blue-600 text-white border border-transparent dark:bg-blue-200 dark:hover:bg-blue-300 dark:text-blue-900 focus:ring-blue-500';
		}

		// Default to primary if no match
		return 'bg-blue-600 hover:bg-blue-700 text-white border border-transparent dark:bg-blue-200 dark:hover:bg-blue-300 dark:text-blue-900 shadow-sm focus:ring-blue-500';
	}

	// Determine if we need a dark or light loading spinner based on background
	function getSpinnerClasses() {
		// For dark mode, we now have light backgrounds, so we need dark spinners
		if (variant === 'outline' || variant === 'ghost') {
			return 'border-current border-t-transparent';
		} else {
			return 'border-white border-t-transparent dark:border-gray-800 dark:border-t-transparent';
		}
	}

	// Combine classes
	$: classes = [...getBaseClasses(), getVariantClasses()].join(' ');
	$: spinnerClasses = getSpinnerClasses();
	$: isLink = !!href && !disabled;
</script>

{#if isLink}
	<a {href} class={classes} {...$$restProps} on:click on:mouseenter on:mouseleave>
		{#if loading}
			<span
				class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 {spinnerClasses}"
				aria-hidden="true"
			></span>
		{/if}
		{#if icon && iconPosition === 'start'}
			<span class="inline-flex items-center {$$slots.default ? 'ml-2' : ''}">
				<svelte:component this={icon} />
			</span>
		{/if}
		{#if $$slots.default}
			<slot />
		{/if}
		{#if icon && iconPosition === 'end'}
			<span class="mr-2 inline-flex items-center">
				<svelte:component this={icon} />
			</span>
		{/if}
	</a>
{:else}
	<button
		{type}
		{disabled}
		class={classes}
		aria-disabled={disabled || loading}
		on:click
		on:focus
		on:blur
		on:mouseenter
		on:mouseleave
		{...$$restProps}
	>
		{#if loading}
			<span
				class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 {spinnerClasses}"
				aria-hidden="true"
			></span>
		{/if}
		{#if icon && iconPosition === 'start'}
			<span class="inline-flex items-center {$$slots.default ? 'ml-2' : ''}">
				<svelte:component this={icon} />
			</span>
		{/if}
		{#if $$slots.default}
			<slot />
		{/if}
		{#if icon && iconPosition === 'end'}
			<span class="mr-2 inline-flex items-center">
				<svelte:component this={icon} />
			</span>
		{/if}
	</button>
{/if}
