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
	import { fade, fly } from 'svelte/transition';

	// Property type options with icons
	const propertyTypes = [
		{ value: 'residential', label: 'سكني', icon: 'home' },
		{ value: 'commercial', label: 'تجاري', icon: 'store' },
		{ value: 'land', label: 'أرض', icon: 'map' },
		{ value: 'industrial', label: 'صناعي', icon: 'industry' },
		{ value: 'mixed_use', label: 'متعدد الاستخدام', icon: 'building' }
	];

	// Pagination state
	let currentPage = 1;
	let pageSize = 12; // Increased for better grid layout

	// Filter state with default values
	let filters = {
		property_type: '',
		city: '',
		min_price: '',
		max_price: '',
		bedrooms: '',
		bathrooms: '',
		keyword: ''
	};

	// UI State
	let isFiltersPanelOpen = false;
	let searchTimer;
	let sortBy = 'newest';

	// Load properties with current filters
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
				search: filters.keyword,
				ordering: getSortOrder(sortBy)
			};

			await fetchProperties(queryParams);
		} catch (error) {
			console.error('Error loading properties:', error);
		}
	}

	function getSortOrder(sort) {
		switch (sort) {
			case 'price_low':
				return 'market_value';
			case 'price_high':
				return '-market_value';
			case 'newest':
				return '-created_at';
			case 'oldest':
				return 'created_at';
			default:
				return '-created_at';
		}
	}

	// Reset all filters
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

	// Handle search with debounce
	function handleSearch() {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			currentPage = 1;
			loadProperties();
		}, 300); // Reduced debounce time for better responsiveness
	}

	// Handle page change
	function handlePageChange(newPage) {
		currentPage = newPage;
		loadProperties();
		// Smooth scroll to top
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	// Format price with proper spacing
	function formatPrice(price) {
		return new Intl.NumberFormat('ar-SA', {
			style: 'decimal',
			maximumFractionDigits: 0
		}).format(price);
	}

	// Handle sort change
	function handleSortChange() {
		currentPage = 1;
		loadProperties();
	}

	onMount(() => {
		loadProperties();
	});
</script>

<svelte:head>
	<title>العقارات | منصة المزادات العقارية</title>
	<meta
		name="description"
		content="استعرض أحدث العقارات المتاحة للبيع والمزاد في منصة المزادات العقارية"
	/>
</svelte:head>

<div class="min-h-screen bg-slate-50 pt-8 pb-12">
	<div class="container mx-auto px-4">
		<!-- Page Header -->
		<div class="mb-8 text-center">
			<h1 class="text-4xl font-bold text-slate-900">العقارات المتاحة</h1>
			<p class="mt-3 text-lg text-slate-600">اكتشف مجموعة متنوعة من العقارات المميزة</p>
		</div>

		<!-- Search and Sort Bar -->
		<div
			class="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-xl bg-white p-4 shadow-sm"
		>
			<!-- Search Input -->
			<div class="relative flex-1">
				<input
					type="text"
					bind:value={filters.keyword}
					on:input={handleSearch}
					class="w-full rounded-lg border-2 border-slate-200 bg-slate-50 py-3 pr-12 text-slate-900 placeholder-slate-400 transition-colors focus:border-blue-500 focus:outline-none"
					placeholder="ابحث عن عقار..."
				/>
				<i class="fas fa-search absolute top-1/2 right-4 -translate-y-1/2 text-slate-400"></i>
			</div>

			<!-- Sort Dropdown -->
			<div class="flex items-center gap-4">
				<select
					bind:value={sortBy}
					on:change={handleSortChange}
					class="rounded-lg border-2 border-slate-200 bg-slate-50 px-4 py-3 text-slate-700"
				>
					<option value="newest">الأحدث</option>
					<option value="price_low">السعر: الأقل إلى الأعلى</option>
					<option value="price_high">السعر: الأعلى إلى الأقل</option>
				</select>

				<!-- Filters Toggle Button -->
				<button
					class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-white transition hover:bg-blue-700"
					on:click={() => (isFiltersPanelOpen = !isFiltersPanelOpen)}
				>
					<i class="fas fa-filter"></i>
					<span>الفلاتر</span>
				</button>
			</div>
		</div>

		<!-- Filters Panel -->
		{#if isFiltersPanelOpen}
			<div
				class="mb-6 rounded-xl bg-white p-6 shadow-sm"
				transition:fly={{ y: -20, duration: 200 }}
			>
				<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
					<!-- Property Type -->
					<div>
						<label class="mb-2 block text-sm font-medium text-slate-700">نوع العقار</label>
						<div class="grid grid-cols-2 gap-2">
							{#each propertyTypes as type}
								<button
									class="flex items-center gap-2 rounded-lg border-2 p-3 text-sm transition {filters.property_type ===
									type.value
										? 'border-blue-500 bg-blue-50 text-blue-700'
										: 'border-slate-200 text-slate-600 hover:border-blue-200 hover:bg-blue-50'}"
									on:click={() => {
										filters.property_type = filters.property_type === type.value ? '' : type.value;
										loadProperties();
									}}
								>
									<i class="fas fa-{type.icon}"></i>
									<span>{type.label}</span>
								</button>
							{/each}
						</div>
					</div>

					<!-- City Input -->
					<div>
						<label class="mb-2 block text-sm font-medium text-slate-700">المدينة</label>
						<input
							type="text"
							bind:value={filters.city}
							on:input={handleSearch}
							class="w-full rounded-lg border-2 border-slate-200 p-3 text-slate-900 placeholder-slate-400 transition-colors focus:border-blue-500 focus:outline-none"
							placeholder="أدخل اسم المدينة..."
						/>
					</div>

					<!-- Price Range -->
					<div>
						<label class="mb-2 block text-sm font-medium text-slate-700">نطاق السعر</label>
						<div class="flex gap-2">
							<input
								type="number"
								bind:value={filters.min_price}
								on:change={loadProperties}
								class="w-full rounded-lg border-2 border-slate-200 p-3 text-slate-900 placeholder-slate-400"
								placeholder="من"
							/>
							<input
								type="number"
								bind:value={filters.max_price}
								on:change={loadProperties}
								class="w-full rounded-lg border-2 border-slate-200 p-3 text-slate-900 placeholder-slate-400"
								placeholder="إلى"
							/>
						</div>
					</div>

					<!-- Rooms -->
					<div>
						<label class="mb-2 block text-sm font-medium text-slate-700">الغرف</label>
						<div class="flex gap-2">
							<select
								bind:value={filters.bedrooms}
								on:change={loadProperties}
								class="w-1/2 rounded-lg border-2 border-slate-200 p-3 text-slate-900"
							>
								<option value="">غرف النوم</option>
								{#each Array(6) as _, i}
									<option value={i + 1}>{i + 1}</option>
								{/each}
								<option value="7">7+</option>
							</select>
							<select
								bind:value={filters.bathrooms}
								on:change={loadProperties}
								class="w-1/2 rounded-lg border-2 border-slate-200 p-3 text-slate-900"
							>
								<option value="">الحمامات</option>
								{#each Array(4) as _, i}
									<option value={i + 1}>{i + 1}</option>
								{/each}
								<option value="5">5+</option>
							</select>
						</div>
					</div>
				</div>

				<!-- Reset Filters -->
				<div class="mt-6 flex justify-end">
					<button
						class="flex items-center gap-2 rounded-lg bg-slate-200 px-4 py-2 text-slate-700 transition hover:bg-slate-300"
						on:click={resetFilters}
					>
						<i class="fas fa-undo"></i>
						<span>إعادة تعيين</span>
					</button>
				</div>
			</div>
		{/if}

		<!-- Properties Grid -->
		<div class="space-y-6">
			{#if $loadingProperties}
				<!-- Loading State -->
				<div class="flex min-h-[400px] items-center justify-center">
					<div class="text-center">
						<div class="mb-4 text-blue-600">
							<i class="fas fa-spinner fa-spin fa-3x"></i>
						</div>
						<p class="text-lg text-slate-600">جاري تحميل العقارات...</p>
					</div>
				</div>
			{:else if $propertyError}
				<!-- Error State -->
				<div class="rounded-xl bg-red-50 p-6 text-center">
					<div class="mb-4 text-red-500">
						<i class="fas fa-exclamation-circle fa-3x"></i>
					</div>
					<h3 class="mb-2 text-lg font-semibold text-red-700">حدث خطأ</h3>
					<p class="mb-4 text-red-600">{$propertyError}</p>
					<button
						class="rounded-lg bg-red-600 px-6 py-2 text-white transition hover:bg-red-700"
						on:click={loadProperties}
					>
						إعادة المحاولة
					</button>
				</div>
			{:else if $properties.length === 0}
				<!-- Empty State -->
				<div class="rounded-xl bg-white p-12 text-center shadow-sm">
					<div class="mb-4 text-slate-400">
						<i class="fas fa-home fa-4x"></i>
					</div>
					<h3 class="mb-2 text-xl font-semibold text-slate-900">لم يتم العثور على عقارات</h3>
					<p class="mb-6 text-slate-600">جرب تغيير معايير البحث أو إعادة تعيين الفلاتر</p>
					<button
						class="rounded-lg bg-blue-600 px-6 py-2 text-white transition hover:bg-blue-700"
						on:click={resetFilters}
					>
						إعادة تعيين الفلاتر
					</button>
				</div>
			{:else}
				<!-- Properties Grid -->
				<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
					{#each $properties as property (property.id)}
						<a
							href="/properties/{property.slug}"
							class="group relative overflow-hidden rounded-xl bg-white shadow-sm transition-all duration-300 hover:shadow-xl"
							transition:fade
						>
							<!-- Property Image -->
							<div class="relative aspect-[4/3] overflow-hidden">
								{#if property.media && property.media[0]}
									<img
										src={property.media[0].file_url}
										alt={property.title}
										class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
										loading="lazy"
									/>
								{:else}
									<div class="flex h-full items-center justify-center bg-slate-100">
										<i class="fas fa-home text-4xl text-slate-300"></i>
									</div>
								{/if}

								<!-- Status Badge -->
								<div class="absolute top-3 right-3">
									<span
										class="rounded-full px-3 py-1 text-sm font-medium {property.status ===
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
									<div class="absolute top-3 left-3">
										<span class="rounded-full bg-blue-600 px-3 py-1 text-sm text-white">
											مميز
										</span>
									</div>
								{/if}
							</div>

							<!-- Property Details -->
							<div class="p-4">
								<h3 class="mb-2 line-clamp-1 text-lg font-semibold text-slate-900">
									{property.title}
								</h3>

								<div class="mb-3 flex items-center gap-1 text-sm text-slate-600">
									<i class="fas fa-map-marker-alt"></i>
									<span class="line-clamp-1">{property.address}</span>
								</div>

								<!-- Features -->
								<div class="mb-4 grid grid-cols-3 gap-2 text-center text-sm">
									{#if property.size_sqm}
										<div class="rounded-lg bg-slate-50 p-2">
											<i class="fas fa-ruler-combined mb-1 text-blue-600"></i>
											<div class="text-slate-700">{property.size_sqm} م²</div>
										</div>
									{/if}
									{#if property.bedrooms}
										<div class="rounded-lg bg-slate-50 p-2">
											<i class="fas fa-bed mb-1 text-blue-600"></i>
											<div class="text-slate-700">{property.bedrooms} غرف</div>
										</div>
									{/if}
									{#if property.bathrooms}
										<div class="rounded-lg bg-slate-50 p-2">
											<i class="fas fa-bath mb-1 text-blue-600"></i>
											<div class="text-slate-700">{property.bathrooms} حمام</div>
										</div>
									{/if}
								</div>

								<!-- Price -->
								<div class="flex items-center justify-between border-t border-slate-100 pt-4">
									<div class="text-lg font-bold text-blue-600">
										{property.market_value
											? formatPrice(property.market_value) + ' ريال'
											: 'السعر عند الطلب'}
									</div>
									<div class="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
										{property.property_type_display}
									</div>
								</div>
							</div>
						</a>
					{/each}
				</div>

				<!-- Pagination -->
				{#if $propertiesCount > pageSize}
					<div class="mt-12 flex justify-center">
						<nav class="inline-flex items-center gap-1 rounded-lg bg-white p-2 shadow-sm">
							<button
								class="rounded px-3 py-2 text-slate-600 transition hover:bg-slate-100 disabled:opacity-50"
								disabled={currentPage === 1}
								on:click={() => handlePageChange(currentPage - 1)}
							>
								<i class="fas fa-chevron-right"></i>
							</button>

							{#each Array(Math.ceil($propertiesCount / pageSize)) as _, i}
								{#if i === 0 || i === Math.ceil($propertiesCount / pageSize) - 1 || (i >= currentPage - 2 && i <= currentPage + 2)}
									<button
										class="min-w-[40px] rounded px-3 py-2 text-sm transition {i + 1 === currentPage
											? 'bg-blue-600 text-white'
											: 'text-slate-600 hover:bg-slate-100'}"
										on:click={() => handlePageChange(i + 1)}
									>
										{i + 1}
									</button>
								{:else if (i === 1 && currentPage > 3) || (i === Math.ceil($propertiesCount / pageSize) - 2 && currentPage < Math.ceil($propertiesCount / pageSize) - 3)}
									<span class="px-2 py-2 text-slate-400">...</span>
								{/if}
							{/each}

							<button
								class="rounded px-3 py-2 text-slate-600 transition hover:bg-slate-100 disabled:opacity-50"
								disabled={currentPage === Math.ceil($propertiesCount / pageSize)}
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

<style>
	/* Additional custom styles can be added here */
	.line-clamp-1 {
		display: -webkit-box;
		-webkit-line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
