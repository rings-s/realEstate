<script>
	import { onMount } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import {
		properties,
		propertiesList,
		isLoading,
		error,
		filters,
		pagination
	} from '$lib/stores/properties';
	import { PROPERTY_TYPES, PROPERTY_STATUS, SORT_OPTIONS } from '$lib/config/constants';
	import {
		Search,
		Filter,
		X,
		Building,
		MapPin,
		ChevronDown,
		ArrowUp,
		ArrowDown
	} from 'lucide-svelte';

	import Alert from '$lib/components/common/Alert.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import PropertyCard from '$lib/components/property/PropertyCard.svelte';

	// Local state
	let searchQuery = '';
	let activeFilters = false;
	let filterValues = {
		property_type: '',
		status: '',
		city: '',
		bedrooms_min: '',
		bedrooms_max: '',
		price_min: '',
		price_max: '',
		is_featured: false
	};

	// Extract cities from properties for filter dropdown
	$: cities = [...new Set($propertiesList.map((p) => p.city).filter(Boolean))];

	// Initialize filters from URL params or store
	onMount(async () => {
		// If URL has query params, use those to set initial filters
		if (typeof window !== 'undefined' && window.location.search) {
			const params = new URLSearchParams(window.location.search);

			// Set search if available
			if (params.has('search')) {
				searchQuery = params.get('search');
			}

			// Set other filters
			Object.keys(filterValues).forEach((key) => {
				if (params.has(key)) {
					const value = params.get(key);
					filterValues[key] = value === 'true' ? true : value === 'false' ? false : value;
				}
			});

			// Apply filters
			if (searchQuery || Object.values(filterValues).some((v) => v !== '' && v !== false)) {
				activeFilters = true;
				applyFilters();
			} else {
				// Load properties with default filters
				await properties.loadProperties();
			}
		} else {
			// Load properties with default filters
			await properties.loadProperties();
		}
	});

	// Apply filters function
	async function applyFilters() {
		try {
			// Create filter object
			const filterObj = {
				search: searchQuery.trim()
			};

			// Add other filters if they have values
			Object.entries(filterValues).forEach(([key, value]) => {
				if (value !== '' && value !== false) {
					filterObj[key] = value;
				}
			});

			// Update URL with filters
			if (typeof window !== 'undefined') {
				const params = new URLSearchParams();
				Object.entries(filterObj).forEach(([key, value]) => {
					if (value !== '') {
						params.set(key, value);
					}
				});

				const newUrl = `${window.location.pathname}?${params.toString()}`;
				window.history.pushState({}, '', newUrl);
			}

			// Apply filters
			await properties.updateFilters(filterObj);
		} catch (err) {
			console.error('Error applying filters:', err);
			addToast(t('filter_error', $language, { default: 'حدث خطأ أثناء تطبيق الفلاتر' }), 'error');
		}
	}

	// Reset filters function
	function resetFilters() {
		searchQuery = '';
		filterValues = {
			property_type: '',
			status: '',
			city: '',
			bedrooms_min: '',
			bedrooms_max: '',
			price_min: '',
			price_max: '',
			is_featured: false
		};

		// Update URL by removing query params
		if (typeof window !== 'undefined') {
			const newUrl = window.location.pathname;
			window.history.pushState({}, '', newUrl);
		}

		// Reset filters in store and reload properties
		properties.updateFilters({});
	}

	// Toggle filters panel
	function toggleFilters() {
		activeFilters = !activeFilters;
	}

	// Change sort order
	function changeSort(event) {
		const sortOrder = event.target.value;
		properties.updateFilters({ ordering: sortOrder });
	}

	// Handle page change from pagination component
	function handlePageChange(event) {
		const { page } = event.detail;
		properties.changePage(page);

		// Scroll to top of list
		if (typeof window !== 'undefined') {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	// Format price range for display
	function formatPriceRange(min, max) {
		if (min && max) {
			return `${min} - ${max}`;
		} else if (min) {
			return `${min}+`;
		} else if (max) {
			return `0 - ${max}`;
		}
		return '';
	}

	// Format bedrooms range for display
	function formatBedroomsRange(min, max) {
		if (min && max) {
			return `${min} - ${max}`;
		} else if (min) {
			return `${min}+`;
		} else if (max) {
			return `0 - ${max}`;
		}
		return '';
	}

	// Get active filter count for badge
	$: activeFilterCount = Object.values(filterValues).filter((v) => v !== '' && v !== false).length;
</script>

<div class="container mx-auto px-4 py-6">
	<div class="flex flex-col space-y-6">
		<!-- Page Header -->
		<div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
			<h1 class="h2 {$isRTL ? 'text-right' : 'text-left'}">
				{t('properties', $language, { default: 'العقارات' })}
			</h1>

			<!-- Search & Filter Bar -->
			<div class="w-full md:w-auto flex flex-col sm:flex-row gap-2">
				<!-- Search Box -->
				<div class="input-group w-full sm:w-auto">
					<input
						type="text"
						class="input"
						placeholder={t('search_properties', $language, { default: 'بحث عن عقار...' })}
						bind:value={searchQuery}
						on:keydown={(e) => e.key === 'Enter' && applyFilters()}
					/>
					<button class="variant-filled-primary" on:click={applyFilters}>
						<Search size={18} />
					</button>
				</div>

				<!-- Filter Button -->
				<button
					class="btn variant-ghost-surface {activeFilters ? 'variant-soft-primary' : ''}"
					on:click={toggleFilters}
				>
					<Filter size={18} class={$isRTL ? 'ml-2' : 'mr-2'} />
					{t('filters', $language, { default: 'الفلاتر' })}
					{#if activeFilterCount > 0}
						<span class="badge bg-primary-500 text-white {$isRTL ? 'mr-2' : 'ml-2'}">
							{activeFilterCount}
						</span>
					{/if}
				</button>

				<!-- Sort Dropdown -->
				<div class="input-group w-full sm:w-auto">
					<select class="select" on:change={changeSort} value={$filters.ordering || '-created_at'}>
						<option disabled>{t('sort_by', $language, { default: 'ترتيب حسب' })}</option>
						{#each SORT_OPTIONS as option}
							<option value={option.value}>
								{t(option.label, $language, { default: option.label })}
							</option>
						{/each}
					</select>
					<div class="input-group-shim">
						<ChevronDown size={18} />
					</div>
				</div>
			</div>
		</div>

		<!-- Filter Panel -->
		{#if activeFilters}
			<div class="card p-4 bg-surface-100-800-token" transition:slide={{ duration: 300 }}>
				<div class="flex justify-between items-center mb-4">
					<h3 class="h4">{t('filter_properties', $language, { default: 'تصفية العقارات' })}</h3>
					<button class="btn btn-sm variant-ghost-error" on:click={resetFilters}>
						<X size={16} class={$isRTL ? 'ml-2' : 'mr-2'} />
						{t('reset_filters', $language, { default: 'إعادة ضبط' })}
					</button>
				</div>

				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
					<!-- Property Type -->
					<label class="label">
						<span>{t('property_type', $language, { default: 'نوع العقار' })}</span>
						<select class="select" bind:value={filterValues.property_type}>
							<option value="">{t('all_types', $language, { default: 'كل الأنواع' })}</option>
							{#each PROPERTY_TYPES as type}
								<option value={type.value}>
									{t(type.value, $language, { default: type.label })}
								</option>
							{/each}
						</select>
					</label>

					<!-- Property Status -->
					<label class="label">
						<span>{t('status', $language, { default: 'الحالة' })}</span>
						<select class="select" bind:value={filterValues.status}>
							<option value="">{t('all_statuses', $language, { default: 'كل الحالات' })}</option>
							{#each PROPERTY_STATUS as status}
								<option value={status.value}>
									{t(status.value, $language, { default: status.label })}
								</option>
							{/each}
						</select>
					</label>

					<!-- City -->
					<label class="label">
						<span>{t('city', $language, { default: 'المدينة' })}</span>
						<select class="select" bind:value={filterValues.city}>
							<option value="">{t('all_cities', $language, { default: 'كل المدن' })}</option>
							{#each cities as city}
								<option value={city}>{city}</option>
							{/each}
						</select>
					</label>

					<!-- Featured properties -->
					<label
						class="flex items-center space-x-2 {$isRTL ? 'space-x-reverse' : ''} h-full pb-1 pt-6"
					>
						<input type="checkbox" class="checkbox" bind:checked={filterValues.is_featured} />
						<span>{t('featured_only', $language, { default: 'العقارات المميزة فقط' })}</span>
					</label>

					<!-- Price Range -->
					<div class="sm:col-span-2">
						<span class="label-text">{t('price_range', $language, { default: 'نطاق السعر' })}</span>
						<div class="flex items-center gap-2">
							<input
								type="number"
								class="input"
								placeholder={t('min', $language, { default: 'الحد الأدنى' })}
								bind:value={filterValues.price_min}
							/>
							<span>-</span>
							<input
								type="number"
								class="input"
								placeholder={t('max', $language, { default: 'الحد الأقصى' })}
								bind:value={filterValues.price_max}
							/>
						</div>
					</div>

					<!-- Bedrooms Range -->
					<div class="sm:col-span-2">
						<span class="label-text"
							>{t('bedrooms_range', $language, { default: 'عدد غرف النوم' })}</span
						>
						<div class="flex items-center gap-2">
							<input
								type="number"
								class="input"
								placeholder={t('min', $language, { default: 'الحد الأدنى' })}
								bind:value={filterValues.bedrooms_min}
							/>
							<span>-</span>
							<input
								type="number"
								class="input"
								placeholder={t('max', $language, { default: 'الحد الأقصى' })}
								bind:value={filterValues.bedrooms_max}
							/>
						</div>
					</div>
				</div>

				<div class="flex justify-end mt-4">
					<button class="btn variant-filled-primary" on:click={applyFilters}>
						{t('apply_filters', $language, { default: 'تطبيق الفلاتر' })}
					</button>
				</div>
			</div>
		{/if}

		<!-- Active Filters Display -->
		{#if activeFilterCount > 0}
			<div class="flex flex-wrap gap-2 {$isRTL ? 'justify-end' : 'justify-start'}">
				{#if filterValues.property_type}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<Building size={14} />
						<span>{t(filterValues.property_type, $language)}</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.property_type = '';
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}

				{#if filterValues.status}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<span>{t(filterValues.status, $language)}</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.status = '';
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}

				{#if filterValues.city}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<MapPin size={14} />
						<span>{filterValues.city}</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.city = '';
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}

				{#if filterValues.price_min || filterValues.price_max}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<span>
							{t('price', $language, { default: 'السعر' })}:
							{formatPriceRange(filterValues.price_min, filterValues.price_max)}
						</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.price_min = '';
								filterValues.price_max = '';
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}

				{#if filterValues.bedrooms_min || filterValues.bedrooms_max}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<span>
							{t('bedrooms', $language, { default: 'غرف النوم' })}:
							{formatBedroomsRange(filterValues.bedrooms_min, filterValues.bedrooms_max)}
						</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.bedrooms_min = '';
								filterValues.bedrooms_max = '';
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}

				{#if filterValues.is_featured}
					<div class="badge variant-soft-primary p-2 flex items-center gap-1">
						<span>{t('featured', $language, { default: 'مميز' })}</span>
						<button
							class="btn btn-icon btn-xs variant-ghost text-primary-500"
							on:click={() => {
								filterValues.is_featured = false;
								applyFilters();
							}}
						>
							<X size={14} />
						</button>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Loading State -->
		{#if $isLoading}
			<div class="flex justify-center py-12">
				<div class="spinner-icon"></div>
			</div>
			<!-- Error State -->
		{:else if $error}
			<Alert type="error" message={$error} />
			<!-- Empty State -->
		{:else if $propertiesList.length === 0}
			<div class="card p-12 text-center">
				<h3 class="h3 mb-4">
					{t('no_properties_found', $language, { default: 'لم يتم العثور على عقارات' })}
				</h3>
				<p class="mb-6">
					{t('try_adjusting_filters', $language, {
						default: 'حاول تعديل الفلاتر للعثور على المزيد من العقارات'
					})}
				</p>
				<button class="btn variant-filled-primary" on:click={resetFilters}>
					{t('reset_filters', $language, { default: 'إعادة ضبط الفلاتر' })}
				</button>
			</div>
			<!-- Property Grid -->
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
				{#each $propertiesList as property (property.id)}
					<PropertyCard {property} />
				{/each}
			</div>

			<!-- Pagination -->
			<div class="mt-8">
				<Pagination
					page={$pagination.page}
					totalPages={$pagination.totalPages}
					totalItems={$pagination.totalItems}
					pageSize={$pagination.pageSize}
					on:change={handlePageChange}
					showPageSizeSelector={false}
				/>
			</div>
		{/if}
	</div>
</div>

<style>
	.spinner-icon {
		border: 4px solid rgba(0, 0, 0, 0.1);
		border-left-color: var(--color-primary-500);
		border-radius: 50%;
		width: 36px;
		height: 36px;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
