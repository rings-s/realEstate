<!--
  Register Page
-->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { language } from '$lib/stores/ui';
	import { isAuthenticated } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import RegisterForm from '$lib/components/auth/RegisterForm.svelte';

	// Redirect if already authenticated
	onMount(() => {
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});
</script>

<svelte:head>
	<title>{t('register', $language)} | {t('app_name', $language)}</title>
</svelte:head>

<div class="container mx-auto py-12 px-4">
	<RegisterForm />
</div>
