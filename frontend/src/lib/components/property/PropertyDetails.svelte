<!-- src/lib/components/property/PropertyDetails.svelte -->
<script>
	export let property;
	export let showAllFeatures = false;
	export let showAllAmenities = false;

	function formatNumber(num) {
		return new Intl.NumberFormat('ar-SA').format(num);
	}
</script>

<div class="space-y-8">
	<!-- Basic Info -->
	<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
		<h2 class="mb-6 text-xl font-bold text-slate-900">معلومات أساسية</h2>

		<div class="grid grid-cols-2 gap-6 md:grid-cols-4">
			{#if property.property_type}
				<div class="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
					<i class="fas fa-home mb-2 text-2xl text-blue-600"></i>
					<div class="text-sm text-slate-600">نوع العقار</div>
					<div class="mt-1 font-semibold text-slate-900">{property.property_type_display}</div>
				</div>
			{/if}

			{#if property.size_sqm}
				<div class="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
					<i class="fas fa-ruler-combined mb-2 text-2xl text-blue-600"></i>
					<div class="text-sm text-slate-600">المساحة</div>
					<div class="mt-1 font-semibold text-slate-900">{formatNumber(property.size_sqm)} م²</div>
				</div>
			{/if}

			{#if property.bedrooms}
				<div class="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
					<i class="fas fa-bed mb-2 text-2xl text-blue-600"></i>
					<div class="text-sm text-slate-600">غرف النوم</div>
					<div class="mt-1 font-semibold text-slate-900">{property.bedrooms}</div>
				</div>
			{/if}

			{#if property.bathrooms}
				<div class="rounded-lg border border-slate-200 bg-slate-50 p-4 text-center">
					<i class="fas fa-bath mb-2 text-2xl text-blue-600"></i>
					<div class="text-sm text-slate-600">الحمامات</div>
					<div class="mt-1 font-semibold text-slate-900">{property.bathrooms}</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Description -->
	<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
		<h2 class="mb-4 text-xl font-bold text-slate-900">وصف العقار</h2>
		<div class="prose max-w-none leading-relaxed text-slate-700">
			{property.description}
		</div>
	</div>

	<!-- Features -->
	{#if property.features && property.features.length > 0}
		<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-6 text-xl font-bold text-slate-900">المميزات</h2>

			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each showAllFeatures ? property.features : property.features.slice(0, 6) as feature}
					<div class="flex items-center space-x-3 space-x-reverse">
						<div
							class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-50"
						>
							<i class="fas fa-check text-blue-600"></i>
						</div>
						<span class="text-slate-700">{feature}</span>
					</div>
				{/each}
			</div>

			{#if property.features.length > 6}
				<button
					class="mt-6 flex items-center text-blue-600 transition-colors hover:text-blue-700"
					on:click={() => (showAllFeatures = !showAllFeatures)}
				>
					{#if showAllFeatures}
						<i class="fas fa-chevron-up ml-2"></i>
						عرض أقل
					{:else}
						<i class="fas fa-chevron-down ml-2"></i>
						عرض المزيد ({property.features.length - 6})
					{/if}
				</button>
			{/if}
		</div>
	{/if}

	<!-- Specifications -->
	{#if property.specifications && Object.keys(property.specifications).length > 0}
		<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
			<h2 class="mb-6 text-xl font-bold text-slate-900">المواصفات</h2>

			<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
				{#each Object.entries(property.specifications) as [key, value]}
					<div class="flex items-center justify-between border-b border-slate-100 py-3">
						<span class="text-slate-600">{key}</span>
						<span class="font-medium text-slate-900">{value}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
