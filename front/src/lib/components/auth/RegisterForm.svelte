<script>
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { language, isRTL, textClass, uiStore } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import { User, Mail, Lock, Eye, EyeOff, Phone, Calendar, Users } from 'lucide-svelte';
	import * as authService from '$lib/services/authService';
	import { ROLES } from '$lib/utils/permissions';
	import { fade } from 'svelte/transition';

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
	let validationErrors = {};

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
		validationErrors = {};

		// Form validation
		const requiredFields = {
			email,
			password,
			confirm_password,
			first_name,
			last_name,
			role
		};

		// Check required fields
		let missingFields = [];
		for (const [field, value] of Object.entries(requiredFields)) {
			if (!value) {
				missingFields.push(field);
			}
		}

		if (missingFields.length > 0) {
			error = t('fill_required_fields', $language, { default: 'يرجى ملء جميع الحقول المطلوبة' });
			validationErrors = missingFields.reduce((acc, field) => {
				acc[field] = true;
				return acc;
			}, {});
			return;
		}

		// Password validation
		if (password !== confirm_password) {
			error = t('passwords_not_match', $language);
			validationErrors.confirm_password = true;
			return;
		}

		if (password.length < 8) {
			error = t('password_too_short', $language);
			validationErrors.password = true;
			return;
		}

		// Terms validation
		if (!agreeTerms) {
			error = t('terms_required', $language, { default: 'يجب الموافقة على الشروط والأحكام' });
			validationErrors.agreeTerms = true;
			return;
		}

		loading = true;

		try {
			// Prepare data object for registration
			const userData = {
				email,
				password,
				confirm_password,
				first_name,
				last_name,
				role
			};

			// Add optional fields if provided
			if (phone_number) userData.phone_number = phone_number;
			if (date_of_birth) userData.date_of_birth = date_of_birth;

			// Call register service
			await authService.register(userData);

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

			// Handle validation errors from the backend
			if (err.details && typeof err.details === 'object') {
				validationErrors = err.details;

				// Create a readable error message from validation errors
				const errorMessages = [];
				for (const [field, message] of Object.entries(err.details)) {
					const fieldName = t(field, $language, { default: field });
					errorMessages.push(`${fieldName}: ${message}`);
				}

				error = errorMessages.join('. ');
			} else {
				error =
					err.message ||
					t('registration_failed', $language, { default: 'فشل التسجيل. يرجى المحاولة مرة أخرى.' });
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="card p-5 w-full max-w-md mx-auto shadow-lg">
	<header class="text-center mb-5">
		<h2 class="text-2xl font-bold">{t('register', $language)}</h2>
		<p class="text-surface-600-300-token text-sm mt-1">
			{t('register_subtitle', $language, { default: 'إنشاء حساب جديد للوصول إلى المنصة' })}
		</p>
	</header>

	<!-- Error message -->
	{#if error}
		<div class="alert variant-filled-error mb-4" transition:fade={{ duration: 200 }}>
			<div class="text-sm">{error}</div>
		</div>
	{/if}

	<!-- Success message -->
	{#if success}
		<div class="alert variant-filled-success mb-4" transition:fade={{ duration: 200 }}>
			<div class="text-sm">
				{t('verification_sent', $language, {
					default: 'تم إرسال رمز التحقق إلى بريدك الإلكتروني.'
				})}
			</div>
		</div>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class={$textClass}>
		<!-- Name Fields (2 columns) -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<!-- First Name -->
			<label class="label">
				<span class="text-sm font-medium">{t('first_name', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim flex items-center justify-center">
						<User class="w-4 h-4" />
					</div>
					<input
						type="text"
						bind:value={first_name}
						placeholder={t('first_name_placeholder', $language, { default: 'الاسم الأول' })}
						class="input h-9 text-sm {validationErrors.first_name ? 'input-error' : ''}"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
					/>
				</div>
			</label>

			<!-- Last Name -->
			<label class="label">
				<span class="text-sm font-medium">{t('last_name', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim flex items-center justify-center">
						<User class="w-4 h-4" />
					</div>
					<input
						type="text"
						bind:value={last_name}
						placeholder={t('last_name_placeholder', $language, { default: 'اسم العائلة' })}
						class="input h-9 text-sm {validationErrors.last_name ? 'input-error' : ''}"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
					/>
				</div>
			</label>
		</div>

		<!-- Email Field -->
		<label class="label mt-3">
			<span class="text-sm font-medium">{t('email', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim flex items-center justify-center">
					<Mail class="w-4 h-4" />
				</div>
				<input
					type="email"
					bind:value={email}
					placeholder={t('email_placeholder', $language, { default: 'أدخل بريدك الإلكتروني' })}
					class="input h-9 text-sm {validationErrors.email ? 'input-error' : ''}"
					dir={$isRTL ? 'rtl' : 'ltr'}
					autocomplete="email"
					required
				/>
			</div>
		</label>

		<!-- Password Fields (2 columns) -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
			<!-- Password -->
			<label class="label">
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
							class="input h-9 text-sm {validationErrors.password ? 'input-error' : ''}"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
							minlength="8"
						/>
					{:else}
						<input
							type="password"
							bind:value={password}
							placeholder={t('password_placeholder', $language, { default: 'أدخل كلمة المرور' })}
							class="input h-9 text-sm {validationErrors.password ? 'input-error' : ''}"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
							minlength="8"
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
				{#if validationErrors.password}
					<div class="text-xs text-error-500 mt-1">
						{t('password_requirements', $language, {
							default: 'يجب أن تحتوي كلمة المرور على 8 أحرف على الأقل'
						})}
					</div>
				{/if}
			</label>

			<!-- Confirm Password -->
			<label class="label">
				<span class="text-sm font-medium">{t('confirm_password', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr_auto]">
					<div class="input-group-shim flex items-center justify-center">
						<Lock class="w-4 h-4" />
					</div>
					{#if showConfirmPassword}
						<input
							type="text"
							bind:value={confirm_password}
							placeholder={t('confirm_password_placeholder', $language, {
								default: 'تأكيد كلمة المرور'
							})}
							class="input h-9 text-sm {validationErrors.confirm_password ? 'input-error' : ''}"
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
							class="input h-9 text-sm {validationErrors.confirm_password ? 'input-error' : ''}"
							dir={$isRTL ? 'rtl' : 'ltr'}
							required
						/>
					{/if}
					<button
						type="button"
						class="input-group-shim flex items-center justify-center"
						on:click={toggleConfirmPassword}
					>
						{#if showConfirmPassword}
							<EyeOff class="w-4 h-4" />
						{:else}
							<Eye class="w-4 h-4" />
						{/if}
					</button>
				</div>
				{#if validationErrors.confirm_password}
					<div class="text-xs text-error-500 mt-1">
						{t('passwords_not_match', $language, {
							default: 'كلمات المرور غير متطابقة'
						})}
					</div>
				{/if}
			</label>
		</div>

		<!-- Optional Fields -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
			<!-- Phone Number -->
			<label class="label">
				<span class="text-sm font-medium">{t('phone_number', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim flex items-center justify-center">
						<Phone class="w-4 h-4" />
					</div>
					<input
						type="tel"
						bind:value={phone_number}
						placeholder={t('phone_placeholder', $language, { default: 'رقم الهاتف (اختياري)' })}
						class="input h-9 text-sm {validationErrors.phone_number ? 'input-error' : ''}"
						dir={$isRTL ? 'rtl' : 'ltr'}
						autocomplete="tel"
					/>
				</div>
				{#if validationErrors.phone_number}
					<div class="text-xs text-error-500 mt-1">
						{t('invalid_phone', $language, { default: 'يجب أن يكون رقم الهاتف بصيغة صحيحة' })}
					</div>
				{/if}
			</label>

			<!-- Role Selection -->
			<label class="label">
				<span class="text-sm font-medium">{t('role', $language)}</span>
				<div class="input-group input-group-divider grid-cols-[auto_1fr]">
					<div class="input-group-shim flex items-center justify-center">
						<Users class="w-4 h-4" />
					</div>
					<select
						bind:value={role}
						class="select h-9 text-sm {validationErrors.role ? 'input-error' : ''}"
						dir={$isRTL ? 'rtl' : 'ltr'}
						required
					>
						<option value={ROLES.BUYER}>{t('buyer', $language)}</option>
						<option value={ROLES.SELLER}>{t('seller', $language)}</option>
						<option value={ROLES.AGENT}>{t('agent', $language)}</option>
					</select>
				</div>
			</label>
		</div>

		<!-- Date of Birth (optional) -->
		<label class="label mt-3">
			<span class="text-sm font-medium">{t('date_of_birth', $language)}</span>
			<div class="input-group input-group-divider grid-cols-[auto_1fr]">
				<div class="input-group-shim flex items-center justify-center">
					<Calendar class="w-4 h-4" />
				</div>
				<input
					type="date"
					bind:value={date_of_birth}
					class="input h-9 text-sm {validationErrors.date_of_birth ? 'input-error' : ''}"
					dir={$isRTL ? 'rtl' : 'ltr'}
				/>
			</div>
		</label>

		<!-- Terms and Conditions -->
		<label
			class="flex items-center mt-4 space-x-2 {$isRTL ? 'flex-row-reverse space-x-reverse' : ''}"
		>
			<input
				type="checkbox"
				bind:checked={agreeTerms}
				class="checkbox {validationErrors.agreeTerms ? 'checkbox-error' : ''}"
				required
			/>
			<span class="text-sm">
				{t('agree_terms', $language, { default: 'أوافق على' })}
				<a href="/terms" class="anchor">{t('terms_and_conditions', $language)}</a>
			</span>
		</label>

		<!-- Submit Button -->
		<button type="submit" class="btn variant-filled-primary w-full h-10 mt-5" disabled={loading}>
			{#if loading}
				<span class="loading-spinner h-4 w-4 mr-2"></span>
				<span>{t('registering', $language, { default: 'جاري التسجيل...' })}</span>
			{:else}
				{t('register', $language)}
			{/if}
		</button>
	</form>

	<!-- Login Link -->
	<div class="mt-5 text-center">
		<p class="text-sm">
			{t('have_account', $language, { default: 'لديك حساب بالفعل؟' })}
			<a href="/auth/login" class="anchor">{t('login', $language)}</a>
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
