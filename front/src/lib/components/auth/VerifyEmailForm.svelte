<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { isAuthenticated } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { Mail, Check, RefreshCw } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';

	// Form data
	let email = '';
	let verification_code = '';
	let loading = false;
	let error = '';
	let resendLoading = false;

	onMount(() => {
		// Get email from URL query parameter
		const urlParams = new URLSearchParams(window.location.search);
		email = urlParams.get('email') || '';

		// If already authenticated, redirect to dashboard
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});

	async function handleVerify() {
		if (!email || !verification_code) {
			error = t('verification_required_fields', $language, {
				default: 'البريد الإلكتروني ورمز التحقق مطلوبان'
			});
			return;
		}

		loading = true;
		error = '';

		try {
			const response = await authService.verifyEmail(email, verification_code);
			console.log('Verification successful:', response);

			// Handle successful verification
			uiStore.showToast(
				t('email_verified_success', $language, {
					default: 'تم التحقق من البريد الإلكتروني بنجاح'
				}),
				'success'
			);

			// Redirect to dashboard or login
			if (response.token) {
				// If token is provided, we're logged in
				goto('/dashboard');
			} else {
				goto('/auth/login?verified=true');
			}
		} catch (err) {
			console.log('Verification error:', err);
			error =
				err.message ||
				t('verification_failed', $language, {
					default: 'فشل التحقق من البريد الإلكتروني'
				});
		} finally {
			loading = false;
		}
	}

	async function handleResendCode() {
		if (!email) {
			error = t('email_required', $language);
			return;
		}

		resendLoading = true;
		error = '';

		try {
			await authService.resendVerification(email);

			uiStore.showToast(
				t('verification_code_resent', $language, {
					default: 'تم إعادة إرسال رمز التحقق'
				}),
				'success'
			);
		} catch (err) {
			error =
				err.message ||
				t('resend_failed', $language, {
					default: 'فشل إعادة إرسال رمز التحقق'
				});
		} finally {
			resendLoading = false;
		}
	}
</script>

<div class="card p-6 w-full max-w-lg mx-auto">
	<header class="text-center mb-6">
		<h2 class="h2">{t('verify_email', $language)}</h2>
		<p class="text-surface-600-300-token">
			{t('verification_subtitle', $language, {
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

	<form on:submit|preventDefault={handleVerify} class={$textClass}>
		<!-- Email Field -->
		<label class="label mt-4">
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
					readonly={!!email}
					required
				/>
			</div>
		</label>

		<!-- Verification Code Field -->
		<label class="label mt-4">
			<span>{t('verification_code', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim">
					<Check class="w-5 h-5" />
				</div>
				<input
					type="text"
					bind:value={verification_code}
					placeholder={t('verification_code_placeholder', $language, {
						default: 'أدخل رمز التحقق المكون من 6 أرقام'
					})}
					class="input"
					dir={$isRTL ? 'rtl' : 'ltr'}
					required
				/>
			</div>
		</label>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
			{#if loading}
				<span class="loading loading-spinner loading-sm"></span>
				{t('verifying', $language, { default: 'جاري التحقق...' })}
			{:else}
				{t('verify_button', $language, { default: 'تحقق' })}
			{/if}
		</button>
	</form>

	<!-- Resend Code -->
	<div class="mt-6 text-center">
		<p>
			{t('didnt_receive_code', $language, { default: 'لم تستلم الرمز؟' })}
			<button
				class="btn btn-sm variant-ghost-primary"
				on:click={handleResendCode}
				disabled={resendLoading}
			>
				{#if resendLoading}
					<span class="loading loading-spinner loading-xs"></span>
					{t('resending', $language, { default: 'جاري إعادة الإرسال...' })}
				{:else}
					{t('resend_code', $language, { default: 'إعادة إرسال الرمز' })}
				{/if}
			</button>
		</p>
	</div>

	<!-- Back to Login Link -->
	<div class="mt-4 text-center">
		<a href="/auth/login" class="anchor">
			{t('back_to_login', $language, { default: 'العودة إلى تسجيل الدخول' })}
		</a>
	</div>
</div>
