<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { Home, Building, Gavel, Info, Phone } from 'lucide-svelte';

	/**
	 * Props
	 */
	// Whether to show full footer or simple version
	export let minimal = false;
	// Year for copyright notice (defaults to current year)
	export let year = new Date().getFullYear();
	// Company name
	export let companyName = t('app_name', $language, { default: 'منصة مزادات العقارات' });
	// Additional classes
	export let classes = '';
</script>

{#if minimal}
	<!-- Simple footer with just copyright -->
	<footer class="border-t border-surface-300-600-token p-4 {classes}">
		<div class="container mx-auto px-4">
			<div class="flex flex-col sm:flex-row justify-between items-center">
				<p class="text-sm text-surface-500-400-token py-2 {$isRTL ? 'text-right' : 'text-left'}">
					&copy; {year}
					{companyName}. {t('all_rights_reserved', $language, { default: 'جميع الحقوق محفوظة.' })}
				</p>
			</div>
		</div>
	</footer>
{:else}
	<!-- Full footer with links and information -->
	<footer class="border-t border-surface-300-600-token pt-12 pb-8 {classes}">
		<div class="container mx-auto px-4">
			<!-- Main footer content -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
				<!-- Column 1: About -->
				<div class={$isRTL ? 'text-right' : 'text-left'}>
					<h3 class="h3 mb-4">{t('about_us', $language, { default: 'من نحن' })}</h3>
					<p class="text-surface-500-400-token mb-4">
						{t('footer_about_text', $language, {
							default:
								'منصة رائدة لمزادات العقارات، نوفر تجربة فريدة للبيع والشراء بكل ثقة وشفافية.'
						})}
					</p>
					<div class="flex {$isRTL ? 'justify-end' : 'justify-start'} gap-4 mt-4">
						<!-- Social media icons -->
						<a href="#" class="btn btn-sm btn-icon variant-ghost-surface" aria-label="Facebook">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
							</svg>
						</a>
						<a href="#" class="btn btn-sm btn-icon variant-ghost-surface" aria-label="Twitter">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path
									d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"
								/>
							</svg>
						</a>
						<a href="#" class="btn btn-sm btn-icon variant-ghost-surface" aria-label="Instagram">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
								<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
								<line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
							</svg>
						</a>
						<a href="#" class="btn btn-sm btn-icon variant-ghost-surface" aria-label="LinkedIn">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path
									d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"
								/>
								<rect x="2" y="9" width="4" height="12" />
								<circle cx="4" cy="4" r="2" />
							</svg>
						</a>
					</div>
				</div>

				<!-- Column 2: Quick Links -->
				<div class={$isRTL ? 'text-right' : 'text-left'}>
					<h3 class="h3 mb-4">{t('quick_links', $language, { default: 'روابط سريعة' })}</h3>
					<ul class="space-y-2">
						<li>
							<a
								href="/"
								class="flex items-center gap-2 text-surface-500-400-token hover:text-primary-500"
							>
								<Home class="w-4 h-4" />
								<span>{t('home', $language, { default: 'الرئيسية' })}</span>
							</a>
						</li>
						<li>
							<a
								href="/properties"
								class="flex items-center gap-2 text-surface-500-400-token hover:text-primary-500"
							>
								<Building class="w-4 h-4" />
								<span>{t('properties', $language, { default: 'العقارات' })}</span>
							</a>
						</li>
						<li>
							<a
								href="/auctions"
								class="flex items-center gap-2 text-surface-500-400-token hover:text-primary-500"
							>
								<Gavel class="w-4 h-4" />
								<span>{t('auctions', $language, { default: 'المزادات' })}</span>
							</a>
						</li>
						<li>
							<a
								href="/about"
								class="flex items-center gap-2 text-surface-500-400-token hover:text-primary-500"
							>
								<Info class="w-4 h-4" />
								<span>{t('about', $language, { default: 'من نحن' })}</span>
							</a>
						</li>
						<li>
							<a
								href="/contact"
								class="flex items-center gap-2 text-surface-500-400-token hover:text-primary-500"
							>
								<Phone class="w-4 h-4" />
								<span>{t('contact', $language, { default: 'اتصل بنا' })}</span>
							</a>
						</li>
					</ul>
				</div>

				<!-- Column 3: Legal -->
				<div class={$isRTL ? 'text-right' : 'text-left'}>
					<h3 class="h3 mb-4">{t('legal', $language, { default: 'القانونية' })}</h3>
					<ul class="space-y-2">
						<li>
							<a href="/terms" class="text-surface-500-400-token hover:text-primary-500">
								{t('terms_of_service', $language, { default: 'شروط الخدمة' })}
							</a>
						</li>
						<li>
							<a href="/privacy" class="text-surface-500-400-token hover:text-primary-500">
								{t('privacy_policy', $language, { default: 'سياسة الخصوصية' })}
							</a>
						</li>
						<li>
							<a href="/cookies" class="text-surface-500-400-token hover:text-primary-500">
								{t('cookie_policy', $language, { default: 'سياسة ملفات تعريف الارتباط' })}
							</a>
						</li>
						<li>
							<a href="/disclaimer" class="text-surface-500-400-token hover:text-primary-500">
								{t('disclaimer', $language, { default: 'إخلاء المسؤولية' })}
							</a>
						</li>
						<li>
							<a href="/licenses" class="text-surface-500-400-token hover:text-primary-500">
								{t('licenses', $language, { default: 'التراخيص' })}
							</a>
						</li>
					</ul>
				</div>

				<!-- Column 4: Contact -->
				<div class={$isRTL ? 'text-right' : 'text-left'}>
					<h3 class="h3 mb-4">{t('contact_us', $language, { default: 'اتصل بنا' })}</h3>
					<address class="not-italic">
						<p class="flex items-center gap-2 mb-2 text-surface-500-400-token">
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
							>
								<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
								<circle cx="12" cy="10" r="3" />
							</svg>
							<span
								>{t('company_address', $language, {
									default: 'شارع الملك فهد، الرياض، المملكة العربية السعودية'
								})}</span
							>
						</p>
						<p class="flex items-center gap-2 mb-2 text-surface-500-400-token">
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
							>
								<path
									d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"
								/>
							</svg>
							<span>{t('company_phone', $language, { default: '+966 123 456 789' })}</span>
						</p>
						<p class="flex items-center gap-2 mb-2 text-surface-500-400-token">
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
							>
								<path
									d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"
								/>
								<polyline points="22,6 12,13 2,6" />
							</svg>
							<span
								>{t('company_email', $language, { default: 'info@realestate-auctions.com' })}</span
							>
						</p>
					</address>

					<!-- Newsletter -->
					<div class="mt-4">
						<h4 class="font-medium mb-2">
							{t('newsletter', $language, { default: 'النشرة الإخبارية' })}
						</h4>
						<form class="flex {$isRTL ? 'flex-row-reverse' : 'flex-row'}">
							<input
								type="email"
								placeholder={t('your_email', $language, { default: 'بريدك الإلكتروني' })}
								class="input {$isRTL ? 'rounded-r-none border-r-0' : 'rounded-l-none border-l-0'}"
								aria-label={t('email_for_newsletter', $language, {
									default: 'البريد الإلكتروني للنشرة الإخبارية'
								})}
							/>
							<button
								type="submit"
								class="btn variant-filled-primary {$isRTL ? 'rounded-l-none' : 'rounded-r-none'}"
							>
								{t('subscribe', $language, { default: 'اشترك' })}
							</button>
						</form>
					</div>
				</div>
			</div>

			<!-- Copyright bar -->
			<div class="border-t border-surface-300-600-token pt-4 text-center">
				<p class="text-sm text-surface-500-400-token">
					&copy; {year}
					{companyName}. {t('all_rights_reserved', $language, { default: 'جميع الحقوق محفوظة.' })}
				</p>
			</div>
		</div>
	</footer>
{/if}
