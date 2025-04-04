<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores/auth';
	import { theme } from '$lib/stores/theme';

	// Import our refactored ResetPasswordForm component
	import ResetPasswordForm from '$lib/components/auth/ResetPasswordForm.svelte';

	// Redirect if already authenticated
	onMount(() => {
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});
</script>

<svelte:head>
	<title>استعادة كلمة المرور | منصة المزادات العقارية</title>
	<meta name="description" content="استعادة كلمة المرور لحسابك في منصة المزادات العقارية" />
</svelte:head>

<div
	class="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8 dark:bg-gray-900 {$theme ===
	'dark'
		? 'dark'
		: ''}"
>
	<div class="w-full max-w-md space-y-8">
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
						fill-rule="evenodd"
						d="M15.75 1.5a6.75 6.75 0 00-6.651 7.906c.067.39-.032.717-.221.906l-6.5 6.499a3 3 0 00-.878 2.121v2.818c0 .414.336.75.75.75H6a.75.75 0 00.75-.75v-1.5h1.5A.75.75 0 009 19.5V18h1.5a.75.75 0 00.53-.22l2.658-2.658c.19-.189.517-.288.906-.22A6.75 6.75 0 1015.75 1.5zm0 3a.75.75 0 000 1.5A2.25 2.25 0 0118 8.25a.75.75 0 001.5 0 3.75 3.75 0 00-3.75-3.75z"
						clip-rule="evenodd"
					/>
				</svg>
			</div>

			<h1
				class="text-center text-2xl font-bold tracking-tight text-gray-900 md:text-3xl dark:text-white"
			>
				استعادة كلمة المرور
			</h1>

			<p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
				لا تقلق! سنساعدك في استعادة الوصول إلى حسابك
			</p>
		</div>

		<!-- Reset Password Form -->
		<div class="mt-6 overflow-hidden rounded-xl bg-white shadow-md dark:bg-gray-800">
			<div class="p-6 sm:p-8">
				<ResetPasswordForm redirectTo="/login" />
			</div>
		</div>

		<!-- Footer Links -->
		<div class="text-center text-sm">
			<p class="mt-3 text-sm text-gray-600 dark:text-gray-400">
				تذكرت كلمة المرور؟
				<a
					href="/login"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					العودة إلى تسجيل الدخول
				</a>
			</p>
			<p class="mt-2 text-xs text-gray-500 dark:text-gray-500">
				إذا استمرت المشكلة، يرجى
				<a
					href="/contact"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					التواصل مع الدعم الفني
				</a>
			</p>
		</div>
	</div>
</div>
