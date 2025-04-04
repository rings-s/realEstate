<!-- src/lib/components/common/Textarea.svelte -->
<script>
	export let label = '';
	export let name = '';
	export let value = '';
	export let placeholder = '';
	export let rows = 3;
	export let required = false;
	export let disabled = false;
	export let readonly = false;
	export let error = '';
	export let helpText = '';

	// Binding support
	function handleInput(event) {
		value = event.target.value;
	}
</script>

<div class="mb-4">
	{#if label}
		<label for={name} class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
			{label}
			{#if required}
				<span class="text-red-500">*</span>
			{/if}
		</label>
	{/if}

	<textarea
		{name}
		id={name}
		{placeholder}
		{rows}
		{required}
		{disabled}
		{readonly}
		{value}
		on:input={handleInput}
		class="w-full rounded-md border {error
			? 'border-red-500'
			: 'border-gray-300 dark:border-gray-600'} bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100"
		aria-invalid={!!error}
		aria-describedby={error ? `${name}-error` : helpText ? `${name}-description` : undefined}
	></textarea>

	{#if error}
		<p id="{name}-error" class="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
	{:else if helpText}
		<p id="{name}-description" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{helpText}</p>
	{/if}
</div>
