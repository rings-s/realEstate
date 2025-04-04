<script>
	/**
	 * Advanced footer component with responsive columns and social links
	 * @component
	 */
	import { slide } from 'svelte/transition';
	import { theme } from '$lib/stores/theme';
	import { createEventDispatcher } from 'svelte';

	// Props
	export let companyName = 'منصة المزادات العقارية';
	export let logo = undefined; // URL to logo image
	export let columns = []; // Footer navigation columns
	export let showLanguageSwitcher = false;
	export let currentLanguage = 'ar';
	export let showAppLinks = false; // Show app store links
	export let showNewsletter = true; // Show newsletter signup
	export let copyright = `© ${new Date().getFullYear()} جميع الحقوق محفوظة`;
	export let socialLinks = []; // Social media links

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Local state
	let newsletterEmail = '';
	let isSubscribing = false;
	let subscribeSuccess = false;
	let subscribeError = false;
	let newsletterMessage = '';
	let mobileExpandedSection = null;

	// Handle newsletter subscription
	async function handleSubscribe(e) {
		e.preventDefault();
		if (!newsletterEmail) return;

		isSubscribing = true;
		subscribeSuccess = false;
		subscribeError = false;

		try {
			// Simulate API call
			await new Promise((resolve) => setTimeout(resolve, 1000));

			// Success
			subscribeSuccess = true;
			newsletterMessage = 'تم الاشتراك بنجاح! شكراً لك.';
			newsletterEmail = '';
		} catch (error) {
			// Error
			subscribeError = true;
			newsletterMessage = 'حدث خطأ أثناء الاشتراك. الرجاء المحاولة مرة أخرى.';
		} finally {
			isSubscribing = false;
		}
	}

	// Toggle mobile accordion sections
	function toggleSection(sectionId) {
		if (mobileExpandedSection === sectionId) {
			mobileExpandedSection = null;
		} else {
			mobileExpandedSection = sectionId;
		}
	}
</script>

<footer class="border-t border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<!-- Main footer content -->
		<div class="py-12 md:py-16">
			<div class="grid grid-cols-1 gap-8 lg:grid-flow-col-dense lg:grid-cols-12">
				<!-- Branding and description -->
				<div class="col-span-12 lg:col-span-4">
					<div class="flex items-center">
						{#if logo}
							<img class="h-10 w-auto" src={logo} alt={companyName} />
						{:else}
							<div
								class="bg-primary-600 flex h-10 w-10 items-center justify-center rounded-md text-white"
							>
								<span class="text-lg font-bold">{companyName.charAt(0)}</span>
							</div>
						{/if}
						<h2 class="mr-3 text-xl font-bold text-gray-900 dark:text-white">{companyName}</h2>
					</div>

					<p class="mt-4 text-base text-gray-600 dark:text-gray-400">
						<slot name="description">
							منصة رائدة في المزادات العقارية توفر تجربة سلسة وآمنة لبيع وشراء العقارات عبر نظام
							المزادات الإلكترونية.
						</slot>
					</p>

					<!-- Social links -->
					{#if socialLinks && socialLinks.length > 0}
						<div class="mt-6">
							<p class="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">تابعنا على</p>
							<div class="flex space-x-4 space-x-reverse">
								{#each socialLinks as link}
									<a
										href={link.url}
										target="_blank"
										rel="noopener noreferrer"
										class="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
										aria-label={link.name}
									>
										{@html link.icon}
									</a>
								{/each}
							</div>
						</div>
					{/if}

					<!-- App store links -->
					{#if showAppLinks}
						<div class="mt-6">
							<p class="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">حمل التطبيق</p>
							<div class="flex flex-wrap gap-3">
								<a
									href="#app-store"
									class="flex items-center rounded-md bg-black px-3 py-2 text-white hover:bg-gray-900"
									target="_blank"
									rel="noopener noreferrer"
									aria-label="تحميل من متجر آبل"
								>
									<svg
										class="ml-2 h-6 w-6"
										viewBox="0 0 24 24"
										fill="currentColor"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											d="M17.0298 7.84128C15.6868 6.91966 14.1798 6.39618 12.6136 6.3324C10.9828 6.26686 9.39528 6.77604 8.06708 7.76746C6.98148 8.5746 6.11528 9.67644 5.56628 10.9554C5.01668 12.2345 4.80228 13.6404 4.94748 15.0295C5.09268 16.4184 5.59308 17.7372 6.39988 18.8529C7.20728 19.968 8.29028 20.8386 9.53748 21.3754C10.7853 21.9123 12.1504 22.0952 13.4995 21.9064C14.8486 21.7175 16.1267 21.1638 17.2072 20.2998C17.7508 19.8677 18.2374 19.3638 18.6548 18.8C18.974 18.3754 19.2416 17.9164 19.4524 17.4322C18.2434 16.865 17.2358 16.0042 16.542 14.9419C15.8482 13.8796 15.4976 12.6574 15.5326 11.418C15.5618 10.2148 15.9233 9.0435 16.5768 8.03202C16.714 7.95918 16.8692 7.9022 17.0298 7.84128Z"
										/>
										<path
											d="M20.3697 15.5858C20.1673 14.8016 19.858 14.0462 19.4496 13.34C19.114 12.7695 18.7087 12.2409 18.2448 11.766C17.9508 11.3926 17.623 11.0454 17.2657 10.7292C16.8017 10.3142 16.2798 9.96903 15.7165 9.7056C15.1533 9.44217 14.5562 9.26315 13.9452 9.17458C13.1877 9.06178 12.4195 9.06178 11.6619 9.17458C11.0506 9.26232 10.4531 9.44096 9.8897 9.7044C9.3264 9.96787 8.80455 10.3132 8.34065 10.7286C7.98449 11.0424 7.65889 11.3877 7.3669 11.7588C6.90389 12.2338 6.50076 12.7617 6.1681 13.3316C5.75954 14.0352 5.45141 14.7882 5.2525 15.5705C5.09322 16.2115 5.01087 16.8706 5.0077 17.5322C5.0077 19.5864 5.8345 21.5488 7.3105 22.9953C7.93586 23.6101 8.67356 24.0975 9.4809 24.4303C10.2882 24.763 11.1472 24.9352 12.0142 24.9376C12.8811 24.94 13.7411 24.7725 14.5499 24.4442C15.3588 24.1159 16.0987 23.6325 16.7268 23.0211C17.2442 22.5139 17.6755 21.9236 18.0024 21.2778C18.2716 20.7344 18.4781 20.163 18.6182 19.5756C18.8434 18.6636 18.9443 17.7254 18.9187 16.7858C18.9166 16.3793 18.8981 15.9812 18.8632 15.5858H20.3697Z"
										/>
										<path
											d="M11.2622 3.96176C11.2622 3.08816 11.4562 2.22888 11.8294 1.45152C12.2026 0.674162 12.744 0.000801086 13.4116 -0.485759C12.6401 -0.323199 11.8874 -0.0607592 11.1626 0.281761C10.4379 0.624281 9.74962 1.04361 9.11222 1.53536C8.47482 2.02711 7.89422 2.58939 7.38462 3.20936C6.87502 3.82933 6.44042 4.50214 6.09102 5.21296C6.09102 5.21296 6.09102 5.51456 6.33702 5.79176C6.64582 6.13576 6.96102 6.48096 7.27982 6.82496C7.53282 7.10276 8.24262 7.75296 8.24262 7.75296C8.75105 7.03032 9.43243 6.44587 10.2241 6.05704C11.0158 5.66822 11.8939 5.48594 12.7728 5.52654C12.7742 5.52768 11.8366 5.14136 11.2622 3.96176Z"
										/>
									</svg>
									<div>
										<div class="text-xs text-gray-300">Download on the</div>
										<div class="font-medium">App Store</div>
									</div>
								</a>
								<a
									href="#google-play"
									class="flex items-center rounded-md bg-black px-3 py-2 text-white hover:bg-gray-900"
									target="_blank"
									rel="noopener noreferrer"
									aria-label="تحميل من متجر جوجل بلاي"
								>
									<svg
										class="ml-2 h-6 w-6"
										viewBox="0 0 24 24"
										fill="currentColor"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											d="M14.2234 12.0046L5.92236 20.291C5.41838 20.147 4.95362 19.8879 4.56335 19.5347C4.17309 19.1814 3.86785 18.7431 3.66903 18.2533C3.47021 17.7635 3.38338 17.2341 3.41523 16.7053C3.44709 16.1766 3.59681 15.6618 3.85536 15.1982L11.2394 12.0046L3.85536 8.811C3.59681 8.34736 3.44709 7.8326 3.41523 7.30387C3.38338 6.77513 3.47021 6.24573 3.66903 5.75592C3.86785 5.26611 4.17309 4.82779 4.56335 4.47456C4.95362 4.12132 5.41838 3.86225 5.92236 3.7182L14.2234 12.0046Z"
											fill="white"
										/>
										<path
											d="M5.9224 3.71915L16.1274 9.13555L19.4664 5.80015C19.2814 5.44795 19.0293 5.13581 18.7253 4.88143C18.4213 4.62705 18.0709 4.43579 17.6934 4.31815C17.216 4.18378 16.7158 4.16066 16.228 4.25071C15.7402 4.34076 15.2781 4.5417 14.8754 4.83795L5.9224 3.71915Z"
											fill="white"
										/>
										<path
											d="M16.1266 14.8735L5.92163 20.2909L14.8746 19.1721C15.2773 19.4683 15.7395 19.6693 16.2272 19.7593C16.715 19.8494 17.2153 19.8263 17.6927 19.6919C18.1701 19.5575 18.6079 19.3165 18.9705 18.9969C19.3332 18.6773 19.6231 18.2857 19.8261 17.846L19.8656 17.752L16.1266 14.8735Z"
											fill="white"
										/>
										<path
											d="M16.1274 9.13645L11.2394 12.0045L16.1274 14.8726L19.8664 11.9941C20.076 11.5578 20.1899 11.0801 20.1994 10.5939C20.209 10.1078 20.1138 9.6256 19.9204 9.18045C19.8799 9.08565 19.8329 8.99435 19.7799 8.90655L16.1274 9.13645Z"
											fill="white"
										/>
									</svg>
									<div>
										<div class="text-xs text-gray-300">GET IT ON</div>
										<div class="font-medium">Google Play</div>
									</div>
								</a>
							</div>
						</div>
					{/if}
				</div>

				<!-- Footer navigation columns -->
				<div class="col-span-12 lg:col-span-5">
					<div class="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-2">
						{#each columns as column, i}
							<div>
								<!-- Mobile accordion header -->
								<div class="flex items-center justify-between md:hidden">
									<h3 class="text-lg font-bold text-gray-900 dark:text-white">{column.title}</h3>
									<button
										class="focus:ring-primary-500 rounded-full p-1 text-gray-500 focus:ring-2 focus:outline-none"
										on:click={() => toggleSection(i)}
										aria-expanded={mobileExpandedSection === i}
										aria-controls={`footer-section-${i}`}
										aria-label={mobileExpandedSection === i
											? `طي ${column.title}`
											: `توسيع ${column.title}`}
									>
										<svg
											class="h-5 w-5 transition-transform duration-200 {mobileExpandedSection === i
												? 'rotate-180 transform'
												: ''}"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 9l-7 7-7-7"
											/>
										</svg>
									</button>
								</div>

								<!-- Desktop heading -->
								<h3 class="hidden text-lg font-bold text-gray-900 md:block dark:text-white">
									{column.title}
								</h3>

								<!-- Links -->
								<div
									id={`footer-section-${i}`}
									class={`${mobileExpandedSection === i ? 'block' : 'hidden'} md:block`}
								>
									{#if mobileExpandedSection === i}
										<ul class="mt-4 space-y-3" transition:slide={{ duration: 200 }}>
											{#each column.links as link}
												<li>
													<a
														href={link.url}
														class="hover:text-primary-600 dark:hover:text-primary-400 text-base text-gray-600 dark:text-gray-400"
													>
														{link.label}
													</a>
												</li>
											{/each}
										</ul>
									{:else}
										<ul class="mt-4 space-y-3 md:block">
											{#each column.links as link}
												<li>
													<a
														href={link.url}
														class="hover:text-primary-600 dark:hover:text-primary-400 text-base text-gray-600 dark:text-gray-400"
													>
														{link.label}
													</a>
												</li>
											{/each}
										</ul>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>

				<!-- Newsletter signup -->
				{#if showNewsletter}
					<div class="col-span-12 lg:col-span-3">
						<h3 class="text-lg font-bold text-gray-900 dark:text-white">
							اشترك في النشرة البريدية
						</h3>
						<p class="mt-4 text-base text-gray-600 dark:text-gray-400">
							احصل على آخر الأخبار والتحديثات عن المزادات القادمة.
						</p>

						<form class="mt-4" on:submit={handleSubscribe}>
							<div class="flex flex-col gap-2 md:flex-row">
								<div class="flex-1">
									<label for="email-input" class="sr-only">البريد الإلكتروني</label>
									<input
										id="email-input"
										type="email"
										bind:value={newsletterEmail}
										placeholder="أدخل بريدك الإلكتروني"
										required
										class="focus:ring-primary-500 focus:border-primary-500 w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:ring-2 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
										disabled={isSubscribing}
									/>
								</div>
								<button
									type="submit"
									class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 rounded-md px-4 py-2 text-sm font-medium text-white focus:ring-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
									disabled={isSubscribing}
									aria-label="اشتراك في النشرة البريدية"
								>
									{#if isSubscribing}
										<svg
											class="mr-2 inline h-4 w-4 animate-spin"
											viewBox="0 0 24 24"
											fill="none"
											xmlns="http://www.w3.org/2000/svg"
										>
											<circle
												class="opacity-25"
												cx="12"
												cy="12"
												r="10"
												stroke="currentColor"
												stroke-width="4"
											></circle>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
											></path>
										</svg>
										جاري...
									{:else}
										اشتراك
									{/if}
								</button>
							</div>

							{#if newsletterMessage}
								<p
									class={`mt-2 text-sm ${subscribeSuccess ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}
								>
									{newsletterMessage}
								</p>
							{/if}
						</form>

						<!-- Language switcher -->
						{#if showLanguageSwitcher}
							<div class="mt-6">
								<h3 class="mb-2 text-base font-bold text-gray-900 dark:text-white">اللغة</h3>
								<div class="relative">
									<select
										class="focus:ring-primary-500 focus:border-primary-500 w-full appearance-none rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:ring-2 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-white"
										value={currentLanguage}
										on:change={(e) => dispatch('languageChange', { language: e.target.value })}
										aria-label="اختر اللغة"
									>
										<option value="ar">العربية</option>
										<option value="en">English</option>
									</select>
									<div
										class="pointer-events-none absolute inset-y-0 left-0 flex items-center px-2 text-gray-700 dark:text-gray-400"
									>
										<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
											<path
												fill-rule="evenodd"
												d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
												clip-rule="evenodd"
											/>
										</svg>
									</div>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- Footer bottom section -->
		<div
			class="flex flex-col space-y-4 border-t border-gray-200 py-6 md:flex-row md:items-center md:justify-between dark:border-gray-800"
		>
			<div class="text-sm text-gray-500 dark:text-gray-400">
				{copyright}
			</div>

			<div class="flex flex-wrap justify-center space-x-4 space-x-reverse md:justify-end">
				<a
					href="/terms"
					class="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
				>
					الشروط والأحكام
				</a>
				<a
					href="/privacy"
					class="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
				>
					سياسة الخصوصية
				</a>
				<a
					href="/cookies"
					class="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
				>
					سياسة ملفات تعريف الارتباط
				</a>
			</div>
		</div>
	</div>
</footer>
