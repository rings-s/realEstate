<!-- Fixed Footer with proper href attributes for accessibility -->
<script>
	import { theme, language, isRTL, textClass, toggleTheme, toggleLanguage } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';

	// Props
	export let minimal = false; // Whether to show minimal footer in dashboard

	// Current year for copyright
	const currentYear = new Date().getFullYear();
</script>

<footer
	class="{minimal
		? 'py-2 mt-auto'
		: 'py-6'} border-t border-surface-300-600-token bg-surface-100-800-token"
>
	<div class="container mx-auto px-4">
		{#if !minimal}
			<!-- Full Footer with navigation -->
			<div class="grid grid-cols-1 md:grid-cols-4 gap-y-6 gap-x-8 mb-6 text-sm">
				<!-- Column 1: About -->
				<div class={$textClass}>
					<h3 class="font-bold mb-3">
						{t('app_name', $language, { default: 'منصة مزادات العقارات' })}
					</h3>
					<p class="text-surface-600-300-token mb-4 text-sm">
						{t('footer_about', $language, {
							default: 'منصة متخصصة في مزادات العقارات تجمع البائعين والمشترين في مكان واحد.'
						})}
					</p>

					<!-- Theme & Language Toggles -->
					<div class="flex items-center gap-3 mt-4">
						<button
							class="btn btn-sm variant-ghost-surface h-8"
							on:click={toggleTheme}
							aria-label={$theme === 'dark'
								? t('light_mode', $language)
								: t('dark_mode', $language)}
						>
							{$theme === 'dark'
								? t('light_mode', $language, { default: 'الوضع النهاري' })
								: t('dark_mode', $language, { default: 'الوضع الليلي' })}
						</button>

						<button
							class="btn btn-sm variant-ghost-surface h-8"
							on:click={toggleLanguage}
							aria-label={$language === 'ar' ? 'English' : 'العربية'}
						>
							{$language === 'ar' ? 'English' : 'العربية'}
						</button>
					</div>
				</div>

				<!-- Column 2: Quick Links -->
				<div class={$textClass}>
					<h3 class="font-bold mb-3">
						{t('quick_links', $language, { default: 'روابط سريعة' })}
					</h3>
					<ul class="space-y-2">
						<li><a href="/" class="hover:underline text-sm">{t('home', $language)}</a></li>
						<li>
							<a href="/properties" class="hover:underline text-sm">{t('properties', $language)}</a>
						</li>
						<li>
							<a href="/auctions" class="hover:underline text-sm">{t('auctions', $language)}</a>
						</li>
						<li>
							<a href="/dashboard" class="hover:underline text-sm">{t('dashboard', $language)}</a>
						</li>
					</ul>
				</div>

				<!-- Column 3: User Links -->
				<div class={$textClass}>
					<h3 class="font-bold mb-3">
						{t('user_account', $language, { default: 'حساب المستخدم' })}
					</h3>
					<ul class="space-y-2">
						<li>
							<a href="/auth/login" class="hover:underline text-sm">{t('login', $language)}</a>
						</li>
						<li>
							<a href="/auth/register" class="hover:underline text-sm">{t('register', $language)}</a
							>
						</li>
						<li>
							<a href="/auth/reset-password" class="hover:underline text-sm"
								>{t('reset_password', $language)}</a
							>
						</li>
						<li>
							<a href="/dashboard/profile" class="hover:underline text-sm"
								>{t('profile', $language)}</a
							>
						</li>
					</ul>
				</div>

				<!-- Column 4: Support -->
				<div class={$textClass}>
					<h3 class="font-bold mb-3">{t('support', $language, { default: 'الدعم' })}</h3>
					<ul class="space-y-2">
						<li>
							<a href="/about" class="hover:underline text-sm"
								>{t('about_us', $language, { default: 'من نحن' })}</a
							>
						</li>
						<li>
							<a href="/contact" class="hover:underline text-sm"
								>{t('contact_us', $language, { default: 'اتصل بنا' })}</a
							>
						</li>
						<li>
							<a href="/faq" class="hover:underline text-sm"
								>{t('faq', $language, { default: 'الأسئلة الشائعة' })}</a
							>
						</li>
						<li>
							<a href="/terms" class="hover:underline text-sm"
								>{t('terms', $language, { default: 'الشروط والأحكام' })}</a
							>
						</li>
					</ul>
				</div>
			</div>
		{/if}

		<!-- Copyright - Always shown -->
		<div class="border-t border-surface-300-600-token pt-3 {minimal ? '' : 'mt-4'}">
			<div class="flex flex-col md:flex-row justify-between items-center gap-2">
				<p
					class="text-center md:text-{$isRTL ? 'right' : 'left'} text-surface-600-300-token text-xs"
				>
					&copy; {currentYear}
					{t('app_name', $language, { default: 'منصة مزادات العقارات' })}.
					{t('all_rights_reserved', $language, { default: 'جميع الحقوق محفوظة' })}.
				</p>

				{#if minimal}
					<!-- Minimal footer has language & theme toggle in the right side -->
					<div class="flex items-center gap-1">
						<button
							class="btn btn-sm btn-icon variant-ghost-surface h-8 w-8 aspect-square"
							on:click={toggleTheme}
							aria-label={$theme === 'dark'
								? t('light_mode', $language)
								: t('dark_mode', $language)}
						>
							{#if $theme === 'dark'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="16"
									height="16"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"
									></line><line x1="12" y1="21" x2="12" y2="23"></line><line
										x1="4.22"
										y1="4.22"
										x2="5.64"
										y2="5.64"
									></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line
										x1="1"
										y1="12"
										x2="3"
										y2="12"
									></line><line x1="21" y1="12" x2="23" y2="12"></line><line
										x1="4.22"
										y1="19.78"
										x2="5.64"
										y2="18.36"
									></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg
								>
							{:else}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="16"
									height="16"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg
								>
							{/if}
						</button>

						<button
							class="btn btn-sm btn-icon variant-ghost-surface h-8 w-8 aspect-square"
							on:click={toggleLanguage}
							aria-label={$language === 'ar' ? 'English' : 'العربية'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"
								></line><path
									d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
								></path></svg
							>
						</button>
					</div>
				{:else}
					<!-- Social media links for full footer - Fixed with proper URLs -->
					<div class="flex items-center gap-2">
						<a
							href="https://facebook.com/realestate-platform"
							class="btn btn-sm btn-icon variant-ghost-surface h-8 w-8 aspect-square"
							aria-label="Facebook"
							target="_blank"
							rel="noopener noreferrer"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"
								></path></svg
							>
						</a>
						<a
							href="https://twitter.com/realestate-platform"
							class="btn btn-sm btn-icon variant-ghost-surface h-8 w-8 aspect-square"
							aria-label="Twitter"
							target="_blank"
							rel="noopener noreferrer"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								><path
									d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"
								></path></svg
							>
						</a>
						<a
							href="https://instagram.com/realestate-platform"
							class="btn btn-sm btn-icon variant-ghost-surface h-8 w-8 aspect-square"
							aria-label="Instagram"
							target="_blank"
							rel="noopener noreferrer"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path
									d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"
								></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg
							>
						</a>
					</div>
				{/if}
			</div>
		</div>
	</div>
</footer>
