<!--
  Verify Email Page
-->
<script>
	import { language } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import VerifyEmailForm from '$lib/components/auth/VerifyEmailForm.svelte';
</script>

<svelte:head>
	<title>{t('verify_email', $language)} | {t('app_name', $language)}</title>
</svelte:head>

<div class="container mx-auto py-12 px-4">
	<VerifyEmailForm />
</div>
