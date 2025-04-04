<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { uiStore, TOAST_TYPES } from '$lib/stores/ui';
	import { rules } from '$lib/utils/validation';
	import authService from '$lib/services/auth';

	// Form components
	import Button from '../common/Button.svelte';
	import Input from '../common/Input.svelte';
	import Alert from '../common/Alert.svelte';

	// Props
	export let redirectTo = '/dashboard';

	// Form state
	let email = '';
	let verificationCode = '';
	let loading = false;
	let error = null;
	let success = false;
	let resendDisabled = false;
	let resendTimer = 0;
	let timerInterval = null;

	// Validation errors
	let emailError = '';
	let codeError = '';

	// Initialize component
	onMount(() => {
		// Check if email was provided in URL query
		const urlParams = new URLSearchParams(window.location.search);
		const urlEmail = urlParams.get('email');

		if (urlEmail) {
			email = urlEmail;
		}

		// Focus first empty input
		setTimeout(() => {
			const input = email
				? document.getElementById('verification-code-input')
				: document.getElementById('email-input');

			if (input) input.focus();
		}, 100);
	});

	// Validation functions
	function validateEmail() {
		if (!email) {
			emailError = rules.required(email);
			return false;
		}

		emailError = rules.email(email) !== true ? rules.email(email) : '';
		return !emailError;
	}

	function validateCode() {
		if (!verificationCode) {
			codeError = rules.required(verificationCode);
			return false;
		}

		if (verificationCode.length !== 6 || !rules.number(verificationCode)) {
			codeError = 'رمز التحقق يجب أن يتكون من 6 أرقام';
			return false;
		}

		codeError = '';
		return true;
	}

	function validateForm() {
		const isEmailValid = validateEmail();
		const isCodeValid = validateCode();
		return isEmailValid && isCodeValid;
	}

	// Handle form submission
	async function handleSubmit() {
		if (!validateForm()) return;

		loading = true;
		error = null;

		try {
			const response = await auth.verifyEmail(email, verificationCode);
			success = true;
			uiStore.addToast('تم التحقق من بريدك الإلكتروني بنجاح!', TOAST_TYPES.SUCCESS);

			// Redirect after 2 seconds
			setTimeout(() => {
				goto(redirectTo);
			}, 2000);
		} catch (err) {
			error = err.message || 'رمز التحقق غير صحيح أو منتهي الصلاحية. الرجاء المحاولة مرة أخرى.';
			console.error('Email verification error:', err);
		} finally {
			loading = false;
		}
	}

	// Resend verification code
	async function resendVerificationCode() {
		if (!validateEmail() || resendDisabled) return;

		loading = true;
		error = null;

		try {
			await authService.resendVerification(email);
			uiStore.addToast('تم إعادة إرسال رمز التحقق إلى بريدك الإلكتروني', TOAST_TYPES.SUCCESS);

			// Disable resend button for 60 seconds
			resendDisabled = true;
			resendTimer = 60;

			timerInterval = setInterval(() => {
				resendTimer--;
				if (resendTimer <= 0) {
					clearInterval(timerInterval);
					resendDisabled = false;
				}
			}, 1000);
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء إعادة إرسال رمز التحقق. الرجاء المحاولة مرة أخرى.';
			console.error('Resend verification code error:', err);
		} finally {
			loading = false;
		}
	}

	// Handle input focus for verification code
	function handleCodeInput(e) {
		const input = e.target;
		const value = input.value.replace(/\D/g, ''); // Keep only digits

		// Update verification code with only digits
		verificationCode = value.slice(0, 6);

		// Auto validate after 6 digits
		if (verificationCode.length === 6 && codeError) validateCode();
	}

	// Clean up on component destroy
	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
	});
</script>

<div class="flex w-full items-center justify-center p-4">
	<form
		on:submit|preventDefault={handleSubmit}
		class="shadow-card w-full max-w-md rounded-lg bg-white p-6 sm:p-8"
	>
		<h1 class="font-heading text-primary-600 mb-6 text-center text-2xl font-bold sm:text-3xl">
			التحقق من البريد الإلكتروني
		</h1>

		{#if error}
			<Alert type="error" message={error} dismissible={true} on:dismiss={() => (error = null)} />
		{/if}

		{#if success}
			<div class="flex flex-col items-center py-4 text-center">
				<div class="mb-4 text-green-500">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="h-16 w-16"
					>
						<path d="M0 0h24v24H0V0z" fill="none" />
						<path
							d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm4.59-12.42L10 14.17l-2.59-2.58L6 13l4 4 8-8z"
						/>
					</svg>
				</div>
				<h2 class="mb-2 text-xl font-bold text-green-600">تم التحقق من بريدك الإلكتروني بنجاح!</h2>
				<p class="mb-2 text-gray-600">سيتم تحويلك إلى لوحة التحكم...</p>
			</div>
		{:else}
			<p class="mb-4 text-sm text-gray-600">
				لقد أرسلنا رمز تحقق مكون من 6 أرقام إلى بريدك الإلكتروني. يرجى إدخال الرمز أدناه للتحقق من
				حسابك.
			</p>

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
					required
					dir="ltr"
					disabled={loading}
				/>
			</div>

			<div class="mb-6">
				<label for="verification-code-input" class="mb-1 block text-sm font-medium text-gray-700"
					>رمز التحقق</label
				>

				<div class="space-y-4">
					<div>
						<Input
							id="verification-code-input"
							type="text"
							placeholder="أدخل رمز التحقق المكون من 6 أرقام"
							value={verificationCode}
							error={codeError}
							on:input={handleCodeInput}
							on:blur={validateCode}
							maxlength="6"
							pattern="[0-9]*"
							inputmode="numeric"
							required
							dir="ltr"
							disabled={loading}
							class="text-center tracking-wider"
						/>
					</div>

					<div class="flex justify-between gap-2">
						{#each Array(6) as _, i}
							<div
								class={`flex h-12 flex-1 items-center justify-center border-2 ${verificationCode.length > i ? 'border-primary-500 bg-primary-50' : 'border-gray-300'} rounded-md text-xl font-bold`}
							>
								{verificationCode[i] || ''}
							</div>
						{/each}
					</div>
				</div>
			</div>

			<div class="mb-6 text-center">
				<button
					type="button"
					class={`text-sm ${resendDisabled ? 'cursor-not-allowed text-gray-400' : 'text-primary-600 hover:text-primary-700 hover:underline'} focus:ring-primary-500 rounded-md px-2 py-1 font-medium focus:ring-2 focus:ring-offset-2 focus:outline-none`}
					on:click={resendVerificationCode}
					disabled={resendDisabled || loading}
				>
					{resendDisabled ? `إعادة الإرسال (${resendTimer})` : 'لم تستلم الرمز؟ إعادة إرسال'}
				</button>
			</div>

			<Button type="submit" variant="primary" fullWidth={true} disabled={loading} {loading}>
				تأكيد
			</Button>

			<div class="mt-6 text-center text-sm">
				<a
					href="/login"
					class="text-primary-600 hover:text-primary-700 font-semibold transition-colors hover:underline"
				>
					العودة إلى تسجيل الدخول
				</a>
			</div>
		{/if}
	</form>
</div>
