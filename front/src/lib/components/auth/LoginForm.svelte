<script>
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { User, Lock, Eye, EyeOff, Mail } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';
	import { fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	// Form data
	let email = '';
	let password = '';
	let rememberMe = false;
	let showPassword = false;

	// Form state
	let loading = false;
	let error = '';

	// Toggle password visibility
	const togglePassword = () => {
		showPassword = !showPassword;
	};

	// Handle form submission
	async function handleSubmit() {
		error = '';

		// Validate form
		if (!email) {
			error = t('email_required', $language);
			return;
		}

		if (!password) {
			error = t('password_required', $language);
			return;
		}

		loading = true;

		try {
			// Call login service
			const response = await authService.login(email, password);

			// Update auth store with user data
			if (response.user) {
				isAuthenticated.set(true);
				currentUser.set(response.user);

				// Show success message
				uiStore.showToast(
					t('login_success', $language, { default: 'تم تسجيل الدخول بنجاح' }),
					'success'
				);

				// Navigate to dashboard
				goto('/dashboard');
			} else {
				throw new Error(t('login_error', $language, { default: 'حدث خطأ أثناء تسجيل الدخول' }));
			}
		} catch (err) {
			console.error('Login error:', err);

			// Handle different error types
			if (err.message && err.message.includes('email_not_verified')) {
				error = t('email_not_verified', $language, {
					default: 'البريد الإلكتروني غير مُوثق. يرجى التحقق من بريدك الإلكتروني لرمز التحقق.'
				});

				// Offer to resend verification email
				const resendLink = document.createElement('a');
				resendLink.href = `/auth/verify-email?email=${encodeURIComponent(email)}`;
				resendLink.textContent = t('resend_verification', $language, {
					default: 'إعادة إرسال رمز التحقق'
				});
				resendLink.className = 'anchor ml-2';

				// Add the link to the error message
				setTimeout(() => {
					const errorElement = document.querySelector('.error-message');
					if (errorElement) {
						errorElement.appendChild(document.createTextNode(' '));
						errorElement.appendChild(resendLink);
					}
				}, 0);
			} else if (err.message && err.message.includes('account_disabled')) {
				error = t('account_disabled', $language, {
					default: 'تم تعطيل الحساب. يرجى الاتصال بالدعم.'
				});
			} else {
				error =
					err.message ||
					t('invalid_credentials', $language, { default: 'بيانات الاعتماد غير صالحة' });
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="card p-5 w-full max-w-md mx-auto shadow-lg">
	<header class="text-center mb-5">
		<h2 class="text-2xl font-bold">{t('login', $language)}</h2>
		<p class="text-surface-600-300-token text-sm mt-1">
			{t('login_subtitle', $language, { default: 'تسجيل الدخول للوصول إلى حسابك' })}
		</p>
	</header>

	<!-- Error message -->
	{#if error}
		<div class="alert variant-filled-error mb-4" transition:fade={{ duration: 200 }}>
			<div class="error-message text-sm">{error}</div>
		</div>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class={$textClass}>
		<!-- Email Field -->
		<label class="label">
			<span class="text-sm font-medium">{t('email', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim flex items-center justify-center">
					<Mail class="w-4 h-4" />
				</div>
				<input
					type="email"
					bind:value={email}
					placeholder={t('email_placeholder', $language, { default: 'أدخل بريدك الإلكتروني' })}
					class="input h-9 text-sm"
					dir={$isRTL ? 'rtl' : 'ltr'}
					autocomplete="email"
					required
				/>
			</div>
		</label>

		<!-- Password Field -->
		<label class="label mt-3">
			<span class="text-sm font-medium">{t('password', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
				<div class="input-group-shim flex items-center justify-center">
					<Lock class="w-4 h-4" />
				</div>
				{#if showPassword}
					<input
						type="text"
						bind:value={password}
						placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
						class="input h-9 text-sm"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="current-password"
						required
					/>
				{:else}
					<input
						type="password"
						bind:value={password}
						placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
						class="input h-9 text-sm"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="current-password"
						required
					/>
				{/if}
				<button
					type="button"
					class="input-group-shim flex items-center justify-center"
					on:click={togglePassword}
				>
					{#if showPassword}
						<EyeOff class="w-4 h-4" />
					{:else}
						<Eye class="w-4 h-4" />
					{/if}
				</button>
			</div>
		</label>

		<!-- Remember Me & Forgot Password -->
		<div class="flex justify-between items-center mt-3">
			<label class="flex items-center space-x-2 {$isRTL ? 'flex-row-reverse space-x-reverse' : ''}">
				<input type="checkbox" bind:checked={rememberMe} class="checkbox" />
				<span class="text-sm">{t('remember_me', $language)}</span>
			</label>

			<a href="/auth/reset-password" class="anchor text-sm">{t('forgot_password', $language)}</a>
		</div>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full h-10 mt-5" disabled={loading}>
			{#if loading}
				<span class="loading-spinner h-4 w-4 mr-2"></span>
				<span>{t('logging_in', $language, { default: 'جاري تسجيل الدخول...' })}</span>
			{:else}
				{t('login', $language)}
			{/if}
		</button>
	</form>

	<!-- Register Link -->
	<div class="mt-5 text-center">
		<p class="text-sm">
			{t('no_account', $language, { default: 'ليس لديك حساب؟' })}
			<a href="/auth/register" class="anchor">{t('register', $language)}</a>
		</p>
	</div>
</div>

<style>
	.loading-spinner {
		border: 2px solid rgba(255, 255, 255, 0.2);
		border-top-color: currentColor;
		border-radius: 50%;
		animation: loading-spinner 0.8s linear infinite;
	}

	@keyframes loading-spinner {
		to {
			transform: rotate(360deg);
		}
	}
</style>
