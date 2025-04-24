<!-- src/lib/components/Toast.svelte -->
<script>
	import { toasts, removeToast } from '$lib/stores/ui';

	function getIcon(type) {
		switch (type) {
			case 'success':
				return 'fas fa-check-circle';
			case 'error':
				return 'fas fa-exclamation-circle';
			case 'warning':
				return 'fas fa-exclamation-triangle';
			case 'info':
			default:
				return 'fas fa-info-circle';
		}
	}

	function getColor(type) {
		switch (type) {
			case 'success':
				return 'bg-green-50 border-green-500 text-green-700';
			case 'error':
				return 'bg-red-50 border-red-500 text-red-700';
			case 'warning':
				return 'bg-amber-50 border-amber-500 text-amber-700';
			case 'info':
			default:
				return 'bg-blue-50 border-blue-500 text-blue-700';
		}
	}

	function getIconColor(type) {
		switch (type) {
			case 'success':
				return 'text-green-500';
			case 'error':
				return 'text-red-500';
			case 'warning':
				return 'text-amber-500';
			case 'info':
			default:
				return 'text-blue-500';
		}
	}
</script>

<div class="fixed top-4 right-0 left-0 z-50 flex flex-col items-center">
	{#each $toasts as toast (toast.id)}
		<div
			class="mb-3 w-full max-w-md rounded-lg border-r-4 shadow-md {getColor(
				toast.type
			)} animate-slide-in transform transition-all duration-300"
			role="alert"
		>
			<div class="flex p-4">
				<div class="flex-shrink-0">
					<i class="{getIcon(toast.type)} {getIconColor(toast.type)} text-lg"></i>
				</div>
				<div class="mr-3 flex-1">
					<p class="text-sm">{toast.message}</p>
				</div>
				<div>
					<button
						type="button"
						class="text-slate-400 hover:text-slate-600"
						on:click={() => removeToast(toast.id)}
					>
						<i class="fas fa-times"></i>
					</button>
				</div>
			</div>
		</div>
	{/each}
</div>

<style>
	@keyframes slide-in {
		0% {
			transform: translateY(-100%);
			opacity: 0;
		}
		100% {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.animate-slide-in {
		animation: slide-in 0.3s ease-out forwards;
	}
</style>
