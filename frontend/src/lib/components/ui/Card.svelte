<script>
	export let title = '';
	export let subtitle = '';
</script>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		{#if title || subtitle}
			<div class="mb-6 text-center">
				{#if title}
					<h1 class="text-2xl font-bold text-slate-900">{title}</h1>
				{/if}
				{#if subtitle}
					<p class="mt-2 text-slate-600">{subtitle}</p>
				{/if}
			</div>
		{/if}

		<slot />

		<slot name="footer" />
	</div>
</div>
