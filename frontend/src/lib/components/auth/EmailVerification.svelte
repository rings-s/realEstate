<!-- src/lib/components/auth/EmailVerification.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { verifyEmail, resendVerification } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	export let defaultEmail = '';
	export let redirectTo = '/';

	let email = defaultEmail;
	let code = '';
	let loading = false;
	let resending = false;
	let error = '';
	let success = false;

	async function handleSubmit() {
		loading = true;
		error = '';

		const result = await verifyEmail(email, code);

		loading = false;

		if (result.success) {
			success = true;
			addToast('تم التحقق من البريد الإلكتروني بنجاح', 'success');
			setTimeout(() => goto(redirectTo), 2000);
		} else {
			error = result.error || 'فشل التحقق. يرجى التأكد من صحة الرمز.';
		}
	}

	async function handleResendCode() {
		resending = true;
		error = '';

		try {
			const result = await resendVerification(email);
			if (result.success) {
				addToast('تم إعادة إرسال رمز التحقق بنجاح', 'success');
			} else {
				error = result.error || 'فشل في إعادة إرسال رمز التحقق';
			}
		} catch (err) {
			error = err.message || 'حدث خطأ غير متوقع';
		} finally {
			resending = false;
		}
	}
</script>

{#if success}
	<div class="mb-6 rounded border-l-4 border-green-400 bg-green-50 p-4">
		<div class="flex">
			<div class="flex-shrink-0">
				<i class="fas fa-check-circle text-green-400"></i>
			</div>
			<div class="mr-3">
				<p class="text-sm text-green-700">تم التحقق من بريدك الإلكتروني بنجاح! جاري تحويلك...</p>
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
		<label for="code" class="mb-1 block text-sm font-medium text-slate-700">رمز التحقق</label>
		<input
			type="text"
			id="code"
			bind:value={code}
			required
			class="input"
			placeholder="أدخل رمز التحقق"
			dir="ltr"
		/>
	</div>

	<div>
		<button type="submit" class="btn-primary w-full" disabled={loading || success}>
			{#if loading}
				<i class="fas fa-spinner fa-spin ml-2"></i>
				جاري التحقق...
			{:else}
				تحقق من البريد الإلكتروني
			{/if}
		</button>
	</div>
</form>

<div class="mt-6 text-center">
	<p class="text-sm text-slate-600">
		لم تستلم رمز التحقق؟
		<button class="text-blue-600 hover:underline" on:click={handleResendCode} disabled={resending}>
			{#if resending}
				جاري إعادة الإرسال...
			{:else}
				إعادة إرسال الرمز
			{/if}
		</button>
	</p>
</div>
