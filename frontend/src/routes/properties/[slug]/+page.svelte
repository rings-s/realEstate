<!-- src/routes/properties/[slug]/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		currentProperty,
		loadingProperties,
		propertyError,
		fetchPropertyBySlug
	} from '$lib/stores/properties';
	import { isAuthenticated, hasPermission, user } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
	import PropertyImages from '$lib/components/property/PropertyImages.svelte';
	import PropertyDetails from '$lib/components/property/PropertyDetails.svelte';
	import PropertyMap from '$lib/components/property/PropertyMap.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let property = null;
	let loading = true;
	let error = null;
	let showContactForm = false;
	let message = '';

	// Initialize data
	onMount(async () => {
		try {
			const { slug } = $page.params;
			loading = true;

			if (!slug) {
				error = 'معرف العقار غير صالح';
				return;
			}

			const data = await fetchPropertyBySlug(slug);

			if (!data) {
				error = 'العقار غير موجود أو غير متاح';
				return;
			}

			property = data;

			// Make sure property has the expected structure
			if (!property.media) property.media = [];
			if (!property.location) property.location = { latitude: null, longitude: null };
		} catch (err) {
			console.error('Error loading property:', err);
			error = err.message || 'حدث خطأ أثناء تحميل بيانات العقار';
			addToast('حدث خطأ أثناء تحميل بيانات العقار', 'error');
		} finally {
			loading = false;
		}
	});

	// Format price with currency
	function formatPrice(price) {
		if (!price) return 'السعر عند الطلب';

		return new Intl.NumberFormat('ar-SA', {
			style: 'decimal',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(price);
	}

	// Handle contact form submission
	async function handleContactSubmit() {
		if (!$isAuthenticated) {
			addToast('يجب تسجيل الدخول للتواصل مع المالك', 'warning');
			goto('/login?redirect=' + $page.url.pathname);
			return;
		}

		if (!message.trim()) {
			addToast('يرجى كتابة رسالة', 'error');
			return;
		}

		try {
			// API call to send message would go here
			addToast('تم إرسال رسالتك بنجاح', 'success');
			showContactForm = false;
			message = '';
		} catch (error) {
			addToast('حدث خطأ أثناء إرسال الرسالة', 'error');
		}
	}

	// Handle favorite toggle
	async function toggleFavorite() {
		if (!$isAuthenticated) {
			addToast('يجب تسجيل الدخول لإضافة العقار للمفضلة', 'warning');
			return;
		}

		try {
			// API call to toggle favorite would go here
			property.is_favorite = !property.is_favorite;
			addToast(
				property.is_favorite ? 'تمت إضافة العقار للمفضلة' : 'تمت إزالة العقار من المفضلة',
				'success'
			);
		} catch (error) {
			addToast('حدث خطأ أثناء تحديث المفضلة', 'error');
		}
	}
</script>

<svelte:head>
	<title>{property ? property.title : 'تحميل العقار...'} | منصة المزادات العقارية</title>
	<meta name="description" content={property?.description?.substring(0, 160) || ''} />
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
	{#if loading}
		<div class="flex min-h-[60vh] items-center justify-center">
			<div class="text-center">
				<LoadingSpinner size="lg" />
				<p class="mt-4 text-lg text-slate-600">جاري تحميل بيانات العقار...</p>
			</div>
		</div>
	{:else if error}
		<div class="flex min-h-[60vh] items-center justify-center">
			<div class="text-center">
				<div class="mb-4 text-red-500">
					<i class="fas fa-exclamation-circle text-5xl"></i>
				</div>
				<h2 class="mb-2 text-2xl font-bold text-slate-900">عذراً</h2>
				<p class="mb-4 text-slate-600">{error}</p>
				<a href="/properties" class="btn-primary">
					<i class="fas fa-arrow-right ml-2"></i>
					العودة إلى العقارات
				</a>
			</div>
		</div>
	{:else if property}
		<div class="space-y-8">
			<!-- Navigation -->
			<div class="flex items-center justify-between">
				<a href="/properties" class="text-slate-600 hover:text-blue-600">
					<i class="fas fa-arrow-right ml-2"></i>
					العودة إلى العقارات
				</a>

				{#if $isAuthenticated && hasPermission('edit_property') && property.owner?.id === $user?.id}
					<div class="flex gap-2">
						<a href="/properties/{property.slug}/edit" class="btn-secondary">
							<i class="fas fa-edit ml-2"></i>
							تعديل العقار
						</a>
						{#if property.status === 'available'}
							<a href="/auctions/create?property={property.id}" class="btn-primary">
								<i class="fas fa-gavel ml-2"></i>
								إنشاء مزاد
							</a>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Property Title -->
			<div>
				<h1 class="text-3xl font-bold text-slate-900">{property.title}</h1>
				<div class="mt-2 flex flex-wrap items-center gap-4">
					<div class="flex items-center text-slate-600">
						<i class="fas fa-map-marker-alt ml-2"></i>
						{property.address || 'عنوان غير متوفر'}
					</div>
					<div class="flex items-center text-slate-600">
						<i class="fas fa-calendar ml-2"></i>
						تم النشر {new Date(property.created_at).toLocaleDateString('ar-SA')}
					</div>
				</div>
			</div>

			<!-- Property Images -->
			<PropertyImages images={property.media || []} mainTitle={property.title} />

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
						<div class="mb-4 flex items-center justify-between">
							<div>
								<div class="text-2xl font-bold text-blue-600">
									{property.market_value
										? formatPrice(property.market_value) + ' ريال'
										: 'السعر عند الطلب'}
								</div>
								{#if property.size_sqm && property.market_value}
									<div class="mt-1 text-sm text-slate-600">
										{formatPrice(property.market_value / property.size_sqm)} ريال/م²
									</div>
								{/if}
							</div>
							<button
								class="rounded-full p-2 text-slate-400 hover:bg-slate-50 hover:text-red-500"
								on:click={toggleFavorite}
								title={property.is_favorite ? 'إزالة من المفضلة' : 'إضافة للمفضلة'}
							>
								<i class="fas fa-heart text-xl {property.is_favorite ? 'text-red-500' : ''}"></i>
							</button>
						</div>

						<div class="flex flex-wrap gap-2">
							<span
								class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-800"
							>
								{property.property_type_display || property.property_type || 'نوع العقار غير محدد'}
							</span>
							<span
								class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {property.status ===
								'available'
									? 'bg-green-100 text-green-800'
									: property.status === 'auction'
										? 'bg-amber-100 text-amber-800'
										: 'bg-slate-100 text-slate-800'}"
							>
								{property.status_display || property.status || 'الحالة غير محددة'}
							</span>
						</div>
					</div>

					<!-- Location Map -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-slate-900">الموقع</h2>
						<PropertyMap
							latitude={property.location?.latitude || 24.774265}
							longitude={property.location?.longitude || 46.738586}
							editable={false}
						/>
						<div class="mt-4 space-y-2 text-sm text-slate-600">
							<div>
								<i class="fas fa-map-marker-alt ml-2"></i>
								{property.address || 'العنوان غير متوفر'}
							</div>
							<div>
								<i class="fas fa-city ml-2"></i>
								{property.city || 'المدينة غير متوفرة'}
							</div>
						</div>
					</div>

					<!-- Owner/Contact Card -->
					{#if property.owner_details}
						<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
							<h2 class="mb-4 text-xl font-bold text-slate-900">تواصل مع المالك</h2>
							<div class="mb-4 flex items-center">
								<img
									src={property.owner_details.avatar_url || '/images/default-avatar.jpg'}
									alt="صورة المالك"
									class="h-12 w-12 rounded-full border object-cover"
								/>
								<div class="mr-3">
									<div class="font-medium">
										{property.owner_details.first_name || ''}
										{property.owner_details.last_name || ''}
									</div>
									<div class="text-sm text-slate-500">
										{property.owner_details.primary_role?.name || 'مالك العقار'}
									</div>
								</div>
							</div>

							{#if !showContactForm}
								<button class="btn-primary w-full" on:click={() => (showContactForm = true)}>
									<i class="fas fa-comments ml-2"></i>
									تواصل مع المالك
								</button>
							{:else}
								<form on:submit|preventDefault={handleContactSubmit} class="space-y-4">
									<div>
										<label for="message" class="mb-1 block text-sm font-medium text-slate-700"
											>الرسالة</label
										>
										<textarea
											id="message"
											bind:value={message}
											rows="4"
											class="input"
											placeholder="اكتب رسالتك هنا..."
										></textarea>
									</div>
									<div class="flex gap-2">
										<button
											type="button"
											class="btn-secondary flex-1"
											on:click={() => (showContactForm = false)}
										>
											إلغاء
										</button>
										<button type="submit" class="btn-primary flex-1"> إرسال الرسالة </button>
									</div>
								</form>
							{/if}

							{#if property.owner_details.phone_number}
								<div class="mt-4 border-t border-slate-100 pt-4">
									<a
										href={`tel:${property.owner_details.phone_number}`}
										class="flex items-center justify-center gap-2 text-slate-700 hover:text-blue-600"
									>
										<i class="fas fa-phone"></i>
										<span>{property.owner_details.phone_number}</span>
									</a>
								</div>
							{/if}
						</div>
					{/if}

					<!-- Share Card -->
					<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
						<h2 class="mb-4 text-xl font-bold text-slate-900">مشاركة العقار</h2>
						<div class="flex justify-center gap-4">
							<button
								class="flex items-center justify-center rounded-full bg-blue-500 p-3 text-white hover:bg-blue-600"
								on:click={() =>
									window.open(
										`https://twitter.com/intent/tweet?url=${encodeURIComponent(
											window.location.href
										)}&text=${encodeURIComponent(property.title)}`,
										'_blank'
									)}
							>
								<i class="fab fa-twitter text-xl"></i>
							</button>
							<button
								class="flex items-center justify-center rounded-full bg-blue-600 p-3 text-white hover:bg-blue-700"
								on:click={() =>
									window.open(
										`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
											window.location.href
										)}`,
										'_blank'
									)}
							>
								<i class="fab fa-facebook-f text-xl"></i>
							</button>
							<button
								class="flex items-center justify-center rounded-full bg-green-500 p-3 text-white hover:bg-green-600"
								on:click={() =>
									window.open(
										`https://wa.me/?text=${encodeURIComponent(
											property.title + '\n' + window.location.href
										)}`,
										'_blank'
									)}
							>
								<i class="fab fa-whatsapp text-xl"></i>
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
