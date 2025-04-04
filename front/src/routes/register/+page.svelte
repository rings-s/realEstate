<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores/auth';
	import { theme } from '$lib/stores/theme';

	// Import our refactored RegisterForm component
	import RegisterForm from '$lib/components/auth/RegisterForm.svelte';

	// Redirect if already authenticated
	onMount(() => {
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});
</script>

<svelte:head>
	<title>إنشاء حساب جديد | منصة المزادات العقارية</title>
	<meta
		name="description"
		content="إنشاء حساب جديد في منصة المزادات العقارية للمشاركة في المزادات والاستثمار في أفضل العقارات"
	/>
</svelte:head>

<div
	class="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8 dark:bg-gray-900 {$theme ===
	'dark'
		? 'dark'
		: ''}"
>
	<div class="w-full max-w-xl space-y-8">
		<!-- Logo/Brand -->
		<div class="flex flex-col items-center justify-center">
			<div
				class="bg-primary-100 dark:bg-primary-900 mb-2 flex h-12 w-12 items-center justify-center rounded-full"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="text-primary-600 dark:text-primary-300 h-7 w-7"
				>
					<path
						d="M11.47 3.84a.75.75 0 011.06 0l8.69 8.69a.75.75 0 101.06-1.06l-8.689-8.69a2.25 2.25 0 00-3.182 0l-8.69 8.69a.75.75 0 001.061 1.06l8.69-8.69z"
					/>
					<path
						d="M12 5.432l8.159 8.159c.03.03.06.058.091.086v6.198c0 1.035-.84 1.875-1.875 1.875H15a.75.75 0 01-.75-.75v-4.5a.75.75 0 00-.75-.75h-3a.75.75 0 00-.75.75V21a.75.75 0 01-.75.75H5.625a1.875 1.875 0 01-1.875-1.875v-6.198c.031-.028.062-.056.091-.086L12 5.432z"
					/>
				</svg>
			</div>

			<h1
				class="text-center text-2xl font-bold tracking-tight text-gray-900 md:text-3xl dark:text-white"
			>
				إنشاء حساب جديد
			</h1>

			<p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
				انضم إلينا للمشاركة في المزادات العقارية والوصول إلى فرص استثمارية مميزة
			</p>
		</div>

		<!-- Registration Form -->
		<div class="mt-6 overflow-hidden rounded-xl bg-white shadow-md dark:bg-gray-800">
			<div class="p-6 sm:p-8">
				<RegisterForm redirectTo="/email-verification" />
			</div>
		</div>

		<!-- Footer Links -->
		<div class="text-center text-sm">
			<p class="mt-3 text-sm text-gray-600 dark:text-gray-400">
				لديك حساب بالفعل؟
				<a
					href="/login"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					تسجيل الدخول
				</a>
			</p>
			<p class="mt-2 text-xs text-gray-500 dark:text-gray-500">
				بإنشاء حساب جديد، أنت توافق على
				<a
					href="/terms"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					شروط الاستخدام
				</a>
				و
				<a
					href="/privacy"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					سياسة الخصوصية
				</a>
			</p>
		</div>
	</div>
</div>
