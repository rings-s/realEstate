<script>
	/**
	 * Card component for displaying content in a box
	 * @component
	 */
	export let variant = 'default'; // default, elevated, outlined, flat
	export let padding = 'lg'; // none, sm, md, lg, xl
	export let rounded = 'lg'; // none, sm, md, lg, xl, 2xl, full
	export let shadow = 'md'; // none, sm, md, lg
	export let hover = false; // Enable hover effect
	export let clickable = false; // Make card look clickable
	export let headerBorder = true; // Show border below header
	export let footerBorder = true; // Show border above footer
	export let horizontal = false; // Horizontal layout

	// Padding classes
	const paddingClasses = {
		none: 'p-0',
		sm: 'p-2',
		md: 'p-3',
		lg: 'p-5',
		xl: 'p-6'
	};

	// Rounded classes
	const roundedClasses = {
		none: 'rounded-none',
		sm: 'rounded-sm',
		md: 'rounded-md',
		lg: 'rounded-lg',
		xl: 'rounded-xl',
		'2xl': 'rounded-2xl',
		full: 'rounded-full'
	};

	// Shadow classes
	const shadowClasses = {
		none: 'shadow-none',
		sm: 'shadow-sm',
		md: 'shadow',
		lg: 'shadow-lg'
	};

	// Variant-specific classes
	const variantClasses = {
		default: 'bg-white',
		elevated: 'bg-white shadow',
		outlined: 'bg-white border border-gray-200',
		flat: 'bg-gray-50'
	};

	// Hover classes
	const hoverClasses = hover ? 'transition-transform duration-200 hover:scale-[1.02]' : '';

	// Clickable classes
	const clickableClasses = clickable
		? 'cursor-pointer hover:shadow-md transition-shadow duration-200'
		: '';

	// Compute classes string
	$: classes = [
		variantClasses[variant],
		roundedClasses[rounded],
		variant !== 'elevated' ? shadowClasses[shadow] : '',
		hoverClasses,
		clickableClasses,
		$$props.class || ''
	].join(' ');
</script>

<div class={classes} on:click on:keydown {...$$restProps}>
	{#if horizontal}
		<div class="flex flex-col md:flex-row">
			{#if $$slots.image}
				<div
					class={`overflow-hidden ${roundedClasses[rounded].replace('rounded', 'rounded-t md:rounded-t-none md:rounded-l')}`}
				>
					<slot name="image" />
				</div>
			{/if}

			<div class="flex flex-1 flex-col">
				{#if $$slots.header}
					<div
						class={`${paddingClasses[padding]} ${headerBorder ? 'border-b border-gray-200' : ''}`}
					>
						<slot name="header" />
					</div>
				{/if}

				<div class={paddingClasses[padding]}>
					<slot />
				</div>

				{#if $$slots.footer}
					<div
						class={`mt-auto ${paddingClasses[padding]} ${footerBorder ? 'border-t border-gray-200' : ''}`}
					>
						<slot name="footer" />
					</div>
				{/if}
			</div>
		</div>
	{:else}
		{#if $$slots.image}
			<div class={`overflow-hidden ${roundedClasses[rounded].replace('rounded', 'rounded-t')}`}>
				<slot name="image" />
			</div>
		{/if}

		{#if $$slots.header}
			<div class={`${paddingClasses[padding]} ${headerBorder ? 'border-b border-gray-200' : ''}`}>
				<slot name="header" />
			</div>
		{/if}

		<div class={paddingClasses[padding]}>
			<slot />
		</div>

		{#if $$slots.footer}
			<div class={`${paddingClasses[padding]} ${footerBorder ? 'border-t border-gray-200' : ''}`}>
				<slot name="footer" />
			</div>
		{/if}
	{/if}
</div>
