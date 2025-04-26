<!-- src/routes/+layout.svelte -->
<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { user, token, isVerified, isAuthenticated, logout } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
	import Toast from '$lib/components/Toast.svelte';
	import '../app.css';

	// State variables
	let showSidebar = false;
	let loading = true;
	let profileMenuOpen = false;

	// Navigation items
	const navItems = [
		{ title: 'الرئيسية', href: '/', icon: 'home' },
		{ title: 'العقارات', href: '/properties', icon: 'building' },
		{ title: 'المزادات', href: '/auctions', icon: 'gavel' },
		{ title: 'الرسائل', href: '/messages', icon: 'message' },
		{ title: 'الإشعارات', href: '/notifications', icon: 'bell' },
		{ title: 'العقود', href: '/contracts', icon: 'file-contract' },
		{ title: 'المستندات', href: '/documents', icon: 'file' }
	];

	// Initialize component
	onMount(() => {
		// Set loading state
		loading = false;
	});

	// UI control functions
	function toggleSidebar() {
		showSidebar = !showSidebar;
	}

	function toggleProfileMenu() {
		profileMenuOpen = !profileMenuOpen;
	}

	function handleClickOutside(event) {
		if (profileMenuOpen && !event.target.closest('.profile-menu')) {
			profileMenuOpen = false;
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

	// Close sidebar when route changes
	$: if ($page.url.pathname) {
		showSidebar = false;
	}
</script>

<svelte:window on:click={handleClickOutside} />

<svelte:head>
	<title>منصة المزادات العقارية</title>
	<meta name="description" content="منصة المزادات العقارية الرائدة في المملكة العربية السعودية" />
	<link
		rel="stylesheet"
		href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
	/>
</svelte:head>

<div class="flex min-h-screen flex-col" dir="rtl">
	<!-- Header -->
	<header class="relative z-30 bg-white shadow-sm">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
			<div class="flex items-center">
				<button
					class="mr-2 rounded p-1 text-slate-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none lg:hidden"
					on:click={toggleSidebar}
					aria-label="Toggle menu"
				>
					<i class="fas fa-bars text-xl"></i>
				</button>
				<a href="/" class="text-2xl font-bold text-blue-600">منصة المزادات</a>
			</div>

			<div class="flex items-center space-x-4 space-x-reverse">
				{#if $isAuthenticated && $user}
					<div class="profile-menu relative">
						<button
							class="flex items-center space-x-1 space-x-reverse rounded-full focus:ring-2 focus:ring-blue-500 focus:outline-none"
							on:click={toggleProfileMenu}
							aria-expanded={profileMenuOpen}
							aria-haspopup="true"
						>
							<img
								src={$user?.avatar_url || '/images/default-avatar.jpg'}
								alt="صورة الملف الشخصي"
								class="h-10 w-10 rounded-full border-2 border-blue-100 object-cover"
							/>
							<span class="hidden font-medium text-slate-700 md:inline">
								{$user?.first_name || $user?.email || 'المستخدم'}
							</span>
							<i
								class="fas fa-chevron-down text-xs text-slate-500 transition-transform duration-200"
								class:rotate-180={profileMenuOpen}
							></i>
						</button>
						{#if profileMenuOpen}
							<div
								class="ring-opacity-5 absolute left-0 z-50 mt-2 w-48 rounded-md bg-white py-1 shadow-lg ring-1 ring-black transition-all duration-200 ease-out"
							>
								<a href="/profile" class="block px-4 py-2 text-slate-700 hover:bg-slate-100">
									<i class="fas fa-user-circle mr-2"></i>
									الملف الشخصي
								</a>
								<button
									on:click={handleLogout}
									class="w-full px-4 py-2 text-right text-red-600 hover:bg-slate-100"
								>
									<i class="fas fa-sign-out-alt mr-2"></i>
									تسجيل الخروج
								</button>
							</div>
						{/if}
					</div>
				{:else if !loading}
					<a href="/login" class="btn-secondary">تسجيل الدخول</a>
					<a href="/register" class="btn-primary">تسجيل حساب جديد</a>
				{/if}
			</div>
		</div>
	</header>

	<div class="flex flex-1">
		<!-- Sidebar Navigation -->
		<aside
			class="fixed inset-y-0 right-0 z-40 w-64 transform bg-white shadow-lg transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 lg:shadow-none {showSidebar
				? 'translate-x-0'
				: 'translate-x-full'}"
		>
			<div class="flex items-center justify-between border-b p-4 lg:hidden">
				<h2 class="text-lg font-bold">القائمة</h2>
				<button
					on:click={toggleSidebar}
					class="rounded p-1 text-slate-500 hover:text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
					aria-label="إغلاق القائمة"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<nav class="p-4">
				<ul class="space-y-1">
					{#each navItems as item}
						<li>
							<a
								href={item.href}
								class="flex items-center rounded-md px-4 py-3 transition-colors duration-200 {$page
									.url.pathname === item.href
									? 'bg-blue-50 text-blue-600'
									: 'text-slate-700 hover:bg-slate-50'}"
								aria-current={$page.url.pathname === item.href ? 'page' : undefined}
							>
								<i class="fas fa-{item.icon} w-5 text-center"></i>
								<span class="mr-3">{item.title}</span>
							</a>
						</li>
					{/each}
				</ul>

				{#if !$isAuthenticated && !loading}
					<div class="mt-8 rounded-lg bg-blue-50 p-4">
						<h3 class="font-medium text-blue-800">مرحباً بك في منصتنا</h3>
						<p class="mt-1 text-sm text-blue-600">
							سجل الدخول للمشاركة في المزادات واكتشاف العقارات الجديدة
						</p>
						<div class="mt-3 space-y-2">
							<a href="/login" class="btn-secondary w-full">تسجيل الدخول</a>
							<a href="/register" class="btn-primary w-full">تسجيل جديد</a>
						</div>
					</div>
				{/if}
			</nav>
		</aside>

		<!-- Overlay for mobile sidebar -->
		{#if showSidebar}
			<div
				class="bg-opacity-50 fixed inset-0 z-30 bg-black lg:hidden"
				on:click={toggleSidebar}
				aria-hidden="true"
			></div>
		{/if}

		<Toast />

		<!-- Main Content -->
		<main class="flex-1 p-4 sm:p-6 lg:p-8">
			{#if $isAuthenticated && $user && !$isVerified}
				<div class="mb-6 rounded border-l-4 border-amber-400 bg-amber-50 p-4">
					<div class="flex">
						<div class="flex-shrink-0">
							<i class="fas fa-exclamation-triangle text-amber-400"></i>
						</div>
						<div class="mr-3">
							<p class="text-sm text-amber-700">
								لم يتم التحقق من بريدك الإلكتروني بعد. يرجى التحقق من بريدك للحصول على رمز التفعيل.
								<a href="/verify-email" class="font-medium underline">إعادة إرسال رمز التفعيل</a>
							</p>
						</div>
					</div>
				</div>
			{/if}

			<slot />
		</main>
	</div>

	<footer class="border-t bg-white py-6">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<p class="text-center text-sm text-slate-500">
				&copy; {new Date().getFullYear()} منصة المزادات العقارية. جميع الحقوق محفوظة.
			</p>
		</div>
	</footer>
</div>

<style>
	/* Global Styles */
	:global(body) {
		font-family: 'Tajawal', sans-serif;
	}

	/* TailwindCSS v4 compatible utility classes */
	:global(.btn-primary) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border: 1px solid transparent;
		background-color: rgb(37, 99, 235); /* blue-600 */
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: white;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		border-radius: 0.375rem;
		transition-property: background-color, border-color, color, fill, stroke;
		transition-duration: 150ms;
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
	}

	:global(.btn-primary:hover) {
		background-color: rgb(29, 78, 216); /* blue-700 */
	}

	:global(.btn-secondary) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border: 1px solid rgb(226, 232, 240); /* slate-300 */
		background-color: white;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: rgb(51, 65, 85); /* slate-700 */
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		border-radius: 0.375rem;
		transition-property: background-color, border-color, color, fill, stroke;
		transition-duration: 150ms;
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
	}

	:global(.btn-secondary:hover) {
		background-color: rgb(248, 250, 252); /* slate-50 */
	}

	:global(.input) {
		display: block;
		width: 100%;
		border: 1px solid rgb(226, 232, 240); /* slate-300 */
		padding: 0.5rem 0.75rem;
		color: rgb(51, 65, 85); /* slate-700 */
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		border-radius: 0.375rem;
		transition-property: border-color, box-shadow;
		transition-duration: 150ms;
		transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
	}

	:global(.input:focus) {
		outline: none;
		border-color: rgb(59, 130, 246); /* blue-500 */
		box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3); /* blue-500 with opacity */
	}
</style>
