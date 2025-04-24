<!-- src/routes/properties/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { fetchProperties } from '$lib/services/properties';

	let properties = [];
	let loading = true;
	let error = null;
	let totalCount = 0;
	let currentPage = 1;
	let pageSize = 9;

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

	// Available filter options
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

	async function loadProperties() {
		loading = true;
		error = null;

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

			const data = await fetchProperties(queryParams);
			properties = data.results || [];
			totalCount = data.count || 0;
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء تحميل العقارات';
			console.error(error);
			properties = [];
		} finally {
			loading = false;
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

		// Scroll to top of the results
		window.scrollTo({
			top: 0,
			behavior: 'smooth'
		});
	}

	onMount(() => {
		loadProperties();
	});
</script>

<svelte:head>
	<title>العقارات | منصة المزادات العقارية</title>
</svelte:head>

<div>
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-2xl font-bold text-slate-900">العقارات</h1>
		<a href="/properties/add" class="btn-primary">
			<i class="fas fa-plus ml-2"></i>
			إضافة عقار جديد
		</a>
	</div>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-4">
		<!-- Filters Sidebar -->
		<div class="rounded-lg bg-white p-4 shadow">
			<h2 class="mb-4 text-lg font-medium">تصفية النتائج</h2>

			<form on:submit|preventDefault={handleSearch} class="space-y-4">
				<!-- Search Keyword -->
				<div>
					<label for="keyword" class="mb-1 block text-sm font-medium text-slate-700"
						>كلمة البحث</label
					>
					<div class="relative">
						<input
							type="text"
							id="keyword"
							bind:value={filters.keyword}
							class="input pl-10"
							placeholder="ابحث عن عقار..."
						/>
						<div class="absolute top-2.5 left-3 text-slate-400">
							<i class="fas fa-search"></i>
						</div>
					</div>
				</div>

				<!-- Property Type -->
				<div>
					<label for="property_type" class="mb-1 block text-sm font-medium text-slate-700"
						>نوع العقار</label
					>
					<select id="property_type" bind:value={filters.property_type} class="input">
						<option value="">جميع الأنواع</option>
						{#each propertyTypes as type}
							<option value={type.value}>{type.label}</option>
						{/each}
					</select>
				</div>

				<!-- City -->
				<div>
					<label for="city" class="mb-1 block text-sm font-medium text-slate-700">المدينة</label>
					<select id="city" bind:value={filters.city} class="input">
						<option value="">جميع المدن</option>
						{#each cities as city}
							<option value={city}>{city}</option>
						{/each}
					</select>
				</div>

				<!-- Price Range -->
				<div>
					<label class="mb-1 block text-sm font-medium text-slate-700">نطاق السعر</label>
					<div class="grid grid-cols-2 gap-2">
						<input
							type="number"
							bind:value={filters.min_price}
							class="input"
							placeholder="الحد الأدنى"
						/>
						<input
							type="number"
							bind:value={filters.max_price}
							class="input"
							placeholder="الحد الأقصى"
						/>
					</div>
				</div>

				<!-- Bedrooms & Bathrooms -->
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label for="bedrooms" class="mb-1 block text-sm font-medium text-slate-700"
							>غرف النوم</label
						>
						<select id="bedrooms" bind:value={filters.bedrooms} class="input">
							<option value="">الكل</option>
							{#each bedOptions as bed}
								<option value={bed}>{bed}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="bathrooms" class="mb-1 block text-sm font-medium text-slate-700"
							>الحمامات</label
						>
						<select id="bathrooms" bind:value={filters.bathrooms} class="input">
							<option value="">الكل</option>
							{#each bathOptions as bath}
								<option value={bath}>{bath}</option>
							{/each}
						</select>
					</div>
				</div>

				<div class="flex justify-between pt-2">
					<button type="button" on:click={resetFilters} class="btn-secondary">
						<i class="fas fa-undo ml-1"></i>
						إعادة تعيين
					</button>
					<button type="submit" class="btn-primary">
						<i class="fas fa-filter ml-1"></i>
						تصفية
					</button>
				</div>
			</form>
		</div>

		<!-- Property Listings -->
		<div class="lg:col-span-3">
			{#if loading}
				<div class="flex h-64 items-center justify-center">
					<div class="text-center">
						<i class="fas fa-spinner fa-spin mb-4 text-3xl text-blue-600"></i>
						<p class="text-slate-500">جاري تحميل العقارات...</p>
					</div>
				</div>
			{:else if error}
				<div class="flex items-start rounded-lg border border-red-200 bg-red-50 p-4">
					<i class="fas fa-exclamation-circle mt-0.5 ml-3 text-red-500"></i>
					<div>
						<h3 class="font-medium text-red-800">حدث خطأ</h3>
						<p class="mt-1 text-sm text-red-700">{error}</p>
						<button
							on:click={loadProperties}
							class="mt-2 text-sm font-medium text-red-700 hover:underline"
						>
							إعادة المحاولة
						</button>
					</div>
				</div>
			{:else if properties.length === 0}
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
				<div class="mb-4">
					<p class="text-slate-500">
						تم العثور على <span class="font-medium text-slate-700">{totalCount}</span> عقار
					</p>
				</div>

				<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each properties as property}
						<a
							href={`/properties/${property.slug}`}
							class="block overflow-hidden rounded-lg bg-white shadow transition-transform hover:-translate-y-1 hover:shadow-md"
						>
							<div class="relative h-48 overflow-hidden">
								<img
									src={(property.media && property.media[0]?.file_url) ||
										'/images/property-placeholder.jpg'}
									alt={property.title}
									class="h-full w-full object-cover"
								/>

								<div class="absolute top-2 right-2">
									<span
										class="bg-opacity-80 inline-flex items-center rounded px-2 py-1 text-xs font-medium {property.status ===
										'available'
											? 'bg-green-100 text-green-800'
											: property.status === 'auction'
												? 'bg-amber-100 text-amber-800'
												: 'bg-slate-100 text-slate-800'}"
									>
										{property.status_display}
									</span>
								</div>

								{#if property.is_featured}
									<div class="absolute top-2 left-2">
										<span
											class="bg-opacity-80 inline-flex items-center rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800"
										>
											<i class="fas fa-star ml-1"></i>
											مميز
										</span>
									</div>
								{/if}
							</div>

							<div class="p-4">
								<div class="flex items-start justify-between">
									<h3 class="mb-1 flex-1 font-bold text-slate-900">{property.title}</h3>
									<span class="font-bold whitespace-nowrap text-blue-600">
										{#if property.market_value}
											{property.market_value.toLocaleString()} ريال
										{:else}
											السعر عند الطلب
										{/if}
									</span>
								</div>

								<p class="mb-3 flex items-center text-sm text-slate-500">
									<i class="fas fa-map-marker-alt ml-1"></i>
									{property.city}, {property.address}
								</p>

								<div class="flex gap-3 border-t pt-3">
									{#if property.size_sqm}
										<div class="flex items-center text-sm text-slate-700">
											<i class="fas fa-ruler-combined ml-1"></i>
											{property.size_sqm} م²
										</div>
									{/if}

									{#if property.bedrooms}
										<div class="flex items-center text-sm text-slate-700">
											<i class="fas fa-bed ml-1"></i>
											{property.bedrooms} غرف
										</div>
									{/if}

									{#if property.bathrooms}
										<div class="flex items-center text-sm text-slate-700">
											<i class="fas fa-bath ml-1"></i>
											{property.bathrooms} حمامات
										</div>
									{/if}
								</div>
							</div>
						</a>
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
</div>
