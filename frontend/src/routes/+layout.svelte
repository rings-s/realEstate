<!-- src/routes/+layout.svelte -->
<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { user, token, isVerified, isAuthenticated, logout } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
	import Toast from '$lib/components/Toast.svelte';
	import '../app.css';

	// State variables
	let sidebarExpanded = true;
	let sidebarMobileOpen = false;
	let profileMenuOpen = false;
	let loading = true;

	// Navigation items with more structured data
	const navItems = [
		{
			title: 'الرئيسية',
			href: '/',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                   </svg>`,
			badge: null
		},
		{
			title: 'العقارات',
			href: '/properties',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                   </svg>`,
			badge: null
		},
		{
			title: 'المزادات',
			href: '/auctions',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
                   </svg>`,
			badge: '12'
		},
		{
			title: 'الرسائل',
			href: '/messages',
			icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                   </svg>`,
			badge: '3'
		}
	];

	// Initialize component
	onMount(() => {
		loading = false;
		// Check screen size and set initial sidebar state
		handleResize();
		// Add resize listener
		window.addEventListener('resize', handleResize);
		return () => window.removeEventListener('resize', handleResize);
	});

	function handleResize() {
		sidebarExpanded = window.innerWidth >= 1024;
	}

	function toggleSidebar() {
		if (window.innerWidth >= 1024) {
			sidebarExpanded = !sidebarExpanded;
		} else {
			sidebarMobileOpen = !sidebarMobileOpen;
		}
	}

	// Handle logout
	async function handleLogout() {
		try {
			await logout();
			addToast('تم تسجيل الخروج بنجاح', 'success');
		} catch (error) {
			console.error('Logout error:', error);
			addToast('حدث خطأ أثناء تسجيل الخروج', 'error');
		}
	}

	// Close sidebar when route changes on mobile
	$: if ($page.url.pathname) {
		sidebarMobileOpen = false;
	}
</script>

<div class="flex min-h-screen bg-slate-50" dir="rtl">
	<!-- Sidebar -->
	<aside
		class="fixed inset-y-0 right-0 z-50 flex w-64 flex-col transition-all duration-300 ease-in-out lg:static lg:translate-x-0
               {sidebarExpanded ? 'translate-x-0' : 'translate-x-64'}
               {sidebarMobileOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}"
	>
		<!-- Sidebar Header -->
		<div class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4">
			<div class="flex items-center space-x-3 space-x-reverse">
				<img src="/logo.svg" alt="Logo" class="h-8 w-8" />
				<span class="text-lg font-bold text-slate-900 {!sidebarExpanded ? 'lg:hidden' : ''}">
					منصة المزادات
				</span>
			</div>
			<button
				class="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
				on:click={toggleSidebar}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="h-6 w-6 transition-transform duration-300 {sidebarExpanded ? 'rotate-180' : ''}"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
				</svg>
			</button>
		</div>

		<!-- Sidebar Content -->
		<div class="flex-1 overflow-y-auto bg-white pb-4">
			<nav class="mt-4 space-y-1 px-2">
				{#each navItems as item}
					<a
						href={item.href}
						class="group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200
                               {$page.url.pathname === item.href
							? 'bg-blue-50 text-blue-600'
							: 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'}"
						aria-current={$page.url.pathname === item.href ? 'page' : undefined}
					>
						<div class="mr-1 flex h-6 w-6 flex-shrink-0 items-center justify-center">
							{@html item.icon}
						</div>
						<span class="mr-3 {!sidebarExpanded ? 'lg:hidden' : ''}">
							{item.title}
						</span>
						{#if item.badge}
							<span
								class="mr-auto flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-blue-100 px-1.5 text-xs font-medium text-blue-600 {!sidebarExpanded
									? 'lg:hidden'
									: ''}"
							>
								{item.badge}
							</span>
						{/if}
					</a>
				{/each}
			</nav>

			<!-- User Section -->
			{#if $isAuthenticated && $user}
				<div class="mt-6 border-t border-slate-200 px-4 pt-4">
					<div class="flex items-center">
						<img
							src={$user?.avatar_url || '/images/default-avatar.jpg'}
							alt="Profile"
							class="h-10 w-10 rounded-full object-cover"
						/>
						<div class="mr-3 {!sidebarExpanded ? 'lg:hidden' : ''}">
							<p class="text-sm font-medium text-slate-900">
								{$user?.first_name || $user?.email}
							</p>
							<p class="text-xs text-slate-500">
								{$user?.email}
							</p>
						</div>
					</div>

					<div class="mt-4 space-y-1 {!sidebarExpanded ? 'lg:hidden' : ''}">
						<a
							href="/profile"
							class="flex items-center rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-slate-900"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-2 h-5 w-5"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
								/>
							</svg>
							الملف الشخصي
						</a>
						<button
							on:click={handleLogout}
							class="flex w-full items-center rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-2 h-5 w-5"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
								/>
							</svg>
							تسجيل الخروج
						</button>
					</div>
				</div>
			{:else if !loading}
				<div class="mt-6 px-4 {!sidebarExpanded ? 'lg:hidden' : ''}">
					<a
						href="/login"
						class="block rounded-lg bg-blue-600 px-4 py-2 text-center text-sm font-medium text-white hover:bg-blue-700"
					>
						تسجيل الدخول
					</a>
					<a
						href="/register"
						class="mt-2 block rounded-lg border border-slate-300 px-4 py-2 text-center text-sm font-medium text-slate-700 hover:bg-slate-50"
					>
						إنشاء حساب
					</a>
				</div>
			{/if}
		</div>
	</aside>

	<!-- Main Content -->
	<div class="flex flex-1 flex-col">
		<!-- Verification Banner -->
		{#if $isAuthenticated && $user && !$isVerified}
			<div class="bg-gradient-to-r from-amber-50 to-amber-100 px-4 py-3 shadow-sm">
				<div class="flex items-center justify-between">
					<div class="flex items-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="ml-2 h-5 w-5 text-amber-500"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
								clip-rule="evenodd"
							/>
						</svg>
						<p class="text-sm text-amber-800">
							لم يتم التحقق من بريدك الإلكتروني بعد. يرجى التحقق من بريدك للحصول على رمز التفعيل.
						</p>
					</div>
					<a
						href="/verify-email"
						class="text-sm font-medium text-amber-800 underline hover:text-amber-900"
					>
						إعادة إرسال رمز التفعيل
					</a>
				</div>
			</div>
		{/if}

		<!-- Mobile Header -->
		<header class="bg-white shadow-sm lg:hidden">
			<div class="flex h-16 items-center justify-between px-4">
				<button
					class="rounded-lg p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-900"
					on:click={toggleSidebar}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 12h16M4 18h16"
						/>
					</svg>
				</button>

				<div class="flex items-center space-x-4 space-x-reverse">
					<!-- Notifications -->
					<button
						class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
							/>
						</svg>
						<span
							class="absolute -top-1 -right-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-medium text-white"
						>
							3
						</span>
					</button>

					<!-- Messages -->
					<button
						class="relative rounded-full p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
							/>
						</svg>
						<span
							class="absolute -top-1 -right-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-blue-500 px-1.5 text-xs font-medium text-white"
						>
							2
						</span>
					</button>
				</div>
			</div>
		</header>

		<!-- Page Content -->
		<main class="flex-1">
			<slot />
		</main>

		<!-- Footer -->
		<footer class="border-t bg-white py-6">
			<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
				<div class="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0">
					<p class="text-sm text-slate-500">
						© {new Date().getFullYear()} منصة المزادات العقارية. جميع الحقوق محفوظة.
					</p>
					<div class="flex space-x-4 space-x-reverse">
						<a href="/privacy" class="text-sm text-slate-500 hover:text-slate-900">
							سياسة الخصوصية
						</a>
						<a href="/terms" class="text-sm text-slate-500 hover:text-slate-900">
							الشروط والأحكام
						</a>
						<a href="/contact" class="text-sm text-slate-500 hover:text-slate-900"> اتصل بنا </a>
					</div>
				</div>
			</div>
		</footer>
	</div>
</div>

<Toast />

<style>
	/* Smooth scrollbar for sidebar */
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: rgba(226, 232, 240, 1) white; /* Using direct color values instead of theme function */
	}

	.overflow-y-auto::-webkit-scrollbar {
		width: 6px;
	}

	.overflow-y-auto::-webkit-scrollbar-track {
		background: white;
	}

	.overflow-y-auto::-webkit-scrollbar-thumb {
		background-color: rgba(226, 232, 240, 1); /* slate-200 equivalent */
		border-radius: 3px;
	}

	/* Animation classes */
	.slide-in {
		animation: slideIn 0.3s ease-out forwards;
	}

	.slide-out {
		animation: slideOut 0.3s ease-out forwards;
	}

	@keyframes slideIn {
		from {
			transform: translateX(100%);
		}
		to {
			transform: translateX(0);
		}
	}

	@keyframes slideOut {
		from {
			transform: translateX(0);
		}
		to {
			transform: translateX(100%);
		}
	}
</style>
