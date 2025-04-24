<!-- src/lib/components/auth/ResetPasswordForm.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { verifyResetCode, resetPassword } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	export let defaultEmail = '';

	let email = defaultEmail;
	let resetCode = '';
	let newPassword = '';
	let confirmPassword = '';
	let verifiedCode = false;
	let loading = false;
	let error = '';

	async function verifyCode() {
		if (!email || !resetCode) {
			error = 'يرجى إدخال البريد الإلكتروني ورمز إعادة التعيين';
			return;
		}

		loading = true;
		error = '';

		try {
			const result = await verifyResetCode(email, resetCode);

			if (result.success) {
				verifiedCode = true;
				addToast('تم التحقق من الرمز بنجاح', 'success');
			} else {
				error = result.error || 'رمز غير صالح أو منتهي الصلاحية';
			}
		} catch (err) {
			error = err.message || 'حدث خطأ غير متوقع';
		} finally {
			loading = false;
		}
	}

	async function handleReset() {
		if (newPassword !== confirmPassword) {
			error = 'كلمتا المرور غير متطابقتين';
			return;
		}

		if (newPassword.length < 8) {
			error = 'كلمة المرور يجب أن تكون على الأقل 8 أحرف';
			return;
		}

		loading = true;
		error = '';

		try {
			const result = await resetPassword(email, resetCode, newPassword, confirmPassword);

			if (result.success) {
				addToast('تم إعادة تعيين كلمة المرور بنجاح', 'success');
				setTimeout(() => goto('/login'), 1500);
			} else {
				error = result.error || 'فشل في إعادة تعيين كلمة المرور';
			}
		} catch (err) {
			error = err.message || 'حدث خطأ غير متوقع';
		} finally {
			loading = false;
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

{#if !verifiedCode}
	<form on:submit|preventDefault={verifyCode} class="space-y-4">
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
			<label for="resetCode" class="mb-1 block text-sm font-medium text-slate-700"
				>رمز إعادة التعيين</label
			>
			<input
				type="text"
				id="resetCode"
				bind:value={resetCode}
				required
				class="input"
				placeholder="أدخل رمز إعادة التعيين"
				dir="ltr"
			/>
			<p class="mt-1 text-xs text-slate-500">
				لم تحصل على الرمز؟ <a href="/reset-password/request" class="text-blue-600 hover:underline"
					>طلب رمز جديد</a
				>
			</p>
		</div>

		<div>
			<button type="submit" class="btn-primary w-full" disabled={loading}>
				{#if loading}
					<i class="fas fa-spinner fa-spin ml-2"></i>
					جاري التحقق...
				{:else}
					التحقق من الرمز
				{/if}
			</button>
		</div>
	</form>
{:else}
	<form on:submit|preventDefault={handleReset} class="space-y-4">
		<div>
			<label for="newPassword" class="mb-1 block text-sm font-medium text-slate-700"
				>كلمة المرور الجديدة</label
			>
			<input
				type="password"
				id="password"
				bind:value={formData.password}
				required
				class="input"
				placeholder="أدخل كلمة المرور"
				minlength="8"
				autocomplete="new-password"
			/>
		</div>

		<div>
			<label for="confirmPassword" class="mb-1 block text-sm font-medium text-slate-700"
				>تأكيد كلمة المرور الجديدة</label
			>
			<input
				type="password"
				id="confirmPassword"
				bind:value={confirmPassword}
				required
				minlength="8"
				class="input"
				placeholder="أعد إدخال كلمة المرور الجديدة"
			/>
		</div>

		<div>
			<button type="submit" class="btn-primary w-full" disabled={loading}>
				{#if loading}
					<i class="fas fa-spinner fa-spin ml-2"></i>
					جاري إعادة تعيين كلمة المرور...
				{:else}
					إعادة تعيين كلمة المرور
				{/if}
			</button>
		</div>
	</form>
{/if}
