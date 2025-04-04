<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import PropertyMap from './PropertyMap.svelte';

	// Props
	export let property = null;
	export let loading = false;

	// State
	let activeTab = 'info'; // info, features, location, documents
	let activeImageIndex = 0;
	let images = [];
	let features = [];
	let amenities = [];
	let documents = [];

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Handle JSON fields
	$: {
		if (property) {
			try {
				// Parse images
				if (property.images) {
					images =
						typeof property.images === 'string'
							? JSON.parse(property.images)
							: Array.isArray(property.images)
								? property.images
								: [];
				}

				// Parse features
				if (property.features) {
					features =
						typeof property.features === 'string'
							? JSON.parse(property.features)
							: Array.isArray(property.features)
								? property.features
								: [];
				}

				// Parse amenities
				if (property.amenities) {
					amenities =
						typeof property.amenities === 'string'
							? JSON.parse(property.amenities)
							: Array.isArray(property.amenities)
								? property.amenities
								: [];
				}

				// Parse documents
				if (property.documents) {
					documents =
						typeof property.documents === 'string'
							? JSON.parse(property.documents)
							: Array.isArray(property.documents)
								? property.documents
								: [];
				}
			} catch (e) {
				console.error('Error parsing JSON fields:', e);
			}
		}
	}

	// Format price with thousand separator
	function formatPrice(price) {
		return price?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
	}

	// Handle image navigation
	function nextImage() {
		activeImageIndex = (activeImageIndex + 1) % images.length;
	}

	function prevImage() {
		activeImageIndex = (activeImageIndex - 1 + images.length) % images.length;
	}

	function setActiveImage(index) {
		activeImageIndex = index;
	}

	// Set tab
	function setTab(tab) {
		activeTab = tab;
	}

	// Handle contact owner
	function contactOwner() {
		dispatch('contact', { property });
	}

	// Handle bid/auction
	function bid() {
		dispatch('bid', { property });
	}
</script>

<div class="overflow-hidden rounded-lg bg-white shadow-lg dark:bg-gray-800">
	{#if loading}
		<!-- Loading state -->
		<div class="flex flex-col items-center justify-center p-8">
			<div
				class="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"
			></div>
			<p class="text-gray-600 dark:text-gray-300">جاري تحميل تفاصيل العقار...</p>
		</div>
	{:else if !property}
		<!-- Error state -->
		<div class="flex flex-col items-center justify-center p-8">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="mb-4 h-12 w-12 text-red-500"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<p class="text-gray-600 dark:text-gray-300">لم يتم العثور على بيانات العقار.</p>
		</div>
	{:else}
		<!-- Property details -->
		<div>
			<!-- Image gallery -->
			<div class="relative h-64 bg-gray-300 md:h-96 dark:bg-gray-700">
				{#if images.length > 0}
					<img
						src={images[activeImageIndex]?.path || '/images/placeholder-property.jpg'}
						alt={property.title}
						class="h-full w-full object-cover"
					/>

					<!-- Image navigation -->
					{#if images.length > 1}
						<button
							class="bg-opacity-50 hover:bg-opacity-70 absolute top-1/2 left-2 -translate-y-1/2 transform rounded-full bg-black p-2 text-white"
							on:click={prevImage}
							aria-label="الصورة السابقة"
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
									d="M15 19l-7-7 7-7"
								/>
							</svg>
						</button>

						<button
							class="bg-opacity-50 hover:bg-opacity-70 absolute top-1/2 right-2 -translate-y-1/2 transform rounded-full bg-black p-2 text-white"
							on:click={nextImage}
							aria-label="الصورة التالية"
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
									d="M9 5l7 7-7 7"
								/>
							</svg>
						</button>

						<!-- Image thumbnails -->
						<div
							class="absolute right-0 bottom-2 left-0 flex justify-center space-x-2 rtl:space-x-reverse"
						>
							{#each images as image, index}
								<button
									class="h-3 w-3 rounded-full {index === activeImageIndex
										? 'bg-white'
										: 'bg-opacity-70 bg-gray-400'}"
									on:click={() => setActiveImage(index)}
									aria-label={`الصورة ${index + 1}`}
									aria-current={index === activeImageIndex}
								></button>
							{/each}
						</div>
					{/if}
				{:else}
					<div class="flex h-full w-full items-center justify-center bg-gray-200 dark:bg-gray-700">
						<p class="text-gray-500 dark:text-gray-400">لا توجد صور متاحة</p>
					</div>
				{/if}

				<!-- Property status badge -->
				{#if property.status}
					<div
						class="absolute top-2 right-2 rounded px-2 py-1 text-xs font-semibold
            {property.status === 'active'
							? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
							: property.status === 'sold'
								? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
								: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'}"
					>
						{property.status === 'active'
							? 'نشط'
							: property.status === 'sold'
								? 'مباع'
								: property.status === 'pending_approval'
									? 'قيد الموافقة'
									: property.status === 'under_contract'
										? 'تحت التعاقد'
										: property.status === 'inactive'
											? 'غير نشط'
											: property.status === 'rejected'
												? 'مرفوض'
												: property.status}
					</div>
				{/if}
			</div>

			<!-- Property header & actions -->
			<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
				<div class="flex flex-wrap items-start justify-between gap-2">
					<div>
						<h1 class="text-2xl font-bold text-gray-900 dark:text-white">{property.title}</h1>
						<p class="mt-1 text-gray-600 dark:text-gray-300">
							<span class="inline-flex items-center">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
										clip-rule="evenodd"
									/>
								</svg>
								{property.district}, {property.city}
							</span>
						</p>
					</div>

					<div class="text-center">
						<div class="text-2xl font-bold text-green-600 dark:text-green-400">
							{formatPrice(property.estimated_value)} ريال
						</div>
						{#if property.price_per_sqm}
							<div class="text-sm text-gray-500 dark:text-gray-400">
								{formatPrice(property.price_per_sqm)} ريال/م²
							</div>
						{/if}
					</div>
				</div>

				<!-- Quick info/stats -->
				<div class="mt-4 flex flex-wrap gap-6">
					{#if property.area}
						<div class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
								/>
							</svg>
							<div>
								<span class="font-medium text-gray-900 dark:text-white">{property.area} م²</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">المساحة</p>
							</div>
						</div>
					{/if}

					{#if property.bedrooms !== undefined && property.bedrooms !== null}
						<div class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
								/>
							</svg>
							<div>
								<span class="font-medium text-gray-900 dark:text-white">{property.bedrooms}</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">غرف النوم</p>
							</div>
						</div>
					{/if}

					{#if property.bathrooms !== undefined && property.bathrooms !== null}
						<div class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"
								/>
							</svg>
							<div>
								<span class="font-medium text-gray-900 dark:text-white">{property.bathrooms}</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">الحمامات</p>
							</div>
						</div>
					{/if}

					{#if property.property_type}
						<div class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
								/>
							</svg>
							<div>
								<span class="font-medium text-gray-900 dark:text-white">
									{property.property_type === 'apartment'
										? 'شقة'
										: property.property_type === 'villa'
											? 'فيلا'
											: property.property_type === 'land'
												? 'أرض'
												: property.property_type === 'commercial'
													? 'تجاري'
													: property.property_type === 'building'
														? 'مبنى'
														: property.property_type === 'farm'
															? 'مزرعة'
															: property.property_type === 'industrial'
																? 'صناعي'
																: property.property_type === 'office'
																	? 'مكتب'
																	: property.property_type === 'retail'
																		? 'محل تجاري'
																		: property.property_type === 'mixed_use'
																			? 'متعدد الاستخدامات'
																			: property.property_type}
								</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">نوع العقار</p>
							</div>
						</div>
					{/if}

					{#if property.year_built}
						<div class="flex items-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
							<div>
								<span class="font-medium text-gray-900 dark:text-white">{property.year_built}</span>
								<p class="text-xs text-gray-500 dark:text-gray-400">سنة البناء</p>
							</div>
						</div>
					{/if}
				</div>

				<!-- Call to action buttons -->
				<div class="mt-6 flex flex-wrap gap-3">
					<button
						class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
						on:click={contactOwner}
					>
						تواصل مع المالك
					</button>

					{#if property.status === 'active'}
						<button
							class="rounded-md bg-green-600 px-4 py-2 text-white transition hover:bg-green-700"
							on:click={bid}
						>
							المزايدة على العقار
						</button>
					{/if}

					<button
						class="rounded-md border border-gray-300 px-4 py-2 text-gray-700 transition hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
						on:click={() => dispatch('share', { property })}
					>
						مشاركة
					</button>
				</div>
			</div>

			<!-- Tabs -->
			<div class="border-b border-gray-200 dark:border-gray-700">
				<div class="flex overflow-x-auto">
					<button
						class="px-4 py-3 text-sm font-medium whitespace-nowrap {activeTab === 'info'
							? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
							: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
						on:click={() => setTab('info')}
					>
						تفاصيل العقار
					</button>

					<button
						class="px-4 py-3 text-sm font-medium whitespace-nowrap {activeTab === 'features'
							? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
							: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
						on:click={() => setTab('features')}
					>
						المميزات والمرافق
					</button>

					<button
						class="px-4 py-3 text-sm font-medium whitespace-nowrap {activeTab === 'location'
							? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
							: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
						on:click={() => setTab('location')}
					>
						الموقع
					</button>

					{#if documents.length > 0}
						<button
							class="px-4 py-3 text-sm font-medium whitespace-nowrap {activeTab === 'documents'
								? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
								: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
							on:click={() => setTab('documents')}
						>
							المستندات
						</button>
					{/if}
				</div>
			</div>

			<!-- Tab content -->
			<div class="p-6">
				{#if activeTab === 'info'}
					<!-- Property details tab -->
					<div>
						<h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">الوصف</h2>
						<p class="mb-6 whitespace-pre-line text-gray-700 dark:text-gray-300">
							{property.description || 'لا يوجد وصف متاح لهذا العقار.'}
						</p>

						<h3 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">تفاصيل العقار</h3>
						<div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
							<div class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700">
								<span class="text-gray-600 dark:text-gray-400">رقم العقار</span>
								<span class="font-medium text-gray-900 dark:text-white"
									>{property.property_number}</span
								>
							</div>

							{#if property.condition}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">حالة العقار</span>
									<span class="font-medium text-gray-900 dark:text-white">
										{property.condition === 'excellent'
											? 'ممتاز'
											: property.condition === 'very_good'
												? 'جيد جدا'
												: property.condition === 'good'
													? 'جيد'
													: property.condition === 'fair'
														? 'مقبول'
														: property.condition === 'poor'
															? 'سيئ'
															: property.condition === 'under_construction'
																? 'تحت الإنشاء'
																: property.condition === 'new'
																	? 'جديد'
																	: property.condition}
									</span>
								</div>
							{/if}

							{#if property.total_floors !== undefined && property.total_floors !== null}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">عدد الطوابق</span>
									<span class="font-medium text-gray-900 dark:text-white"
										>{property.total_floors}</span
									>
								</div>
							{/if}

							{#if property.floor_number !== undefined && property.floor_number !== null}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">الطابق</span>
									<span class="font-medium text-gray-900 dark:text-white"
										>{property.floor_number}</span
									>
								</div>
							{/if}

							{#if property.built_up_area}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">المساحة المبنية</span>
									<span class="font-medium text-gray-900 dark:text-white"
										>{property.built_up_area} م²</span
									>
								</div>
							{/if}

							{#if property.facing_direction}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">اتجاه الواجهة</span>
									<span class="font-medium text-gray-900 dark:text-white">
										{property.facing_direction === 'north'
											? 'شمال'
											: property.facing_direction === 'east'
												? 'شرق'
												: property.facing_direction === 'south'
													? 'جنوب'
													: property.facing_direction === 'west'
														? 'غرب'
														: property.facing_direction === 'northeast'
															? 'شمال شرق'
															: property.facing_direction === 'southeast'
																? 'جنوب شرق'
																: property.facing_direction === 'southwest'
																	? 'جنوب غرب'
																	: property.facing_direction === 'northwest'
																		? 'شمال غرب'
																		: property.facing_direction}
									</span>
								</div>
							{/if}

							{#if property.current_usage}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">الاستخدام الحالي</span>
									<span class="font-medium text-gray-900 dark:text-white">
										{property.current_usage === 'residential'
											? 'سكني'
											: property.current_usage === 'commercial'
												? 'تجاري'
												: property.current_usage === 'mixed'
													? 'مختلط'
													: property.current_usage === 'industrial'
														? 'صناعي'
														: property.current_usage === 'agricultural'
															? 'زراعي'
															: property.current_usage}
									</span>
								</div>
							{/if}

							{#if property.is_verified}
								<div
									class="flex justify-between border-b border-gray-200 py-2 dark:border-gray-700"
								>
									<span class="text-gray-600 dark:text-gray-400">التحقق</span>
									<span class="flex items-center font-medium text-green-600 dark:text-green-400">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="mr-1 h-5 w-5"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
											/>
										</svg>
										تم التحقق
									</span>
								</div>
							{/if}
						</div>
					</div>
				{:else if activeTab === 'features'}
					<!-- Features & amenities tab -->
					<div>
						{#if features.length > 0}
							<h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">المميزات</h2>
							<div class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
								{#each features as feature}
									<div class="flex items-center text-gray-700 dark:text-gray-300">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="ml-2 h-5 w-5 text-blue-500"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												fill-rule="evenodd"
												d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
												clip-rule="evenodd"
											/>
										</svg>
										<span>{feature.name || feature}</span>
									</div>
								{/each}
							</div>
						{/if}

						{#if amenities.length > 0}
							<h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">المرافق</h2>
							<div class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
								{#each amenities as amenity}
									<div class="flex items-center text-gray-700 dark:text-gray-300">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="ml-2 h-5 w-5 text-green-500"
											viewBox="0 0 20 20"
											fill="currentColor"
										>
											<path
												fill-rule="evenodd"
												d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
												clip-rule="evenodd"
											/>
										</svg>
										<span>{amenity.name || amenity}</span>
									</div>
								{/each}
							</div>
						{/if}

						{#if !features.length && !amenities.length}
							<div class="p-6 text-center">
								<p class="text-gray-500 dark:text-gray-400">
									لم يتم تحديد أي مميزات أو مرافق لهذا العقار.
								</p>
							</div>
						{/if}
					</div>
				{:else if activeTab === 'location'}
					<!-- Location tab -->
					<div>
						<h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">الموقع</h2>
						<div class="mb-4">
							<p class="text-gray-700 dark:text-gray-300">
								{property.address ||
									`${property.district}، ${property.city}، ${property.country || 'المملكة العربية السعودية'}`}
							</p>
						</div>

						<!-- Map component -->
						<PropertyMap
							location={property.location}
							height="400px"
							interactive={false}
							showControls={true}
						/>
					</div>
				{:else if activeTab === 'documents'}
					<!-- Documents tab -->
					<div>
						<h2 class="mb-4 text-xl font-semibold text-gray-900 dark:text-white">المستندات</h2>
						{#if documents.length > 0}
							<ul class="divide-y divide-gray-200 dark:divide-gray-700">
								{#each documents as document}
									<li class="flex justify-between py-3">
										<div class="flex items-center">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="ml-2 h-5 w-5 text-blue-500"
												fill="none"
												viewBox="0 0 24 24"
												stroke="currentColor"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
												/>
											</svg>
											<span class="text-gray-700 dark:text-gray-300"
												>{document.title || document.name || 'مستند'}</span
											>
										</div>
										<a
											href={document.path || document.url || '#'}
											target="_blank"
											class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
											rel="noopener noreferrer"
										>
											عرض
										</a>
									</li>
								{/each}
							</ul>
						{:else}
							<div class="p-6 text-center">
								<p class="text-gray-500 dark:text-gray-400">لم يتم إضافة أي مستندات لهذا العقار.</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
