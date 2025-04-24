<!-- src/routes/reset-password/request/+page.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { resetPasswordRequest } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	let email = '';
	let loading = false;
	let error = '';
	let success = false;

	async function handleSubmit() {
		loading = true;
		error = '';

		try {
			const result = await resetPasswordRequest(email);

			if (result.success) {
				success = true;
				addToast('تم إرسال رمز إعادة تعيين كلمة المرور إلى بريدك الإلكتروني', 'success');
				setTimeout(() => goto('/reset-password'), 2000);
			} else {
				error = result.error || 'حدث خطأ أثناء طلب إعادة تعيين كلمة المرور';
			}
		} catch (err) {
			error = err.message || 'حدث خطأ غير متوقع';
		} finally {
			loading = false;
		}
	}
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

		{#if success}
			<div class="mb-6 rounded border-l-4 border-green-400 bg-green-50 p-4">
				<div class="flex">
					<div class="flex-shrink-0">
						<i class="fas fa-check-circle text-green-400"></i>
					</div>
					<div class="mr-3">
						<p class="text-sm text-green-700">
							تم إرسال تعليمات إعادة تعيين كلمة المرور إلى بريدك الإلكتروني. جاري التحويل...
						</p>
					</div>
				</div>
			</div>
		{:else if error}
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
				<button type="submit" class="btn-primary w-full" disabled={loading || success}>
					{#if loading}
						<i class="fas fa-spinner fa-spin ml-2"></i>
						جاري الإرسال...
					{:else}
						إرسال رمز إعادة التعيين
					{/if}
				</button>
			</div>
		</form>

		<div class="mt-6 text-center">
			<p class="text-sm text-slate-600">
				تذكرت كلمة المرور؟
				<a href="/login" class="text-blue-600 hover:underline">تسجيل الدخول</a>
			</p>
		</div>
	</div>
</div>
