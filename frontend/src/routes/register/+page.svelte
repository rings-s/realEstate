<!-- src/routes/register/+page.svelte -->
<script>
	import { register } from '$lib/services/auth';
	import { goto } from '$app/navigation';

	let formData = {
		email: '',
		password: '',
		confirm_password: '',
		first_name: '',
		last_name: '',
		phone_number: ''
	};

	let loading = false;
	let error = '';
	let step = 1;

	async function handleSubmit() {
		loading = true;
		error = '';

		if (formData.password !== formData.confirm_password) {
			error = 'كلمات المرور غير متطابقة';
			loading = false;
			return;
		}

		const result = await register(formData);

		loading = false;

		if (result.success) {
			step = 2;
		} else {
			error = result.error || 'حدث خطأ أثناء التسجيل. يرجى المحاولة مرة أخرى.';
		}
	}
</script>

<svelte:head>
	<title>تسجيل حساب جديد | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		{#if step === 1}
			<div class="mb-6 text-center">
				<h1 class="text-2xl font-bold text-slate-900">تسجيل حساب جديد</h1>
				<p class="mt-2 text-slate-600">قم بإنشاء حساب للمشاركة في المزادات العقارية</p>
			</div>

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

				<!-- Password Fields -->
				<div>
					<label for="password" class="mb-1 block text-sm font-medium text-slate-700"
						>كلمة المرور</label
					>
					<input
						type="password"
						id="password"
						bind:value={formData.password}
						required
						class="input"
						placeholder="أدخل كلمة المرور"
						minlength="8"
					/>
				</div>

				<div>
					<label for="confirm_password" class="mb-1 block text-sm font-medium text-slate-700"
						>تأكيد كلمة المرور</label
					>
					<input
						type="password"
						id="confirm_password"
						bind:value={formData.confirm_password}
						required
						class="input"
						placeholder="أعد إدخال كلمة المرور"
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
		{:else if step === 2}
			<div class="text-center">
				<div
					class="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100"
				>
					<i class="fas fa-check text-2xl text-green-600"></i>
				</div>
				<h2 class="text-2xl font-bold text-slate-900">تم التسجيل بنجاح</h2>
				<p class="mt-2 text-slate-600">
					لقد أرسلنا رمز التحقق إلى بريدك الإلكتروني {formData.email}. يرجى التحقق من بريدك
					الإلكتروني وإدخال الرمز للمتابعة.
				</p>

				<div class="mt-6">
					<a href="/verify-email" class="btn-primary w-full">التحقق من البريد الإلكتروني</a>
					<button class="mt-4 text-sm text-blue-600 hover:underline" on:click={() => (step = 1)}>
						العودة إلى التسجيل
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
