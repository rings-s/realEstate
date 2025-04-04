<script>
	/**
	 * Pagination component
	 * @component
	 */
	import { createEventDispatcher } from 'svelte';

	export let totalItems = 0;
	export let pageSize = 10;
	export let currentPage = 1;
	export let showPageNumbers = true;
	export let maxPageNumbers = 5;
	export let size = 'md'; // sm, md, lg
	export let align = 'center'; // start, center, end
	export let showPageSize = false;
	export let pageSizeOptions = [10, 25, 50, 100];

	const dispatch = createEventDispatcher();

	// Size classes
	const sizeClasses = {
		sm: 'px-2 py-1 text-sm',
		md: 'px-3 py-2 text-base',
		lg: 'px-4 py-3 text-lg'
	};

	// Alignment classes
	const alignClasses = {
		start: 'justify-start',
		center: 'justify-center',
		end: 'justify-end'
	};

	// Calculate total pages
	$: totalPages = Math.ceil(totalItems / pageSize);

	// Generate page numbers array
	$: pageNumbers = getPageNumbers(currentPage, totalPages, maxPageNumbers);

	// Handle page change
	function changePage(page) {
		if (page !== currentPage && page >= 1 && page <= totalPages) {
			currentPage = page;
			dispatch('pageChange', { page });
		}
	}

	// Handle page size change
	function changePageSize(event) {
		const newPageSize = parseInt(event.target.value);
		pageSize = newPageSize;
		currentPage = 1;
		dispatch('pageSizeChange', { pageSize: newPageSize });
	}

	// Generate array of page numbers to display
	function getPageNumbers(current, total, max) {
		if (total <= max) {
			return Array.from({ length: total }, (_, i) => i + 1);
		}

		const half = Math.floor(max / 2);
		let start = current - half;
		let end = current + half;

		if (start < 1) {
			end += 1 - start;
			start = 1;
		}

		if (end > total) {
			start -= end - total;
			end = total;
		}

		start = Math.max(start, 1);

		const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

		// Add ellipsis indicators
		if (start > 1) {
			pages.unshift('...');
			pages.unshift(1);
		}

		if (end < total) {
			pages.push('...');
			pages.push(total);
		}

		return pages;
	}
</script>

<div class="mt-4 flex flex-col items-center space-y-3">
	<!-- Page info text -->
	<div class="text-sm text-gray-700">
		<span>عرض </span>
		<span class="font-medium">{Math.min((currentPage - 1) * pageSize + 1, totalItems)}</span>
		<span> إلى </span>
		<span class="font-medium">{Math.min(currentPage * pageSize, totalItems)}</span>
		<span> من </span>
		<span class="font-medium">{totalItems}</span>
		<span> عنصر</span>
	</div>

	<div class="xs:mt-0 mt-2 inline-flex gap-x-2">
		<!-- Page size selector -->
		{#if showPageSize}
			<div class="ml-4">
				<label for="page-size" class="ml-2 text-sm font-medium text-gray-700"
					>عناصر في الصفحة:</label
				>
				<select
					id="page-size"
					class="focus:ring-primary-500 focus:border-primary-500 rounded-md border border-gray-300 p-1.5 text-sm text-gray-900"
					on:change={changePageSize}
					value={pageSize}
				>
					{#each pageSizeOptions as option}
						<option value={option}>{option}</option>
					{/each}
				</select>
			</div>
		{/if}

		<!-- Pagination -->
		<div class={`inline-flex ${alignClasses[align]}`}>
			<!-- Previous button -->
			<button
				class={`${sizeClasses[size]} mr-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 ${currentPage <= 1 ? 'cursor-not-allowed opacity-50' : ''}`}
				on:click={() => changePage(currentPage - 1)}
				disabled={currentPage <= 1}
				aria-label="Previous"
			>
				<svg
					class="h-5 w-5"
					fill="currentColor"
					viewBox="0 0 20 20"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						fill-rule="evenodd"
						d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
						clip-rule="evenodd"
					></path>
				</svg>
			</button>

			<!-- Page numbers -->
			{#if showPageNumbers}
				{#each pageNumbers as page}
					{#if page === '...'}
						<span
							class={`${sizeClasses[size]} rounded-md border border-gray-300 bg-white text-gray-500`}
						>
							{page}
						</span>
					{:else}
						<button
							class={`${sizeClasses[size]} rounded-md border ${page === currentPage ? 'bg-primary-50 border-primary-500 text-primary-600' : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'}`}
							on:click={() => changePage(page)}
							aria-current={page === currentPage ? 'page' : undefined}
							aria-label={`Page ${page}`}
						>
							{page}
						</button>
					{/if}
				{/each}
			{/if}

			<!-- Next button -->
			<button
				class={`${sizeClasses[size]} ml-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 ${currentPage >= totalPages ? 'cursor-not-allowed opacity-50' : ''}`}
				on:click={() => changePage(currentPage + 1)}
				disabled={currentPage >= totalPages}
				aria-label="Next"
			>
				<svg
					class="h-5 w-5"
					fill="currentColor"
					viewBox="0 0 20 20"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						fill-rule="evenodd"
						d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
						clip-rule="evenodd"
					></path>
				</svg>
			</button>
		</div>
	</div>
</div>
