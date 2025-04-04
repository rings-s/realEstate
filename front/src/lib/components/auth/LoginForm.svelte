<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { uiStore, TOAST_TYPES } from '$lib/stores/ui';
	import { rules } from '$lib/utils/validation';

	// Form components
	import Button from '../common/Button.svelte';
	import Input from '../common/Input.svelte';
	import Alert from '../common/Alert.svelte';

	// Props
	export let redirectTo = '/dashboard';

	// Form state
	let email = '';
	let password = '';
	let rememberMe = false;
	let loading = false;
	let error = null;
	let emailError = '';
	let passwordError = '';
	let hasAttemptedLogin = false; // Track if user has attempted login

	// Validation
	function validateEmail() {
		if (!hasAttemptedLogin && !email) return true; // Don't show error on initial load

		emailError = rules.email(email) !== true ? rules.email(email) : '';
		if (!email) emailError = rules.required(email);
		return !emailError;
	}

	function validatePassword() {
		if (!hasAttemptedLogin && !password) return true; // Don't show error on initial load

		passwordError = !password ? rules.required(password) : '';
		return !passwordError;
	}

	function validateForm() {
		hasAttemptedLogin = true; // Mark that validation has been attempted
		const isEmailValid = validateEmail();
		const isPasswordValid = validatePassword();
		return isEmailValid && isPasswordValid;
	}

	// Handle form submission
	async function handleSubmit() {
		if (!validateForm()) return;

		loading = true;
		error = null;
		passwordError = '';

		try {
			await auth.login(email, password);
			uiStore.addToast('تم تسجيل الدخول بنجاح', TOAST_TYPES.SUCCESS);
			goto(redirectTo);
		} catch (err) {
			console.error('Login error:', err);

			// Check error type to display specific messages
			if (
				err.code === 'auth/wrong-password' ||
				err.code === 'auth/invalid-credential' ||
				err.message?.includes('password') ||
				err.message?.includes('credential')
			) {
				// Show specific password error
				passwordError = 'كلمة المرور غير صحيحة، يرجى المحاولة مرة أخرى';
			} else if (err.code === 'auth/user-not-found' || err.code === 'auth/invalid-email') {
				// Show specific email error
				emailError = 'البريد الإلكتروني غير مسجل في النظام';
			} else {
				// General error
				error = err.message || 'فشل تسجيل الدخول. الرجاء التحقق من بياناتك والمحاولة مرة أخرى.';
			}
		} finally {
			loading = false;
		}
	}

	// Handle "Enter" key press
	function handleKeyPress(event) {
		if (event.key === 'Enter' && !loading) {
			handleSubmit();
		}
	}

	onMount(() => {
		// Focus email input on mount
		const emailInput = document.getElementById('email-input');
		if (emailInput) emailInput.focus();
	});
</script>

<div class="w-full">
	<form on:submit|preventDefault={handleSubmit} class="w-full">
		{#if error}
			<Alert
				type="error"
				message={error}
				dismissible={true}
				on:dismiss={() => (error = null)}
				class="mb-4"
			/>
		{/if}

		<div class="mb-4">
			<Input
				id="email-input"
				type="email"
				label="البريد الإلكتروني"
				placeholder="أدخل بريدك الإلكتروني"
				value={email}
				error={emailError}
				on:input={(e) => {
					email = e.target.value;
					if (emailError) validateEmail();
				}}
				on:blur={validateEmail}
				on:keypress={handleKeyPress}
				required
				dir="ltr"
			/>
		</div>

		<div class="mb-4">
			<Input
				type="password"
				label="كلمة المرور"
				placeholder="أدخل كلمة المرور"
				value={password}
				error={passwordError}
				on:input={(e) => {
					password = e.target.value;
					if (passwordError) passwordError = '';
				}}
				on:blur={() => hasAttemptedLogin && validatePassword()}
				on:keypress={handleKeyPress}
				required
			/>
		</div>

		<div class="mb-6 flex items-center justify-between text-sm">
			<label class="flex cursor-pointer items-center">
				<input
					type="checkbox"
					bind:checked={rememberMe}
					class="form-checkbox text-primary-600 dark:text-primary-500 rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
				/>
				<span class="mr-2 text-gray-700 dark:text-gray-300">تذكرني</span>
			</label>

			<a
				href="/password-reset"
				class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium transition-colors hover:underline"
			>
				نسيت كلمة المرور؟
			</a>
		</div>

		<Button type="submit" variant="primary" fullWidth={true} disabled={loading} {loading}>
			تسجيل الدخول
		</Button>

		<div class="mt-6 text-center text-sm">
			<span class="text-gray-600 dark:text-gray-400">ليس لديك حساب؟</span>
			<a
				href="/register"
				class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 mr-2 font-semibold transition-colors hover:underline"
			>
				إنشاء حساب جديد
			</a>
		</div>
	</form>
</div>
