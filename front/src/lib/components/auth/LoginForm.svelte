<script>
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { User, Lock, Eye, EyeOff, Mail } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';
	import { isAuthenticated, currentUser } from '$lib/stores/auth';

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

<div class="card p-6 w-full max-w-md mx-auto">
	<header class="text-center mb-6">
		<h2 class="h2">{t('login', $language)}</h2>
		<p class="text-surface-600-300-token">
			{t('login_subtitle', $language, { default: 'تسجيل الدخول للوصول إلى حسابك' })}
		</p>
	</header>

	<!-- Error message -->
	{#if error}
		<div class="alert variant-filled-error mb-4">
			<div class="error-message">{error}</div>
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
				/>
			</div>
		</label>

		<!-- Password Field -->
		<label class="label mt-4">
			<span>{t('password', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
				<div class="input-group-shim">
					<Lock class="w-5 h-5" />
				</div>
				{#if showPassword}
					<input
						type="text"
						bind:value={password}
						placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="current-password"
						required
					/>
				{:else}
					<input
						type="password"
						bind:value={password}
						placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="current-password"
						required
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

		<!-- Remember Me & Forgot Password -->
		<div class="flex justify-between items-center mt-4">
			<label class="flex items-center space-x-2 {$isRTL ? 'flex-row-reverse space-x-reverse' : ''}">
				<input type="checkbox" bind:checked={rememberMe} class="checkbox" />
				<span>{t('remember_me', $language)}</span>
			</label>

			<a href="/auth/reset-password" class="anchor">{t('forgot_password', $language)}</a>
		</div>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
			{#if loading}
				<span class="spinner-circle-secondary loading loading-spinner loading-sm"></span>
				<span class="ml-2">{t('logging_in', $language, { default: 'جاري تسجيل الدخول...' })}</span>
			{:else}
				{t('login', $language)}
			{/if}
		</button>
	</form>

	<!-- Register Link -->
	<div class="mt-6 text-center">
		<p>
			{t('no_account', $language, { default: 'ليس لديك حساب؟' })}
			<a href="/auth/register" class="anchor">{t('register', $language)}</a>
		</p>
	</div>
</div>
