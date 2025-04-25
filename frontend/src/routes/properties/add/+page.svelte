<!-- src/routes/properties/add/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { createProperty } from '$lib/stores/properties';
	import { goto } from '$app/navigation';
	import { addToast } from '$lib/stores/ui';
	import RoomEditor from '$lib/components/property/RoomEditor.svelte';

	let property = {
		title: '',
		property_type: 'residential',
		description: '',
		size_sqm: '',
		bedrooms: '',
		bathrooms: '',
		floors: '',
		address: '',
		city: '',
		state: '',
		postal_code: '',
		country: 'المملكة العربية السعودية',
		market_value: '',
		features: [],
		rooms: [], // Add rooms array
		location: {
			latitude: null,
			longitude: null
		}
	};

	let newFeature = '';
	let uploadedImages = [];
	let loading = false;
	let error = '';
	let currentStep = 1;
	let totalSteps = 4; // Add one more step for rooms

	let map = null;
	let marker = null;

	const propertyTypes = [
		{ value: 'residential', label: 'سكني' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'land', label: 'أرض' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'mixed_use', label: 'متعدد الاستخدام' }
	];

	const cityOptions = [
		'الرياض',
		'جدة',
		'مكة المكرمة',
		'المدينة المنورة',
		'الدمام',
		'الخبر',
		'جازان',
		'حائل',
		'تبوك',
		'أبها'
	];

	onMount(() => {
		// Load Leaflet map script
		const script = document.createElement('script');
		script.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
		script.integrity =
			'sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==';
		script.crossOrigin = '';

		const link = document.createElement('link');
		link.rel = 'stylesheet';
		link.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css';
		link.integrity =
			'sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==';
		link.crossOrigin = '';

		document.head.appendChild(link);
		document.body.appendChild(script);
		script.onload = initMap;

		return () => {
			if (map) {
				map.remove();
				map = null;
			}
		};
	});

	function initMap() {
		if (typeof L === 'undefined') {
			setTimeout(initMap, 100);
			return;
		}

		if (!map && currentStep === 2) {
			setTimeout(() => {
				// Default center: Riyadh, Saudi Arabia
				const defaultLat = 24.774265;
				const defaultLng = 46.738586;

				map = L.map('property-map').setView([defaultLat, defaultLng], 13);

				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
				}).addTo(map);

				// Add marker if we have coordinates
				if (property.location.latitude && property.location.longitude) {
					marker = L.marker([property.location.latitude, property.location.longitude], {
						draggable: true
					}).addTo(map);
				} else {
					// Add draggable marker at center
					marker = L.marker([defaultLat, defaultLng], {
						draggable: true
					}).addTo(map);

					// Update property with default location
					property.location = {
						latitude: defaultLat,
						longitude: defaultLng
					};
				}

				// Update coordinates when marker is dragged
				marker.on('dragend', function (event) {
					const position = marker.getLatLng();
					property.location = {
						latitude: position.lat,
						longitude: position.lng
					};
				});

				// Update marker when clicking on the map
				map.on('click', function (e) {
					if (marker) {
						marker.setLatLng(e.latlng);
					} else {
						marker = L.marker(e.latlng, {
							draggable: true
						}).addTo(map);
					}

					property.location = {
						latitude: e.latlng.lat,
						longitude: e.latlng.lng
					};
				});
			}, 100);
		}
	}

	function addFeature() {
		if (newFeature.trim()) {
			property.features = [...property.features, newFeature.trim()];
			newFeature = '';
		}
	}

	function removeFeature(index) {
		property.features = property.features.filter((_, i) => i !== index);
	}

	function handleStep(direction) {
		if (direction === 'next' && currentStep < totalSteps) {
			currentStep += 1;
			if (currentStep === 2) {
				setTimeout(initMap, 100);
			}
		} else if (direction === 'prev' && currentStep > 1) {
			currentStep -= 1;
		}
	}

	function handleImageUpload(event) {
		const files = Array.from(event.target.files);

		// Validate files
		const validFiles = files.filter((file) => {
			// Check file type
			if (!file.type.match('image.*')) {
				addToast(`${file.name} ليس ملف صورة صالح`, 'error');
				return false;
			}

			// Check file size (max 5MB)
			if (file.size > 5 * 1024 * 1024) {
				addToast(`${file.name} أكبر من الحد المسموح (5 ميجابايت)`, 'error');
				return false;
			}

			return true;
		});

		// Create previews for valid files
		validFiles.forEach((file) => {
			const reader = new FileReader();
			reader.onload = (e) => {
				uploadedImages = [
					...uploadedImages,
					{
						file,
						preview: e.target.result,
						name: file.name
					}
				];
			};
			reader.readAsDataURL(file);
		});
	}

	function removeImage(index) {
		uploadedImages = uploadedImages.filter((_, i) => i !== index);
	}

	// Handle room updates from RoomEditor
	function handleRoomUpdate(event) {
		property.rooms = event.detail.rooms;
	}

	async function handleSubmit() {
		loading = true;
		error = '';

		try {
			// Prepare the property data
			const propertyData = {
				...property,
				features: property.features.length ? property.features : undefined,
				rooms: property.rooms.length ? property.rooms : undefined, // Include rooms data
				market_value: property.market_value ? Number(property.market_value) : undefined,
				size_sqm: property.size_sqm ? Number(property.size_sqm) : undefined,
				bedrooms: property.bedrooms ? Number(property.bedrooms) : undefined,
				bathrooms: property.bathrooms ? Number(property.bathrooms) : undefined,
				floors: property.floors ? Number(property.floors) : undefined
			};

			// Create the property
			const result = await createProperty(propertyData);

			if (!result.success) {
				error = result.error || 'فشل في إنشاء العقار';
				loading = false;
				return;
			}

			// Handle image uploads if needed
			// This would typically be done after property creation
			// and would involve another API call to upload images

			addToast('تم إنشاء العقار بنجاح', 'success');
			goto('/properties');
		} catch (err) {
			error = err.message || 'حدث خطأ أثناء إنشاء العقار';
			console.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>إضافة عقار جديد | منصة المزادات العقارية</title>
</svelte:head>

<div>
	<div class="mb-6">
		<a href="/properties" class="inline-flex items-center text-slate-600 hover:text-blue-600">
			<i class="fas fa-arrow-right ml-2"></i>
			العودة إلى العقارات
		</a>
	</div>

	<div class="overflow-hidden rounded-lg bg-white shadow-md">
		<div class="border-b p-6">
			<h1 class="text-2xl font-bold text-slate-900">إضافة عقار جديد</h1>
			<p class="mt-1 text-slate-600">قم بإدخال بيانات العقار بشكل كامل للحصول على أفضل النتائج</p>
		</div>

		<!-- Step Indicator -->
		<div class="border-b bg-slate-50 px-6 py-4">
			<div class="flex items-center">
				<div class="relative flex items-center">
					<div
						class={`flex h-10 w-10 items-center justify-center rounded-full ${currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-300 text-slate-600'}`}
					>
						<i class="fas fa-home"></i>
					</div>
					<div class="absolute -bottom-6 w-max" style="right: -40px">
						<span
							class={`text-sm ${currentStep === 1 ? 'font-medium text-blue-600' : 'text-slate-500'}`}
						>
							البيانات الأساسية
						</span>
					</div>
				</div>

				<div class={`mx-2 h-1 flex-1 ${currentStep >= 2 ? 'bg-blue-600' : 'bg-slate-300'}`}></div>

				<div class="relative flex items-center">
					<div
						class={`flex h-10 w-10 items-center justify-center rounded-full ${currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-300 text-slate-600'}`}
					>
						<i class="fas fa-map-marker-alt"></i>
					</div>
					<div class="absolute -bottom-6 w-max" style="right: -40px">
						<span
							class={`text-sm ${currentStep === 2 ? 'font-medium text-blue-600' : 'text-slate-500'}`}
						>
							الموقع والعنوان
						</span>
					</div>
				</div>

				<div class={`mx-2 h-1 flex-1 ${currentStep >= 3 ? 'bg-blue-600' : 'bg-slate-300'}`}></div>

				<div class="relative flex items-center">
					<div
						class={`flex h-10 w-10 items-center justify-center rounded-full ${currentStep >= 3 ? 'bg-blue-600 text-white' : 'bg-slate-300 text-slate-600'}`}
					>
						<i class="fas fa-door-open"></i>
					</div>
					<div class="absolute -bottom-6 w-max" style="right: -40px">
						<span
							class={`text-sm ${currentStep === 3 ? 'font-medium text-blue-600' : 'text-slate-500'}`}
						>
							الغرف والمرافق
						</span>
					</div>
				</div>

				<div class={`mx-2 h-1 flex-1 ${currentStep >= 4 ? 'bg-blue-600' : 'bg-slate-300'}`}></div>

				<div class="relative flex items-center">
					<div
						class={`flex h-10 w-10 items-center justify-center rounded-full ${currentStep >= 4 ? 'bg-blue-600 text-white' : 'bg-slate-300 text-slate-600'}`}
					>
						<i class="fas fa-images"></i>
					</div>
					<div class="absolute -bottom-6 w-max" style="right: -30px">
						<span
							class={`text-sm ${currentStep === 4 ? 'font-medium text-blue-600' : 'text-slate-500'}`}
						>
							الصور والمميزات
						</span>
					</div>
				</div>
			</div>
		</div>

		<div class="mt-6 p-6">
			{#if error}
				<div class="mb-6 rounded border-l-4 border-red-400 bg-red-50 p-4">
					<div class="flex">
						<div class="flex-shrink-0">
							<i class="fas fa-exclamation-circle text-red-400"></i>
						</div>
						<div class="mr-3">
							<p class="text-sm text-red-700">{error}</p>
						</div>
					</div>
				</div>
			{/if}

			<form on:submit|preventDefault={handleSubmit}>
				<!-- Step 1: Basic Information -->
				{#if currentStep === 1}
					<div class="space-y-4">
						<div>
							<label for="title" class="required mb-1 block text-sm font-medium text-slate-700"
								>عنوان العقار</label
							>
							<input
								type="text"
								id="title"
								bind:value={property.title}
								required
								class="input"
								placeholder="أدخل عنوان العقار"
							/>
							<p class="mt-1 text-sm text-slate-500">اختر عنوانًا واضحًا ومميزًا للعقار</p>
						</div>

						<div>
							<label
								for="property_type"
								class="required mb-1 block text-sm font-medium text-slate-700">نوع العقار</label
							>
							<select id="property_type" bind:value={property.property_type} required class="input">
								{#each propertyTypes as type}
									<option value={type.value}>{type.label}</option>
								{/each}
							</select>
						</div>

						<div>
							<label
								for="description"
								class="required mb-1 block text-sm font-medium text-slate-700">وصف العقار</label
							>
							<textarea
								id="description"
								bind:value={property.description}
								required
								rows="5"
								class="input"
								placeholder="اكتب وصفًا تفصيليًا للعقار..."
							></textarea>
							<p class="mt-1 text-sm text-slate-500">
								قم بوصف العقار بشكل مفصل، واذكر جميع المميزات المهمة
							</p>
						</div>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							<div>
								<label for="size_sqm" class="mb-1 block text-sm font-medium text-slate-700"
									>المساحة (متر مربع)</label
								>
								<input
									type="number"
									id="size_sqm"
									bind:value={property.size_sqm}
									min="1"
									class="input"
									placeholder="المساحة"
								/>
							</div>

							<div>
								<label for="market_value" class="mb-1 block text-sm font-medium text-slate-700"
									>القيمة التقديرية (ريال)</label
								>
								<input
									type="number"
									id="market_value"
									bind:value={property.market_value}
									min="0"
									class="input"
									placeholder="القيمة التقديرية"
								/>
							</div>
						</div>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
							<div>
								<label for="bedrooms" class="mb-1 block text-sm font-medium text-slate-700"
									>عدد غرف النوم</label
								>
								<input
									type="number"
									id="bedrooms"
									bind:value={property.bedrooms}
									min="0"
									class="input"
									placeholder="عدد غرف النوم"
								/>
							</div>

							<div>
								<label for="bathrooms" class="mb-1 block text-sm font-medium text-slate-700"
									>عدد الحمامات</label
								>
								<input
									type="number"
									id="bathrooms"
									bind:value={property.bathrooms}
									min="0"
									class="input"
									placeholder="عدد الحمامات"
								/>
							</div>

							<div>
								<label for="floors" class="mb-1 block text-sm font-medium text-slate-700"
									>عدد الطوابق</label
								>
								<input
									type="number"
									id="floors"
									bind:value={property.floors}
									min="0"
									class="input"
									placeholder="عدد الطوابق"
								/>
							</div>
						</div>
					</div>
				{:else if currentStep === 2}
					<div class="space-y-4">
						<div>
							<label for="address" class="required mb-1 block text-sm font-medium text-slate-700"
								>العنوان</label
							>
							<input
								type="text"
								id="address"
								bind:value={property.address}
								required
								class="input"
								placeholder="أدخل عنوان العقار بالتفصيل"
							/>
						</div>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							<div>
								<label for="city" class="required mb-1 block text-sm font-medium text-slate-700"
									>المدينة</label
								>
								<select id="city" bind:value={property.city} required class="input">
									<option value="">اختر المدينة</option>
									{#each cityOptions as city}
										<option value={city}>{city}</option>
									{/each}
								</select>
							</div>

							<div>
								<label for="state" class="mb-1 block text-sm font-medium text-slate-700"
									>المنطقة/المحافظة</label
								>
								<input
									type="text"
									id="state"
									bind:value={property.state}
									class="input"
									placeholder="المنطقة أو المحافظة"
								/>
							</div>
						</div>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							<div>
								<label for="postal_code" class="mb-1 block text-sm font-medium text-slate-700"
									>الرمز البريدي</label
								>
								<input
									type="text"
									id="postal_code"
									bind:value={property.postal_code}
									class="input"
									placeholder="الرمز البريدي"
								/>
							</div>

							<div>
								<label for="country" class="mb-1 block text-sm font-medium text-slate-700"
									>الدولة</label
								>
								<input
									type="text"
									id="country"
									bind:value={property.country}
									class="input"
									placeholder="الدولة"
								/>
							</div>
						</div>

						<div>
							<label class="mb-1 block text-sm font-medium text-slate-700">الموقع على الخريطة</label
							>
							<p class="mb-2 text-sm text-slate-500">
								انقر على الخريطة لتحديد موقع العقار بدقة أو اسحب المؤشر
							</p>
							<div id="property-map" class="h-96 rounded-lg border"></div>

							{#if property.location.latitude && property.location.longitude}
								<div class="mt-2 flex gap-4 text-sm">
									<div>
										<span class="text-slate-500">خط العرض:</span>
										<span class="font-medium">{property.location.latitude.toFixed(6)}</span>
									</div>
									<div>
										<span class="text-slate-500">خط الطول:</span>
										<span class="font-medium">{property.location.longitude.toFixed(6)}</span>
									</div>
								</div>
							{/if}
						</div>
					</div>
				{:else if currentStep === 3}
					<!-- Room Editor Step -->
					<div class="space-y-4">
						<h3 class="text-lg font-semibold text-slate-900">إدارة الغرف والمرافق</h3>
						<p class="text-sm text-slate-600">
							أضف الغرف والمرافق الموجودة في العقار مع تفاصيلها المختلفة
						</p>

						<!-- Room Editor Component -->
						<RoomEditor rooms={property.rooms} on:update={handleRoomUpdate} />
					</div>
				{:else if currentStep === 4}
					<div class="space-y-6">
						<div>
							<label class="mb-1 block text-sm font-medium text-slate-700">صور العقار</label>
							<p class="mb-2 text-sm text-slate-500">
								أضف صورًا للعقار بجودة عالية. الحد الأقصى 10 صور
							</p>

							<div class="rounded-lg border-2 border-dashed border-slate-300 p-4 text-center">
								<input
									type="file"
									id="property-images"
									class="hidden"
									accept="image/*"
									multiple
									on:change={handleImageUpload}
								/>
								<label for="property-images" class="cursor-pointer">
									<div class="flex flex-col items-center justify-center py-6">
										<i class="fas fa-cloud-upload-alt mb-2 text-3xl text-slate-400"></i>
										<p class="text-sm text-slate-500">اسحب وأفلت الصور هنا أو انقر للتصفح</p>
										<p class="mt-1 text-xs text-slate-400">PNG، JPG، GIF حتى 5MB</p>
									</div>
								</label>
							</div>

							{#if uploadedImages.length > 0}
								<div class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
									{#each uploadedImages as image, i}
										<div class="relative h-36 overflow-hidden rounded-lg border">
											<img
												src={image.preview}
												alt={image.name}
												class="h-full w-full object-cover"
											/>

											<button
												type="button"
												class="absolute top-1 left-1 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white shadow"
												on:click={() => removeImage(i)}
											>
												<i class="fas fa-times text-xs"></i>
											</button>

											{#if i === 0}
												<div
													class="absolute top-0 right-0 bg-blue-500 px-2 py-1 text-xs text-white"
												>
													الصورة الرئيسية
												</div>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>

						<div>
							<label class="mb-1 block text-sm font-medium text-slate-700">مميزات العقار</label>
							<div class="flex">
								<input
									type="text"
									bind:value={newFeature}
									class="input flex-1"
									placeholder="أضف ميزة للعقار"
									on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
								/>
								<button type="button" class="btn-primary mr-2" on:click={addFeature}>
									إضافة
								</button>
							</div>

							{#if property.features.length > 0}
								<div class="mt-3 flex flex-wrap gap-2">
									{#each property.features as feature, i}
										<div class="flex items-center rounded-full bg-slate-200 px-3 py-1 text-sm">
											<span>{feature}</span>
											<button
												type="button"
												class="mr-1 text-slate-500 hover:text-red-500"
												on:click={() => removeFeature(i)}
											>
												<i class="fas fa-times-circle"></i>
											</button>
										</div>
									{/each}
								</div>
							{:else}
								<p class="mt-2 text-sm text-slate-500">لم يتم إضافة مميزات بعد</p>
							{/if}
						</div>
					</div>
				{/if}

				<div class="mt-8 flex justify-between">
					<button
						type="button"
						class="btn-secondary"
						disabled={currentStep === 1}
						on:click={() => handleStep('prev')}
					>
						<i class="fas fa-arrow-right ml-2"></i>
						السابق
					</button>

					{#if currentStep < totalSteps}
						<button type="button" class="btn-primary" on:click={() => handleStep('next')}>
							التالي
							<i class="fas fa-arrow-left mr-2"></i>
						</button>
					{:else}
						<button type="submit" class="btn-primary" disabled={loading}>
							{#if loading}
								<i class="fas fa-spinner fa-spin ml-2"></i>
								جاري الإنشاء...
							{:else}
								إنشاء العقار
							{/if}
						</button>
					{/if}
				</div>
			</form>
		</div>
	</div>
</div>

<style>
	/* Leaflet map styles */
	:global(#property-map) {
		height: 400px;
		width: 100%;
	}

	/* Required field indicator */
	.required::after {
		content: '*';
		color: #e53e3e;
		margin-right: 3px;
	}
</style>
