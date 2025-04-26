<!-- src/routes/properties/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { properties, loadingProperties, propertyError } from '$lib/stores/properties';
	import { fetchProperties } from '$lib/stores/properties';
	import { isAuthenticated, hasPermission } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
	import PropertyCard from '$lib/components/property/PropertyCard.svelte';

	// Filters state
	let filters = {
		property_type: '',
		city: '',
		min_price: '',
		max_price: '',
		bedrooms: '',
		bathrooms: '',
		keyword: ''
	};

	// Pagination
	let currentPage = 1;
	let pageSize = 12;
	let totalProperties = 0;

	// Sorting
	let sortBy = 'newest';

	// UI State
	let showFilters = false;
	let searchTimer;

	async function loadData() {
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
				search: filters.keyword,
				ordering: sortBy
			};

			const result = await fetchProperties(queryParams);
			totalProperties = result.count;
		} catch (error) {
			addToast('حدث خطأ أثناء تحميل العقارات', 'error');
		}
	}

	function handleSearch() {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			currentPage = 1;
			loadData();
		}, 300);
	}

	onMount(loadData);
</script>

<svelte:head>
	<title>العقارات | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
	<!-- Header with Add Button -->
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-2xl font-bold text-slate-900">العقارات المتاحة</h1>

		{#if $isAuthenticated && hasPermission('create_property')}
			<a href="/properties/add" class="btn-primary">
				<i class="fas fa-plus ml-2"></i>
				إضافة عقار جديد
			</a>
		{/if}
	</div>

	<!-- Search and Filters -->
	<div class="mb-6 rounded-xl bg-white p-4 shadow-sm">
		<div class="flex flex-wrap gap-4">
			<!-- Search Input -->
			<div class="flex-1">
				<input
					type="text"
					bind:value={filters.keyword}
					on:input={handleSearch}
					class="input"
					placeholder="ابحث عن عقار..."
				/>
			</div>

			<!-- Sort Dropdown -->
			<select bind:value={sortBy} on:change={loadData} class="input w-48">
				<option value="newest">الأحدث</option>
				<option value="price_low">السعر: الأقل إلى الأعلى</option>
				<option value="price_high">السعر: الأعلى إلى الأقل</option>
			</select>

			<!-- Filters Toggle -->
			<button class="btn-secondary" on:click={() => (showFilters = !showFilters)}>
				<i class="fas fa-filter ml-2"></i>
				الفلترة
			</button>
		</div>

		<!-- Expanded Filters -->
		{#if showFilters}
			<div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
				<!-- Filter fields -->
			</div>
		{/if}
	</div>

	<!-- Properties Grid -->
	{#if $loadingProperties}
		<div class="py-12 text-center">
			<i class="fas fa-spinner fa-spin text-3xl text-blue-600"></i>
			<p class="mt-4 text-slate-600">جاري تحميل العقارات...</p>
		</div>
	{:else if $propertyError}
		<div class="py-12 text-center">
			<i class="fas fa-exclamation-circle text-3xl text-red-500"></i>
			<p class="mt-4 text-red-600">{$propertyError}</p>
			<button class="btn-primary mt-4" on:click={loadData}> إعادة المحاولة </button>
		</div>
	{:else if $properties.length === 0}
		<div class="py-12 text-center">
			<i class="fas fa-home text-3xl text-slate-400"></i>
			<p class="mt-4 text-slate-600">لم يتم العثور على عقارات</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
			{#each $properties as property (property.id)}
				<PropertyCard {property} />
			{/each}
		</div>

		<!-- Pagination -->
		{#if totalProperties > pageSize}
			<div class="mt-8 flex justify-center">
				<!-- Pagination buttons -->
			</div>
		{/if}
	{/if}
</div>
