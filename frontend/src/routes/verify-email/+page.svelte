<!-- src/routes/verify-email/+page.svelte -->
<script>
	import EmailVerification from '$lib/components/auth/EmailVerification.svelte';
</script>

<svelte:head>
	<title>التحقق من البريد الإلكتروني | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">التحقق من البريد الإلكتروني</h1>
			<p class="mt-2 text-slate-600">أدخل الرمز المرسل إلى بريدك الإلكتروني للتحقق من حسابك</p>
		</div>

		<EmailVerification />
	</div>
</div>
