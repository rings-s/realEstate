<script>
	export let type = 'info'; // success, error, warning, info
	export let message = '';
	export let dismissible = false;

	let visible = true;

	function dismiss() {
		visible = false;
	}

	const typeClasses = {
		success: 'bg-green-50 border-green-400 text-green-700',
		error: 'bg-red-50 border-red-400 text-red-700',
		warning: 'bg-amber-50 border-amber-400 text-amber-700',
		info: 'bg-blue-50 border-blue-400 text-blue-700'
	};

	const iconClasses = {
		success: 'fas fa-check-circle text-green-400',
		error: 'fas fa-exclamation-circle text-red-400',
		warning: 'fas fa-exclamation-triangle text-amber-400',
		info: 'fas fa-info-circle text-blue-400'
	};
</script>

{#if visible}
	<div class="mb-4 rounded border-l-4 p-4 {typeClasses[type]}">
		<div class="flex">
			<div class="flex-shrink-0">
				<i class={iconClasses[type]}></i>
			</div>
			<div class="mr-3 flex-1">
				<p class="text-sm">{@html message}</p>
			</div>
			{#if dismissible}
				<button on:click={dismiss} class="text-slate-400 hover:text-slate-600">
					<i class="fas fa-times"></i>
				</button>
			{/if}
		</div>
	</div>
{/if}
