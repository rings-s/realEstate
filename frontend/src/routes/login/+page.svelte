<!-- src/routes/login/+page.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { login } from '$lib/services/auth';

	let email = '';
	let password = '';
	let loading = false;
	let error = '';

	async function handleSubmit() {
		loading = true;
		error = '';

		const result = await login(email, password);

		loading = false;

		if (result.success) {
			goto('/');
		} else {
			error = result.error || 'خطأ في تسجيل الدخول. يرجى التحقق من بياناتك.';
		}
	}
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

		{#if error}
			<div class="mb-6 rounded border-l-4 border-red-400 bg-red-50 p-4">
				<div class="flex">
					<div class="flex-shrink-0">
						<i class="fas fa-exclamation-circle text-red-400"></i>
					</div>
					<div class="mr-3">
						<p class="text-sm text-red-700">{error}</p>
					</div>
				</div>
			</div>
		{/if}

		<form on:submit|preventDefault={handleSubmit} class="space-y-4">
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-slate-700"
					>البريد الإلكتروني</label
				>
				<input
					type="email"
					id="email"
					bind:value={email}
					required
					class="input"
					placeholder="أدخل بريدك الإلكتروني"
					dir="ltr"
				/>
			</div>

			<div>
				<div class="flex items-center justify-between">
					<label for="password" class="block text-sm font-medium text-slate-700">كلمة المرور</label>
					<a href="/reset-password" class="text-sm text-blue-600 hover:underline"
						>نسيت كلمة المرور؟</a
					>
				</div>
				<input
					type="password"
					id="password"
					bind:value={password}
					required
					class="input mt-1"
					placeholder="أدخل كلمة المرور"
				/>
			</div>

			<div class="flex items-center">
				<input
					id="remember"
					type="checkbox"
					class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
				/>
				<label for="remember" class="mr-2 block text-sm text-slate-700"> تذكر تسجيل الدخول </label>
			</div>

			<div>
				<button type="submit" class="btn-primary w-full" disabled={loading}>
					{#if loading}
						<i class="fas fa-spinner fa-spin ml-2"></i>
						جاري تسجيل الدخول...
					{:else}
						تسجيل الدخول
					{/if}
				</button>
			</div>
		</form>

		<div class="mt-6 text-center">
			<p class="text-sm text-slate-600">
				ليس لديك حساب؟
				<a href="/register" class="text-blue-600 hover:underline">إنشاء حساب جديد</a>
			</p>
		</div>
	</div>
</div>
