<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fetchPropertyBySlug } from '$lib/stores/properties';
	import { isAuthenticated, hasPermission } from '$lib/stores/auth';
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
			<!-- Navigation -->
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
						<!-- Price details -->
					</div>

					<!-- Location Card -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-slate-900">الموقع</h2>
						<PropertyMap
							latitude={property.location?.latitude}
							longitude={property.location?.longitude}
							editable={false}
						/>
					</div>

					<!-- Contact Card -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<!-- Contact details -->
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
