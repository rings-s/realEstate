<!-- src/routes/properties/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		propertiesStore,
		properties as propertiesData,
		propertyFilters,
		propertyPagination
	} from '$lib/stores/properties';
	import { auth } from '$lib/stores/auth';
	import { uiStore } from '$lib/stores/ui';
	import { processEntityData, PROPERTY_JSON_FIELDS } from '$lib/utils/jsonFields';

	// Import common components
	import PropertyCard from '$lib/components/properties/PropertyCard.svelte';
	import PropertyFilters from '$lib/components/properties/PropertyFilters.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import SearchBar from '$lib/components/common/SearchBar.svelte';
	import Breadcrumb from '$lib/components/common/Breadcrumb.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Icon from '$lib/components/common/Icon.svelte';
	import Tabs from '$lib/components/common/Tabs.svelte';

	// ========== STATE MANAGEMENT ==========
	// Page state
	let error = null;
	let showFilters = false;
	let activeFilters = {};
	let pageSize = 12;
	let currentPage = 1;
	let totalPages = 0;
	let totalItems = 0;
	let properties = [];
	let hasMorePages = false;
	let searchQuery = '';
	let activeView = 'grid'; // grid or list
	let selectedTab = 0; // 0 = all, 1 = active, 2 = sold
	let loadingRequestId = null; // Track the current request ID

	// Track if initial load has been done
	let initialLoadCompleted = false;

	// Error state
	let errorInfo = {
		title: '',
		message: '',
		details: null,
		suggestions: []
	};

	// Retry state
	let retryCount = 0;
	const MAX_RETRIES = 3;

	// ========== CONFIGURATION ==========
	// List configurations
	const propertyTypes = [
		{ value: 'apartment', label: 'شقة' },
		{ value: 'villa', label: 'فيلا' },
		{ value: 'land', label: 'أرض' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'building', label: 'مبنى' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'office', label: 'مكتب' },
		{ value: 'retail', label: 'محل تجاري' }
	];

	const propertyStatus = [
		{ value: 'active', label: 'نشط' },
		{ value: 'pending_approval', label: 'قيد الموافقة' },
		{ value: 'under_contract', label: 'تحت التعاقد' },
		{ value: 'sold', label: 'مباع' },
		{ value: 'inactive', label: 'غير نشط' }
	];

	const cities = [
		'الرياض',
		'جدة',
		'مكة',
		'المدينة المنورة',
		'الدمام',
		'الخبر',
		'تبوك',
		'القصيم',
		'حائل',
		'أبها',
		'الطائف',
		'جازان',
		'نجران',
		'الباحة',
		'سكاكا',
		'عرعر'
	];

	const priceRange = { min: 0, max: 10000000 };
	const areaRange = { min: 0, max: 10000 };

	// Breadcrumb navigation
	const breadcrumbItems = [{ label: 'العقارات', href: '/properties' }];

	// Tabs configuration
	const tabs = [
		{ label: 'جميع العقارات', value: '' },
		{ label: 'العقارات النشطة', value: 'active' },
		{ label: 'العقارات المباعة', value: 'sold' }
	];

	// ========== API & DATA FUNCTIONS ==========
	/**
	 * Load properties with applied filters - simplified without loading state
	 * @param {number} page - Page number
	 * @param {object} filters - Filter parameters
	 */
	async function loadProperties(page = 1, filters = {}) {
		// Generate a unique request ID
		const requestId = Date.now().toString();
		loadingRequestId = requestId;

		// Reset error state
		error = null;
		errorInfo = {
			title: '',
			message: '',
			details: null,
			suggestions: []
		};

		// Update state
		currentPage = page;
		activeFilters = { ...filters };

		try {
			// Build final filter params
			const params = {
				...filters,
				page,
				page_size: pageSize
			};

			// Only add is_published=true for non-admin users
			if (!$auth.user?.is_staff) {
				params.is_published = true;
			}

			console.log(`[Request ${requestId}] Loading properties with params:`, params);

			// Fetch properties with applied filters
			const result = await propertiesStore.loadProperties(params);

			// If this is not the most recent request, ignore the results
			if (loadingRequestId !== requestId) {
				console.log(`[Request ${requestId}] Ignored stale response`);
				return;
			}

			// Process result data
			if (Array.isArray(result.results)) {
				properties = result.results.map((property) =>
					processEntityData(property, PROPERTY_JSON_FIELDS)
				);
				totalItems = result.count || 0;
				totalPages = Math.ceil(totalItems / pageSize);
				hasMorePages = currentPage < totalPages;
			} else if (Array.isArray(result)) {
				properties = result.map((property) => processEntityData(property, PROPERTY_JSON_FIELDS));
				totalItems = result.length;
				totalPages = Math.ceil(totalItems / pageSize);
				hasMorePages = false;
			} else {
				properties = [];
				totalItems = 0;
				totalPages = 0;
				hasMorePages = false;
			}

			// Reset retry count on success
			retryCount = 0;

			// Mark initial load as completed
			initialLoadCompleted = true;

			console.log(
				`[Request ${requestId}] Completed successfully with ${properties.length} properties`
			);
		} catch (err) {
			// Only handle errors for the most recent request
			if (loadingRequestId !== requestId) {
				return;
			}

			console.error(`[Request ${requestId}] Error loading properties:`, err);
			error = err;

			// Format the error for better user guidance
			errorInfo = formatApiError(err);

			// Show error toast
			uiStore.addToast(errorInfo.title || 'حدث خطأ أثناء تحميل العقارات', 'error');
		}
	}

	/**
	 * Format API errors for better user feedback
	 * @param {Error} err - The API error
	 */
	function formatApiError(err) {
		// Default error information
		const formattedError = {
			title: 'حدث خطأ أثناء تحميل العقارات',
			message: 'لا يمكن الاتصال بالخادم حاليًا. يرجى المحاولة مرة أخرى لاحقًا.',
			details: null,
			suggestions: [
				'تأكد من اتصالك بالإنترنت',
				'حاول تحديث الصفحة',
				'قد تكون هناك مشكلة مؤقتة في الخادم'
			]
		};

		// Check if it's a network error
		if (err.message === 'Failed to fetch' || err.message?.includes('NetworkError')) {
			formattedError.title = 'خطأ في الاتصال بالشبكة';
			formattedError.message = 'لا يمكن الاتصال بالخادم. يرجى التحقق من اتصالك بالإنترنت.';
			return formattedError;
		}

		// Check if it's a permission error (based on error shared)
		if (
			err.message &&
			(err.message.includes('permission_denied') ||
				err.message.includes('not authenticated') ||
				err.message.includes('not authorized'))
		) {
			formattedError.title = 'خطأ في صلاحيات الوصول';
			formattedError.message =
				'ليس لديك الصلاحية للوصول إلى هذه البيانات. يرجى تسجيل الدخول مرة أخرى.';
			formattedError.suggestions = [
				'تأكد من تسجيل الدخول',
				'قد تكون الجلسة قد انتهت صلاحيتها',
				'اتصل بمسؤول النظام إذا استمرت المشكلة'
			];
			return formattedError;
		}

		// Handle renderer errors (like the one in the error message)
		if (
			err.message &&
			(err.message.includes('renderer not set') || err.message.includes('accepted_renderer'))
		) {
			formattedError.title = 'خطأ في معالجة البيانات';
			formattedError.message = 'هناك مشكلة في الخادم. جاري العمل على إصلاحها.';
			formattedError.details = 'خطأ في الطلب: renderer not set on Response';
			formattedError.suggestions = [
				'حاول تحديث الصفحة',
				'حاول تسجيل الخروج وإعادة تسجيل الدخول',
				'اتصل بمسؤول النظام إذا استمرت المشكلة'
			];
			return formattedError;
		}

		// If we have a status code, provide more specific guidance
		if (err.status) {
			switch (err.status) {
				case 401:
					formattedError.title = 'غير مصرح';
					formattedError.message = 'يرجى تسجيل الدخول للوصول إلى هذه البيانات.';
					break;
				case 403:
					formattedError.title = 'غير مسموح';
					formattedError.message = 'ليس لديك صلاحية للوصول إلى هذه البيانات.';
					break;
				case 404:
					formattedError.title = 'البيانات غير موجودة';
					formattedError.message = 'العقارات التي تبحث عنها غير موجودة.';
					break;
				case 500:
					formattedError.title = 'خطأ في الخادم';
					formattedError.message = 'هناك مشكلة في الخادم. جاري العمل على إصلاحها.';
					formattedError.details = err.data?.error || err.message || 'خطأ داخلي في الخادم';
					break;
				default:
					formattedError.details = err.data?.error || err.message || null;
			}
		}

		return formattedError;
	}

	/**
	 * Retry API request with exponential backoff and improved error handling
	 */
	function retryWithBackoff() {
		if (retryCount < MAX_RETRIES) {
			retryCount++;
			const delay = Math.pow(2, retryCount) * 1000; // 2s, 4s, 8s

			// Show retry toast
			uiStore.addToast(`جاري إعادة المحاولة (${retryCount}/${MAX_RETRIES})...`, 'info');

			// Clear the current error to show loading state during retry
			error = null;

			setTimeout(() => {
				loadProperties(currentPage, activeFilters);
			}, delay);
		} else {
			// Max retries reached
			uiStore.addToast(
				'تعذر الاتصال بالخادم بعد عدة محاولات. يرجى التحقق من اتصالك بالإنترنت أو المحاولة لاحقًا.',
				'error'
			);
			retryCount = 0;
		}
	}

	// ========== EVENT HANDLERS ==========
	/**
	 * Handle filter application
	 */
	function handleFilterApply(event) {
		const filters = event.detail;
		console.log('Applied filters:', filters);
		loadProperties(1, filters);
	}

	/**
	 * Handle filter reset
	 */
	function handleFilterReset() {
		activeFilters = {};
		searchQuery = '';
		loadProperties(1, {});
	}

	/**
	 * Handle property selection to navigate to detail page
	 */
	function handlePropertySelect(event) {
		const { property } = event.detail;
		goto(`/properties/${property.slug}`);
	}

	/**
	 * Handle pagination change
	 */
	function handlePageChange(event) {
		const page = event.detail;
		if (page !== currentPage) {
			loadProperties(page, activeFilters);
			// Scroll to top of the page
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	/**
	 * Toggle filters visibility
	 */
	function toggleFilters() {
		showFilters = !showFilters;
	}

	/**
	 * Add new property button action
	 */
	function handleAddProperty() {
		goto('/properties/add');
	}

	/**
	 * Handle search query
	 */
	function handleSearch(event) {
		searchQuery = event.detail;
		const newFilters = { ...activeFilters, search: searchQuery };
		loadProperties(1, newFilters);
	}

	/**
	 * Toggle view between grid and list
	 */
	function toggleView(view) {
		activeView = view;
	}

	/**
	 * Handle tab change - optimized to prevent duplicate loading
	 */
	function handleTabChange(event) {
		const newTabIndex = event.detail.index;

		// Don't reload if same tab is clicked
		if (selectedTab === newTabIndex) {
			return;
		}

		selectedTab = newTabIndex;
		const status = tabs[selectedTab].value;
		const newFilters = { ...activeFilters };

		// Update status filter
		if (status) {
			newFilters.status = status;
		} else {
			delete newFilters.status;
		}

		loadProperties(1, newFilters);
	}

	/**
	 * Handle page size change
	 */
	function handlePageSizeChange(event) {
		pageSize = event.detail.pageSize;
		loadProperties(1, activeFilters);
	}

	// ========== LIFECYCLE ==========
	// Load properties on mount
	onMount(async () => {
		// Get any URL parameters for filters
		const urlParams = new URLSearchParams(window.location.search);
		const urlFilters = {};

		for (const [key, value] of urlParams.entries()) {
			urlFilters[key] = value;
		}

		// Apply any filters from URL
		if (Object.keys(urlFilters).length > 0) {
			activeFilters = urlFilters;
			if (urlFilters.search) {
				searchQuery = urlFilters.search;
			}

			// Set initial tab based on status filter if present
			if (urlFilters.status) {
				const tabIndex = tabs.findIndex((tab) => tab.value === urlFilters.status);
				if (tabIndex !== -1) {
					selectedTab = tabIndex;
				}
			}
		}

		// Only load once on mount
		if (!initialLoadCompleted) {
			await loadProperties(1, activeFilters);
		}
	});
</script>

<svelte:head>
	<title>قائمة العقارات | نظام المزادات العقارية</title>
	<meta
		name="description"
		content="استعراض العقارات المتاحة للبيع والمزاد في منصة المزادات العقارية"
	/>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<!-- Breadcrumb navigation -->
	<div class="mb-6">
		<Breadcrumb items={breadcrumbItems} separator="chevron" home={true} />
	</div>

	<!-- Page header with actions -->
	<div class="mb-6 flex flex-wrap items-center justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">العقارات</h1>
			<p class="mt-2 text-gray-600 dark:text-gray-400">استعراض العقارات المتاحة للبيع والمزاد</p>
		</div>

		<div class="flex flex-wrap gap-3">
			<!-- View toggle -->
			<div
				class="flex rounded-md border border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-800"
			>
				<button
					class={`px-3 py-2 ${activeView === 'grid' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300'}`}
					on:click={() => toggleView('grid')}
					aria-label="عرض شبكي"
				>
					<Icon name="grid" customClass="h-5 w-5" />
				</button>
				<button
					class={`px-3 py-2 ${activeView === 'list' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300'}`}
					on:click={() => toggleView('list')}
					aria-label="عرض قائمة"
				>
					<Icon name="list" customClass="h-5 w-5" />
				</button>
			</div>

			<!-- Filter toggle -->
			<Button variant="outline" on:click={toggleFilters}>
				<Icon name="filter" customClass="ml-2" />
				{showFilters ? 'إخفاء الفلاتر' : 'عرض الفلاتر'}
			</Button>

			<!-- Add property button for authenticated users -->
			{#if $auth.isAuthenticated}
				<Button variant="primary" on:click={handleAddProperty}>
					<Icon name="plus" customClass="ml-2" />
					إضافة عقار
				</Button>
			{/if}
		</div>
	</div>

	<!-- Tabs for property status filtering -->
	<div class="mb-6">
		<Tabs
			{tabs}
			activeTab={selectedTab}
			variant="underline"
			fullWidth={false}
			on:change={handleTabChange}
		/>
	</div>

	<!-- Search and filters -->
	<div class="mb-6 space-y-4">
		<!-- Search bar -->
		<Card variant="default" padding="md">
			<SearchBar
				value={searchQuery}
				placeholder="ابحث عن عقار حسب العنوان، الوصف، أو المدينة..."
				on:search={handleSearch}
			/>
		</Card>

		<!-- Advanced filters -->
		<PropertyFilters
			{showFilters}
			{activeFilters}
			{propertyTypes}
			{propertyStatus}
			{cities}
			{priceRange}
			{areaRange}
			on:filter={handleFilterApply}
			on:reset={handleFilterReset}
			on:toggleFilters={toggleFilters}
		/>
	</div>

	<!-- Active filters summary -->
	{#if Object.keys(activeFilters).length > 0 && Object.keys(activeFilters).some((key) => key !== 'page' && key !== 'page_size' && key !== 'ordering')}
		<Card variant="default" padding="md" class="mb-6">
			<div class="flex flex-wrap items-center gap-2">
				<span class="text-sm font-medium text-gray-700 dark:text-gray-300">الفلاتر النشطة:</span>

				{#each Object.entries(activeFilters) as [key, value]}
					{#if value && key !== 'page' && key !== 'page_size' && key !== 'ordering'}
						<span
							class="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800 dark:bg-blue-900 dark:text-blue-200"
						>
							{key === 'property_type'
								? 'نوع العقار'
								: key === 'city'
									? 'المدينة'
									: key === 'district'
										? 'الحي'
										: key === 'status'
											? 'الحالة'
											: key === 'bedrooms'
												? 'عدد الغرف'
												: key === 'bathrooms'
													? 'عدد الحمامات'
													: key === 'min_price'
														? 'السعر الأدنى'
														: key === 'max_price'
															? 'السعر الأقصى'
															: key === 'min_area'
																? 'المساحة الأدنى'
																: key === 'max_area'
																	? 'المساحة الأقصى'
																	: key === 'search'
																		? 'البحث'
																		: key}: {value}
						</span>
					{/if}
				{/each}

				<Button variant="ghost" size="sm" on:click={handleFilterReset}>مسح الفلاتر</Button>
			</div>
		</Card>
	{/if}

	<!-- Results summary -->
	{#if !error && properties.length > 0}
		<div class="mb-4 text-sm text-gray-600 dark:text-gray-400">
			تم العثور على {totalItems} عقار
			{#if Object.keys(activeFilters).length > 0 && Object.keys(activeFilters).some((key) => key !== 'page' && key !== 'page_size' && key !== 'ordering')}
				مطابق للفلاتر
			{/if}
		</div>
	{/if}

	<!-- Property Listings -->
	<div>
		{#if error}
			<!-- Error state -->
			<Card variant="default" padding="lg" class="mb-6">
				<div class="mb-4">
					<Alert
						type="error"
						title={errorInfo.title || 'خطأ في تحميل العقارات'}
						message={errorInfo.message ||
							error.message ||
							'حدث خطأ أثناء تحميل العقارات. يرجى المحاولة مرة أخرى.'}
						dismissible={true}
					/>
				</div>

				{#if errorInfo.details}
					<div class="mb-4 rounded-md bg-gray-50 p-4 dark:bg-gray-700">
						<h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">تفاصيل الخطأ:</h4>
						<code class="block text-sm whitespace-pre-wrap text-gray-600 dark:text-gray-400">
							{errorInfo.details}
						</code>
					</div>
				{/if}

				{#if errorInfo.suggestions && errorInfo.suggestions.length > 0}
					<div class="mb-4">
						<h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">اقتراحات:</h4>
						<ul class="list-inside list-disc text-sm text-gray-600 dark:text-gray-400">
							{#each errorInfo.suggestions as suggestion}
								<li>{suggestion}</li>
							{/each}
						</ul>
					</div>
				{/if}

				<div class="flex justify-end gap-3">
					<Button variant="outline" on:click={handleFilterReset}>إعادة تعيين الفلاتر</Button>
					<Button variant="primary" on:click={retryWithBackoff}>إعادة المحاولة</Button>
				</div>
			</Card>
		{:else if properties.length === 0}
			<!-- Empty state -->
			<Card variant="default" padding="lg" class="py-12 text-center">
				<div class="flex flex-col items-center justify-center">
					<Icon name="home" customClass="h-16 w-16 text-gray-400 mb-4" />
					<h3 class="text-lg font-medium text-gray-900 dark:text-white">
						لم يتم العثور على عقارات
					</h3>
					<p class="mt-2 text-gray-600 dark:text-gray-400">
						لم يتم العثور على أي عقارات تطابق معايير البحث.
					</p>
					<Button variant="primary" class="mt-4" on:click={handleFilterReset}>
						إعادة تعيين الفلاتر
					</Button>
				</div>
			</Card>
		{:else}
			<!-- Properties Grid/List View -->
			{#if activeView === 'grid'}
				<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
					{#each properties as property (property.id)}
						<Card
							variant="elevated"
							hover={true}
							padding="none"
							clickable={true}
							on:click={() => handlePropertySelect({ detail: { property } })}
						>
							<PropertyCard {property} />
						</Card>
					{/each}
				</div>
			{:else}
				<div class="space-y-4">
					{#each properties as property (property.id)}
						<Card
							variant="elevated"
							horizontal={true}
							hover={true}
							clickable={true}
							on:click={() => handlePropertySelect({ detail: { property } })}
						>
							<!-- Image slot -->
							<div slot="image" class="h-full w-48">
								<img
									src={property.main_image_url || '/images/placeholder-property.jpg'}
									alt={property.title}
									class="h-full w-full object-cover"
								/>
							</div>

							<!-- Content -->
							<div class="flex-1 p-4">
								<div class="mb-2 flex items-start justify-between">
									<div>
										<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
											{property.title}
										</h3>
										<p class="text-sm text-gray-600 dark:text-gray-300">
											{property.district}, {property.city}
										</p>
									</div>
									<span class="font-bold text-green-600 dark:text-green-400">
										{property.estimated_value?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')} ريال
									</span>
								</div>

								<div class="mb-3 flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-300">
									{#if property.area}
										<div class="flex items-center">
											<Icon name="layout" customClass="mr-1 h-4 w-4" />
											<span>{property.area} م²</span>
										</div>
									{/if}

									{#if property.bedrooms !== undefined && property.bedrooms !== null}
										<div class="flex items-center">
											<Icon name="bed" customClass="mr-1 h-4 w-4" />
											<span>{property.bedrooms} غرف</span>
										</div>
									{/if}

									{#if property.bathrooms !== undefined && property.bathrooms !== null}
										<div class="flex items-center">
											<Icon name="droplet" customClass="mr-1 h-4 w-4" />
											<span>{property.bathrooms} حمامات</span>
										</div>
									{/if}
								</div>

								{#if property.description}
									<p class="mb-3 line-clamp-2 text-sm text-gray-600 dark:text-gray-300">
										{property.description}
									</p>
								{/if}

								<div class="flex flex-wrap gap-2">
									<span
										class="rounded-full px-2 py-1 text-xs font-medium
										{property.status === 'active'
											? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
											: property.status === 'sold'
												? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
												: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}"
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
															: property.status}
									</span>

									{#if property.is_verified}
										<span
											class="rounded-full bg-teal-100 px-2 py-1 text-xs font-medium text-teal-800 dark:bg-teal-900 dark:text-teal-200"
										>
											موثق
										</span>
									{/if}
								</div>
							</div>
						</Card>
					{/each}
				</div>
			{/if}

			<!-- Pagination -->
			{#if totalPages > 1}
				<div class="mt-8">
					<Pagination
						{currentPage}
						{totalPages}
						{totalItems}
						{pageSize}
						maxPageNumbers={5}
						showPageSize={true}
						on:pageChange={handlePageChange}
						on:pageSizeChange={handlePageSizeChange}
					/>
				</div>
			{/if}
		{/if}
	</div>
</div>
