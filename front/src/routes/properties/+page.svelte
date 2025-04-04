<!-- src/routes/properties/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { propertiesStore } from '$lib/stores/properties';
	import { isAuthenticated, hasRole } from '$lib/stores/auth';
	import { uiStore } from '$lib/stores/ui';
	import PropertyCard from '$lib/components/properties/PropertyCard.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import FilterBar from '$lib/components/properties/FilterBar.svelte';
	import SearchBar from '$lib/components/common/SearchBar.svelte';

	// Properties state
	let properties = [];
	let isLoading = true;
	let error = null;
	let currentPage = 1;
	let totalPages = 1;
	let totalResults = 0;
	let pageSize = 12;

	// Filter state
	let filters = {
		property_type: '',
		city: '',
		min_price: '',
		max_price: '',
		status: 'active' // Default to active properties
	};

	// Search state
	let searchQuery = '';

	// Cities list for filters - matching backend options
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

	// Property types matching backend
	const propertyTypes = [
		{ value: 'apartment', label: 'شقة' },
		{ value: 'villa', label: 'فيلا' },
		{ value: 'land', label: 'أرض' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'building', label: 'مبنى' },
		{ value: 'farm', label: 'مزرعة' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'office', label: 'مكتب' },
		{ value: 'retail', label: 'محل تجاري' },
		{ value: 'mixed_use', label: 'متعدد الاستخدامات' }
	];

	// Property statuses matching backend
	const propertyStatuses = [
		{ value: 'active', label: 'نشط' },
		{ value: 'sold', label: 'مباع' },
		{ value: 'pending_approval', label: 'قيد الموافقة' },
		{ value: 'under_contract', label: 'تحت التعاقد' },
		{ value: 'inactive', label: 'غير نشط' }
	];

	// Load properties with filters and pagination
	async function loadProperties() {
		isLoading = true;
		error = null;

		try {
			uiStore.startLoading('جاري تحميل العقارات...');

			// Build query params for backend API
			const queryParams = {
				page: currentPage,
				page_size: pageSize,
				search: searchQuery,
				...filters
			};

			// Filter out empty values
			Object.keys(queryParams).forEach((key) => {
				if (!queryParams[key]) delete queryParams[key];
			});

			// Load properties from store
			const result = await propertiesStore.loadProperties(queryParams);

			properties = result.results;
			totalPages = result.total_pages;
			totalResults = result.count;

			// Process JSON fields for each property
			properties = properties.map((property) => ({
				...property,
				images: typeof property.images === 'string' ? JSON.parse(property.images) : property.images,
				features:
					typeof property.features === 'string' ? JSON.parse(property.features) : property.features,
				amenities:
					typeof property.amenities === 'string'
						? JSON.parse(property.amenities)
						: property.amenities
			}));

			uiStore.stopLoading();
		} catch (err) {
			error = err;
			uiStore.stopLoading();
			uiStore.addToast('حدث خطأ أثناء تحميل العقارات. يرجى المحاولة مرة أخرى.', 'error');
		} finally {
			isLoading = false;
		}
	}

	// Handle page change from pagination component
	function handlePageChange(event) {
		currentPage = event.detail.page;
		loadProperties();
	}

	// Handle filter changes
	function handleFilterChange(event) {
		filters = { ...filters, ...event.detail };
		currentPage = 1; // Reset to first page when filters change
		loadProperties();
	}

	// Handle search
	function handleSearch(event) {
		searchQuery = event.detail;
		currentPage = 1; // Reset to first page when search changes
		loadProperties();
	}

	// Handle filter reset
	function handleResetFilters() {
		filters = {
			property_type: '',
			city: '',
			min_price: '',
			max_price: '',
			status: 'active'
		};
		searchQuery = '';
		currentPage = 1;
		loadProperties();
	}

	// Add property button clicked
	function handleAddProperty() {
		goto('/properties/add');
	}

	// Initialize component
	onMount(() => {
		loadProperties();
	});
</script>

<svelte:head>
	<title>استعراض العقارات | نظام المزادات العقارية</title>
	<meta
		name="description"
		content="استعراض العقارات المتاحة للبيع والمزاد في منصة المزادات العقارية"
	/>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<div class="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">العقارات</h1>
			<p class="mt-2 text-gray-600 dark:text-gray-400">استعراض العقارات المتاحة في النظام</p>
		</div>

		<!-- Add property button - only for authenticated users with seller, agent, or admin roles -->
		{#if $isAuthenticated && ($hasRole('seller') || $hasRole('agent') || $hasRole('admin'))}
			<Button on:click={handleAddProperty} variant="solid" color="primary">إضافة عقار جديد</Button>
		{/if}
	</div>

	<!-- Search and filters section -->
	<div class="mb-8 rounded-lg bg-white p-4 shadow dark:bg-gray-800">
		<div class="mb-4">
			<SearchBar
				placeholder="ابحث عن عقار بالعنوان أو الحي أو الوصف..."
				value={searchQuery}
				on:search={handleSearch}
			/>
		</div>

		<FilterBar
			{cities}
			{propertyTypes}
			{propertyStatuses}
			{filters}
			on:filter={handleFilterChange}
			on:reset={handleResetFilters}
		/>
	</div>

	<!-- Results count and sorting -->
	{#if !isLoading && !error}
		<div class="mb-4 flex flex-wrap items-center justify-between gap-4">
			<div class="text-gray-600 dark:text-gray-400">
				{totalResults} نتيجة
			</div>
		</div>
	{/if}

	<!-- Properties grid -->
	{#if isLoading}
		<div class="flex min-h-[50vh] items-center justify-center">
			<Loader size="lg" />
		</div>
	{:else if error}
		<Alert
			type="error"
			title="خطأ في تحميل العقارات"
			message={error.message || 'حدث خطأ أثناء تحميل العقارات. يرجى المحاولة مرة أخرى.'}
		/>
	{:else if properties.length === 0}
		<Alert
			type="info"
			title="لا توجد عقارات"
			message="لا توجد عقارات متاحة تطابق معايير البحث. يرجى تغيير معايير البحث أو المحاولة مرة أخرى."
		/>
	{:else}
		<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
			{#each properties as property (property.id)}
				<PropertyCard {property} />
			{/each}
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="mt-8 flex justify-center">
				<Pagination {currentPage} {totalPages} on:pageChange={handlePageChange} />
			</div>
		{/if}
	{/if}
</div>
