<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores/auth';
	import { theme } from '$lib/stores/theme';

	// Import our refactored VerifyEmailForm component
	import VerifyEmailForm from '$lib/components/auth/VerifyEmailForm.svelte';

	// Email from URL query
	let email = '';

	onMount(() => {
		// If already authenticated and verified, redirect to dashboard
		if ($isAuthenticated) {
			goto('/dashboard');
		}

		// Get email from URL parameters
		const params = new URLSearchParams(window.location.search);
		email = params.get('email') || '';
	});
</script>

<svelte:head>
	<title>تأكيد البريد الإلكتروني | منصة المزادات العقارية</title>
	<meta name="description" content="تأكيد البريد الإلكتروني لحسابك في منصة المزادات العقارية" />
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
						d="M1.5 8.67v8.58a3 3 0 003 3h15a3 3 0 003-3V8.67l-8.928 5.493a3 3 0 01-3.144 0L1.5 8.67z"
					/>
					<path
						d="M22.5 6.908V6.75a3 3 0 00-3-3h-15a3 3 0 00-3 3v.158l9.714 5.978a1.5 1.5 0 001.572 0L22.5 6.908z"
					/>
				</svg>
			</div>

			<h1
				class="text-center text-2xl font-bold tracking-tight text-gray-900 md:text-3xl dark:text-white"
			>
				تأكيد البريد الإلكتروني
			</h1>

			<p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
				أدخل رمز التحقق الذي تم إرساله إلى بريدك الإلكتروني
			</p>
		</div>

		<!-- Email Verification Form -->
		<div class="mt-6 overflow-hidden rounded-xl bg-white shadow-md dark:bg-gray-800">
			<div class="p-6 sm:p-8">
				<VerifyEmailForm redirectTo="/dashboard" />
			</div>
		</div>

		<!-- Why We Require Verification -->
		<div class="mt-6 rounded-lg bg-gray-50 p-4 dark:bg-gray-800/50">
			<h3 class="mb-2 text-sm font-medium text-gray-900 dark:text-white">
				لماذا نطلب تأكيد البريد الإلكتروني؟
			</h3>
			<ul class="space-y-1 text-right text-xs text-gray-600 dark:text-gray-400">
				<li class="flex items-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-2 h-4 w-4 text-green-500"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
					<span>حماية حسابك من الوصول غير المصرح به</span>
				</li>
				<li class="flex items-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-2 h-4 w-4 text-green-500"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
					<span>التأكد من أن بريدك الإلكتروني صحيح</span>
				</li>
				<li class="flex items-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-2 h-4 w-4 text-green-500"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
					<span>ضمان تلقي الإشعارات الهامة والتحديثات</span>
				</li>
			</ul>
		</div>

		<!-- Footer Links -->
		<div class="text-center text-sm">
			<p class="mt-3 text-sm text-gray-600 dark:text-gray-400">
				واجهت مشكلة؟
				<a
					href="/contact"
					class="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
				>
					تواصل مع الدعم الفني
				</a>
			</p>
		</div>
	</div>
</div>
