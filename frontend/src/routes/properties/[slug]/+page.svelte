<!-- src/routes/properties/[slug]/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fetchPropertyBySlug } from '$lib/stores/properties';
	import { addToast } from '$lib/stores/ui';
	import PropertyImages from '$lib/components/property/PropertyImages.svelte';
	import PropertyDetails from '$lib/components/property/PropertyDetails.svelte';
	import PropertyMap from '$lib/components/property/PropertyMap.svelte';

	let property = null;
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			const { slug } = $page.params;
			const data = await fetchPropertyBySlug(slug);

			if (!data) {
				error = 'العقار غير موجود';
				return;
			}

			property = data;
		} catch (err) {
			error = err.message;
			addToast('حدث خطأ أثناء تحميل بيانات العقار', 'error');
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{property ? property.title : 'تحميل العقار...'} | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
	{#if loading}
		<div class="py-12 text-center">
			<i class="fas fa-spinner fa-spin text-3xl text-blue-600"></i>
			<p class="mt-4 text-slate-600">جاري تحميل بيانات العقار...</p>
		</div>
	{:else if error}
		<div class="py-12 text-center">
			<i class="fas fa-exclamation-circle text-3xl text-red-500"></i>
			<p class="mt-4 text-red-600">{error}</p>
			<a href="/properties" class="btn-primary mt-4"> العودة إلى العقارات </a>
		</div>
	{:else if property}
		<div class="space-y-8">
			<!-- Back Navigation -->
			<div>
				<a href="/properties" class="text-slate-600 hover:text-blue-600">
					<i class="fas fa-arrow-right ml-2"></i>
					العودة إلى العقارات
				</a>
			</div>

			<!-- Property Images -->
			<PropertyImages images={property.media} mainTitle={property.title} />

			<!-- Content Grid -->
			<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
				<!-- Main Content -->
				<div class="lg:col-span-2">
					<PropertyDetails {property} />
				</div>

				<!-- Sidebar -->
				<div class="space-y-6">
					<!-- Price Card -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<div class="mb-2 text-2xl font-bold text-blue-600">
							{property.market_value
								? property.market_value.toLocaleString() + ' ريال'
								: 'السعر عند الطلب'}
						</div>
						<div class="flex flex-wrap gap-2">
							<span
								class="inline-flex items-center rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-800"
							>
								{property.property_type_display}
							</span>
							<span
								class="inline-flex items-center rounded px-2 py-1 text-xs font-medium {property.status ===
								'available'
									? 'bg-green-100 text-green-800'
									: property.status === 'auction'
										? 'bg-amber-100 text-amber-800'
										: 'bg-slate-100 text-slate-800'}"
							>
								{property.status_display}
							</span>
						</div>
					</div>

					<!-- Location Map -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-slate-900">الموقع</h2>
						<PropertyMap
							latitude={property.location?.latitude}
							longitude={property.location?.longitude}
							editable={false}
						/>
						<div class="mt-4 space-y-2 text-sm text-slate-600">
							<div><i class="fas fa-map-marker-alt ml-2"></i>{property.address}</div>
							<div><i class="fas fa-city ml-2"></i>{property.city}</div>
						</div>
					</div>

					<!-- Contact Card -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-slate-900">تواصل مع المالك</h2>
						{#if property.owner_details}
							<div class="mb-4 flex items-center">
								<img
									src={property.owner_details.avatar_url || '/images/default-avatar.jpg'}
									alt="صورة المالك"
									class="h-12 w-12 rounded-full border object-cover"
								/>
								<div class="mr-3">
									<div class="font-medium">
										{property.owner_details.first_name}
										{property.owner_details.last_name}
									</div>
									<div class="text-sm text-slate-500">
										{property.owner_details.primary_role?.name || 'مالك العقار'}
									</div>
								</div>
							</div>
							<div class="space-y-3">
								{#if property.owner_details.phone_number}
									<a
										href={`tel:${property.owner_details.phone_number}`}
										class="flex items-center text-slate-700 hover:text-blue-600"
									>
										<i class="fas fa-phone ml-3 text-blue-600"></i>
										<span>{property.owner_details.phone_number}</span>
									</a>
								{/if}
								{#if property.owner_details.email}
									<a
										href={`mailto:${property.owner_details.email}`}
										class="flex items-center text-slate-700 hover:text-blue-600"
									>
										<i class="fas fa-envelope ml-3 text-blue-600"></i>
										<span>{property.owner_details.email}</span>
									</a>
								{/if}
							</div>
						{/if}
						<button class="btn-primary mt-4 w-full">
							<i class="fas fa-comments ml-2"></i>
							إرسال رسالة
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
