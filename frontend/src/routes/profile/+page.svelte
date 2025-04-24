<!-- src/routes/profile/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { user, updateUserProfile, updateAvatar, changePassword } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';

	let profileData = {
		first_name: '',
		last_name: '',
		phone_number: '',
		date_of_birth: '',
		bio: '',
		company_name: '',
		address: '',
		city: '',
		state: '',
		postal_code: '',
		country: ''
	};

	let avatar = null;
	let avatarPreview = null;
	let loadingProfile = false;
	let loadingAvatar = false;
	let profileError = '';
	let activeTab = 'personal';

	// Password change fields
	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';
	let loadingPassword = false;
	let passwordError = '';

	onMount(() => {
		// Initialize form with user data
		if ($user) {
			profileData = {
				first_name: $user.first_name || '',
				last_name: $user.last_name || '',
				phone_number: $user.phone_number || '',
				date_of_birth: $user.date_of_birth
					? new Date($user.date_of_birth).toISOString().split('T')[0]
					: '',
				bio: $user.bio || '',
				company_name: $user.company_name || '',
				address: $user.address || '',
				city: $user.city || '',
				state: $user.state || '',
				postal_code: $user.postal_code || '',
				country: $user.country || ''
			};

			avatarPreview = $user.avatar_url;
		}
	});

	async function handleProfileUpdate() {
		loadingProfile = true;
		profileError = '';

		const result = await updateUserProfile(profileData);

		loadingProfile = false;

		if (result.success) {
			addToast('تم تحديث الملف الشخصي بنجاح', 'success');
		} else {
			profileError = result.error || 'فشل في تحديث الملف الشخصي';
		}
	}

	async function handleAvatarChange(event) {
		const file = event.target.files[0];
		if (!file) return;

		// File type validation
		const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
		if (!validTypes.includes(file.type)) {
			addToast('نوع الملف غير مدعوم. يرجى اختيار صورة JPEG أو PNG أو GIF', 'error');
			return;
		}

		// File size validation (max 2MB)
		if (file.size > 2 * 1024 * 1024) {
			addToast('حجم الملف كبير جدًا. الحد الأقصى هو 2 ميجابايت', 'error');
			return;
		}

		// Create preview
		const reader = new FileReader();
		reader.onload = (e) => {
			avatarPreview = e.target.result;
		};
		reader.readAsDataURL(file);

		// Update avatar
		avatar = file;
		await handleAvatarUpload();
	}

	async function handleAvatarUpload() {
		if (!avatar) return;

		loadingAvatar = true;

		const formData = new FormData();
		formData.append('avatar', avatar);

		const result = await updateAvatar(formData);

		loadingAvatar = false;

		if (result.success) {
			addToast('تم تحديث الصورة الشخصية بنجاح', 'success');
		} else {
			addToast(result.error || 'فشل في تحديث الصورة الشخصية', 'error');
		}
	}

	async function handlePasswordChange() {
		if (newPassword !== confirmPassword) {
			passwordError = 'كلمتا المرور غير متطابقتين';
			return;
		}

		loadingPassword = true;
		passwordError = '';

		const result = await changePassword(currentPassword, newPassword, confirmPassword);

		loadingPassword = false;

		if (result.success) {
			addToast('تم تغيير كلمة المرور بنجاح', 'success');
			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
		} else {
			passwordError = result.error || 'فشل في تغيير كلمة المرور';
		}
	}
</script>

<svelte:head>
	<title>الملف الشخصي | منصة المزادات العقارية</title>
</svelte:head>

<div>
	<h1 class="mb-6 text-2xl font-bold text-slate-900">الملف الشخصي</h1>

	<div class="overflow-hidden rounded-lg bg-white shadow">
		<!-- Profile header -->
		<div class="bg-gradient-to-r from-blue-700 to-blue-500 p-6 text-white">
			<div class="flex flex-col items-center gap-6 md:flex-row">
				<div class="relative">
					<div
						class="h-24 w-24 overflow-hidden rounded-full border-4 border-white bg-white shadow-md"
					>
						<img
							src={avatarPreview || '/images/default-avatar.jpg'}
							alt="الصورة الشخصية"
							class="h-full w-full object-cover"
						/>

						<!-- Loading overlay -->
						{#if loadingAvatar}
							<div
								class="bg-opacity-50 absolute inset-0 flex items-center justify-center rounded-full bg-black"
							>
								<i class="fas fa-spinner fa-spin text-xl text-white"></i>
							</div>
						{/if}
					</div>

					<label
						class="absolute -bottom-2 -left-2 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-blue-800 shadow"
					>
						<i class="fas fa-camera text-white"></i>
						<input type="file" accept="image/*" class="sr-only" on:change={handleAvatarChange} />
					</label>
				</div>

				<div>
					<h2 class="text-xl font-bold">{$user?.first_name || ''} {$user?.last_name || ''}</h2>
					<p class="text-blue-100">{$user?.email}</p>
					<p class="mt-1 text-blue-100">
						<i class="fas fa-calendar ml-1"></i>
						تاريخ الانضمام: {new Date($user?.date_joined).toLocaleDateString('ar-SA')}
					</p>
				</div>
			</div>
		</div>

		<!-- Tab navigation -->
		<div class="border-b">
			<nav class="-mb-px flex">
				<button
					class="mr-8 border-b-2 px-1 py-4 text-sm font-medium {activeTab === 'personal'
						? 'border-blue-500 text-blue-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => (activeTab = 'personal')}
				>
					<i class="fas fa-user ml-2"></i>
					البيانات الشخصية
				</button>

				<button
					class="mr-8 border-b-2 px-1 py-4 text-sm font-medium {activeTab === 'contact'
						? 'border-blue-500 text-blue-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => (activeTab = 'contact')}
				>
					<i class="fas fa-map-marker-alt ml-2"></i>
					بيانات الاتصال
				</button>

				<button
					class="mr-8 border-b-2 px-1 py-4 text-sm font-medium {activeTab === 'company'
						? 'border-blue-500 text-blue-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => (activeTab = 'company')}
				>
					<i class="fas fa-building ml-2"></i>
					بيانات الشركة
				</button>

				<button
					class="mr-8 border-b-2 px-1 py-4 text-sm font-medium {activeTab === 'security'
						? 'border-blue-500 text-blue-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => (activeTab = 'security')}
				>
					<i class="fas fa-lock ml-2"></i>
					الأمان
				</button>
			</nav>
		</div>

		<div class="p-6">
			{#if profileError}
				<div class="mb-6 rounded border-l-4 border-red-400 bg-red-50 p-4">
					<div class="flex">
						<div class="flex-shrink-0">
							<i class="fas fa-exclamation-circle text-red-400"></i>
						</div>
						<div class="mr-3">
							<p class="text-sm text-red-700">{profileError}</p>
						</div>
					</div>
				</div>
			{/if}

			{#if activeTab === 'personal'}
				<form on:submit|preventDefault={handleProfileUpdate} class="space-y-4">
					<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
						<div>
							<label for="first_name" class="mb-1 block text-sm font-medium text-slate-700"
								>الاسم الأول</label
							>
							<input
								type="text"
								id="first_name"
								bind:value={profileData.first_name}
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
								bind:value={profileData.last_name}
								class="input"
								placeholder="الاسم الأخير"
							/>
						</div>
					</div>

					<div>
						<label for="date_of_birth" class="mb-1 block text-sm font-medium text-slate-700"
							>تاريخ الميلاد</label
						>
						<input
							type="date"
							id="date_of_birth"
							bind:value={profileData.date_of_birth}
							class="input"
							dir="ltr"
						/>
					</div>

					<div>
						<label for="bio" class="mb-1 block text-sm font-medium text-slate-700">نبذة شخصية</label
						>
						<textarea
							id="bio"
							bind:value={profileData.bio}
							rows="4"
							class="input"
							placeholder="اكتب نبذة مختصرة عنك..."
						></textarea>
					</div>

					<div class="flex justify-end">
						<button type="submit" class="btn-primary" disabled={loadingProfile}>
							{#if loadingProfile}
								<i class="fas fa-spinner fa-spin ml-2"></i>
								جاري الحفظ...
							{:else}
								حفظ التغييرات
							{/if}
						</button>
					</div>
				</form>
			{:else if activeTab === 'contact'}
				<form on:submit|preventDefault={handleProfileUpdate} class="space-y-4">
					<div>
						<label for="phone_number" class="mb-1 block text-sm font-medium text-slate-700"
							>رقم الهاتف</label
						>
						<input
							type="tel"
							id="phone_number"
							bind:value={profileData.phone_number}
							class="input"
							placeholder="+966XXXXXXXXX"
							dir="ltr"
						/>
					</div>

					<div>
						<label for="address" class="mb-1 block text-sm font-medium text-slate-700"
							>العنوان</label
						>
						<textarea
							id="address"
							bind:value={profileData.address}
							rows="2"
							class="input"
							placeholder="أدخل عنوانك التفصيلي..."
						></textarea>
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label for="city" class="mb-1 block text-sm font-medium text-slate-700">المدينة</label
							>
							<input
								type="text"
								id="city"
								bind:value={profileData.city}
								class="input"
								placeholder="المدينة"
							/>
						</div>

						<div>
							<label for="state" class="mb-1 block text-sm font-medium text-slate-700"
								>المنطقة/المحافظة</label
							>
							<input
								type="text"
								id="state"
								bind:value={profileData.state}
								class="input"
								placeholder="المنطقة/المحافظة"
							/>
						</div>
					</div>

					<div class="grid grid-cols-2 gap-4">
						<div>
							<label for="postal_code" class="mb-1 block text-sm font-medium text-slate-700"
								>الرمز البريدي</label
							>
							<input
								type="text"
								id="postal_code"
								bind:value={profileData.postal_code}
								class="input"
								placeholder="الرمز البريدي"
							/>
						</div>

						<div>
							<label for="country" class="mb-1 block text-sm font-medium text-slate-700"
								>الدولة</label
							>
							<input
								type="text"
								id="country"
								bind:value={profileData.country}
								class="input"
								placeholder="الدولة"
							/>
						</div>
					</div>

					<div class="flex justify-end">
						<button type="submit" class="btn-primary" disabled={loadingProfile}>
							{#if loadingProfile}
								<i class="fas fa-spinner fa-spin ml-2"></i>
								جاري الحفظ...
							{:else}
								حفظ التغييرات
							{/if}
						</button>
					</div>
				</form>
			{:else if activeTab === 'company'}
				<form on:submit|preventDefault={handleProfileUpdate} class="space-y-4">
					<div>
						<label for="company_name" class="mb-1 block text-sm font-medium text-slate-700"
							>اسم الشركة</label
						>
						<input
							type="text"
							id="company_name"
							bind:value={profileData.company_name}
							class="input"
							placeholder="اسم الشركة أو المؤسسة"
						/>
					</div>

					<!-- Additional company fields can be added here -->

					<div class="flex justify-end">
						<button type="submit" class="btn-primary" disabled={loadingProfile}>
							{#if loadingProfile}
								<i class="fas fa-spinner fa-spin ml-2"></i>
								جاري الحفظ...
							{:else}
								حفظ التغييرات
							{/if}
						</button>
					</div>
				</form>
			{:else if activeTab === 'security'}
				<form on:submit|preventDefault={handlePasswordChange} class="space-y-4">
					<h3 class="mb-4 text-lg font-medium text-slate-900">تغيير كلمة المرور</h3>

					{#if passwordError}
						<div class="mb-4 rounded border-l-4 border-red-400 bg-red-50 p-4">
							<div class="flex">
								<div class="flex-shrink-0">
									<i class="fas fa-exclamation-circle text-red-400"></i>
								</div>
								<div class="mr-3">
									<p class="text-sm text-red-700">{passwordError}</p>
								</div>
							</div>
						</div>
					{/if}

					<div>
						<label for="current_password" class="mb-1 block text-sm font-medium text-slate-700"
							>كلمة المرور الحالية</label
						>
						<input
							type="password"
							id="current_password"
							bind:value={currentPassword}
							required
							class="input"
							placeholder="أدخل كلمة المرور الحالية"
						/>
					</div>

					<div>
						<label for="new_password" class="mb-1 block text-sm font-medium text-slate-700"
							>كلمة المرور الجديدة</label
						>
						<input
							type="password"
							id="new_password"
							bind:value={newPassword}
							required
							minlength="8"
							class="input"
							placeholder="أدخل كلمة المرور الجديدة"
						/>
					</div>

					<div>
						<label for="confirm_password" class="mb-1 block text-sm font-medium text-slate-700"
							>تأكيد كلمة المرور الجديدة</label
						>
						<input
							type="password"
							id="confirm_password"
							bind:value={confirmPassword}
							required
							minlength="8"
							class="input"
							placeholder="أعد إدخال كلمة المرور الجديدة"
						/>
					</div>

					<div class="flex justify-end">
						<button type="submit" class="btn-primary" disabled={loadingPassword}>
							{#if loadingPassword}
								<i class="fas fa-spinner fa-spin ml-2"></i>
								جاري تغيير كلمة المرور...
							{:else}
								تغيير كلمة المرور
							{/if}
						</button>
					</div>
				</form>

				<hr class="my-8" />

				<div>
					<h3 class="mb-4 text-lg font-medium text-slate-900">الحسابات المرتبطة</h3>
					<p class="mb-4 text-slate-500">ربط حسابك بخدمات أخرى لتسهيل تسجيل الدخول</p>

					<div class="space-y-3">
						<div class="flex items-center justify-between rounded-lg border p-3">
							<div class="flex items-center">
								<i class="fab fa-google ml-3 text-xl text-red-500"></i>
								<span>Google</span>
							</div>
							<button class="btn-secondary text-sm">ربط الحساب</button>
						</div>

						<div class="flex items-center justify-between rounded-lg border p-3">
							<div class="flex items-center">
								<i class="fab fa-twitter ml-3 text-xl text-blue-400"></i>
								<span>Twitter</span>
							</div>
							<button class="btn-secondary text-sm">ربط الحساب</button>
						</div>

						<div class="flex items-center justify-between rounded-lg border p-3">
							<div class="flex items-center">
								<i class="fab fa-facebook ml-3 text-xl text-blue-600"></i>
								<span>Facebook</span>
							</div>
							<button class="btn-secondary text-sm">ربط الحساب</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
