<!-- src/lib/components/property/PropertyForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import PropertyMap from './PropertyMap.svelte';
	import RoomEditor from './RoomEditor.svelte';
	import { addToast } from '$lib/stores/ui';

	const dispatch = createEventDispatcher();

	// Form Data
	export let initialData = null;
	export let loading = false;

	let formData = {
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
		minimum_bid: '',
		features: [],
		rooms: [],
		location: {
			latitude: null,
			longitude: null
		},
		media: [],
		...initialData
	};

	// Form State
	let currentStep = 1;
	let totalSteps = 4;
	let errors = {};
	let newFeature = '';
	let uploadedImages = [];

	const propertyTypes = [
		{ value: 'residential', label: 'سكني', icon: 'home' },
		{ value: 'commercial', label: 'تجاري', icon: 'store' },
		{ value: 'land', label: 'أرض', icon: 'map' },
		{ value: 'industrial', label: 'صناعي', icon: 'industry' },
		{ value: 'mixed_use', label: 'متعدد الاستخدام', icon: 'building' }
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

	// Validate each step individually
	function validateStep(step) {
		errors = {};

		switch (step) {
			case 1:
				// Only validate title and property type in step 1
				if (!formData.title.trim()) {
					errors.title = 'عنوان العقار مطلوب';
				}
				if (!formData.property_type) {
					errors.property_type = 'نوع العقار مطلوب';
				}
				break;

			case 2:
				// Validate location in step 2
				if (!formData.address.trim()) {
					errors.address = 'العنوان مطلوب';
				}
				if (!formData.city) {
					errors.city = 'المدينة مطلوبة';
				}
				break;

			case 3:
				// Room validation is optional
				break;

			case 4:
				// Only require images in the final step
				if (uploadedImages.length === 0) {
					errors.images = 'يرجى إضافة صورة واحدة على الأقل';
				}
				break;
		}

		return Object.keys(errors).length === 0;
	}

	// Navigation between steps
	function handleStep(direction) {
		if (direction === 'next') {
			if (!validateStep(currentStep)) {
				// Show errors for current step only
				for (const [field, message] of Object.entries(errors)) {
					addToast(message, 'error');
				}
				return;
			}
			if (currentStep < totalSteps) {
				currentStep += 1;
			}
		} else if (direction === 'prev' && currentStep > 1) {
			currentStep -= 1;
		}
	}

	// Form Submission
	async function handleSubmit() {
		if (!validateForm()) return;

		loading = true;
		try {
			const formData = new FormData();

			// Append basic property data
			Object.keys(propertyData).forEach((key) => {
				if (key !== 'images') {
					formData.append(key, propertyData[key]);
				}
			});

			// Append images
			uploadedImages.forEach((image, index) => {
				formData.append(`images[${index}]`, image.file);
			});

			const response = await fetch('/api/properties/', {
				method: 'POST',
				body: formData,
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (!response.ok) throw new Error('Failed to create property');

			addToast('Property created successfully', 'success');
			goto('/properties');
		} catch (error) {
			addToast(error.message, 'error');
		} finally {
			loading = false;
		}
	}
	function validateForm() {
		const errors = [];

		if (!propertyData.title) errors.push('Title is required');
		if (!propertyData.property_type) errors.push('Property type is required');
		if (!propertyData.address) errors.push('Address is required');
		if (!propertyData.city) errors.push('City is required');
		if (uploadedImages.length === 0) errors.push('At least one image is required');

		if (errors.length > 0) {
			errors.forEach((error) => addToast(error, 'error'));
			return false;
		}

		return true;
	}

	// Features Management
	function addFeature() {
		if (newFeature.trim()) {
			formData.features = [...formData.features, newFeature.trim()];
			newFeature = '';
		}
	}

	function removeFeature(index) {
		formData.features = formData.features.filter((_, i) => i !== index);
	}

	// Image Management
	async function handleImageUpload(event) {
		const files = Array.from(event.target.files);

		for (const file of files) {
			// Validate file size (5MB max)
			if (file.size > 5 * 1024 * 1024) {
				addToast(`File ${file.name} is larger than 5MB`, 'error');
				continue;
			}

			// Validate file type
			if (!file.type.startsWith('image/')) {
				addToast(`File ${file.name} is not an image`, 'error');
				continue;
			}

			const formData = new FormData();
			formData.append('image', file);

			try {
				const response = await fetch('/api/upload-image/', {
					method: 'POST',
					body: formData,
					headers: {
						Authorization: `Bearer ${token}` // Get from auth store
					}
				});

				if (!response.ok) throw new Error('Upload failed');

				const data = await response.json();
				uploadedImages = [
					...uploadedImages,
					{
						file: data.url,
						preview: data.url,
						name: file.name
					}
				];
			} catch (error) {
				addToast(`Failed to upload ${file.name}`, 'error');
			}
		}
	}

	function removeImage(index) {
		uploadedImages = uploadedImages.filter((_, i) => i !== index);
	}

	// Location Update
	function handleLocationUpdate(location) {
		formData.location = location;
	}

	// Room Update
	function handleRoomUpdate(event) {
		formData.rooms = event.detail.rooms;
	}
</script>

<!-- Form Steps Progress -->
<div class="mb-8">
	<div class="flex justify-between">
		{#each Array(totalSteps) as _, i}
			<div class="relative flex flex-col items-center">
				<div
					class="flex h-10 w-10 items-center justify-center rounded-full {currentStep > i + 1
						? 'bg-green-600 text-white'
						: currentStep === i + 1
							? 'bg-blue-600 text-white'
							: 'bg-slate-200 text-slate-600'}"
				>
					<i
						class="fas fa-{i === 0
							? 'home'
							: i === 1
								? 'map-marker-alt'
								: i === 2
									? 'door-open'
									: 'images'}"
					></i>
				</div>
				<span
					class="absolute -bottom-6 text-sm font-medium {currentStep === i + 1
						? 'text-blue-600'
						: 'text-slate-500'}"
				>
					{i === 0 ? 'معلومات أساسية' : i === 1 ? 'الموقع' : i === 2 ? 'الغرف' : 'الصور والمميزات'}
				</span>
			</div>

			{#if i < totalSteps - 1}
				<div class="mt-5 h-1 flex-1 {currentStep > i + 1 ? 'bg-green-600' : 'bg-slate-200'}"></div>
			{/if}
		{/each}
	</div>
</div>

<!-- Form Steps Content -->
<div class="mt-12">
	{#if currentStep === 1}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
			<div class="space-y-6">
				<!-- Basic Information Fields -->
				<div class="form-group">
					<label class="label required">عنوان العقار</label>
					<input
						type="text"
						class="input {errors.title ? 'border-red-500' : ''}"
						bind:value={formData.title}
						placeholder="أدخل عنواناً مميزاً للعقار"
					/>
					{#if errors.title}
						<span class="text-sm text-red-500">{errors.title}</span>
					{/if}
				</div>

				<div class="form-group">
					<label class="label required">نوع العقار</label>
					<select
						class="input {errors.property_type ? 'border-red-500' : ''}"
						bind:value={formData.property_type}
					>
						{#each propertyTypes as type}
							<option value={type.value}>{type.label}</option>
						{/each}
					</select>
					{#if errors.property_type}
						<span class="text-sm text-red-500">{errors.property_type}</span>
					{/if}
				</div>

				<div class="form-group">
					<label class="label">وصف العقار</label>
					<textarea
						class="input"
						bind:value={formData.description}
						rows="4"
						placeholder="أدخل وصفاً تفصيلياً للعقار"
					></textarea>
				</div>

				<!-- Additional optional fields -->
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<div class="form-group">
						<label class="label">المساحة (متر مربع)</label>
						<input
							type="number"
							class="input"
							bind:value={formData.size_sqm}
							placeholder="المساحة"
							min="0"
						/>
					</div>

					<div class="form-group">
						<label class="label">السعر المتوقع</label>
						<input
							type="number"
							class="input"
							bind:value={formData.market_value}
							placeholder="السعر بالريال"
							min="0"
						/>
					</div>
				</div>
			</div>
		</div>
	{:else if currentStep === 2}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
			<!-- Location Fields -->
			<div class="space-y-6">
				<div class="form-group">
					<label class="label required">العنوان</label>
					<input
						type="text"
						class="input {errors.address ? 'border-red-500' : ''}"
						bind:value={formData.address}
						placeholder="أدخل عنوان العقار"
					/>
					{#if errors.address}
						<span class="text-sm text-red-500">{errors.address}</span>
					{/if}
				</div>

				<div class="form-group">
					<label class="label required">المدينة</label>
					<select class="input {errors.city ? 'border-red-500' : ''}" bind:value={formData.city}>
						<option value="">اختر المدينة</option>
						{#each cityOptions as city}
							<option value={city}>{city}</option>
						{/each}
					</select>
					{#if errors.city}
						<span class="text-sm text-red-500">{errors.city}</span>
					{/if}
				</div>

				<PropertyMap
					latitude={formData.location.latitude}
					longitude={formData.location.longitude}
					editable={true}
					onLocationChange={handleLocationUpdate}
				/>
			</div>
		</div>
	{:else if currentStep === 3}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
			<RoomEditor rooms={formData.rooms} on:update={handleRoomUpdate} />
		</div>
	{:else if currentStep === 4}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
			<!-- Images and Features -->
			<div class="space-y-6">
				<div class="form-group">
					<label class="label required">صور العقار</label>
					<div
						class="rounded-lg border-2 border-dashed border-slate-300 p-6 text-center transition-colors hover:border-blue-500"
						class:border-red-500={errors.images}
					>
						<input
							type="file"
							accept="image/*"
							multiple
							class="hidden"
							on:change={handleImageUpload}
							id="property-images"
						/>
						<label for="property-images" class="block cursor-pointer">
							<i class="fas fa-cloud-upload-alt mb-2 text-4xl text-slate-400"></i>
							<p class="text-slate-600">اسحب الصور هنا أو انقر للاختيار</p>
							<p class="mt-1 text-sm text-slate-500">الحد الأقصى 5 ميجابايت للصورة</p>
						</label>
					</div>
					{#if errors.images}
						<span class="text-sm text-red-500">{errors.images}</span>
					{/if}
				</div>

				{#if uploadedImages.length > 0}
					<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
						{#each uploadedImages as image, i}
							<div class="group relative">
								<img
									src={image.preview}
									alt={image.name}
									class="h-40 w-full rounded-lg object-cover"
								/>
								<button
									type="button"
									class="absolute top-2 right-2 h-8 w-8 rounded-full bg-red-500 text-white opacity-0 transition-opacity group-hover:opacity-100"
									on:click={() => removeImage(i)}
								>
									<i class="fas fa-times"></i>
								</button>
								{#if i === 0}
									<div
										class="absolute top-2 left-2 rounded bg-blue-500 px-2 py-1 text-xs text-white"
									>
										الصورة الرئيسية
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}

				<!-- Features -->
				<div class="form-group">
					<label class="label">مميزات العقار</label>
					<div class="flex gap-2">
						<input
							type="text"
							class="input flex-1"
							bind:value={newFeature}
							placeholder="أضف ميزة جديدة"
							on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
						/>
						<button type="button" class="btn-primary" on:click={addFeature}> إضافة </button>
					</div>

					{#if formData.features.length > 0}
						<div class="mt-4 flex flex-wrap gap-2">
							{#each formData.features as feature, i}
								<div class="flex items-center rounded-full bg-blue-50 px-3 py-1 text-blue-700">
									<span>{feature}</span>
									<button
										type="button"
										class="ml-2 text-blue-400 hover:text-blue-600"
										on:click={() => removeFeature(i)}
									>
										<i class="fas fa-times"></i>
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<!-- Navigation Buttons -->
	<div class="mt-8 flex justify-between">
		<button
			type="button"
			class="btn-secondary"
			on:click={() => handleStep('prev')}
			disabled={currentStep === 1}
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
			<button type="button" class="btn-primary" on:click={handleSubmit} disabled={loading}>
				{#if loading}
					<i class="fas fa-spinner fa-spin ml-2"></i>
					جاري الحفظ...
				{:else}
					حفظ العقار
				{/if}
			</button>
		{/if}
	</div>
</div>

<style>
	.label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: #334155;
	}

	.label.required::after {
		content: '*';
		margin-right: 0.25rem;
		color: #ef4444;
	}

	.form-group {
		margin-top: 0.25rem;
	}

	:global(.form-transition-enter-active),
	:global(.form-transition-leave-active) {
		transition:
			opacity 0.3s,
			transform 0.3s;
	}

	:global(.form-transition-enter),
	:global(.form-transition-leave-to) {
		opacity: 0;
		transform: translateY(20px);
	}
</style>
