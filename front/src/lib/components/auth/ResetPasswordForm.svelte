<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { uiStore, TOAST_TYPES } from '$lib/stores/ui';
	import { rules } from '$lib/utils/validation';
	import authService from '$lib/services/auth';

	// Form components
	import Button from '../common/Button.svelte';
	import Input from '../common/Input.svelte';
	import Alert from '../common/Alert.svelte';

	// Props
	export let redirectTo = '/login';

	// Form steps
	const STEPS = {
		REQUEST: 'request',
		VERIFY: 'verify',
		RESET: 'reset',
		SUCCESS: 'success'
	};

	// Form state
	let email = '';
	let resetCode = '';
	let newPassword = '';
	let confirmPassword = '';
	let currentStep = STEPS.REQUEST;
	let loading = false;
	let error = null;
	let successMessage = '';

	// Validation errors
	let emailError = '';
	let resetCodeError = '';
	let newPasswordError = '';
	let confirmPasswordError = '';

	// Check URL parameters for email and step
	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const urlEmail = urlParams.get('email');
		const urlStep = urlParams.get('step');

		if (urlEmail) {
			email = urlEmail;
		}

		if (urlStep && Object.values(STEPS).includes(urlStep)) {
			currentStep = urlStep;
		}

		// Focus first input
		setTimeout(() => {
			const firstInput = document.querySelector('input');
			if (firstInput) firstInput.focus();
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

	function validateResetCode() {
		if (!resetCode) {
			resetCodeError = rules.required(resetCode);
			return false;
		}

		if (resetCode.length !== 6 || !rules.number(resetCode)) {
			resetCodeError = 'رمز التحقق يجب أن يتكون من 6 أرقام';
			return false;
		}

		resetCodeError = '';
		return true;
	}

	function validateNewPassword() {
		if (!newPassword) {
			newPasswordError = rules.required(newPassword);
			return false;
		}

		newPasswordError = rules.password(newPassword) !== true ? rules.password(newPassword) : '';
		return !newPasswordError;
	}

	function validateConfirmPassword() {
		if (!confirmPassword) {
			confirmPasswordError = rules.required(confirmPassword);
			return false;
		}

		if (newPassword !== confirmPassword) {
			confirmPasswordError = 'كلمتا المرور غير متطابقتين';
			return false;
		}

		confirmPasswordError = '';
		return true;
	}

	// Request password reset
	async function requestPasswordReset() {
		if (!validateEmail()) return;

		loading = true;
		error = null;

		try {
			await authService.requestPasswordReset(email);
			currentStep = STEPS.VERIFY;

			// Update URL without reloading the page
			const url = new URL(window.location);
			url.searchParams.set('email', email);
			url.searchParams.set('step', STEPS.VERIFY);
			window.history.pushState({}, '', url);

			successMessage = 'تم إرسال رمز التحقق إلى بريدك الإلكتروني';
			uiStore.clearToasts();
			uiStore.addToast(successMessage, TOAST_TYPES.SUCCESS);
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء إرسال رمز التحقق. الرجاء المحاولة مرة أخرى.';
			console.error('Password reset request error:', err);
		} finally {
			loading = false;
		}
	}

	// Verify reset code
	async function verifyResetCode() {
		if (!validateEmail() || !validateResetCode()) return;

		loading = true;
		error = null;

		try {
			await authService.verifyResetCode(email, resetCode);
			currentStep = STEPS.RESET;

			// Update URL without reloading the page
			const url = new URL(window.location);
			url.searchParams.set('step', STEPS.RESET);
			window.history.pushState({}, '', url);

			successMessage = 'تم التحقق من الرمز بنجاح';
			uiStore.clearToasts();
			uiStore.addToast(successMessage, TOAST_TYPES.SUCCESS);
		} catch (err) {
			error = err.message || 'رمز التحقق غير صحيح أو منتهي الصلاحية. الرجاء المحاولة مرة أخرى.';
			console.error('Reset code verification error:', err);
		} finally {
			loading = false;
		}
	}

	// Reset password
	async function resetPassword() {
		if (
			!validateEmail() ||
			!validateResetCode() ||
			!validateNewPassword() ||
			!validateConfirmPassword()
		)
			return;

		loading = true;
		error = null;

		try {
			await authService.resetPassword(email, resetCode, newPassword, confirmPassword);
			currentStep = STEPS.SUCCESS;

			// Update URL without reloading the page
			const url = new URL(window.location);
			url.searchParams.set('step', STEPS.SUCCESS);
			window.history.pushState({}, '', url);

			successMessage = 'تم إعادة تعيين كلمة المرور بنجاح';
			uiStore.clearToasts();
			uiStore.addToast(successMessage, TOAST_TYPES.SUCCESS);
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء إعادة تعيين كلمة المرور. الرجاء المحاولة مرة أخرى.';
			console.error('Password reset error:', err);
		} finally {
			loading = false;
		}
	}

	// Handle form submission based on current step
	function handleSubmit() {
		switch (currentStep) {
			case STEPS.REQUEST:
				requestPasswordReset();
				break;
			case STEPS.VERIFY:
				verifyResetCode();
				break;
			case STEPS.RESET:
				resetPassword();
				break;
			case STEPS.SUCCESS:
				goto(redirectTo);
				break;
		}
	}

	// Go back to previous step
	function goBack() {
		switch (currentStep) {
			case STEPS.VERIFY:
				currentStep = STEPS.REQUEST;
				break;
			case STEPS.RESET:
				currentStep = STEPS.VERIFY;
				break;
			default:
				currentStep = STEPS.REQUEST;
		}

		// Update URL
		const url = new URL(window.location);
		url.searchParams.set('step', currentStep);
		window.history.pushState({}, '', url);

		error = null;
	}

	// Resend reset code
	async function resendResetCode() {
		if (!validateEmail()) return;

		loading = true;
		error = null;

		try {
			await authService.requestPasswordReset(email);
			uiStore.clearToasts();
			uiStore.addToast('تم إعادة إرسال رمز التحقق إلى بريدك الإلكتروني', TOAST_TYPES.SUCCESS);
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء إعادة إرسال رمز التحقق. الرجاء المحاولة مرة أخرى.';
			console.error('Resend reset code error:', err);
		} finally {
			loading = false;
		}
	}
</script>

<div class="w-full">
	{#if error}
		<Alert
			type="error"
			message={error}
			dismissible={true}
			on:dismiss={() => (error = null)}
			class="mb-4"
		/>
	{/if}

	{#if successMessage && (currentStep === STEPS.VERIFY || currentStep === STEPS.RESET)}
		<Alert
			type="success"
			message={successMessage}
			dismissible={true}
			on:dismiss={() => (successMessage = '')}
			class="mb-4"
		/>
	{/if}

	<form on:submit|preventDefault={handleSubmit} class="space-y-6">
		<!-- Progress Indicator -->
		<div class="mb-6">
			<div class="flex justify-between">
				<div
					class={`flex flex-col items-center ${currentStep === STEPS.REQUEST ? 'text-primary-600 dark:text-primary-400' : currentStep !== STEPS.REQUEST ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}
				>
					<div
						class={`flex h-8 w-8 items-center justify-center rounded-full ${
							currentStep === STEPS.REQUEST
								? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
								: currentStep !== STEPS.REQUEST
									? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
									: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
						} text-sm font-medium`}
					>
						1
					</div>
					<span class="mt-1 text-xs">طلب</span>
				</div>

				<div
					class={`flex flex-col items-center ${currentStep === STEPS.VERIFY ? 'text-primary-600 dark:text-primary-400' : currentStep === STEPS.RESET || currentStep === STEPS.SUCCESS ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}
				>
					<div
						class={`flex h-8 w-8 items-center justify-center rounded-full ${
							currentStep === STEPS.VERIFY
								? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
								: currentStep === STEPS.RESET || currentStep === STEPS.SUCCESS
									? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
									: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
						} text-sm font-medium`}
					>
						2
					</div>
					<span class="mt-1 text-xs">تحقق</span>
				</div>

				<div
					class={`flex flex-col items-center ${currentStep === STEPS.RESET ? 'text-primary-600 dark:text-primary-400' : currentStep === STEPS.SUCCESS ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`}
				>
					<div
						class={`flex h-8 w-8 items-center justify-center rounded-full ${
							currentStep === STEPS.RESET
								? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
								: currentStep === STEPS.SUCCESS
									? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
									: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
						} text-sm font-medium`}
					>
						3
					</div>
					<span class="mt-1 text-xs">تعيين</span>
				</div>

				<div
					class={`flex flex-col items-center ${currentStep === STEPS.SUCCESS ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'}`}
				>
					<div
						class={`flex h-8 w-8 items-center justify-center rounded-full ${
							currentStep === STEPS.SUCCESS
								? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
								: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
						} text-sm font-medium`}
					>
						4
					</div>
					<span class="mt-1 text-xs">نجاح</span>
				</div>
			</div>

			<div class="relative mt-3 h-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
				<div
					class="bg-primary-600 dark:bg-primary-500 absolute top-0 right-0 h-full rounded-full transition-all duration-300"
					style={`width: ${
						currentStep === STEPS.REQUEST
							? '25%'
							: currentStep === STEPS.VERIFY
								? '50%'
								: currentStep === STEPS.RESET
									? '75%'
									: '100%'
					}`}
				></div>
			</div>
		</div>

		{#if currentStep === STEPS.REQUEST}
			<p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
				أدخل البريد الإلكتروني المرتبط بحسابك وسنرسل إليك رمز تأكيد لإعادة تعيين كلمة المرور.
			</p>

			<div>
				<Input
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
					class="bg-white dark:bg-gray-700"
				/>
			</div>

			<Button type="submit" variant="primary" fullWidth={true} disabled={loading} {loading}>
				إرسال رمز التأكيد
			</Button>
		{:else if currentStep === STEPS.VERIFY}
			<p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
				أدخل رمز التأكيد المكون من 6 أرقام الذي تم إرساله إلى بريدك الإلكتروني {email}.
			</p>

			<div>
				<Input
					type="text"
					label="رمز التأكيد"
					placeholder="أدخل رمز التأكيد"
					value={resetCode}
					error={resetCodeError}
					on:input={(e) => {
						resetCode = e.target.value.replace(/\D/g, '').substring(0, 6);
						if (resetCodeError) validateResetCode();
					}}
					on:blur={validateResetCode}
					maxlength="6"
					pattern="[0-9]*"
					inputmode="numeric"
					required
					dir="ltr"
					class="bg-white text-center tracking-wider dark:bg-gray-700"
				/>
			</div>

			<div class="mb-2 text-center">
				<button
					type="button"
					class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 focus:ring-primary-500 rounded-md px-2 py-1 text-sm font-medium hover:underline focus:ring-2 focus:ring-offset-2 focus:outline-none dark:focus:ring-offset-gray-800"
					on:click={resendResetCode}
					disabled={loading}
				>
					لم تستلم الرمز؟ إعادة إرسال
				</button>
			</div>

			<div class="flex flex-col gap-4 sm:flex-row sm:justify-between">
				<Button
					type="button"
					variant="outline"
					on:click={goBack}
					disabled={loading}
					class="order-2 w-full sm:order-1 sm:w-auto"
				>
					رجوع
				</Button>

				<Button
					type="submit"
					variant="primary"
					disabled={loading}
					{loading}
					class="order-1 w-full sm:order-2 sm:w-auto"
				>
					تحقق من الرمز
				</Button>
			</div>
		{:else if currentStep === STEPS.RESET}
			<p class="mb-4 text-sm text-gray-600 dark:text-gray-300">
				أدخل كلمة المرور الجديدة الخاصة بك.
			</p>

			<div>
				<Input
					type="password"
					label="كلمة المرور الجديدة"
					placeholder="أدخل كلمة المرور الجديدة"
					value={newPassword}
					error={newPasswordError}
					on:input={(e) => {
						newPassword = e.target.value;
						if (newPasswordError) validateNewPassword();
						if (confirmPassword && confirmPasswordError) validateConfirmPassword();
					}}
					on:blur={validateNewPassword}
					required
					class="bg-white dark:bg-gray-700"
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل وتتضمن حرف كبير وحرف صغير ورقم ورمز خاص
				</p>
			</div>

			<div>
				<Input
					type="password"
					label="تأكيد كلمة المرور الجديدة"
					placeholder="أدخل كلمة المرور الجديدة مرة أخرى"
					value={confirmPassword}
					error={confirmPasswordError}
					on:input={(e) => {
						confirmPassword = e.target.value;
						if (confirmPasswordError) validateConfirmPassword();
					}}
					on:blur={validateConfirmPassword}
					required
					class="bg-white dark:bg-gray-700"
				/>
			</div>

			<div class="flex flex-col gap-4 sm:flex-row sm:justify-between">
				<Button
					type="button"
					variant="outline"
					on:click={goBack}
					disabled={loading}
					class="order-2 w-full sm:order-1 sm:w-auto"
				>
					رجوع
				</Button>

				<Button
					type="submit"
					variant="primary"
					disabled={loading}
					{loading}
					class="order-1 w-full sm:order-2 sm:w-auto"
				>
					إعادة تعيين كلمة المرور
				</Button>
			</div>
		{:else if currentStep === STEPS.SUCCESS}
			<div class="flex flex-col items-center py-4 text-center">
				<div class="mb-4 text-green-500 dark:text-green-400">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2"
						class="h-16 w-16"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				</div>
				<h2 class="mb-2 text-xl font-bold text-green-600 dark:text-green-400">
					تم إعادة تعيين كلمة المرور بنجاح!
				</h2>
				<p class="mb-6 text-gray-600 dark:text-gray-300">
					يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة.
				</p>

				<Button type="button" variant="primary" fullWidth={true} on:click={() => goto('/login')}>
					الذهاب إلى صفحة تسجيل الدخول
				</Button>
			</div>
		{/if}
	</form>
</div>
