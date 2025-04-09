<script>
	import { fade } from 'svelte/transition';
	import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-svelte';
	import { isRTL } from '$lib/stores/ui';

	/**
	 * Props
	 */
	// Alert type: success, error, warning, info
	export let type = 'info';
	// Alert message (can be HTML or text)
	export let message = '';
	// Dismissible alert
	export let dismissible = false;
	// Auto close after ms (0 for no auto-close)
	export let autoClose = 0;
	// Alert icon (defaults based on type)
	export let icon = null;
	// Alert title (optional)
	export let title = '';
	// Border style variants
	export let border = false;
	// Additional classes
	export let classes = '';

	/**
	 * Reactive state
	 */
	// Whether alert is visible
	let visible = true;

	// Auto-close timer
	let timer;

	// Close handler
	function close() {
		visible = false;
		clearTimeout(timer);
	}

	// Type-based variant mapping
	const variantMap = {
		success: 'variant-filled-success',
		error: 'variant-filled-error',
		warning: 'variant-filled-warning',
		info: 'variant-filled-primary'
	};

	// Get default icon based on type
	function getIcon() {
		if (icon) return icon;

		switch (type) {
			case 'success':
				return CheckCircle;
			case 'error':
				return AlertCircle;
			case 'warning':
				return AlertTriangle;
			case 'info':
			default:
				return Info;
		}
	}

	// Set auto-close timer if specified
	$: if (autoClose > 0 && visible) {
		clearTimeout(timer);
		timer = setTimeout(close, autoClose);
	}

	// Clean up timer on component destroy
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		clearTimeout(timer);
	});

	// Get the correct CSS variant
	$: variant = variantMap[type] || 'variant-filled-primary';

	// Get the correct icon component
	$: IconComponent = getIcon();
</script>

{#if visible}
	<div
		transition:fade={{ duration: 200 }}
		class="alert {variant} {border ? 'border border-token' : ''} {classes}"
		role="alert"
	>
		<div class="flex items-center gap-4">
			<svelte:component this={IconComponent} class="w-5 h-5" />
			<div class="flex-1 {$isRTL ? 'text-right' : 'text-left'}">
				{#if title}
					<h3 class="h3">{title}</h3>
				{/if}
				{#if typeof message === 'string'}
					<p>{message}</p>
				{:else}
					<div>{message}</div>
				{/if}
			</div>
			{#if dismissible}
				<button class="btn btn-sm variant-ghost-surface" on:click={close}>
					<X class="w-4 h-4" />
				</button>
			{/if}
		</div>
	</div>
{/if}
