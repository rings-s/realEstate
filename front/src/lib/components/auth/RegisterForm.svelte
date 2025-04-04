<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { uiStore, TOAST_TYPES } from '$lib/stores/ui';
	import { rules } from '$lib/utils/validation';

	// Form components
	import Button from '../common/Button.svelte';
	import Input from '../common/Input.svelte';
	import Select from '../common/Select.svelte';
	import Alert from '../common/Alert.svelte';

	// Props
	export let redirectTo = '/email-verification';

	// Roles options from our model
	const roleOptions = [
		{ value: 'seller', label: 'بائع العقارات' },
		{ value: 'buyer', label: 'مشتري العقارات' },
		{ value: 'agent', label: 'وكيل عقارات' },
		{ value: 'inspector', label: 'مفتش العقارات' },
		{ value: 'legal', label: 'ممثل قانوني' },
		{ value: 'appraiser', label: 'مثمن' }
	];

	// Form state
	let formData = {
		email: '',
		password: '',
		confirm_password: '',
		first_name: '',
		last_name: '',
		phone_number: '',
		role: ''
	};

	let errors = {
		email: '',
		password: '',
		confirm_password: '',
		first_name: '',
		last_name: '',
		phone_number: '',
		role: ''
	};

	let loading = false;
	let generalError = null;
	let currentStep = 1;
	const totalSteps = 2;

	// Validation functions
	function validateEmail() {
		const { email } = formData;
		if (!email) {
			errors.email = rules.required(email);
			return false;
		}

		errors.email = rules.email(email) !== true ? rules.email(email) : '';
		return !errors.email;
	}

	function validatePassword() {
		const { password } = formData;
		if (!password) {
			errors.password = rules.required(password);
			return false;
		}

		errors.password = rules.password(password) !== true ? rules.password(password) : '';
		return !errors.password;
	}

	function validateConfirmPassword() {
		const { password, confirm_password } = formData;
		if (!confirm_password) {
			errors.confirm_password = rules.required(confirm_password);
			return false;
		}

		if (password !== confirm_password) {
			errors.confirm_password = 'كلمتا المرور غير متطابقتين';
			return false;
		}

		errors.confirm_password = '';
		return true;
	}

	function validateName(field) {
		const value = formData[field];
		if (!value) {
			errors[field] = rules.required(value);
			return false;
		}

		errors[field] = rules.minLength(2)(value) !== true ? rules.minLength(2)(value) : '';
		return !errors[field];
	}

	function validatePhone() {
		const { phone_number } = formData;
		if (!phone_number) {
			errors.phone_number = rules.required(phone_number);
			return false;
		}

		errors.phone_number = rules.phone(phone_number) !== true ? rules.phone(phone_number) : '';
		return !errors.phone_number;
	}

	function validateRole() {
		const { role } = formData;
		if (!role) {
			errors.role = rules.required(role);
			return false;
		}

		errors.role = '';
		return true;
	}

	function validateStep(step) {
		let isValid = true;

		if (step === 1) {
			isValid = validateEmail() && validatePassword() && validateConfirmPassword();
		} else if (step === 2) {
			isValid =
				validateName('first_name') &&
				validateName('last_name') &&
				validatePhone() &&
				validateRole();
		}

		return isValid;
	}

	function goToNextStep() {
		if (validateStep(currentStep)) {
			currentStep++;
		}
	}

	function goToPreviousStep() {
		currentStep--;
	}

	// Handle form submission
	async function handleSubmit() {
		if (!validateStep(currentStep)) return;

		loading = true;
		generalError = null;

		try {
			await auth.register(formData);
			uiStore.addToast(
				'تم التسجيل بنجاح! سيتم تحويلك إلى صفحة التحقق من البريد الإلكتروني.',
				TOAST_TYPES.SUCCESS
			);

			// Pass email for verification
			goto(`${redirectTo}?email=${encodeURIComponent(formData.email)}`);
		} catch (err) {
			console.error('Registration error:', err);
			generalError = err.message || 'حدث خطأ أثناء التسجيل. الرجاء المحاولة مرة أخرى.';

			// Scroll to top to show error
			window.scrollTo({ top: 0, behavior: 'smooth' });
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		// Focus the first input on mount
		const firstInput = document.querySelector('input');
		if (firstInput) firstInput.focus();
	});
</script>

<div class="flex w-full items-center justify-center p-4">
	<form
		on:submit|preventDefault={currentStep === totalSteps ? handleSubmit : goToNextStep}
		class="shadow-card w-full max-w-xl rounded-lg p-6 sm:p-8"
	>
		<h1
			class="font-heading text-primary-600 mb-6 text-center text-2xl font-bold sm:text-3xl dark:text-white"
		>
			إنشاء حساب جديد
		</h1>

		{#if generalError}
			<Alert
				type="error"
				message={generalError}
				dismissible={true}
				on:dismiss={() => (generalError = null)}
			/>
		{/if}

		<div class="mb-8">
			<div class="relative mb-4 h-1 rounded-full bg-gray-100">
				<div
					class="bg-primary-500 absolute inset-y-0 right-0 rounded-full transition-all duration-300"
					style={`width: ${(currentStep / totalSteps) * 100}%`}
				></div>
			</div>
			<div class="flex justify-between">
				<div
					class={`flex flex-col items-center ${currentStep >= 1 ? 'text-primary-600' : 'text-gray-400'}`}
				>
					<div
						class={`flex h-6 w-6 items-center justify-center rounded-full ${currentStep >= 1 ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-500'} mb-1 text-sm font-medium`}
					>
						1
					</div>
					<span class="text-xs font-medium sm:text-sm">بيانات الدخول</span>
				</div>
				<div
					class={`flex flex-col items-center ${currentStep >= 2 ? 'text-primary-600' : 'text-gray-400'}`}
				>
					<div
						class={`flex h-6 w-6 items-center justify-center rounded-full ${currentStep >= 2 ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-500'} mb-1 text-sm font-medium`}
					>
						2
					</div>
					<span class="text-xs font-medium sm:text-sm">البيانات الشخصية</span>
				</div>
			</div>
		</div>

		{#if currentStep === 1}
			<div class="space-y-4">
				<div class="mb-4">
					<Input
						type="email"
						label="البريد الإلكتروني"
						placeholder="أدخل بريدك الإلكتروني"
						value={formData.email}
						error={errors.email}
						on:input={(e) => {
							formData.email = e.target.value;
							if (errors.email) validateEmail();
						}}
						on:blur={validateEmail}
						required
						dir="ltr"
					/>
				</div>

				<div class="mb-2">
					<Input
						type="password"
						label="كلمة المرور"
						placeholder="أدخل كلمة المرور"
						value={formData.password}
						error={errors.password}
						on:input={(e) => {
							formData.password = e.target.value;
							if (errors.password) validatePassword();
							if (formData.confirm_password && errors.confirm_password) validateConfirmPassword();
						}}
						on:blur={validatePassword}
						required
					/>
					<p class="mt-1 text-xs text-gray-500">
						كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل وتتضمن حرف كبير وحرف صغير ورقم ورمز خاص
					</p>
				</div>

				<div class="mb-6">
					<Input
						type="password"
						label="تأكيد كلمة المرور"
						placeholder="أدخل كلمة المرور مرة أخرى"
						value={formData.confirm_password}
						error={errors.confirm_password}
						on:input={(e) => {
							formData.confirm_password = e.target.value;
							if (errors.confirm_password) validateConfirmPassword();
						}}
						on:blur={validateConfirmPassword}
						required
					/>
				</div>
			</div>

			<Button type="submit" variant="primary" fullWidth={true} disabled={loading}>التالي</Button>
		{:else if currentStep === 2}
			<div class="space-y-4">
				<div class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
					<div>
						<Input
							type="text"
							label="الاسم الأول"
							placeholder="أدخل اسمك الأول"
							value={formData.first_name}
							error={errors.first_name}
							on:input={(e) => {
								formData.first_name = e.target.value;
								if (errors.first_name) validateName('first_name');
							}}
							on:blur={() => validateName('first_name')}
							required
						/>
					</div>

					<div>
						<Input
							type="text"
							label="اسم العائلة"
							placeholder="أدخل اسم العائلة"
							value={formData.last_name}
							error={errors.last_name}
							on:input={(e) => {
								formData.last_name = e.target.value;
								if (errors.last_name) validateName('last_name');
							}}
							on:blur={() => validateName('last_name')}
							required
						/>
					</div>
				</div>

				<div class="mb-4">
					<Input
						type="tel"
						label="رقم الهاتف"
						placeholder="أدخل رقم الهاتف"
						value={formData.phone_number}
						error={errors.phone_number}
						on:input={(e) => {
							formData.phone_number = e.target.value;
							if (errors.phone_number) validatePhone();
						}}
						on:blur={validatePhone}
						required
						dir="ltr"
					/>
				</div>

				<div class="mb-6">
					<Select
						label="الدور"
						placeholder="اختر دورك في المنصة"
						options={roleOptions}
						value={formData.role}
						error={errors.role}
						on:change={(e) => {
							formData.role = e.detail.value;
							if (errors.role) validateRole();
						}}
						on:blur={validateRole}
						required
					/>
				</div>
			</div>

			<div class="flex flex-col justify-between gap-4 sm:flex-row">
				<Button
					type="button"
					variant="outline"
					on:click={goToPreviousStep}
					disabled={loading}
					class="order-2 w-full sm:order-1 sm:w-auto"
				>
					السابق
				</Button>

				<Button
					type="submit"
					variant="primary"
					disabled={loading}
					{loading}
					class="order-1 w-full sm:order-2 sm:w-auto"
				>
					إنشاء الحساب
				</Button>
			</div>
		{/if}

		<div class="mt-6 text-center text-sm">
			<span class="text-gray-600">لديك حساب بالفعل؟</span>
			<a
				href="/login"
				class="text-primary-600 hover:text-primary-700 mr-2 font-semibold transition-colors hover:underline dark:text-white"
			>
				تسجيل الدخول
			</a>
		</div>
	</form>
</div>
