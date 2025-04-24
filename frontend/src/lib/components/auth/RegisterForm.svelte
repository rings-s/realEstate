<!-- src/lib/components/auth/RegisterForm.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { register } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	export let onSuccess = () => {};

	let formData = {
		email: '',
		password: '',
		confirm_password: '',
		first_name: '',
		last_name: '',
		phone_number: '',
		role: 'bidder' // Default role
	};

	let loading = false;
	let error = '';

	// Available roles
	const roles = [
		{ value: 'bidder', label: 'مزايد' },
		{ value: 'seller', label: 'بائع' },
		{ value: 'agent', label: 'وكيل عقاري' }
	];

	async function handleSubmit() {
		if (formData.password !== formData.confirm_password) {
			error = 'كلمات المرور غير متطابقة';
			return;
		}

		if (formData.password.length < 8) {
			error = 'كلمة المرور يجب أن تكون على الأقل 8 أحرف';
			return;
		}

		loading = true;
		error = '';

		try {
			const result = await register(formData);

			if (result.success) {
				addToast('تم التسجيل بنجاح', 'success');
				onSuccess(formData.email);
			} else {
				error = result.error || 'حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.';
			}
		} catch (err) {
			error = err.message || 'حدث خطأ غير متوقع';
		} finally {
			loading = false;
		}
	}
</script>

{#if error}
	<div class="mb-6 rounded border-l-4 border-red-400 bg-red-50 p-4">
		<div class="flex">
			<div class="flex-shrink-0">
				<i class="fas fa-exclamation-circle text-red-400"></i>
			</div>
			<div class="mr-3">
				<p class="text-sm text-red-700">{error}</p>
			</div>
		</div>
	</div>
{/if}

<form on:submit|preventDefault={handleSubmit} class="space-y-4">
	<!-- Email Field -->
	<div>
		<label for="email" class="mb-1 block text-sm font-medium text-slate-700"
			>البريد الإلكتروني</label
		>
		<input
			type="email"
			id="email"
			bind:value={formData.email}
			required
			class="input"
			placeholder="أدخل بريدك الإلكتروني"
			dir="ltr"
		/>
	</div>

	<!-- Name Fields -->
	<div class="grid grid-cols-2 gap-4">
		<div>
			<label for="first_name" class="mb-1 block text-sm font-medium text-slate-700"
				>الاسم الأول</label
			>
			<input
				type="text"
				id="first_name"
				bind:value={formData.first_name}
				required
				class="input"
				placeholder="الاسم الأول"
			/>
		</div>
		<div>
			<label for="last_name" class="mb-1 block text-sm font-medium text-slate-700"
				>الاسم الأخير</label
			>
			<input
				type="text"
				id="last_name"
				bind:value={formData.last_name}
				required
				class="input"
				placeholder="الاسم الأخير"
			/>
		</div>
	</div>

	<!-- Phone Number -->
	<div>
		<label for="phone_number" class="mb-1 block text-sm font-medium text-slate-700"
			>رقم الهاتف</label
		>
		<input
			type="tel"
			id="phone_number"
			bind:value={formData.phone_number}
			class="input"
			placeholder="+966XXXXXXXXX"
			dir="ltr"
		/>
	</div>

	<!-- User Role -->
	<div>
		<label for="role" class="mb-1 block text-sm font-medium text-slate-700">نوع الحساب</label>
		<select id="role" bind:value={formData.role} class="input">
			{#each roles as role}
				<option value={role.value}>{role.label}</option>
			{/each}
		</select>
	</div>

	<!-- Password Fields -->
	<div>
		<label for="password" class="mb-1 block text-sm font-medium text-slate-700">كلمة المرور</label>
		<input
			type="password"
			id="password"
			bind:value={formData.password}
			required
			class="input"
			placeholder="أدخل كلمة المرور"
			minlength="8"
		/>
		<p class="mt-1 text-xs text-slate-500">يجب أن تكون كلمة المرور 8 أحرف على الأقل</p>
	</div>

	<div>
		<label for="confirm_password" class="mb-1 block text-sm font-medium text-slate-700"
			>تأكيد كلمة المرور</label
		>
		<input
			type="password"
			id="password"
			bind:value={formData.password}
			required
			class="input"
			placeholder="أدخل كلمة المرور"
			minlength="8"
			autocomplete="new-password"
		/>
	</div>

	<div class="flex items-center">
		<input
			id="terms"
			type="checkbox"
			required
			class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
		/>
		<label for="terms" class="mr-2 block text-sm text-slate-700">
			أوافق على <a href="#" class="text-blue-600 hover:underline">الشروط والأحكام</a>
		</label>
	</div>

	<div>
		<button type="submit" class="btn-primary w-full" disabled={loading}>
			{#if loading}
				<i class="fas fa-spinner fa-spin ml-2"></i>
				جاري التسجيل...
			{:else}
				تسجيل حساب جديد
			{/if}
		</button>
	</div>
</form>

<div class="mt-6 text-center">
	<p class="text-sm text-slate-600">
		لديك حساب بالفعل؟
		<a href="/login" class="text-blue-600 hover:underline">تسجيل الدخول</a>
	</p>
</div>
