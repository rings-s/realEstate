<script>
	import { t } from '$lib/config/translations';
	import { language } from '$lib/stores/ui';
	import { createEventDispatcher } from 'svelte';
	import { User } from 'lucide-svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// User object or initials or src
	export let user = null;
	// Image source URL (overrides user.avatar)
	export let src = '';
	// Avatar size: xs, sm, md, lg, xl
	export let size = 'md';
	// Avatar shape: circle, square, rounded
	export let shape = 'circle';
	// Display user initials when no image
	export let initials = '';
	// Border style
	export let border = false;
	// Badge to show (online status, notifications, etc.)
	export let badge = '';
	// Badge position: top-right, bottom-right, top-left, bottom-left
	export let badgePosition = 'bottom-right';
	// Badge color
	export let badgeColor = 'variant-filled-primary';
	// Additional classes
	export let classes = '';
	// Shadow effect
	export let shadow = false;
	// Interactive (clickable)
	export let interactive = false;
	// Alt text
	export let alt = '';

	// Generate initials from user object if available and no explicit initials provided
	$: {
		if (!initials && user) {
			if (user.first_name && user.last_name) {
				initials = `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
			} else if (user.full_name) {
				const nameParts = user.full_name.split(' ');
				if (nameParts.length >= 2) {
					initials = `${nameParts[0][0]}${nameParts[1][0]}`.toUpperCase();
				} else if (nameParts.length === 1) {
					initials = `${nameParts[0][0]}`.toUpperCase();
				}
			} else if (user.email) {
				initials = user.email[0].toUpperCase();
			}
		}
	}

	// Determine image source
	$: imageSrc = src || (user && user.avatar) || '';

	// Determine alt text
	$: altText =
		alt ||
		(user
			? user.full_name || user.first_name + ' ' + user.last_name || user.email
			: t('user_avatar', $language, { default: 'صورة المستخدم' }));

	// Size mapping to Skeleton classes
	$: sizeClass =
		{
			xs: 'avatar-xs',
			sm: 'avatar-sm',
			md: '', // Default avatar size
			lg: 'avatar-lg',
			xl: 'avatar-xl'
		}[size] || '';

	// Shape mapping to Skeleton classes
	$: shapeClass =
		{
			circle: '', // Default avatar shape
			square: 'avatar-square',
			rounded: 'avatar-rounded'
		}[shape] || '';

	// Handle click event
	function handleClick() {
		if (interactive) {
			dispatch('click');
		}
	}

	// Generate badge position class
	$: badgePositionClass = `badge-${badgePosition}`;
</script>

<div
	class="avatar {sizeClass} {shapeClass} {border
		? 'border border-surface-300-600-token'
		: ''} {shadow ? 'shadow-lg' : ''} {classes} {interactive
		? 'cursor-pointer hover:opacity-80 transition-opacity'
		: ''}"
	on:click={handleClick}
	on:keydown={(e) => e.key === 'Enter' && interactive && handleClick()}
	tabindex={interactive ? 0 : -1}
	role={interactive ? 'button' : 'presentation'}
>
	{#if imageSrc}
		<!-- Image avatar -->
		<img src={imageSrc} alt={altText} />
	{:else if initials}
		<!-- Initials avatar -->
		<span class="avatar-initials">{initials}</span>
	{:else}
		<!-- Default placeholder -->
		<span
			class="avatar-icon flex justify-center items-center h-full w-full bg-surface-300-600-token"
		>
			<User class="w-1/2 h-1/2 text-surface-900-50-token" />
		</span>
	{/if}

	{#if badge}
		<!-- Badge -->
		<span class="badge {badgeColor} {badgePositionClass}">{badge}</span>
	{/if}
</div>
