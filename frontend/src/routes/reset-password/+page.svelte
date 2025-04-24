<!-- src/routes/reset-password/+page.svelte -->
<script>
	import { page } from '$app/stores';
	import ResetPasswordForm from '$lib/components/auth/ResetPasswordForm.svelte';

	// Check if there's email in query parameters
	let defaultEmail = $page.url.searchParams.get('email') || '';
</script>

<svelte:head>
	<title>إعادة تعيين كلمة المرور | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">إعادة تعيين كلمة المرور</h1>
			<p class="mt-2 text-slate-600">قم بإدخال البريد الإلكتروني والرمز المرسل إليك</p>
		</div>

		<ResetPasswordForm {defaultEmail} />
	</div>
</div>
