<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let property;
	export let showActions = true;
	export let compact = false;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Handle property click
	function handlePropertyClick() {
		if (property.slug) {
			dispatch('select', { property });
		}
	}

	// Format price with thousand separator
	function formatPrice(price) {
		return price?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') || '0';
	}

	// Get main image URL
	$: mainImage =
		property.main_image_url ||
		(property.images && JSON.parse(property.images)[0]?.path) ||
		'/images/placeholder-property.jpg';
</script>

<div
	class="overflow-hidden rounded-lg bg-white shadow-md transition-shadow duration-300 hover:shadow-lg dark:bg-gray-800 {compact
		? 'h-64'
		: 'h-[26rem]'}"
	on:click={handlePropertyClick}
	on:keydown={(e) => e.key === 'Enter' && handlePropertyClick()}
	role="button"
	tabindex="0"
>
	<!-- Property Image -->
	<div class="relative h-48 overflow-hidden">
		<img
			src={mainImage}
			alt={property.title}
			class="h-full w-full object-cover transition-transform duration-500 hover:scale-110"
		/>

		<!-- Property Status Badge -->
		{#if property.status}
			<div
				class="absolute top-2 right-2 rounded px-2 py-1 text-xs font-semibold
        {property.status === 'active'
					? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
					: property.status === 'sold'
						? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
						: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'}"
			>
				{property.status === 'active'
					? 'نشط'
					: property.status === 'sold'
						? 'مباع'
						: property.status === 'pending_approval'
							? 'قيد الموافقة'
							: property.status === 'under_contract'
								? 'تحت التعاقد'
								: property.status === 'inactive'
									? 'غير نشط'
									: property.status === 'rejected'
										? 'مرفوض'
										: property.status}
			</div>
		{/if}

		<!-- Property Type Badge -->
		{#if property.property_type}
			<div
				class="bg-opacity-50 absolute top-2 left-2 rounded bg-black px-2 py-1 text-xs text-white"
			>
				{property.property_type === 'apartment'
					? 'شقة'
					: property.property_type === 'villa'
						? 'فيلا'
						: property.property_type === 'land'
							? 'أرض'
							: property.property_type === 'commercial'
								? 'تجاري'
								: property.property_type === 'building'
									? 'مبنى'
									: property.property_type === 'farm'
										? 'مزرعة'
										: property.property_type === 'industrial'
											? 'صناعي'
											: property.property_type === 'office'
												? 'مكتب'
												: property.property_type === 'retail'
													? 'محل تجاري'
													: property.property_type === 'mixed_use'
														? 'متعدد الاستخدامات'
														: property.property_type}
			</div>
		{/if}
	</div>

	<!-- Property Info -->
	<div class="p-4">
		<!-- Title and Price -->
		<div class="mb-2 flex items-start justify-between">
			<h3 class="line-clamp-1 text-lg font-semibold text-gray-900 dark:text-white">
				{property.title}
			</h3>
			<span class="font-bold whitespace-nowrap text-green-600 dark:text-green-400"
				>{formatPrice(property.estimated_value)} ريال</span
			>
		</div>

		<!-- Location -->
		{#if property.city || property.district}
			<div class="mb-3 flex items-start">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="mt-0.5 ml-1 h-5 w-5 text-gray-500 dark:text-gray-400"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
						clip-rule="evenodd"
					/>
				</svg>
				<span class="line-clamp-1 text-gray-600 dark:text-gray-300">
					{#if property.district && property.city}
						{property.district}، {property.city}
					{:else if property.district}
						{property.district}
					{:else if property.city}
						{property.city}
					{/if}
				</span>
			</div>
		{/if}

		{#if !compact}
			<!-- Property Features -->
			<div class="mb-3 flex justify-between text-sm text-gray-600 dark:text-gray-300">
				{#if property.area}
					<div class="flex items-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="mr-1 h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
							/>
						</svg>
						<span>{property.area} م²</span>
					</div>
				{/if}

				{#if property.bedrooms !== undefined && property.bedrooms !== null}
					<div class="flex items-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="mr-1 h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
							/>
						</svg>
						<span>{property.bedrooms} غرف</span>
					</div>
				{/if}

				{#if property.bathrooms !== undefined && property.bathrooms !== null}
					<div class="flex items-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="mr-1 h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"
							/>
						</svg>
						<span>{property.bathrooms} حمامات</span>
					</div>
				{/if}
			</div>

			<!-- Property Description -->
			<p class="mb-4 line-clamp-2 text-sm text-gray-600 dark:text-gray-300">
				{property.description || 'لا يوجد وصف متاح لهذا العقار.'}
			</p>
		{/if}

		<!-- Actions -->
		{#if showActions && !compact}
			<div
				class="mt-2 flex items-center justify-between border-t border-gray-200 pt-2 dark:border-gray-700"
			>
				<button
					class="rounded-md bg-blue-600 px-3 py-1 text-sm text-white transition hover:bg-blue-700"
					on:click|stopPropagation={() => dispatch('view', { property })}
				>
					عرض التفاصيل
				</button>

				{#if property.is_verified}
					<div class="flex items-center text-sm text-green-600 dark:text-green-400">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="mr-1 h-5 w-5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
							/>
						</svg>
						<span>موثق</span>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
