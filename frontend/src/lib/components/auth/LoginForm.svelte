<!-- src/lib/components/auth/LoginForm.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { login } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	export let redirectTo = '/';

	let email = '';
	let password = '';
	let rememberMe = false;
	let loading = false;
	let error = '';

	async function handleSubmit() {
		loading = true;
		error = '';

		const result = await login(email, password);

		loading = false;

		if (result.success) {
			addToast('تم تسجيل الدخول بنجاح', 'success');
			goto(redirectTo);
		} else {
			error = result.error || 'خطأ في تسجيل الدخول. يرجى التحقق من بياناتك.';
		}
	}
</script>

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
			<a href="/reset-password/request" class="text-sm text-blue-600 hover:underline"
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
			autocomplete="current-password"
		/>
	</div>

	<div class="flex items-center">
		<input
			id="remember"
			type="checkbox"
			bind:checked={rememberMe}
			class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
		/>
		<label for="remember" class="mr-2 block text-sm text-slate-700">تذكر تسجيل الدخول</label>
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
