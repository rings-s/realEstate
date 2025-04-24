<!-- src/routes/register/+page.svelte -->
<script>
	import { goto } from '$app/navigation';
	import RegisterForm from '$lib/components/auth/RegisterForm.svelte';
	import EmailVerification from '$lib/components/auth/EmailVerification.svelte';

	let step = 1;
	let registeredEmail = '';

	function handleRegisterSuccess(email) {
		registeredEmail = email;
		step = 2;
	}
</script>

<svelte:head>
	<title>تسجيل حساب جديد | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		{#if step === 1}
			<div class="mb-6 text-center">
				<h1 class="text-2xl font-bold text-slate-900">تسجيل حساب جديد</h1>
				<p class="mt-2 text-slate-600">قم بإنشاء حساب للمشاركة في المزادات العقارية</p>
			</div>

			<RegisterForm onSuccess={handleRegisterSuccess} />
		{:else if step === 2}
			<div class="mb-6 text-center">
				<h1 class="text-2xl font-bold text-slate-900">التحقق من البريد الإلكتروني</h1>
				<p class="mt-2 text-slate-600">تم إرسال رمز التحقق إلى بريدك الإلكتروني</p>
			</div>

			<EmailVerification defaultEmail={registeredEmail} redirectTo="/" />

			<div class="mt-4 text-center">
				<button class="text-sm text-blue-600 hover:underline" on:click={() => (step = 1)}>
					العودة إلى التسجيل
				</button>
			</div>
		{/if}
	</div>
</div>
