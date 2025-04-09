<!--
  Reset Password Page
-->
<script>
	import { language } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import ResetPasswordForm from '$lib/components/auth/ResetPasswordForm.svelte';
</script>

<svelte:head>
	<title>{t('reset_password', $language)} | {t('app_name', $language)}</title>
</svelte:head>

<div class="container mx-auto py-12 px-4">
	<ResetPasswordForm />
</div>
