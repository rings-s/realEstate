<!-- src/routes/reset-password/request/+page.svelte -->
<script>
	import ResetPasswordRequestForm from '$lib/components/auth/ResetPasswordRequestForm.svelte';
</script>

<svelte:head>
	<title>طلب إعادة تعيين كلمة المرور | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">طلب إعادة تعيين كلمة المرور</h1>
			<p class="mt-2 text-slate-600">أدخل بريدك الإلكتروني لتلقي رمز إعادة تعيين كلمة المرور</p>
		</div>

		<ResetPasswordRequestForm />
	</div>
</div>
