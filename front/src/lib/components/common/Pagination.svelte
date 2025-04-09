<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { createEventDispatcher } from 'svelte';
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Current page
	export let page = 1;
	// Total number of pages
	export let totalPages = 1;
	// Total number of items
	export let totalItems = 0;
	// Items per page
	export let pageSize = 20;
	// Paginated items count (on current page)
	export let itemsCount = 0;
	// Number of page buttons to show
	export let showPageNumbers = 5;
	// Show abbreviated pagination (prev/next only)
	export let abbreviated = false;
	// Show total items count
	export let showTotalItems = true;
	// Show items per page selector
	export let showPageSizeSelector = false;
	// Available page sizes
	export let pageSizeOptions = [10, 20, 50, 100];
	// Additional classes
	export let classes = '';
	// Page range text
	export let pageRangeText = '';

	// Change page handler
	function changePage(newPage) {
		if (newPage > 0 && newPage <= totalPages && newPage !== page) {
			dispatch('change', { page: newPage });
		}
	}

	// Change page size handler
	function changePageSize(event) {
		const newPageSize = parseInt(event.target.value, 10);
		dispatch('changePageSize', { pageSize: newPageSize });
	}

	// Calculate page numbers to display
	$: pageNumbers = getPageNumbers(page, totalPages, showPageNumbers);

	function getPageNumbers(currentPage, total, max) {
		if (total <= max) {
			// If total pages is less than max buttons, show all pages
			return Array.from({ length: total }, (_, i) => i + 1);
		}

		// Calculate start and end, ensuring we show max buttons
		let start = Math.max(currentPage - Math.floor(max / 2), 1);
		let end = start + max - 1;

		// Adjust if we're near the end
		if (end > total) {
			end = total;
			start = Math.max(end - max + 1, 1);
		}

		// Generate the array of page numbers
		let pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

		// Add ellipsis indicators
		if (start > 1) {
			pages = [1, ...(start > 2 ? [-1] : []), ...pages];
		}

		if (end < total) {
			pages = [...pages, ...(end < total - 1 ? [-2] : []), total];
		}

		return pages;
	}

	// Calculate displayed item range
	$: startItem = (page - 1) * pageSize + 1;
	$: endItem = Math.min(page * pageSize, totalItems);

	// Default page range text if not provided
	$: if (!pageRangeText && totalItems > 0) {
		pageRangeText = t('showing_items', $language, {
			default: 'عرض {{start}} إلى {{end}} من {{total}} عنصر',
			start: startItem,
			end: endItem,
			total: totalItems
		});
	}
</script>

{#if totalPages > 1 || showTotalItems}
	<div class="flex flex-col sm:flex-row justify-between items-center gap-4 {classes}">
		<!-- Items count information -->
		{#if showTotalItems && totalItems > 0}
			<div class="text-sm text-surface-600-300-token">
				{pageRangeText}
			</div>
		{:else}
			<div></div>
		{/if}

		<!-- Pagination controls -->
		<div class="flex items-center gap-1">
			{#if !abbreviated}
				<!-- Full pagination with page numbers -->
				<button
					class="btn btn-sm btn-icon variant-ghost-surface"
					disabled={page === 1}
					aria-label={t('previous_page', $language, { default: 'الصفحة السابقة' })}
					on:click={() => changePage(page - 1)}
				>
					{#if $isRTL}
						<ChevronRight class="w-5 h-5" />
					{:else}
						<ChevronLeft class="w-5 h-5" />
					{/if}
				</button>

				{#each pageNumbers as pageNum}
					{#if pageNum < 0}
						<!-- Ellipsis -->
						<span class="flex items-center justify-center w-8">...</span>
					{:else}
						<!-- Page number button -->
						<button
							class="btn btn-sm {pageNum === page
								? 'variant-filled-primary'
								: 'variant-ghost-surface'}"
							disabled={pageNum === page}
							aria-label={t('go_to_page', $language, {
								default: 'اذهب إلى الصفحة {{page}}',
								page: pageNum
							})}
							aria-current={pageNum === page ? 'page' : undefined}
							on:click={() => changePage(pageNum)}
						>
							{pageNum}
						</button>
					{/if}
				{/each}

				<button
					class="btn btn-sm btn-icon variant-ghost-surface"
					disabled={page === totalPages}
					aria-label={t('next_page', $language, { default: 'الصفحة التالية' })}
					on:click={() => changePage(page + 1)}
				>
					{#if $isRTL}
						<ChevronLeft class="w-5 h-5" />
					{:else}
						<ChevronRight class="w-5 h-5" />
					{/if}
				</button>
			{:else}
				<!-- Abbreviated pagination (prev/next only) -->
				<div class="flex items-center gap-3">
					<button
						class="btn btn-sm {$isRTL ? 'btn-icon-end' : 'btn-icon'} variant-ghost-surface"
						disabled={page === 1}
						on:click={() => changePage(page - 1)}
					>
						{#if $isRTL}
							<span>{t('previous', $language, { default: 'السابق' })}</span>
							<ChevronRight class="w-5 h-5" />
						{:else}
							<ChevronLeft class="w-5 h-5" />
							<span>{t('previous', $language, { default: 'السابق' })}</span>
						{/if}
					</button>

					<span class="text-sm text-surface-600-300-token">
						{t('page_of', $language, {
							default: 'الصفحة {{current}} من {{total}}',
							current: page,
							total: totalPages
						})}
					</span>

					<button
						class="btn btn-sm {$isRTL ? 'btn-icon' : 'btn-icon-end'} variant-ghost-surface"
						disabled={page === totalPages}
						on:click={() => changePage(page + 1)}
					>
						{#if $isRTL}
							<ChevronLeft class="w-5 h-5" />
							<span>{t('next', $language, { default: 'التالي' })}</span>
						{:else}
							<span>{t('next', $language, { default: 'التالي' })}</span>
							<ChevronRight class="w-5 h-5" />
						{/if}
					</button>
				</div>
			{/if}

			<!-- Page size selector -->
			{#if showPageSizeSelector}
				<div class="flex items-center {$isRTL ? 'mr-4' : 'ml-4'}">
					<label class="flex items-center gap-2">
						<span class="text-sm text-surface-600-300-token"
							>{t('items_per_page', $language, { default: 'العناصر في الصفحة' })}</span
						>
						<select
							class="select select-sm"
							value={pageSize}
							on:change={changePageSize}
							aria-label={t('items_per_page', $language, { default: 'العناصر في الصفحة' })}
						>
							{#each pageSizeOptions as option}
								<option value={option}>{option}</option>
							{/each}
						</select>
					</label>
				</div>
			{/if}
		</div>
	</div>
{/if}
