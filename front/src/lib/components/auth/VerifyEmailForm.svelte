<script>
	import { createEventDispatcher } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { Mail, CheckCircle, RefreshCw } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';

	const dispatch = createEventDispatcher();

	// Form data
	let email = '';
	let verification_code = '';

	// Form state
	let loading = false;
	let resending = false;
	let error = '';
	let success = false;

	// Get email from URL query params
	onMount(() => {
		if ($page.url.searchParams.has('email')) {
			email = $page.url.searchParams.get('email');
		}
	});

	// Handle form submission
	async function handleSubmit() {
		error = '';
		success = false;

		// Validate form
		if (!email) {
			error = t('email_required', $language);
			return;
		}

		if (!verification_code) {
			error = t('verification_code_required', $language, { default: 'يرجى إدخال رمز التحقق' });
			return;
		}

		loading = true;

		try {
			// Call verify email service
			const response = await authService.verifyEmail(email, verification_code);

			// Update auth store
			if (response.user) {
				isAuthenticated.set(true);
				currentUser.set(response.user);

				// Show success message
				success = true;
				uiStore.showToast(
					t('email_verified', $language, { default: 'تم التحقق من بريدك الإلكتروني بنجاح' }),
					'success'
				);

				// Navigate to dashboard after a short delay
				setTimeout(() => {
					goto('/dashboard');
				}, 2000);
			} else {
				throw new Error(
					t('verification_error', $language, {
						default: 'حدث خطأ أثناء التحقق من البريد الإلكتروني'
					})
				);
			}
		} catch (err) {
			console.error('Verification error:', err);

			// Parse error messages from backend
			if (err.message && err.message.includes('invalid_code')) {
				error = t('invalid_verification_code', $language, {
					default: 'رمز التحقق غير صالح أو منتهي الصلاحية'
				});
			} else if (err.message && err.message.includes('verification_code_expired')) {
				error = t('verification_code_expired', $language, {
					default: 'انتهت صلاحية رمز التحقق. يرجى طلب رمز جديد.'
				});
			} else {
				error =
					err.message ||
					t('invalid_code', $language, { default: 'رمز التحقق غير صالح أو منتهي الصلاحية' });
			}
		} finally {
			loading = false;
		}
	}

	// Resend verification code
	async function resendCode() {
		if (resending) return;

		if (!email) {
			error = t('email_required', $language);
			return;
		}

		resending = true;
		error = '';

		try {
			console.log(`Requesting verification code resend for: ${email}`);
			await authService.resendVerification(email);

			uiStore.showToast(
				t('verification_resent', $language, { default: 'تم إعادة إرسال رمز التحقق' }),
				'success'
			);
		} catch (err) {
			console.error('Resend error:', err);

			// Handle rate limiting errors
			if (err.message && err.message.includes('rate_limit')) {
				error = t('rate_limit_exceeded', $language, {
					default: 'تم تجاوز الحد الأقصى للمحاولات. يرجى الانتظار قبل المحاولة مرة أخرى.'
				});
			} else {
				error =
					err.message || t('resend_failed', $language, { default: 'فشل إعادة إرسال رمز التحقق' });
			}
		} finally {
			resending = false;
		}
	}
</script>

<div class="card p-6 w-full max-w-md mx-auto">
	<header class="text-center mb-6">
		<h2 class="h2">{t('verify_email', $language)}</h2>
		<p class="text-surface-600-300-token">
			{t('verification_instructions', $language, {
				default: 'أدخل رمز التحقق المرسل إلى بريدك الإلكتروني'
			})}
		</p>
	</header>

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
				{t('email_verified_redirecting', $language, {
					default: 'تم التحقق من بريدك الإلكتروني! جاري توجيهك...'
				})}
			</div>
		</div>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class={$textClass}>
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
					readonly={!!email}
				/>
			</div>
		</label>

		<!-- Verification Code Field -->
		<label class="label mt-4">
			<span>{t('verification_code', $language)}</span>
			<input
				type="text"
				bind:value={verification_code}
				placeholder={t('verification_code_placeholder', $language, {
					default: 'أدخل رمز التحقق المكون من 6 أرقام'
				})}
				class="input"
				dir={$isRTL ? 'rtl' : 'ltr'}
				required
				maxlength="6"
				inputmode="numeric"
			/>
		</label>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
			{#if loading}
				<span class="spinner-circle-secondary w-5 h-5"></span>
				<span class="ml-2">{t('verifying', $language, { default: 'جاري التحقق...' })}</span>
			{:else}
				{t('verify_email', $language)}
			{/if}
		</button>

		<!-- Resend Code -->
		<div class="mt-6 text-center">
			<p>{t('didnt_receive_code', $language, { default: 'لم تستلم الرمز؟' })}</p>
			<button
				type="button"
				class="btn variant-ghost-primary mt-2 {resending ? 'opacity-50' : ''}"
				on:click={resendCode}
				disabled={resending}
			>
				{#if resending}
					<span class="spinner-circle-secondary w-4 h-4"></span>
					<span class="ml-2">{t('resending', $language, { default: 'جاري إعادة الإرسال...' })}</span
					>
				{:else}
					<RefreshCw class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('resend_code', $language)}
				{/if}
			</button>
		</div>

		<!-- Back to Login -->
		<div class="mt-6 text-center">
			<a href="/auth/login" class="anchor"
				>{t('back_to_login', $language, { default: 'العودة إلى تسجيل الدخول' })}</a
			>
		</div>
	</form>
</div>
