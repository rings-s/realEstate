<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let showFilters = false;
	export let activeFilters = {};
	export let propertyTypes = [
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
	export let propertyStatus = [
		{ value: 'active', label: 'نشط' },
		{ value: 'pending_approval', label: 'قيد الموافقة' },
		{ value: 'under_contract', label: 'تحت التعاقد' },
		{ value: 'sold', label: 'مباع' },
		{ value: 'inactive', label: 'غير نشط' }
	];
	export let cities = [];
	export let priceRange = { min: 0, max: 10000000 };
	export let areaRange = { min: 0, max: 10000 };
	export let isCompact = false;

	// State
	let selectedPropertyTypes = [];
	let selectedPropertyStatus = [];
	let selectedCity = '';
	let selectedDistrict = '';
	let bedroomsFilter = '';
	let bathroomsFilter = '';
	let minPrice = 0;
	let maxPrice = 0;
	let minArea = 0;
	let maxArea = 0;
	let searchQuery = '';
	let orderBy = 'created_at';
	let orderDirection = 'desc';

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Initialize from activeFilters
	$: {
		if (activeFilters.property_type) {
			selectedPropertyTypes = Array.isArray(activeFilters.property_type)
				? activeFilters.property_type
				: [activeFilters.property_type];
		}

		if (activeFilters.status) {
			selectedPropertyStatus = Array.isArray(activeFilters.status)
				? activeFilters.status
				: [activeFilters.status];
		}

		selectedCity = activeFilters.city || '';
		selectedDistrict = activeFilters.district || '';
		bedroomsFilter = activeFilters.bedrooms || '';
		bathroomsFilter = activeFilters.bathrooms || '';
		minPrice = activeFilters.min_price || priceRange.min;
		maxPrice = activeFilters.max_price || priceRange.max;
		minArea = activeFilters.min_area || areaRange.min;
		maxArea = activeFilters.max_area || areaRange.max;
		searchQuery = activeFilters.search || '';

		if (activeFilters.ordering) {
			// Split ordering field into field and direction
			const ordering = activeFilters.ordering;
			orderDirection = ordering.startsWith('-') ? 'desc' : 'asc';
			orderBy = ordering.startsWith('-') ? ordering.substring(1) : ordering;
		}
	}

	// Toggle property type selection
	function togglePropertyType(type) {
		if (selectedPropertyTypes.includes(type)) {
			selectedPropertyTypes = selectedPropertyTypes.filter((t) => t !== type);
		} else {
			selectedPropertyTypes = [...selectedPropertyTypes, type];
		}
	}

	// Toggle property status selection
	function togglePropertyStatus(status) {
		if (selectedPropertyStatus.includes(status)) {
			selectedPropertyStatus = selectedPropertyStatus.filter((s) => s !== status);
		} else {
			selectedPropertyStatus = [...selectedPropertyStatus, status];
		}
	}

	// Apply filters
	function applyFilters() {
		const filters = {
			...(selectedPropertyTypes.length > 0 && { property_type: selectedPropertyTypes }),
			...(selectedPropertyStatus.length > 0 && { status: selectedPropertyStatus }),
			...(selectedCity && { city: selectedCity }),
			...(selectedDistrict && { district: selectedDistrict }),
			...(bedroomsFilter && { bedrooms: bedroomsFilter }),
			...(bathroomsFilter && { bathrooms: bathroomsFilter }),
			...(minPrice > priceRange.min && { min_price: minPrice }),
			...(maxPrice < priceRange.max && { max_price: maxPrice }),
			...(minArea > areaRange.min && { min_area: minArea }),
			...(maxArea < areaRange.max && { max_area: maxArea }),
			...(searchQuery && { search: searchQuery }),
			...(orderBy && { ordering: (orderDirection === 'desc' ? '-' : '') + orderBy })
		};

		dispatch('filter', filters);
	}

	// Reset filters
	function resetFilters() {
		selectedPropertyTypes = [];
		selectedPropertyStatus = [];
		selectedCity = '';
		selectedDistrict = '';
		bedroomsFilter = '';
		bathroomsFilter = '';
		minPrice = priceRange.min;
		maxPrice = priceRange.max;
		minArea = areaRange.min;
		maxArea = areaRange.max;
		searchQuery = '';
		orderBy = 'created_at';
		orderDirection = 'desc';

		dispatch('reset');
	}

	// Format price display
	function formatPrice(price) {
		return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
	}

	// Toggle filters visibility
	function toggleFilters() {
		showFilters = !showFilters;
		dispatch('toggleFilters', { showFilters });
	}
</script>

<div class="overflow-hidden rounded-lg bg-white shadow-md dark:bg-gray-800">
	<!-- Search and Toggle -->
	<div class="flex flex-wrap items-center gap-3 border-b border-gray-200 p-4 dark:border-gray-700">
		<!-- Search Bar -->
		<div class="min-w-[200px] flex-1">
			<div class="relative">
				<input
					type="text"
					class="w-full rounded-md border border-gray-300 bg-white py-2 pr-10 pl-4 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
					placeholder="البحث عن عقار..."
					bind:value={searchQuery}
					on:keyup={(e) => e.key === 'Enter' && applyFilters()}
				/>
				<div class="absolute inset-y-0 right-0 flex items-center pr-3">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 text-gray-400"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</div>
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="flex gap-2">
			<button
				class="rounded-md border border-blue-600 px-4 py-2 text-blue-600 transition hover:bg-blue-50 dark:border-blue-500 dark:text-blue-400 dark:hover:bg-gray-700"
				on:click={applyFilters}
			>
				تطبيق
			</button>

			<button
				class="flex items-center gap-1 rounded-md px-3 py-2 text-gray-600 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
				on:click={toggleFilters}
			>
				<span>الفلاتر</span>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
					/>
				</svg>
			</button>
		</div>
	</div>

	{#if showFilters}
		<div class="p-4 {isCompact ? 'max-h-96 overflow-y-auto' : ''}">
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
				<!-- Property Type -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">نوع العقار</h3>
					<div class="max-h-40 space-y-1 overflow-y-auto pr-2">
						{#each propertyTypes as type}
							<label class="flex items-center">
								<input
									type="checkbox"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:text-blue-500"
									checked={selectedPropertyTypes.includes(type.value)}
									on:change={() => togglePropertyType(type.value)}
								/>
								<span class="mr-2 text-sm text-gray-700 dark:text-gray-300">{type.label}</span>
							</label>
						{/each}
					</div>
				</div>

				<!-- Property Status -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">حالة العقار</h3>
					<div class="space-y-1">
						{#each propertyStatus as status}
							<label class="flex items-center">
								<input
									type="checkbox"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:text-blue-500"
									checked={selectedPropertyStatus.includes(status.value)}
									on:change={() => togglePropertyStatus(status.value)}
								/>
								<span class="mr-2 text-sm text-gray-700 dark:text-gray-300">{status.label}</span>
							</label>
						{/each}
					</div>
				</div>

				<!-- Location -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">الموقع</h3>
					<div class="space-y-2">
						<select
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
							bind:value={selectedCity}
						>
							<option value="">اختر المدينة</option>
							{#each cities as city}
								<option value={city.value || city}>{city.label || city}</option>
							{/each}
						</select>

						<input
							type="text"
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
							placeholder="الحي"
							bind:value={selectedDistrict}
						/>
					</div>
				</div>

				<!-- Bedrooms & Bathrooms -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">الغرف</h3>
					<div class="grid grid-cols-2 gap-2">
						<div>
							<label class="mb-1 block text-xs text-gray-500 dark:text-gray-400">غرف النوم</label>
							<select
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={bedroomsFilter}
							>
								<option value="">الكل</option>
								<option value="1">1+</option>
								<option value="2">2+</option>
								<option value="3">3+</option>
								<option value="4">4+</option>
								<option value="5">5+</option>
							</select>
						</div>

						<div>
							<label class="mb-1 block text-xs text-gray-500 dark:text-gray-400">الحمامات</label>
							<select
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={bathroomsFilter}
							>
								<option value="">الكل</option>
								<option value="1">1+</option>
								<option value="2">2+</option>
								<option value="3">3+</option>
								<option value="4">4+</option>
							</select>
						</div>
					</div>
				</div>

				<!-- Price Range -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">نطاق السعر</h3>
					<div class="space-y-2">
						<div class="flex items-center gap-2">
							<input
								type="number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="السعر الأدنى"
								bind:value={minPrice}
								min={priceRange.min}
								max={maxPrice}
							/>
							<span class="text-gray-500 dark:text-gray-400">-</span>
							<input
								type="number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="السعر الأعلى"
								bind:value={maxPrice}
								min={minPrice}
								max={priceRange.max}
							/>
						</div>
						<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
							<span>{formatPrice(minPrice)} ريال</span>
							<span>{formatPrice(maxPrice)} ريال</span>
						</div>
					</div>
				</div>

				<!-- Area Range -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
						نطاق المساحة (م²)
					</h3>
					<div class="space-y-2">
						<div class="flex items-center gap-2">
							<input
								type="number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="المساحة الأدنى"
								bind:value={minArea}
								min={areaRange.min}
								max={maxArea}
							/>
							<span class="text-gray-500 dark:text-gray-400">-</span>
							<input
								type="number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="المساحة الأعلى"
								bind:value={maxArea}
								min={minArea}
								max={areaRange.max}
							/>
						</div>
						<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
							<span>{formatPrice(minArea)} م²</span>
							<span>{formatPrice(maxArea)} م²</span>
						</div>
					</div>
				</div>

				<!-- Sorting Options -->
				<div>
					<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">الترتيب</h3>
					<div class="grid grid-cols-1 gap-2">
						<select
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
							bind:value={orderBy}
						>
							<option value="created_at">تاريخ الإضافة</option>
							<option value="estimated_value">السعر</option>
							<option value="area">المساحة</option>
							<option value="views_count">المشاهدات</option>
						</select>

						<div class="flex">
							<button
								class="flex-1 px-2 py-1 text-sm {orderDirection === 'asc'
									? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
									: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'} rounded-r-md"
								on:click={() => (orderDirection = 'asc')}
							>
								تصاعدي
							</button>
							<button
								class="flex-1 px-2 py-1 text-sm {orderDirection === 'desc'
									? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
									: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'} rounded-l-md"
								on:click={() => (orderDirection = 'desc')}
							>
								تنازلي
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Action buttons -->
			<div class="mt-6 flex justify-end gap-3">
				<button
					class="rounded-md px-4 py-2 text-gray-700 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
					on:click={resetFilters}
				>
					إعادة تعيين
				</button>

				<button
					class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
					on:click={applyFilters}
				>
					تطبيق الفلاتر
				</button>
			</div>
		</div>
	{/if}
</div>
