<!-- src/lib/components/common/Checkbox.svelte -->
<script>
	/**
	 * Checkbox component with label
	 * @component
	 */
	export let id = undefined;
	export let name = undefined;
	export let label = undefined;
	export let checked = false;
	export let value = '';
	export let error = '';
	export let hint = '';
	export let disabled = false;
	export let required = false;
	export let size = 'base'; // sm, base, lg

	// Generate ID if not provided
	$: checkboxId = id || `checkbox-${Math.random().toString(36).substring(2, 9)}`;

	// Size classes
	const sizeClasses = {
		sm: 'h-3.5 w-3.5',
		base: 'h-4 w-4',
		lg: 'h-5 w-5'
	};

	// Label size classes
	const labelSizeClasses = {
		sm: 'text-sm',
		base: 'text-base',
		lg: 'text-lg'
	};

	// Compute checkbox classes
	$: checkboxClasses = [
		'text-primary-600 border-gray-300 focus:ring-primary-500 rounded',
		sizeClasses[size],
		disabled ? 'bg-gray-100 cursor-not-allowed opacity-75' : '',
		$$props.class || ''
	].join(' ');
</script>

<div class="flex items-start">
	<div class="flex h-5 items-center">
		<input
			type="checkbox"
			id={checkboxId}
			{name}
			{value}
			bind:checked
			{disabled}
			{required}
			aria-invalid={!!error}
			aria-describedby={error ? `${checkboxId}-error` : hint ? `${checkboxId}-hint` : undefined}
			class={checkboxClasses}
			on:change
			{...$$restProps}
		/>
	</div>
	{#if label}
		<div class="mr-3 text-gray-700 dark:text-gray-300">
			<label
				for={checkboxId}
				class={`font-medium ${labelSizeClasses[size]} ${disabled ? 'cursor-not-allowed opacity-75' : ''}`}
			>
				{label}
				{#if required}
					<span class="text-red-500">*</span>
				{/if}
			</label>
			{#if error}
				<p id="{checkboxId}-error" class="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
			{:else if hint}
				<p id="{checkboxId}-hint" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{hint}</p>
			{/if}
		</div>
	{/if}
</div>
