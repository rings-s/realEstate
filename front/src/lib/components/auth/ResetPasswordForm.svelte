<script>
	import { createEventDispatcher } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { Mail, Key, Eye, EyeOff, RefreshCw, CheckCircle } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';

	const dispatch = createEventDispatcher();

	// Form state tracking
	let step = 1; // 1 = request reset, 2 = verify code, 3 = set new password
	let loading = false;
	let error = '';
	let success = false;

	// Form data
	let email = '';
	let reset_code = '';
	let new_password = '';
	let confirm_password = '';
	let showPassword = false;
	let showConfirmPassword = false;

	// Get params from URL if available
	onMount(() => {
		if ($page.url.searchParams.has('email')) {
			email = $page.url.searchParams.get('email');

			if ($page.url.searchParams.has('code')) {
				reset_code = $page.url.searchParams.get('code');
				step = 2; // Move to verify code step
			}
		}
	});

	// Toggle password visibility
	const togglePassword = () => {
		showPassword = !showPassword;
	};

	const toggleConfirmPassword = () => {
		showConfirmPassword = !showConfirmPassword;
	};

	// Request password reset
	async function requestReset() {
		error = '';

		if (!email) {
			error = t('email_required', $language);
			return;
		}

		loading = true;

		try {
			await authService.requestPasswordReset(email);
			step = 2; // Move to verify code step

			uiStore.showToast(
				t('reset_code_sent', $language, {
					default: 'تم إرسال رمز إعادة تعيين كلمة المرور. يرجى التحقق من بريدك الإلكتروني.'
				}),
				'success'
			);
		} catch (err) {
			console.error('Reset request error:', err);

			// Handle rate limiting errors
			if (err.message && err.message.includes('rate_limit')) {
				error = t('rate_limit_exceeded', $language, {
					default: 'الرجاء الانتظار 5 دقائق قبل طلب رمز آخر'
				});
			} else {
				error =
					err.message ||
					t('reset_request_failed', $language, { default: 'فشل طلب إعادة تعيين كلمة المرور' });
			}
		} finally {
			loading = false;
		}
	}

	// Verify reset code
	async function verifyCode() {
		error = '';

		if (!email || !reset_code) {
			error = t('email_code_required', $language, {
				default: 'البريد الإلكتروني ورمز إعادة التعيين مطلوبان'
			});
			return;
		}

		loading = true;

		try {
			await authService.verifyResetCode(email, reset_code);
			step = 3; // Move to new password step
		} catch (err) {
			console.error('Code verification error:', err);

			// Handle specific error messages
			if (err.message && err.message.includes('reset_code_expired')) {
				error = t('reset_code_expired', $language, {
					default: 'انتهت صلاحية رمز إعادة التعيين'
				});
			} else {
				error =
					err.message ||
					t('invalid_code', $language, { default: 'رمز إعادة التعيين غير صالح أو منتهي الصلاحية' });
			}
		} finally {
			loading = false;
		}
	}

	// Reset password
	async function resetPassword() {
		error = '';

		if (!email || !reset_code || !new_password || !confirm_password) {
			error = t('all_fields_required', $language, { default: 'جميع الحقول مطلوبة' });
			return;
		}

		if (new_password !== confirm_password) {
			error = t('passwords_not_match', $language);
			return;
		}

		if (new_password.length < 8) {
			error = t('password_too_short', $language);
			return;
		}

		loading = true;

		try {
			// Call reset password service
			const response = await authService.resetPassword(
				email,
				reset_code,
				new_password,
				confirm_password
			);

			// Update auth store if user data is returned
			if (response.user) {
				isAuthenticated.set(true);
				currentUser.set(response.user);
			}

			// Show success message
			success = true;
			uiStore.showToast(
				t('password_reset_success', $language, { default: 'تم إعادة تعيين كلمة المرور بنجاح' }),
				'success'
			);

			// Navigate to dashboard or home after a short delay
			setTimeout(() => {
				goto('/dashboard');
			}, 2000);
		} catch (err) {
			console.error('Password reset error:', err);

			// Handle Django validation errors
			if (err.message && err.message.includes('invalid_password')) {
				error = t('password_requirements', $language, {
					default: 'كلمة المرور غير قوية بما فيه الكفاية. يجب أن تحتوي على أحرف وأرقام ورموز.'
				});
			} else if (err.message && err.message.includes('invalid_code')) {
				error = t('invalid_code', $language, {
					default: 'رمز إعادة التعيين غير صالح أو منتهي الصلاحية'
				});
			} else {
				error =
					err.message ||
					t('password_reset_failed', $language, { default: 'فشل إعادة تعيين كلمة المرور' });
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="card p-6 w-full max-w-md mx-auto">
	<header class="text-center mb-6">
		<h2 class="h2">{t('reset_password', $language)}</h2>
		<p class="text-surface-600-300-token">
			{#if step === 1}
				{t('reset_instructions_step1', $language, {
					default: 'أدخل بريدك الإلكتروني لتلقي رمز إعادة تعيين كلمة المرور'
				})}
			{:else if step === 2}
				{t('reset_instructions_step2', $language, {
					default: 'أدخل رمز إعادة التعيين المرسل إلى بريدك الإلكتروني'
				})}
			{:else}
				{t('reset_instructions_step3', $language, { default: 'أدخل كلمة المرور الجديدة' })}
			{/if}
		</p>
	</header>

	<!-- Step Progress -->
	<div class="flex justify-between mb-8">
		<div class="flex flex-col items-center">
			<div
				class="w-8 h-8 rounded-full flex items-center justify-center {step >= 1
					? 'bg-primary-500 text-white'
					: 'bg-surface-300-600-token'}"
			>
				1
			</div>
			<span class="text-xs mt-1">{t('request', $language, { default: 'الطلب' })}</span>
		</div>
		<div class="flex-1 flex items-center">
			<div class="h-1 w-full {step >= 2 ? 'bg-primary-500' : 'bg-surface-300-600-token'}"></div>
		</div>
		<div class="flex flex-col items-center">
			<div
				class="w-8 h-8 rounded-full flex items-center justify-center {step >= 2
					? 'bg-primary-500 text-white'
					: 'bg-surface-300-600-token'}"
			>
				2
			</div>
			<span class="text-xs mt-1">{t('verify', $language, { default: 'التحقق' })}</span>
		</div>
		<div class="flex-1 flex items-center">
			<div class="h-1 w-full {step >= 3 ? 'bg-primary-500' : 'bg-surface-300-600-token'}"></div>
		</div>
		<div class="flex flex-col items-center">
			<div
				class="w-8 h-8 rounded-full flex items-center justify-center {step >= 3
					? 'bg-primary-500 text-white'
					: 'bg-surface-300-600-token'}"
			>
				3
			</div>
			<span class="text-xs mt-1">{t('reset', $language, { default: 'إعادة التعيين' })}</span>
		</div>
	</div>

	<!-- Error message -->
	{#if error}
		<div class="alert variant-filled-error mb-4">
			<div>{error}</div>
		</div>
	{/if}

	<!-- Success message -->
	{#if success}
		<div class="alert variant-filled-success mb-4 flex items-center gap-2">
			<CheckCircle class="w-5 h-5" />
			<div>
				{t('password_reset_redirecting', $language, {
					default: 'تم إعادة تعيين كلمة المرور بنجاح! جاري توجيهك...'
				})}
			</div>
		</div>
	{/if}

	<!-- Step 1: Request Reset -->
	{#if step === 1}
		<form on:submit|preventDefault={requestReset} class={$textClass}>
			<!-- Email Field -->
			<label class="label">
				<span>{t('email', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim">
						<Mail class="w-5 h-5" />
					</div>
					<input
						type="email"
						bind:value={email}
						placeholder={t('email_placeholder', $language, { default: 'أدخل بريدك الإلكتروني' })}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="email"
						required
					/>
				</div>
			</label>

			<!-- Submit Button -->
			<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
				{#if loading}
					<span class="spinner-circle-secondary w-5 h-5"></span>
					<span class="ml-2">{t('sending', $language, { default: 'جاري الإرسال...' })}</span>
				{:else}
					{t('send_reset_code', $language, { default: 'إرسال رمز إعادة التعيين' })}
				{/if}
			</button>
		</form>

		<!-- Step 2: Verify Code -->
	{:else if step === 2}
		<form on:submit|preventDefault={verifyCode} class={$textClass}>
			<!-- Email Field (readonly) -->
			<label class="label">
				<span>{t('email', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim">
						<Mail class="w-5 h-5" />
					</div>
					<input
						type="email"
						bind:value={email}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						readonly
					/>
				</div>
			</label>

			<!-- Reset Code Field -->
			<label class="label mt-4">
				<span>{t('reset_code', $language, { default: 'رمز إعادة التعيين' })}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim">
						<Key class="w-5 h-5" />
					</div>
					<input
						type="text"
						bind:value={reset_code}
						placeholder={t('reset_code_placeholder', $language, {
							default: 'أدخل الرمز المكون من 6 أرقام'
						})}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
						maxlength="6"
						pattern="[0-9]{6}"
						inputmode="numeric"
					/>
				</div>
			</label>

			<!-- Submit Button -->
			<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
				{#if loading}
					<span class="spinner-circle-secondary w-5 h-5"></span>
					<span class="ml-2">{t('verifying', $language, { default: 'جاري التحقق...' })}</span>
				{:else}
					{t('verify_code', $language, { default: 'التحقق من الرمز' })}
				{/if}
			</button>

			<!-- Resend Code -->
			<div class="mt-6 text-center">
				<button type="button" class="btn variant-ghost-primary" on:click={() => (step = 1)}>
					<RefreshCw class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('resend_code', $language)}
				</button>
			</div>
		</form>

		<!-- Step 3: Set New Password -->
	{:else if step === 3}
		<form on:submit|preventDefault={resetPassword} class={$textClass}>
			<!-- New Password Field -->
			<label class="label">
				<span>{t('new_password', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
					<div class="input-group-shim">
						<Key class="w-5 h-5" />
					</div>
					{#if showPassword}
						<input
							type="text"
							bind:value={new_password}
							placeholder={t('new_password_placeholder', $language, {
								default: 'أدخل كلمة المرور الجديدة'
							})}
							class="input"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
							minlength="8"
						/>
					{:else}
						<input
							type="password"
							bind:value={new_password}
							placeholder={t('new_password_placeholder', $language, {
								default: 'أدخل كلمة المرور الجديدة'
							})}
							class="input"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
							minlength="8"
						/>
					{/if}
					<button type="button" class="input-group-shim" on:click={togglePassword}>
						{#if showPassword}
							<EyeOff class="w-5 h-5" />
						{:else}
							<Eye class="w-5 h-5" />
						{/if}
					</button>
				</div>
			</label>

			<!-- Confirm New Password Field -->
			<label class="label mt-4">
				<span>{t('confirm_password', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
					<div class="input-group-shim">
						<Key class="w-5 h-5" />
					</div>
					{#if showConfirmPassword}
						<input
							type="text"
							bind:value={confirm_password}
							placeholder={t('confirm_password_placeholder', $language, {
								default: 'تأكيد كلمة المرور الجديدة'
							})}
							class="input"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
						/>
					{:else}
						<input
							type="password"
							bind:value={confirm_password}
							placeholder={t('confirm_password_placeholder', $language, {
								default: 'تأكيد كلمة المرور الجديدة'
							})}
							class="input"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
						/>
					{/if}
					<button type="button" class="input-group-shim" on:click={toggleConfirmPassword}>
						{#if showConfirmPassword}
							<EyeOff class="w-5 h-5" />
						{:else}
							<Eye class="w-5 h-5" />
						{/if}
					</button>
				</div>
			</label>

			<!-- Password Requirements -->
			<div class="mt-2 text-sm text-surface-600-300-token {$textClass}">
				{t('password_requirements', $language, {
					default: 'يجب أن تحتوي كلمة المرور على 8 أحرف على الأقل'
				})}
			</div>

			<!-- Submit Button -->
			<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
				{#if loading}
					<span class="spinner-circle-secondary w-5 h-5"></span>
					<span class="ml-2">{t('resetting', $language, { default: 'جاري إعادة التعيين...' })}</span
					>
				{:else}
					{t('reset_password', $language)}
				{/if}
			</button>
		</form>
	{/if}

	<!-- Back to Login -->
	<div class="mt-6 text-center">
		<a href="/auth/login" class="anchor"
			>{t('back_to_login', $language, { default: 'العودة إلى تسجيل الدخول' })}</a
		>
	</div>
</div>
