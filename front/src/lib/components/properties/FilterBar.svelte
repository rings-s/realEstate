<!-- src/lib/components/properties/FilterBar.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Button from '$lib/components/common/Button.svelte';

	export let cities = [];
	export let propertyTypes = [];
	export let propertyStatuses = [];
	export let filters = {
		property_type: '',
		city: '',
		min_price: '',
		max_price: '',
		status: 'active'
	};

	const dispatch = createEventDispatcher();

	// Local state for the form
	let localFilters = { ...filters };

	// Dispatch filter event when apply is clicked
	function applyFilters() {
		dispatch('filter', localFilters);
	}

	// Reset filters
	function resetFilters() {
		localFilters = {
			property_type: '',
			city: '',
			min_price: '',
			max_price: '',
			status: 'active'
		};
		dispatch('reset');
	}

	// Update filter when parent component changes filters
	$: {
		if (JSON.stringify(filters) !== JSON.stringify(localFilters)) {
			localFilters = { ...filters };
		}
	}
</script>

<div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-700">
	<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
		<!-- Property Type -->
		<div>
			<label
				for="property_type"
				class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200"
			>
				نوع العقار
			</label>
			<select
				id="property_type"
				bind:value={localFilters.property_type}
				class="focus:border-primary-500 focus:ring-primary-500 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			>
				<option value="">الكل</option>
				{#each propertyTypes as type}
					<option value={type.value}>{type.label}</option>
				{/each}
			</select>
		</div>

		<!-- City -->
		<div>
			<label for="city" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
				المدينة
			</label>
			<select
				id="city"
				bind:value={localFilters.city}
				class="focus:border-primary-500 focus:ring-primary-500 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			>
				<option value="">الكل</option>
				{#each cities as city}
					<option value={city}>{city}</option>
				{/each}
			</select>
		</div>

		<!-- Min Price -->
		<div>
			<label
				for="min_price"
				class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200"
			>
				السعر الأدنى
			</label>
			<input
				type="number"
				id="min_price"
				bind:value={localFilters.min_price}
				min="0"
				placeholder="السعر الأدنى"
				class="focus:border-primary-500 focus:ring-primary-500 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			/>
		</div>

		<!-- Max Price -->
		<div>
			<label
				for="max_price"
				class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200"
			>
				السعر الأقصى
			</label>
			<input
				type="number"
				id="max_price"
				bind:value={localFilters.max_price}
				min="0"
				placeholder="السعر الأقصى"
				class="focus:border-primary-500 focus:ring-primary-500 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			/>
		</div>

		<!-- Status -->
		<div>
			<label for="status" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
				الحالة
			</label>
			<select
				id="status"
				bind:value={localFilters.status}
				class="focus:border-primary-500 focus:ring-primary-500 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:ring-1 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			>
				<option value="">الكل</option>
				{#each propertyStatuses as status}
					<option value={status.value}>{status.label}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Action buttons -->
	<div class="mt-4 flex justify-end space-x-2 space-x-reverse">
		<Button on:click={resetFilters} variant="outline" color="gray" size="sm">إعادة تعيين</Button>
		<Button on:click={applyFilters} variant="solid" color="primary" size="sm">تطبيق</Button>
	</div>
</div>
