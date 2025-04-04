<script>
	/**
	 * Enhanced loading spinner component with inverted light/dark mode styling
	 * Automatically uses light style in dark mode and dark style in light mode
	 * @component
	 */

	// Props with safe defaults
	export let size = 'md'; // sm, md, lg
	export let color = 'primary'; // primary, secondary, gray, white, black, auto (inverted)
	export let text = ''; // Optional loading text
	export let fullScreen = false; // Whether to display over the full screen
	export let type = 'spinner'; // spinner, dots, pulse
	export let timeout = 0; // Optional timeout in ms, 0 for no timeout
	export let showBackdrop = true; // Show background overlay in fullscreen mode

	import { onMount, onDestroy } from 'svelte';

	// Size maps
	const sizes = {
		sm: { spinner: 'h-5 w-5', dot: 'h-1.5 w-1.5', container: 'space-x-1.5 space-x-reverse' },
		md: { spinner: 'h-8 w-8', dot: 'h-2 w-2', container: 'space-x-2 space-x-reverse' },
		lg: { spinner: 'h-12 w-12', dot: 'h-3 w-3', container: 'space-x-3 space-x-reverse' }
	};

	// Color maps with improved contrast in dark/light modes
	const colors = {
		primary: {
			text: 'text-primary-700 dark:text-primary-300',
			bg: 'bg-primary-700 dark:bg-primary-300'
		},
		secondary: {
			text: 'text-gray-700 dark:text-gray-300',
			bg: 'bg-gray-700 dark:bg-gray-300'
		},
		gray: {
			text: 'text-gray-800 dark:text-gray-200',
			bg: 'bg-gray-800 dark:bg-gray-200'
		},
		white: {
			text: 'text-white dark:text-gray-900',
			bg: 'bg-white dark:text-gray-900'
		},
		black: {
			text: 'text-gray-900 dark:text-white',
			bg: 'bg-gray-900 dark:bg-white'
		},
		auto: {
			text: 'text-gray-900 dark:text-white',
			bg: 'bg-gray-900 dark:bg-white'
		}
	};

	// Safe property access with defaults
	$: spinnerSize = sizes[size]?.spinner || sizes.md.spinner;
	$: dotSize = sizes[size]?.dot || sizes.md.dot;
	$: containerSize = sizes[size]?.container || sizes.md.container;
	$: textColor = colors[color]?.text || colors.primary.text;
	$: bgColor = colors[color]?.bg || colors.primary.bg;

	// Timeout handling
	let timeoutId = null;
	let visible = true;

	onMount(() => {
		if (timeout > 0) {
			timeoutId = setTimeout(() => {
				visible = false;
			}, timeout);
		}
	});

	onDestroy(() => {
		if (timeoutId) {
			clearTimeout(timeoutId);
		}
	});

	// Backdrop style for full screen mode
	$: backdropClass = showBackdrop
		? 'bg-white bg-opacity-70 dark:bg-gray-900 dark:bg-opacity-80'
		: '';
</script>

{#if visible}
	{#if fullScreen}
		<div class="fixed inset-0 z-50 flex items-center justify-center {backdropClass}">
			<div
				class="flex flex-col items-center justify-center rounded-lg bg-white p-8 shadow-lg dark:bg-gray-800"
			>
				{#if type === 'spinner'}
					<!-- SVG Spinner -->
					<svg
						class="animate-spin {spinnerSize} {textColor}"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						aria-hidden="true"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
				{:else if type === 'dots'}
					<!-- Bouncing Dots -->
					<div class="flex {containerSize}">
						<div
							class="rounded-full {dotSize} {bgColor} animate-bounce"
							style="animation-delay: 0s"
						></div>
						<div
							class="rounded-full {dotSize} {bgColor} animate-bounce"
							style="animation-delay: 0.2s"
						></div>
						<div
							class="rounded-full {dotSize} {bgColor} animate-bounce"
							style="animation-delay: 0.4s"
						></div>
					</div>
				{:else if type === 'pulse'}
					<!-- Pulsing Circle -->
					<div class="animate-pulse {spinnerSize} {textColor}">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
							/>
						</svg>
					</div>
				{:else}
					<!-- Fallback -->
					<div class="animate-spin {spinnerSize} {textColor}">
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
					</div>
				{/if}

				<!-- Optional text -->
				{#if text}
					<p class="mt-3 text-center text-sm font-medium {textColor}">{text}</p>
				{/if}
			</div>
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center">
			{#if type === 'spinner'}
				<!-- SVG Spinner -->
				<svg
					class="animate-spin {spinnerSize} {textColor}"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					aria-hidden="true"
				>
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
			{:else if type === 'dots'}
				<!-- Bouncing Dots -->
				<div class="flex {containerSize}">
					<div
						class="rounded-full {dotSize} {bgColor} animate-bounce"
						style="animation-delay: 0s"
					></div>
					<div
						class="rounded-full {dotSize} {bgColor} animate-bounce"
						style="animation-delay: 0.2s"
					></div>
					<div
						class="rounded-full {dotSize} {bgColor} animate-bounce"
						style="animation-delay: 0.4s"
					></div>
				</div>
			{:else if type === 'pulse'}
				<!-- Pulsing Circle -->
				<div class="animate-pulse {spinnerSize} {textColor}">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
						/>
					</svg>
				</div>
			{:else}
				<!-- Fallback -->
				<div class="animate-spin {spinnerSize} {textColor}">
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
				</div>
			{/if}

			<!-- Optional text -->
			{#if text}
				<p class="mt-3 text-center text-sm font-medium {textColor}">{text}</p>
			{/if}
		</div>
	{/if}
{/if}
