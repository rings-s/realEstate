<!-- Improved LoginForm component -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { isAuthenticated, login } from '$lib/stores/auth';
	import { t } from '$lib/config/translations';
	import { Mail, Lock, Eye, EyeOff } from 'lucide-svelte';
  
	// Form data
	let email = '';
	let password = '';
	let showPassword = false;
	let rememberMe = false;
	let loading = false;
	let error = '';
	
	// Toggle password visibility
	const togglePassword = () => {
	  showPassword = !showPassword;
	};
  
	onMount(() => {
	  // Check for verified=true URL param and show success message
	  const urlParams = new URLSearchParams(window.location.search);
	  if (urlParams.get('verified') === 'true') {
		uiStore.showToast(
		  t('verification_success', $language, { 
			default: 'تم التحقق من البريد الإلكتروني بنجاح' 
		  }),
		  'success'
		);
	  }
	  
	  // If already authenticated, redirect to dashboard
	  if ($isAuthenticated) {
		goto('/dashboard');
	  }
	});
  
	// Handle login form submission
	async function handleSubmit() {
	  if (!email || !password) {
		error = t('fill_required_fields', $language);
		return;
	  }
  
	  loading = true;
	  error = '';
  
	  try {
		await login(email, password);
		
		// Redirect to dashboard on success
		goto('/dashboard');
	  } catch (err) {
		// Handle specific error codes
		if (err.message === 'email_not_verified') {
		  error = t('email_not_verified', $language);
		  
		  // Give option to resend verification
		  uiStore.showToast(
			t('verification_required', $language, { 
			  default: 'البريد الإلكتروني غير مؤكد. يرجى التحقق من بريدك الإلكتروني أو طلب رمز تحقق جديد.' 
			}),
			'warning'
		  );
		  
		  // Redirect to verification page
		  goto(`/auth/verify-email?email=${encodeURIComponent(email)}`);
		} else if (err.message === 'account_disabled') {
		  error = t('account_disabled', $language);
		} else if (err.message === 'invalid_credentials') {
		  error = t('invalid_credentials', $language);
		} else {
		  error = err.message || t('login_failed', $language);
		}
	  } finally {
		loading = false;
	  }
	}
</script>
  
  <!-- Form UI here -->

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
