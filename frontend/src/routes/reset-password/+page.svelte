<!-- src/routes/reset-password/+page.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { resetPassword, verifyResetCode } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	let email = '';
	let resetCode = '';
	let password = '';
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
		if (password !== confirmPassword) {
			error = 'كلمتا المرور غير متطابقتين';
			return;
		}

		if (password.length < 8) {
			error = 'كلمة المرور يجب أن تكون على الأقل 8 أحرف';
			return;
		}

		loading = true;
		error = '';

		try {
			const result = await resetPassword(email, resetCode, password, confirmPassword);

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

<svelte:head>
	<title>إعادة تعيين كلمة المرور | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">إعادة تعيين كلمة المرور</h1>
			<p class="mt-2 text-slate-600">
				{#if !verifiedCode}
					قم بإدخال البريد الإلكتروني والرمز المرسل إليك
				{:else}
					قم بإدخال كلمة المرور الجديدة
				{/if}
			</p>
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
						لم تحصل على الرمز؟ <a
							href="/reset-password/request"
							class="text-blue-600 hover:underline">طلب رمز جديد</a
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
					<label for="password" class="mb-1 block text-sm font-medium text-slate-700"
						>كلمة المرور الجديدة</label
					>
					<input
						type="password"
						id="password"
						bind:value={password}
						required
						minlength="8"
						class="input"
						placeholder="أدخل كلمة المرور الجديدة"
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

		<div class="mt-6 text-center">
			<p class="text-sm text-slate-600">
				تذكرت كلمة المرور؟
				<a href="/login" class="text-blue-600 hover:underline">تسجيل الدخول</a>
			</p>
		</div>
	</div>
</div>
