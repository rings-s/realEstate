<!-- src/routes/login/+page.svelte -->
<script>
	import { page } from '$app/stores';
	import LoginForm from '$lib/components/auth/LoginForm.svelte';

	// Get the redirect parameter from the URL if it exists
	$: redirectTo = $page.url.searchParams.get('redirect') || '/';
</script>

<svelte:head>
	<title>تسجيل الدخول | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">تسجيل الدخول</h1>
			<p class="mt-2 text-slate-600">أدخل بياناتك لتسجيل الدخول إلى حسابك</p>
		</div>

		<LoginForm {redirectTo} />
	</div>
</div>
