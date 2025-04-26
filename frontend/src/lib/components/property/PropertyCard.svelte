<!-- src/lib/components/property/PropertyCard.svelte -->
<script>
	export let property;
	export let compact = false;

	function formatPrice(price) {
		return new Intl.NumberFormat('ar-SA').format(price);
	}
</script>

<a
	href="/properties/{property.slug}"
	class="group block overflow-hidden rounded-xl border border-slate-200 bg-white transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
>
	<!-- Image Section -->
	<div class="relative aspect-[4/3] overflow-hidden">
		{#if property.media && property.media[0]}
			<img
				src={property.media[0].file_url}
				alt={property.title}
				class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
				loading="lazy"
			/>
		{:else}
			<div class="flex h-full w-full items-center justify-center bg-slate-100">
				<i class="fas fa-home text-4xl text-slate-300"></i>
			</div>
		{/if}

		<!-- Status Badge -->
		<div class="absolute top-3 right-3">
			<span
				class="rounded-full px-3 py-1 text-sm font-medium {property.status === 'available'
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
				<span class="rounded-full bg-blue-600 px-3 py-1 text-sm text-white"> مميز </span>
			</div>
		{/if}
	</div>

	<!-- Content Section -->
	<div class="p-4">
		<h3 class="mb-2 line-clamp-1 text-lg font-semibold text-slate-900">{property.title}</h3>

		<div class="mb-3 flex items-center gap-1 text-sm text-slate-600">
			<i class="fas fa-map-marker-alt"></i>
			<span class="line-clamp-1">{property.address}</span>
		</div>

		{#if !compact}
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
		{/if}

		<!-- Price & Type -->
		<div class="flex items-center justify-between border-t border-slate-100 pt-4">
			<div class="text-lg font-bold text-blue-600">
				{property.market_value ? formatPrice(property.market_value) + ' ريال' : 'السعر عند الطلب'}
			</div>
			<div class="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
				{property.property_type_display}
			</div>
		</div>
	</div>
</a>
