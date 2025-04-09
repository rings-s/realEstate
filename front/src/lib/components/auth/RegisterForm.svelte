<!--
  RegisterForm Component
  Handles user registration with Arabic language support
-->
<script>
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { User, Mail, Lock, Eye, EyeOff, Phone, Calendar, Users } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';
	import { ROLES } from '$lib/utils/permissions';

	const dispatch = createEventDispatcher();

	// Form data
	let email = '';
	let password = '';
	let confirm_password = '';
	let first_name = '';
	let last_name = '';
	let phone_number = '';
	let role = ROLES.BUYER; // Default role is buyer
	let date_of_birth = '';
	let showPassword = false;
	let showConfirmPassword = false;
	let agreeTerms = false;

	// Form state
	let loading = false;
	let error = '';
	let success = false;

	// Toggle password visibility
	const togglePassword = () => {
		showPassword = !showPassword;
	};

	const toggleConfirmPassword = () => {
		showConfirmPassword = !showConfirmPassword;
	};

	// Handle form submission
	async function handleSubmit() {
		error = '';
		success = false;

		// Form validation
		if (!email || !password || !confirm_password || !first_name || !last_name || !role) {
			error = t('fill_required_fields', $language, { default: 'يرجى ملء جميع الحقول المطلوبة' });
			return;
		}

		if (password !== confirm_password) {
			error = t('passwords_not_match', $language);
			return;
		}

		if (password.length < 8) {
			error = t('password_too_short', $language);
			return;
		}

		if (!agreeTerms) {
			error = t('terms_required', $language, { default: 'يجب الموافقة على الشروط والأحكام' });
			return;
		}

		loading = true;

		try {
			// Call register service
			const response = await authService.register({
				email,
				password,
				confirm_password,
				first_name,
				last_name,
				phone_number,
				role,
				date_of_birth: date_of_birth || undefined
			});

			// Show success message
			success = true;
			uiStore.showToast(
				t('register_success', $language, {
					default: 'تم التسجيل بنجاح! تحقق من بريدك الإلكتروني للتحقق.'
				}),
				'success'
			);

			// Redirect to verification page
			goto(`/auth/verify-email?email=${encodeURIComponent(email)}`);
		} catch (err) {
			console.error('Registration error:', err);
			error =
				err.message ||
				t('registration_failed', $language, { default: 'فشل التسجيل. يرجى المحاولة مرة أخرى.' });
		} finally {
			loading = false;
		}
	}
</script>

<div class="card p-6 w-full max-w-lg mx-auto">
	<header class="text-center mb-6">
		<h2 class="h2">{t('register', $language)}</h2>
		<p class="text-surface-600-300-token">
			{t('register_subtitle', $language, { default: 'إنشاء حساب جديد للوصول إلى المنصة' })}
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
		<div class="alert variant-filled-success mb-4">
			<div>
				{t('verification_sent', $language, {
					default: 'تم إرسال رمز التحقق إلى بريدك الإلكتروني.'
				})}
			</div>
		</div>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class={$textClass}>
		<!-- Name Fields (2 columns) -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<!-- First Name -->
			<label class="label">
				<span>{t('first_name', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim">
						<User class="w-5 h-5" />
					</div>
					<input
						type="text"
						bind:value={first_name}
						placeholder={t('first_name_placeholder', $language, { default: 'الاسم الأول' })}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
					/>
				</div>
			</label>

			<!-- Last Name -->
			<label class="label">
				<span>{t('last_name', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim">
						<User class="w-5 h-5" />
					</div>
					<input
						type="text"
						bind:value={last_name}
						placeholder={t('last_name_placeholder', $language, { default: 'اسم العائلة' })}
						class="input"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
					/>
				</div>
			</label>
		</div>

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
					autocomplete="email"
					required
				/>
			</div>
		</label>

		<!-- Phone Number -->
		<label class="label mt-4">
			<span>{t('phone_number', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim">
					<Phone class="w-5 h-5" />
				</div>
				<input
					type="tel"
					bind:value={phone_number}
					placeholder={t('phone_placeholder', $language, { default: 'رقم الهاتف (اختياري)' })}
					class="input"
					dir={$isRTL ? 'rtl' : 'ltr'}
					autocomplete="tel"
				/>
			</div>
		</label>

		<!-- Date of Birth -->
		<label class="label mt-4">
			<span>{t('date_of_birth', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim">
					<Calendar class="w-5 h-5" />
				</div>
				<input type="date" bind:value={date_of_birth} class="input" dir={$isRTL ? 'rtl' : 'ltr'} />
			</div>
		</label>

		<!-- Role Selection -->
		<label class="label mt-4">
			<span>{t('role', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim">
					<Users class="w-5 h-5" />
				</div>
				<select bind:value={role} class="select" dir={$isRTL ? 'rtl' : 'ltr'} required>
					<option value={ROLES.BUYER}>{t('buyer', $language)}</option>
					<option value={ROLES.SELLER}>{t('seller', $language)}</option>
					<option value={ROLES.AGENT}>{t('agent', $language)}</option>
				</select>
			</div>
		</label>

		<!-- Password Fields -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
			<!-- Password -->
			<label class="label">
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
							required
						/>
					{:else}
						<input
							type="password"
							bind:value={password}
							placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
							class="input"
							dir={$isRTL ? 'rtl' : 'ltr'}
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

			<!-- Confirm Password -->
			<label class="label">
				<span>{t('confirm_password', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
					<div class="input-group-shim">
						<Lock class="w-5 h-5" />
					</div>
					{#if showConfirmPassword}
						<input
							type="text"
							bind:value={confirm_password}
							placeholder={t('confirm_password_placeholder', $language, {
								default: 'تأكيد كلمة المرور'
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
								default: 'تأكيد كلمة المرور'
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
		</div>

		<!-- Terms and Conditions -->
		<label
			class="flex items-center mt-6 space-x-2 {$isRTL ? 'flex-row-reverse space-x-reverse' : ''}"
		>
			<input type="checkbox" bind:checked={agreeTerms} class="checkbox" required />
			<span>
				{t('agree_terms', $language, { default: 'أوافق على' })}
				<a href="/terms" class="anchor">{t('terms_and_conditions', $language)}</a>
			</span>
		</label>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full mt-6" disabled={loading}>
			{#if loading}
				<span class="loading loading-spinner loading-sm"></span>
				{t('registering', $language, { default: 'جاري التسجيل...' })}
			{:else}
				{t('register', $language)}
			{/if}
		</button>
	</form>

	<!-- Login Link -->
	<div class="mt-6 text-center">
		<p>
			{t('have_account', $language, { default: 'لديك حساب بالفعل؟' })}
			<a href="/auth/login" class="anchor">{t('login', $language)}</a>
		</p>
	</div>
</div>
