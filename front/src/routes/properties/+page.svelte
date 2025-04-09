<!--
  Properties Listing Page
  Displays all properties with filtering and pagination
-->
<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { language, isRTL, textClass } from '$lib/stores/ui';
	import { t } from '$lib/config/translations';
	import {
		properties,
		propertiesList,
		isLoading,
		error,
		filters,
		pagination
	} from '$lib/stores/properties';
	import { PROPERTY_TYPES } from '$lib/config/constants';
	import { Building, Search, Filter, X } from 'lucide-svelte';
	import PropertyCard from '$lib/components/property/PropertyCard.svelte';

	// Filter state
	let searchQuery = '';
	let propertyType = '';
	let city = '';
	let status = '';
	let isFilterOpen = false;

	// Get URL params on mount
	onMount(async () => {
		// Get search params from URL
		const params = $page.url.searchParams;
		searchQuery = params.get('search') || '';
		propertyType = params.get('property_type') || '';
		city = params.get('city') || '';
		status = params.get('status') || '';

		// Initial load with URL params
		const initialFilters = {
			search: searchQuery,
			property_type: propertyType,
			city: city,
			status: status,
			is_published: true // Only show published properties
		};

		await properties.loadProperties(initialFilters);
	});

	// Handle search form submission
	function handleSearch(e) {
		e?.preventDefault();

		// Update URL with search params
		const url = new URL(window.location);
		if (searchQuery) url.searchParams.set('search', searchQuery);
		else url.searchParams.delete('search');

		if (propertyType) url.searchParams.set('property_type', propertyType);
		else url.searchParams.delete('property_type');

		if (city) url.searchParams.set('city', city);
		else url.searchParams.delete('city');

		if (status) url.searchParams.set('status', status);
		else url.searchParams.delete('status');

		history.pushState({}, '', url);

		// Update filters and load properties
		properties.updateFilters({
			search: searchQuery,
			property_type: propertyType,
			city: city,
			status: status
		});
	}

	// Reset filters
	function resetFilters() {
		searchQuery = '';
		propertyType = '';
		city = '';
		status = '';
		handleSearch();
	}

	// Handle pagination
	function changePage(newPage) {
		if (newPage < 1 || newPage > $pagination.totalPages) return;
		properties.changePage(newPage);
	}

	// Toggle filter sidebar on mobile
	function toggleFilter() {
		isFilterOpen = !isFilterOpen;
	}
</script>

<svelte:head>
	<title>{t('properties', $language)} | {t('app_name', $language)}</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<!-- Page Header -->
	<header class="mb-8">
		<h1 class="h1 mb-2">{t('properties', $language)}</h1>
		<p class="text-surface-600-300-token">
			{t('properties_subtitle', $language, { default: 'استكشف العقارات المتاحة للبيع والمزاد' })}
		</p>
	</header>

	<!-- Main Content with Filters -->
	<div class="grid grid-cols-1 md:grid-cols-[300px_1fr] gap-6">
		<!-- Filters - Desktop (Side) / Mobile (Modal) -->
		<div
			class="md:block {isFilterOpen
				? 'fixed inset-0 z-40 bg-surface-backdrop-token grid place-items-center'
				: 'hidden'}"
			class:fixed={isFilterOpen}
			class:inset-0={isFilterOpen}
			class:z-40={isFilterOpen}
			class:bg-surface-backdrop-token={isFilterOpen}
			class:place-items-center={isFilterOpen}
		>
			<div class="card p-4 w-full md:w-auto {isFilterOpen ? 'max-w-md mx-auto' : ''}">
				<div class="flex justify-between items-center mb-4">
					<h3 class="h3">{t('filter', $language)}</h3>
					<button class="btn-icon md:hidden variant-ghost" on:click={toggleFilter}>
						<X class="w-5 h-5" />
					</button>
				</div>

				<form on:submit|preventDefault={handleSearch} class={$textClass}>
					<!-- Search -->
					<label class="label">
						<span>{t('search', $language)}</span>
						<div class="input-group input-group-divider grid-cols-[auto_1fr]">
							<div class="input-group-shim">
								<Search class="w-4 h-4" />
							</div>
							<input
								type="text"
								bind:value={searchQuery}
								placeholder={t('search_placeholder', $language, { default: 'ابحث عن عقار...' })}
								class="input"
							/>
						</div>
					</label>

					<!-- Property Type -->
					<label class="label mt-4">
						<span>{t('property_type', $language)}</span>
						<select bind:value={propertyType} class="select w-full">
							<option value="">{t('all_types', $language, { default: 'جميع الأنواع' })}</option>
							{#each PROPERTY_TYPES as type}
								<option value={type.value}
									>{t(type.value, $language, { default: type.label })}</option
								>
							{/each}
						</select>
					</label>

					<!-- City -->
					<label class="label mt-4">
						<span>{t('city', $language)}</span>
						<input
							type="text"
							bind:value={city}
							placeholder={t('city_placeholder', $language, { default: 'المدينة...' })}
							class="input w-full"
						/>
					</label>

					<!-- Status -->
					<label class="label mt-4">
						<span>{t('status', $language)}</span>
						<select bind:value={status} class="select w-full">
							<option value="">{t('all_status', $language, { default: 'جميع الحالات' })}</option>
							<option value="available">{t('available', $language)}</option>
							<option value="under_contract">{t('under_contract', $language)}</option>
							<option value="auction">{t('in_auction', $language)}</option>
						</select>
					</label>

					<!-- Filter Buttons -->
					<div class="flex flex-col gap-2 mt-6">
						<button type="submit" class="btn variant-filled-primary w-full">
							<Filter class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
							{t('apply_filters', $language, { default: 'تطبيق الفلاتر' })}
						</button>

						<button type="button" class="btn variant-ghost w-full" on:click={resetFilters}>
							{t('reset_filters', $language, { default: 'إعادة ضبط الفلاتر' })}
						</button>
					</div>
				</form>
			</div>
		</div>

		<!-- Properties List -->
		<div>
			<!-- Mobile Filter Toggle -->
			<div class="md:hidden mb-4">
				<button class="btn variant-ghost-surface w-full" on:click={toggleFilter}>
					<Filter class="w-4 h-4 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('filters', $language, { default: 'الفلاتر' })}
				</button>
			</div>

			<!-- Results Counter -->
			<div class="mb-4 flex justify-between items-center">
				<p class={$textClass}>
					{$isLoading
						? t('loading', $language)
						: t('showing_results', $language, {
								default: 'عرض {{count}} عقار',
								count: $propertiesList.length
							})}
				</p>

				<!-- Sort Dropdown (could be implemented later) -->
			</div>

			<!-- Loading State -->
			{#if $isLoading}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{#each Array(6) as _, i}
						<div class="card p-4 h-80">
							<div class="placeholder animate-pulse w-full h-40 mb-4 rounded-lg"></div>
							<div class="placeholder animate-pulse w-2/3 h-4 mb-2"></div>
							<div class="placeholder animate-pulse w-full h-4 mb-2"></div>
							<div class="placeholder animate-pulse w-1/2 h-4"></div>
						</div>
					{/each}
				</div>

				<!-- Error State -->
			{:else if $error}
				<div class="alert variant-filled-error">
					<p>{$error}</p>
				</div>

				<!-- Empty State -->
			{:else if $propertiesList.length === 0}
				<div class="card p-12 text-center">
					<Building class="w-16 h-16 mx-auto text-primary-500 mb-4" />
					<h3 class="h3 mb-2">
						{t('no_properties_found', $language, { default: 'لم يتم العثور على عقارات' })}
					</h3>
					<p class="text-surface-600-300-token mb-6">
						{t('try_different_filters', $language, {
							default: 'حاول تغيير معايير البحث للعثور على المزيد من العقارات'
						})}
					</p>
					<button class="btn variant-ghost-primary" on:click={resetFilters}>
						{t('clear_filters', $language, { default: 'مسح الفلاتر' })}
					</button>
				</div>

				<!-- Results List -->
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{#each $propertiesList as property (property.id)}
						<PropertyCard {property} />
					{/each}
				</div>

				<!-- Pagination -->
				{#if $pagination.totalPages > 1}
					<div class="flex justify-center mt-8">
						<nav class="flex space-x-2 rtl:space-x-reverse">
							<!-- Previous Button -->
							<button
								class="btn btn-sm variant-ghost-surface"
								disabled={$pagination.page === 1}
								on:click={() => changePage($pagination.page - 1)}
							>
								{$isRTL ? '›' : '‹'}
							</button>

							<!-- Page Numbers -->
							{#each Array(Math.min(5, $pagination.totalPages)) as _, i}
								{#if $pagination.totalPages <= 5}
									<!-- Show all pages if 5 or fewer -->
									<button
										class="btn btn-sm {$pagination.page === i + 1
											? 'variant-filled-primary'
											: 'variant-ghost-surface'}"
										on:click={() => changePage(i + 1)}
									>
										{i + 1}
									</button>
								{:else}
									<!-- Show ellipsis for larger page counts -->
									{#if $pagination.page <= 3 && i < 5}
										<!-- First 5 pages -->
										<button
											class="btn btn-sm {$pagination.page === i + 1
												? 'variant-filled-primary'
												: 'variant-ghost-surface'}"
											on:click={() => changePage(i + 1)}
										>
											{i + 1}
										</button>
									{:else if $pagination.page > $pagination.totalPages - 3 && i < 5}
										<!-- Last 5 pages -->
										{@const pageNum = $pagination.totalPages - 4 + i}
										<button
											class="btn btn-sm {$pagination.page === pageNum
												? 'variant-filled-primary'
												: 'variant-ghost-surface'}"
											on:click={() => changePage(pageNum)}
										>
											{pageNum}
										</button>
									{:else if i === 0}
										<!-- First page -->
										<button class="btn btn-sm variant-ghost-surface" on:click={() => changePage(1)}>
											1
										</button>
									{:else if i === 1}
										<!-- Ellipsis or second page -->
										{#if $pagination.page > 3}
											<span class="flex items-center justify-center w-8">...</span>
										{:else}
											<button
												class="btn btn-sm variant-ghost-surface"
												on:click={() => changePage(2)}
											>
												2
											</button>
										{/if}
									{:else if i === 2}
										<!-- Current page area -->
										<button
											class="btn btn-sm variant-filled-primary"
											on:click={() => changePage($pagination.page)}
										>
											{$pagination.page}
										</button>
									{:else if i === 3}
										<!-- Ellipsis or second-to-last page -->
										{#if $pagination.page < $pagination.totalPages - 2}
											<span class="flex items-center justify-center w-8">...</span>
										{:else}
											<button
												class="btn btn-sm variant-ghost-surface"
												on:click={() => changePage($pagination.totalPages - 1)}
											>
												{$pagination.totalPages - 1}
											</button>
										{/if}
									{:else if i === 4}
										<!-- Last page -->
										<button
											class="btn btn-sm variant-ghost-surface"
											on:click={() => changePage($pagination.totalPages)}
										>
											{$pagination.totalPages}
										</button>
									{/if}
								{/if}
							{/each}

							<!-- Next Button -->
							<button
								class="btn btn-sm variant-ghost-surface"
								disabled={$pagination.page === $pagination.totalPages}
								on:click={() => changePage($pagination.page + 1)}
							>
								{$isRTL ? '‹' : '›'}
							</button>
						</nav>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
