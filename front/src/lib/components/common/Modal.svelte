<script>
	import { fade, fly } from 'svelte/transition';
	import { X } from 'lucide-svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Show or hide the modal
	export let open = false;
	// Modal title
	export let title = '';
	// Whether to show the close button
	export let showClose = true;
	// Auto-focus the first focusable element
	export let autoFocus = true;
	// Whether to close the modal when clicking outside of it
	export let closeOnOutsideClick = true;
	// Whether to close the modal when pressing the Escape key
	export let closeOnEsc = true;
	// Size of the modal: xs, sm, md, lg, xl, full
	export let size = 'md';
	// Background color variant
	export let background = 'bg-surface-100-800-token';
	// Header color variant
	export let headerBackground = '';
	// Footer color variant
	export let footerBackground = '';
	// Additional classes
	export let classes = '';
	// Whether to use a form in the modal
	export let form = false;
	// Modal position: default (centered), top, bottom
	export let position = 'default';
	// Footer buttons alignment
	export let footerAlign = 'end';

	// Local state
	let modal;
	let focusableElements = [];
	let firstFocusableElement;
	let lastFocusableElement;
	let previousActiveElement;

	// Modal sizes
	const sizes = {
		xs: 'max-w-xs',
		sm: 'max-w-sm',
		md: 'max-w-md',
		lg: 'max-w-lg',
		xl: 'max-w-xl',
		'2xl': 'max-w-2xl',
		'3xl': 'max-w-3xl',
		'4xl': 'max-w-4xl',
		'5xl': 'max-w-5xl',
		full: 'max-w-full'
	};

	// Position classes
	const positions = {
		default: 'items-center justify-center',
		top: 'items-start justify-center pt-10',
		bottom: 'items-end justify-center pb-10'
	};

	// Footer alignments
	const footerAlignments = {
		start: $isRTL ? 'justify-end' : 'justify-start',
		end: $isRTL ? 'justify-start' : 'justify-end',
		center: 'justify-center',
		between: 'justify-between'
	};

	// Size class
	$: sizeClass = sizes[size] || sizes.md;

	// Position class
	$: positionClass = positions[position] || positions.default;

	// Footer alignment class
	$: footerAlignClass = footerAlignments[footerAlign] || footerAlignments.end;

	// Close modal handler
	function closeModal() {
		if (showClose) {
			dispatch('close');
		}
	}

	// Outside click handler
	function handleOutsideClick(event) {
		if (closeOnOutsideClick && modal && !modal.contains(event.target)) {
			closeModal();
		}
	}

	// Escape key handler
	function handleKeydown(event) {
		if (closeOnEsc && event.key === 'Escape') {
			closeModal();
		}

		// Tab trap for accessibility
		if (event.key === 'Tab') {
			if (!focusableElements.length) return;

			// If shift+tab on first element, focus the last element
			if (event.shiftKey && document.activeElement === firstFocusableElement) {
				event.preventDefault();
				lastFocusableElement.focus();
			}
			// If tab on last element, focus the first element
			else if (!event.shiftKey && document.activeElement === lastFocusableElement) {
				event.preventDefault();
				firstFocusableElement.focus();
			}
		}
	}

	// Get all focusable elements within the modal
	function getFocusableElements() {
		if (!modal) return [];

		// List of focusable elements
		const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
		const elements = Array.from(modal.querySelectorAll(selector)).filter(
			(element) => !element.hasAttribute('disabled') && element.offsetParent !== null
		);

		return elements;
	}

	// Update focusable elements when modal opens
	$: if (open && modal) {
		// Save previously focused element
		previousActiveElement = document.activeElement;

		// Get focusable elements
		setTimeout(() => {
			focusableElements = getFocusableElements();
			firstFocusableElement = focusableElements[0];
			lastFocusableElement = focusableElements[focusableElements.length - 1];

			// Auto-focus first element
			if (autoFocus && firstFocusableElement) {
				firstFocusableElement.focus();
			} else {
				// Focus the modal itself if no focusable elements
				modal.focus();
			}
		}, 50);
	}

	// Restore focus when modal closes
	$: if (!open && previousActiveElement) {
		setTimeout(() => {
			previousActiveElement.focus();
		}, 50);
	}

	// Add event listeners
	onMount(() => {
		if (closeOnEsc) {
			document.addEventListener('keydown', handleKeydown);
		}
	});

	// Clean up event listeners
	onDestroy(() => {
		document.removeEventListener('keydown', handleKeydown);
	});

	// Prevent scrolling of the body when modal is open
	$: if (open) {
		document.body.style.overflow = 'hidden';
	} else {
		document.body.style.overflow = '';
	}
</script>

{#if open}
	<!-- Modal backdrop -->
	<div
		class="fixed inset-0 z-50 overflow-y-auto"
		transition:fade={{ duration: 200 }}
		on:click={handleOutsideClick}
		aria-modal="true"
		role="dialog"
		aria-labelledby={title ? 'modal-title' : undefined}
	>
		<!-- Modal layout container -->
		<div class="min-h-full flex {positionClass} p-4">
			<!-- Modal card -->
			<div
				bind:this={modal}
				class="card {sizeClass} shadow-xl {background} {classes}"
				tabindex="-1"
				transition:fly={{ y: 20, duration: 300 }}
			>
				{#if form}
					<!-- Form wrapper if needed -->
					<form on:submit|preventDefault>
						{#if title || showClose}
							<!-- Modal header -->
							<header
								class="card-header {headerBackground ||
									'bg-surface-100-800-token'} p-4 flex items-center justify-between"
							>
								<h2 id="modal-title" class="h3 {$isRTL ? 'text-right' : 'text-left'}">{title}</h2>
								{#if showClose}
									<button
										type="button"
										class="btn btn-sm btn-icon variant-ghost-surface"
										aria-label={t('close', $language, { default: 'إغلاق' })}
										on:click={closeModal}
									>
										<X class="w-5 h-5" />
									</button>
								{/if}
							</header>
						{/if}

						<!-- Modal body -->
						<div class="p-4 {$isRTL ? 'text-right' : 'text-left'}">
							<slot></slot>
						</div>

						<!-- Modal footer (with form buttons) -->
						<footer class="card-footer {footerBackground || 'bg-surface-100-800-token'} p-4">
							<div class="flex flex-wrap {footerAlignClass} gap-2">
								<slot name="footer">
									<button type="button" class="btn variant-ghost-surface" on:click={closeModal}>
										{t('cancel', $language, { default: 'إلغاء' })}
									</button>
									<button type="submit" class="btn variant-filled-primary">
										{t('submit', $language, { default: 'إرسال' })}
									</button>
								</slot>
							</div>
						</footer>
					</form>
				{:else}
					<!-- Regular modal without form -->
					{#if title || showClose}
						<!-- Modal header -->
						<header
							class="card-header {headerBackground ||
								'bg-surface-100-800-token'} p-4 flex items-center justify-between"
						>
							<h2 id="modal-title" class="h3 {$isRTL ? 'text-right' : 'text-left'}">{title}</h2>
							{#if showClose}
								<button
									type="button"
									class="btn btn-sm btn-icon variant-ghost-surface"
									aria-label={t('close', $language, { default: 'إغلاق' })}
									on:click={closeModal}
								>
									<X class="w-5 h-5" />
								</button>
							{/if}
						</header>
					{/if}

					<!-- Modal body -->
					<div class="p-4 {$isRTL ? 'text-right' : 'text-left'}">
						<slot></slot>
					</div>

					<!-- Modal footer -->
					<slot name="footer">
						<footer class="card-footer {footerBackground || 'bg-surface-100-800-token'} p-4">
							<div class="flex flex-wrap {footerAlignClass} gap-2">
								<button type="button" class="btn variant-ghost-surface" on:click={closeModal}>
									{t('close', $language, { default: 'إغلاق' })}
								</button>
							</div>
						</footer>
					</slot>
				{/if}
			</div>
		</div>
	</div>
{/if}
