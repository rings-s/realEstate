<script>
	/**
	 * Modal/Dialog component
	 * @component
	 */
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	export let id = undefined;
	export let title = '';
	export let open = false;
	export let closeOnEscape = true;
	export let closeOnOutsideClick = true;
	export let size = 'md'; // sm, md, lg, xl, full
	export let showCloseButton = true;
	export let preventScroll = true;

	const dispatch = createEventDispatcher();

	// Generate ID if not provided
	$: modalId = id || `modal-${Math.random().toString(36).substring(2, 9)}`;

	// Size classes
	const sizeClasses = {
		sm: 'max-w-md',
		md: 'max-w-lg',
		lg: 'max-w-2xl',
		xl: 'max-w-4xl',
		full: 'max-w-full mx-4'
	};

	// Handle Escape key press
	function handleKeydown(event) {
		if (open && closeOnEscape && event.key === 'Escape') {
			closeModal();
		}
	}

	// Close modal
	function closeModal() {
		open = false;
		dispatch('close');
	}

	// Handle outside click
	function handleOutsideClick(event) {
		if (closeOnOutsideClick && event.target === event.currentTarget) {
			closeModal();
		}
	}

	// Handle body scroll
	onMount(() => {
		document.addEventListener('keydown', handleKeydown);
	});

	$: if (preventScroll) {
		if (open) {
			document.body.style.overflow = 'hidden';
		} else {
			document.body.style.overflow = '';
		}
	}

	onDestroy(() => {
		document.removeEventListener('keydown', handleKeydown);
		document.body.style.overflow = '';
	});
</script>

{#if open}
	<div
		id={modalId}
		role="dialog"
		aria-modal="true"
		aria-labelledby={`${modalId}-title`}
		class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto"
		on:click={handleOutsideClick}
		transition:fade={{ duration: 200 }}
	>
		<!-- Backdrop -->
		<div class="bg-opacity-50 fixed inset-0 bg-black backdrop-blur-sm"></div>

		<!-- Modal content -->
		<div
			class={`relative z-10 flex flex-col rounded-lg bg-white shadow-xl ${sizeClasses[size]} m-4 w-full`}
			transition:scale={{ duration: 200, easing: quintOut, start: 0.95 }}
		>
			<!-- Header -->
			{#if title || showCloseButton}
				<div class="flex items-center justify-between border-b border-gray-200 p-4">
					{#if title}
						<h2 id={`${modalId}-title`} class="text-lg font-medium text-gray-900">
							{title}
						</h2>
					{:else}
						<div></div>
						<!-- Empty div for flex spacing -->
					{/if}

					{#if showCloseButton}
						<button
							type="button"
							class="focus:ring-primary-500 rounded-md bg-white p-1 text-gray-400 hover:text-gray-500 focus:ring-2 focus:outline-none"
							aria-label="إغلاق"
							on:click={closeModal}
						>
							<svg
								class="h-6 w-6"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					{/if}
				</div>
			{/if}

			<!-- Body -->
			<div class="flex-1 overflow-auto p-6">
				<slot />
			</div>

			<!-- Footer -->
			{#if $$slots.footer}
				<div class="flex justify-end border-t border-gray-200 p-4">
					<slot name="footer" />
				</div>
			{/if}
		</div>
	</div>
{/if}
