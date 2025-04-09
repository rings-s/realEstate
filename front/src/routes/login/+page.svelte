<!--
  Login Page
-->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { language } from '$lib/stores/ui';
	import { isAuthenticated } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import LoginForm from '$lib/components/auth/LoginForm.svelte';

	// Redirect if already authenticated
	onMount(() => {
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});
</script>

<svelte:head>
	<title>{t('login', $language)} | {t('app_name', $language)}</title>
</svelte:head>

<div class="container mx-auto py-12 px-4">
	<LoginForm />
</div>
