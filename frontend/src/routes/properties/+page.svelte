<script>
	import { onMount } from 'svelte';
	import {
		properties,
		propertiesCount,
		loadingProperties,
		propertyError
	} from '$lib/stores/properties';
	import { fetchProperties } from '$lib/stores/properties';
	import { addToast } from '$lib/stores/ui';

	// Define propertyTypes here
	const propertyTypes = [
		{ value: 'residential', label: 'سكني' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'land', label: 'أرض' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'mixed_use', label: 'متعدد الاستخدام' }
	];

	const cities = [
		'الرياض',
		'جدة',
		'مكة المكرمة',
		'المدينة المنورة',
		'الدمام',
		'الخبر',
		'جازان',
		'حائل',
		'تبوك',
		'أبها'
	];

	const bedOptions = ['1', '2', '3', '4', '5+'];
	const bathOptions = ['1', '2', '3', '4+'];

	let currentPage = 1;
	let pageSize = 9;

	// Use propertiesCount store instead of local totalCount
	$: totalCount = $propertiesCount;

	// Filter state
	let filters = {
		property_type: '',
		city: '',
		min_price: '',
		max_price: '',
		bedrooms: '',
		bathrooms: '',
		keyword: ''
	};

	// Inside the loadProperties function
	async function loadProperties() {
		try {
			const queryParams = {
				page: currentPage,
				page_size: pageSize,
				property_type: filters.property_type,
				city: filters.city,
				min_market_value: filters.min_price,
				max_market_value: filters.max_price,
				bedrooms: filters.bedrooms,
				bathrooms: filters.bathrooms,
				search: filters.keyword
			};

			console.log('Loading properties with params:', queryParams);

			await fetchProperties(queryParams);

			if ($properties && $properties.length === 0) {
				addToast('لم يتم العثور على عقارات', 'warning');
			}
		} catch (error) {
			console.error('Error loading properties:', error);

			let errorMessage = 'حدث خطأ أثناء تحميل العقارات';

			if (error.message.includes('Authentication required')) {
				errorMessage = 'يرجى تسجيل الدخول لعرض العقارات';
			} else if (error.message.includes('Server error')) {
				errorMessage = 'حدث خطأ في الخادم. يرجى المحاولة مرة أخرى لاحقاً';
			}

			addToast(errorMessage, 'error');
			properties.set([]);
		}
	}

	function handleSearch() {
		currentPage = 1;
		loadProperties();
	}

	function resetFilters() {
		filters = {
			property_type: '',
			city: '',
			min_price: '',
			max_price: '',
			bedrooms: '',
			bathrooms: '',
			keyword: ''
		};
		currentPage = 1;
		loadProperties();
	}

	function handlePageChange(newPage) {
		currentPage = newPage;
		loadProperties();
	}

	onMount(() => {
		loadProperties();
	});
</script>

<div>
	<!-- Rest of your existing code -->
	<div class="lg:col-span-3">
		{#if $loadingProperties}
			<div class="flex h-64 items-center justify-center">
				<div class="text-center">
					<i class="fas fa-spinner fa-spin mb-4 text-3xl text-blue-600"></i>
					<p class="text-slate-500">جاري تحميل العقارات...</p>
				</div>
			</div>
		{:else if $propertyError}
			<div class="flex items-start rounded-lg border border-red-200 bg-red-50 p-4">
				<i class="fas fa-exclamation-circle mt-0.5 ml-3 text-red-500"></i>
				<div>
					<h3 class="font-medium text-red-800">حدث خطأ</h3>
					<p class="mt-1 text-sm text-red-700">{$propertyError}</p>
					<button
						on:click={loadProperties}
						class="mt-2 text-sm font-medium text-red-700 hover:underline"
					>
						إعادة المحاولة
					</button>
				</div>
			</div>
		{:else if $properties.length === 0}
			<div class="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
				<i class="fas fa-home mb-4 text-4xl text-slate-400"></i>
				<h3 class="text-xl font-medium text-slate-700">لم يتم العثور على عقارات</h3>
				<p class="mt-2 text-slate-500">جرب تغيير معايير البحث أو إعادة تعيين الفلاتر</p>
				<button on:click={resetFilters} class="btn-secondary mt-4">
					<i class="fas fa-undo ml-1"></i>
					إعادة تعيين الفلاتر
				</button>
			</div>
		{:else}
			<!-- Existing properties grid -->
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each $properties as property}
					<!-- Your existing property card HTML -->
				{/each}
			</div>

			<!-- Pagination -->
			{#if totalCount > pageSize}
				<div class="mt-8 flex justify-center">
					<nav class="inline-flex rounded-md shadow">
						<button
							class="rounded-r-md border border-slate-300 bg-white px-3 py-2 text-slate-700 hover:bg-slate-50 {currentPage ===
							1
								? 'cursor-not-allowed opacity-50'
								: ''}"
							disabled={currentPage === 1}
							on:click={() => handlePageChange(currentPage - 1)}
						>
							<i class="fas fa-chevron-right"></i>
						</button>

						{#each Array(Math.ceil(totalCount / pageSize)) as _, i}
							{#if i === 0 || i === Math.ceil(totalCount / pageSize) - 1 || (i >= currentPage - 2 && i <= currentPage + 2)}
								<button
									class="border-t border-b border-slate-300 bg-white px-4 py-2 {i + 1 ===
									currentPage
										? 'z-10 border-blue-600 text-blue-600'
										: 'text-slate-700 hover:bg-slate-50'}"
									on:click={() => handlePageChange(i + 1)}
								>
									{i + 1}
								</button>
							{:else if (i === 1 && currentPage > 3) || (i === Math.ceil(totalCount / pageSize) - 2 && currentPage < Math.ceil(totalCount / pageSize) - 3)}
								<span class="border-t border-b border-slate-300 bg-white px-3 py-2 text-slate-700"
									>...</span
								>
							{/if}
						{/each}

						<button
							class="rounded-l-md border border-slate-300 bg-white px-3 py-2 text-slate-700 hover:bg-slate-50 {currentPage ===
							Math.ceil(totalCount / pageSize)
								? 'cursor-not-allowed opacity-50'
								: ''}"
							disabled={currentPage === Math.ceil(totalCount / pageSize)}
							on:click={() => handlePageChange(currentPage + 1)}
						>
							<i class="fas fa-chevron-left"></i>
						</button>
					</nav>
				</div>
			{/if}
		{/if}
	</div>
</div>
