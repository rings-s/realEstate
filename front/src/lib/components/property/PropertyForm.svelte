<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { PROPERTY_TYPES, PROPERTY_STATUS } from '$lib/config/constants';
	import { createEventDispatcher } from 'svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, MapPin, Star, Tag, Info, Plus, Trash2, X } from 'lucide-svelte';
	import propertiesService from '$lib/services/properties';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Property object for editing (null for new property)
	export let property = null;
	// Whether form is in loading state
	export let loading = false;
	// Error message
	export let error = null;
	// Max file size for images in MB
	export let maxFileSize = 5;
	// Max number of images allowed
	export let maxImages = 10;
	// Auto-upload images immediately
	export let autoUpload = true;
	// Max text field lengths
	export let maxTitleLength = 100;
	export let maxDescriptionLength = 2000;

	// Form data
	let formData = {
		title: '',
		property_type: 'residential',
		status: 'available',
		location: {},
		address: '',
		city: '',
		state: '',
		postal_code: '',
		country: 'المملكة العربية السعودية',
		description: '',
		features: [],
		amenities: [],
		rooms: [],
		specifications: {},
		size_sqm: '',
		bedrooms: '',
		bathrooms: '',
		parking_spaces: '',
		year_built: '',
		market_value: '',
		minimum_bid: '',
		pricing_details: {},
		is_published: false,
		is_featured: false,
		meta_title: '',
		meta_description: ''
		// Images handled separately
	};

	// Local state
	let newFeature = '';
	let newAmenity = '';
	let images = [];
	let uploading = false;
	let imageError = null;
	let submitAttempted = false;

	// Initialize form with existing property data
	$: if (property) {
		formData = {
			title: property.title || '',
			property_type: property.property_type || 'residential',
			status: property.status || 'available',
			location: property.location || {},
			address: property.address || '',
			city: property.city || '',
			state: property.state || '',
			postal_code: property.postal_code || '',
			country: property.country || 'المملكة العربية السعودية',
			description: property.description || '',
			features: property.features || [],
			amenities: property.amenities || [],
			rooms: property.rooms || [],
			specifications: property.specifications || {},
			size_sqm: property.size_sqm || '',
			bedrooms: property.bedrooms || '',
			bathrooms: property.bathrooms || '',
			parking_spaces: property.parking_spaces || '',
			year_built: property.year_built || '',
			market_value: property.market_value || '',
			minimum_bid: property.minimum_bid || '',
			pricing_details: property.pricing_details || {},
			is_published: property.is_published || false,
			is_featured: property.is_featured || false,
			meta_title: property.meta_title || '',
			meta_description: property.meta_description || ''
		};

		// Load existing images if any
		if (property.images && Array.isArray(property.images)) {
			images = property.images.map((img) => ({
				id: img.id,
				file: null,
				url: img.image_url || img.image,
				is_primary: img.is_primary,
				caption: img.caption || '',
				uploaded: true,
				progress: 100
			}));
		}
	}

	// Form validation
	$: isValid =
		formData.title.trim() &&
		formData.property_type &&
		formData.address.trim() &&
		formData.city.trim() &&
		formData.description.trim();

	// Validate required fields
	function validate() {
		submitAttempted = true;
		return isValid;
	}

	// Handle form submission
	async function handleSubmit() {
		if (!validate()) {
			addToast(
				t('form_validation_error', $language, { default: 'يرجى ملء جميع الحقول المطلوبة' }),
				'error'
			);
			return;
		}

		try {
			loading = true;
			error = null;

			// Convert numeric fields to proper format
			const propertyData = {
				...formData,
				size_sqm: formData.size_sqm ? parseFloat(formData.size_sqm) : null,
				bedrooms: formData.bedrooms ? parseInt(formData.bedrooms, 10) : null,
				bathrooms: formData.bathrooms ? parseInt(formData.bathrooms, 10) : null,
				parking_spaces: formData.parking_spaces ? parseInt(formData.parking_spaces, 10) : null,
				year_built: formData.year_built ? parseInt(formData.year_built, 10) : null,
				market_value: formData.market_value ? parseFloat(formData.market_value) : null,
				minimum_bid: formData.minimum_bid ? parseFloat(formData.minimum_bid) : null
			};

			// If we have a property ID, update it; otherwise create a new one
			let result;
			if (property && property.id) {
				result = await propertiesService.updateProperty(property.id, propertyData);
			} else {
				result = await propertiesService.createProperty(propertyData);
			}

			// Upload any new images that weren't auto-uploaded
			if (!autoUpload) {
				await uploadPendingImages(result.id);
			}

			// Success
			addToast(
				t(property ? 'property_updated' : 'property_created', $language, {
					default: property ? 'تم تحديث العقار بنجاح' : 'تم إنشاء العقار بنجاح'
				}),
				'success'
			);

			// Notify parent component
			dispatch('success', result);
		} catch (err) {
			console.error('Error saving property:', err);
			error = err.message || t('save_error', $language, { default: 'حدث خطأ أثناء حفظ العقار' });
			dispatch('error', err);
		} finally {
			loading = false;
		}
	}

	// Handle image file selection
	function handleImageSelect(event) {
		const files = event.target.files;
		if (!files.length) return;

		imageError = null;

		// Check if adding these would exceed max images
		if (images.length + files.length > maxImages) {
			imageError = t('max_images_error', $language, {
				default: `يمكنك تحميل ${maxImages} صور كحد أقصى`,
				count: maxImages
			});
			return;
		}

		// Process each file
		for (let i = 0; i < files.length; i++) {
			const file = files[i];

			// Check file size
			if (file.size > maxFileSize * 1024 * 1024) {
				imageError = t('image_size_error', $language, {
					default: `حجم الصورة يجب أن يكون أقل من ${maxFileSize}MB`,
					size: maxFileSize
				});
				continue;
			}

			// Check file type
			if (!file.type.startsWith('image/')) {
				imageError = t('image_type_error', $language, { default: 'يرجى تحميل ملفات صور فقط' });
				continue;
			}

			// Create a temporary URL for preview
			const imageUrl = URL.createObjectURL(file);

			// Add to images array
			const newImage = {
				id: null,
				file,
				url: imageUrl,
				is_primary: images.length === 0, // First image is primary by default
				caption: '',
				uploaded: false,
				progress: 0
			};

			images = [...images, newImage];

			// Auto-upload if enabled
			if (autoUpload && property && property.id) {
				uploadImage(newImage, property.id);
			}
		}

		// Reset file input
		event.target.value = '';
	}

	// Upload a single image
	async function uploadImage(image, propertyId) {
		if (!image.file || image.uploaded) return;

		try {
			uploading = true;

			// Update the image's progress
			const imageIndex = images.findIndex((img) => img.url === image.url);
			if (imageIndex === -1) return;

			images[imageIndex].progress = 10;
			images = [...images];

			// Create form data for upload
			const formData = new FormData();
			formData.append('image', image.file);
			formData.append('is_primary', image.is_primary);
			formData.append('caption', image.caption);

			// Upload the image
			const result = await propertiesService.uploadPropertyImage(propertyId, formData);

			// Update the image with the server response
			images[imageIndex].id = result.id;
			images[imageIndex].url = result.image_url || result.image;
			images[imageIndex].uploaded = true;
			images[imageIndex].progress = 100;
			images = [...images];
		} catch (err) {
			console.error('Error uploading image:', err);
			imageError = t('image_upload_error', $language, {
				default: 'فشل في تحميل الصورة'
			});

			// Remove the failed image
			const imageIndex = images.findIndex((img) => img.url === image.url);
			if (imageIndex !== -1) {
				images.splice(imageIndex, 1);
				images = [...images];
			}
		} finally {
			uploading = false;
		}
	}

	// Upload all pending images
	async function uploadPendingImages(propertyId) {
		const pendingImages = images.filter((img) => !img.uploaded && img.file);

		for (const image of pendingImages) {
			await uploadImage(image, propertyId);
		}
	}

	// Remove an image
	async function removeImage(index) {
		const image = images[index];

		try {
			// If image is already uploaded, delete it from server
			if (image.id && image.uploaded) {
				await propertiesService.deletePropertyImage(image.id);
			}

			// Remove from UI
			images.splice(index, 1);
			images = [...images];

			// If we removed the primary image, set the first image as primary
			if (image.is_primary && images.length > 0) {
				images[0].is_primary = true;

				// Update on server if needed
				if (images[0].id && images[0].uploaded) {
					await propertiesService.updatePropertyImage(images[0].id, { is_primary: true });
				}

				images = [...images];
			}
		} catch (err) {
			console.error('Error removing image:', err);
			imageError = t('image_remove_error', $language, {
				default: 'فشل في حذف الصورة'
			});
		}
	}

	// Set an image as primary
	async function setPrimaryImage(index) {
		try {
			// Update UI first
			images.forEach((img, i) => {
				img.is_primary = i === index;
			});
			images = [...images];

			// If the image is uploaded, update on server
			const image = images[index];
			if (image.id && image.uploaded) {
				await propertiesService.updatePropertyImage(image.id, { is_primary: true });
			}
		} catch (err) {
			console.error('Error setting primary image:', err);
			imageError = t('image_primary_error', $language, {
				default: 'فشل في تعيين الصورة الرئيسية'
			});
		}
	}

	// Add a new feature
	function addFeature() {
		if (newFeature.trim()) {
			formData.features = [...formData.features, newFeature.trim()];
			newFeature = '';
		}
	}

	// Remove a feature
	function removeFeature(index) {
		formData.features.splice(index, 1);
		formData.features = [...formData.features];
	}

	// Add a new amenity
	function addAmenity() {
		if (newAmenity.trim()) {
			formData.amenities = [...formData.amenities, newAmenity.trim()];
			newAmenity = '';
		}
	}

	// Remove an amenity
	function removeAmenity(index) {
		formData.amenities.splice(index, 1);
		formData.amenities = [...formData.amenities];
	}

	// Get current year for year_built validation
	const currentYear = new Date().getFullYear();
</script>

<form
	on:submit|preventDefault={handleSubmit}
	class="space-y-6 {$isRTL ? 'text-right' : 'text-left'}"
>
	<!-- Form error display -->
	{#if error}
		<Alert type="error" message={error} />
	{/if}

	<!-- Basic Information Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<Building class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('basic_information', $language, { default: 'المعلومات الأساسية' })}
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<!-- Title -->
			<label class="label md:col-span-2">
				<span
					>{t('title', $language, { default: 'العنوان' })}<span class="text-error-500">*</span
					></span
				>
				<input
					type="text"
					class="input {!formData.title && submitAttempted ? 'input-error' : ''}"
					bind:value={formData.title}
					maxlength={maxTitleLength}
					required
					placeholder={t('title_placeholder', $language, { default: 'أدخل عنوان العقار' })}
				/>
				<span class="text-sm text-surface-500-400-token {$isRTL ? 'text-left' : 'text-right'}">
					{formData.title.length}/{maxTitleLength}
				</span>
				{#if !formData.title && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>

			<!-- Property Type -->
			<label class="label">
				<span
					>{t('property_type', $language, { default: 'نوع العقار' })}<span class="text-error-500"
						>*</span
					></span
				>
				<select
					class="select {!formData.property_type && submitAttempted ? 'select-error' : ''}"
					bind:value={formData.property_type}
					required
				>
					{#each PROPERTY_TYPES as type}
						<option value={type.value}>{t(type.value, $language, { default: type.label })}</option>
					{/each}
				</select>
				{#if !formData.property_type && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>

			<!-- Status -->
			<label class="label">
				<span
					>{t('status', $language, { default: 'الحالة' })}<span class="text-error-500">*</span
					></span
				>
				<select
					class="select {!formData.status && submitAttempted ? 'select-error' : ''}"
					bind:value={formData.status}
					required
				>
					{#each PROPERTY_STATUS as status}
						<option value={status.value}
							>{t(status.value, $language, { default: status.label })}</option
						>
					{/each}
				</select>
				{#if !formData.status && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>
		</div>
	</div>

	<!-- Location Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<MapPin class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('location', $language, { default: 'الموقع' })}
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<!-- Address -->
			<label class="label md:col-span-2">
				<span
					>{t('address', $language, { default: 'العنوان' })}<span class="text-error-500">*</span
					></span
				>
				<input
					type="text"
					class="input {!formData.address && submitAttempted ? 'input-error' : ''}"
					bind:value={formData.address}
					required
					placeholder={t('address_placeholder', $language, { default: 'أدخل عنوان العقار الكامل' })}
				/>
				{#if !formData.address && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>

			<!-- City -->
			<label class="label">
				<span
					>{t('city', $language, { default: 'المدينة' })}<span class="text-error-500">*</span></span
				>
				<input
					type="text"
					class="input {!formData.city && submitAttempted ? 'input-error' : ''}"
					bind:value={formData.city}
					required
					placeholder={t('city_placeholder', $language, { default: 'أدخل اسم المدينة' })}
				/>
				{#if !formData.city && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>

			<!-- State/Province -->
			<label class="label">
				<span>{t('state', $language, { default: 'المنطقة/المحافظة' })}</span>
				<input
					type="text"
					class="input"
					bind:value={formData.state}
					placeholder={t('state_placeholder', $language, {
						default: 'أدخل اسم المنطقة أو المحافظة'
					})}
				/>
			</label>

			<!-- Postal Code -->
			<label class="label">
				<span>{t('postal_code', $language, { default: 'الرمز البريدي' })}</span>
				<input
					type="text"
					class="input"
					bind:value={formData.postal_code}
					placeholder={t('postal_code_placeholder', $language, { default: 'أدخل الرمز البريدي' })}
				/>
			</label>

			<!-- Country -->
			<label class="label">
				<span>{t('country', $language, { default: 'الدولة' })}</span>
				<input
					type="text"
					class="input"
					bind:value={formData.country}
					placeholder={t('country_placeholder', $language, { default: 'أدخل اسم الدولة' })}
				/>
			</label>
		</div>
	</div>

	<!-- Property Details Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<Info class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('property_details', $language, { default: 'تفاصيل العقار' })}
		</h2>

		<div class="mb-4">
			<!-- Description -->
			<label class="label">
				<span
					>{t('description', $language, { default: 'الوصف' })}<span class="text-error-500">*</span
					></span
				>
				<textarea
					class="textarea {!formData.description && submitAttempted ? 'textarea-error' : ''}"
					bind:value={formData.description}
					rows="6"
					maxlength={maxDescriptionLength}
					required
					placeholder={t('description_placeholder', $language, {
						default: 'أدخل وصفاً مفصلاً للعقار'
					})}
				></textarea>
				<span class="text-sm text-surface-500-400-token {$isRTL ? 'text-left' : 'text-right'}">
					{formData.description.length}/{maxDescriptionLength}
				</span>
				{#if !formData.description && submitAttempted}
					<span class="text-error-500 text-sm"
						>{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}</span
					>
				{/if}
			</label>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Size -->
			<label class="label">
				<span>{t('size_sqm', $language, { default: 'المساحة (متر مربع)' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.size_sqm}
					min="0"
					step="0.01"
					placeholder={t('size_placeholder', $language, { default: 'أدخل المساحة' })}
				/>
			</label>

			<!-- Bedrooms -->
			<label class="label">
				<span>{t('bedrooms', $language, { default: 'غرف النوم' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.bedrooms}
					min="0"
					step="1"
					placeholder={t('bedrooms_placeholder', $language, { default: 'عدد غرف النوم' })}
				/>
			</label>

			<!-- Bathrooms -->
			<label class="label">
				<span>{t('bathrooms', $language, { default: 'الحمامات' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.bathrooms}
					min="0"
					step="1"
					placeholder={t('bathrooms_placeholder', $language, { default: 'عدد الحمامات' })}
				/>
			</label>

			<!-- Parking Spaces -->
			<label class="label">
				<span>{t('parking_spaces', $language, { default: 'مواقف السيارات' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.parking_spaces}
					min="0"
					step="1"
					placeholder={t('parking_placeholder', $language, { default: 'عدد المواقف' })}
				/>
			</label>

			<!-- Year Built -->
			<label class="label">
				<span>{t('year_built', $language, { default: 'سنة البناء' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.year_built}
					min="1900"
					max={currentYear}
					step="1"
					placeholder={t('year_built_placeholder', $language, { default: 'سنة بناء العقار' })}
				/>
			</label>

			<!-- Market Value -->
			<label class="label">
				<span>{t('market_value', $language, { default: 'القيمة السوقية' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.market_value}
					min="0"
					step="0.01"
					placeholder={t('market_value_placeholder', $language, {
						default: 'القيمة السوقية للعقار'
					})}
				/>
			</label>

			<!-- Minimum Bid -->
			<label class="label">
				<span>{t('minimum_bid', $language, { default: 'الحد الأدنى للمزايدة' })}</span>
				<input
					type="number"
					class="input"
					bind:value={formData.minimum_bid}
					min="0"
					step="0.01"
					placeholder={t('minimum_bid_placeholder', $language, { default: 'الحد الأدنى للمزايدة' })}
				/>
			</label>
		</div>
	</div>

	<!-- Features and Amenities Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<Star class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('features_amenities', $language, { default: 'المميزات والمرافق' })}
		</h2>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<!-- Features -->
			<div>
				<h3 class="font-semibold mb-2">{t('features', $language, { default: 'المميزات' })}</h3>

				<!-- Features Input -->
				<div class="flex mb-2">
					<input
						type="text"
						class="input rounded-r-none {$isRTL
							? 'rounded-l-none border-l-0'
							: 'rounded-r-none border-r-0'}"
						bind:value={newFeature}
						placeholder={t('feature_placeholder', $language, { default: 'أضف ميزة جديدة' })}
						on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
					/>
					<button
						type="button"
						class="btn variant-filled-primary {$isRTL ? 'rounded-r-token' : 'rounded-l-token'}"
						on:click={addFeature}
					>
						<Plus class="w-5 h-5" />
					</button>
				</div>

				<!-- Features List -->
				{#if formData.features.length === 0}
					<p class="text-surface-500-400-token text-sm italic">
						{t('no_features', $language, { default: 'لا توجد ميزات محددة' })}
					</p>
				{:else}
					<ul class="space-y-2 max-h-60 overflow-y-auto">
						{#each formData.features as feature, i}
							<li
								class="flex items-center justify-between bg-surface-200-700-token p-2 rounded-token"
							>
								<span>{feature}</span>
								<button
									type="button"
									class="btn btn-sm btn-icon variant-soft-error"
									on:click={() => removeFeature(i)}
									aria-label={t('remove_feature', $language, { default: 'إزالة الميزة' })}
								>
									<X class="w-4 h-4" />
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			<!-- Amenities -->
			<div>
				<h3 class="font-semibold mb-2">{t('amenities', $language, { default: 'المرافق' })}</h3>

				<!-- Amenities Input -->
				<div class="flex mb-2">
					<input
						type="text"
						class="input {$isRTL ? 'rounded-l-none border-l-0' : 'rounded-r-none border-r-0'}"
						bind:value={newAmenity}
						placeholder={t('amenity_placeholder', $language, { default: 'أضف مرفق جديد' })}
						on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addAmenity())}
					/>
					<button
						type="button"
						class="btn variant-filled-primary {$isRTL ? 'rounded-r-token' : 'rounded-l-token'}"
						on:click={addAmenity}
					>
						<Plus class="w-5 h-5" />
					</button>
				</div>

				<!-- Amenities List -->
				{#if formData.amenities.length === 0}
					<p class="text-surface-500-400-token text-sm italic">
						{t('no_amenities', $language, { default: 'لا توجد مرافق محددة' })}
					</p>
				{:else}
					<ul class="space-y-2 max-h-60 overflow-y-auto">
						{#each formData.amenities as amenity, i}
							<li
								class="flex items-center justify-between bg-surface-200-700-token p-2 rounded-token"
							>
								<span>{amenity}</span>
								<button
									type="button"
									class="btn btn-sm btn-icon variant-soft-error"
									on:click={() => removeAmenity(i)}
									aria-label={t('remove_amenity', $language, { default: 'إزالة المرفق' })}
								>
									<X class="w-4 h-4" />
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>
	</div>

	<!-- Images Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}"
				width="24"
				height="24"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"></path>
				<line x1="16" y1="5" x2="22" y2="5"></line>
				<line x1="19" y1="2" x2="19" y2="8"></line>
				<circle cx="9" cy="9" r="2"></circle>
				<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
			</svg>
			{t('images', $language, { default: 'الصور' })}
		</h2>

		<!-- Image error display -->
		{#if imageError}
			<Alert type="error" message={imageError} class="mb-4" />
		{/if}

		<!-- Image upload area -->
		<div class="mb-4">
			<label
				for="property-images"
				class="block w-full h-32 border-2 border-dashed border-surface-300-600-token rounded-token cursor-pointer hover:bg-surface-hover-token transition-colors"
			>
				<div class="flex flex-col items-center justify-center h-full">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="w-10 h-10 text-surface-500-400-token mb-2"
						width="24"
						height="24"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"></path>
						<line x1="16" y1="5" x2="22" y2="5"></line>
						<line x1="19" y1="2" x2="19" y2="8"></line>
						<circle cx="9" cy="9" r="2"></circle>
						<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
					</svg>
					<p class="text-sm text-surface-500-400-token">
						{t('drop_images', $language, { default: 'اسحب الصور هنا أو انقر للاختيار' })}
					</p>
					<p class="text-xs text-surface-500-400-token mt-1">
						{t('max_file_size', $language, {
							default: 'الحد الأقصى لحجم الملف: {size}MB',
							size: maxFileSize
						})}
					</p>
				</div>
				<input
					id="property-images"
					type="file"
					multiple
					accept="image/*"
					class="hidden"
					on:change={handleImageSelect}
				/>
			</label>
			<p class="text-sm text-surface-500-400-token mt-2">
				{t('image_count', $language, {
					default: '{current}/{max} صور',
					current: images.length,
					max: maxImages
				})}
			</p>
		</div>

		<!-- Image preview grid -->
		{#if images.length > 0}
			<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
				{#each images as image, i}
					<div class="relative group">
						<!-- Image preview -->
						<div
							class="aspect-square bg-cover bg-center rounded-token overflow-hidden border {image.is_primary
								? 'border-primary-500'
								: 'border-surface-300-600-token'}"
							style="background-image: url('{image.url}')"
						>
							<!-- Upload progress overlay -->
							{#if !image.uploaded && image.progress < 100}
								<div
									class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white"
								>
									<div class="w-16 h-16">
										<svg
											class="animate-spin"
											viewBox="0 0 24 24"
											fill="none"
											xmlns="http://www.w3.org/2000/svg"
										>
											<circle
												class="opacity-25"
												cx="12"
												cy="12"
												r="10"
												stroke="currentColor"
												stroke-width="4"
											></circle>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0120.709 10H24c0 6.627-5.373 12-12 12v-4c4.411 0 8-3.589 8-8H6.291z"
											></path>
										</svg>
									</div>
								</div>
							{/if}

							<!-- Primary badge -->
							{#if image.is_primary}
								<div
									class="absolute top-2 {$isRTL
										? 'right-2'
										: 'left-2'} badge variant-filled-primary"
								>
									{t('primary', $language, { default: 'رئيسية' })}
								</div>
							{/if}
						</div>

						<!-- Image actions -->
						<div
							class="absolute bottom-0 inset-x-0 p-2 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex justify-between"
						>
							<!-- Set as primary button -->
							{#if !image.is_primary}
								<button
									type="button"
									class="btn btn-sm variant-ghost-primary"
									on:click={() => setPrimaryImage(i)}
									disabled={uploading}
									aria-label={t('set_primary', $language, { default: 'تعيين كصورة رئيسية' })}
								>
									<Star class="w-4 h-4" />
								</button>
							{:else}
								<div></div>
							{/if}

							<!-- Remove button -->
							<button
								type="button"
								class="btn btn-sm variant-ghost-error"
								on:click={() => removeImage(i)}
								disabled={uploading}
								aria-label={t('remove_image', $language, { default: 'إزالة الصورة' })}
							>
								<Trash2 class="w-4 h-4" />
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Publishing Options Section -->
	<div class="card p-4">
		<h2 class="h3 mb-4 flex items-center">
			<Tag class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('publishing_options', $language, { default: 'خيارات النشر' })}
		</h2>

		<div class="space-y-4">
			<!-- Published checkbox -->
			<label class="flex items-center space-x-2 {$isRTL ? 'space-x-reverse' : ''}">
				<input type="checkbox" class="checkbox" bind:checked={formData.is_published} />
				<span>{t('is_published', $language, { default: 'نشر العقار' })}</span>
			</label>

			<!-- Featured checkbox -->
			<label class="flex items-center space-x-2 {$isRTL ? 'space-x-reverse' : ''}">
				<input type="checkbox" class="checkbox" bind:checked={formData.is_featured} />
				<span>{t('is_featured', $language, { default: 'عقار مميز' })}</span>
			</label>

			<!-- SEO options -->
			<div class="pt-4 border-t border-surface-300-600-token">
				<h3 class="font-semibold mb-2">
					{t('seo_options', $language, { default: 'خيارات تحسين محركات البحث' })}
				</h3>

				<!-- Meta Title -->
				<label class="label">
					<span>{t('meta_title', $language, { default: 'عنوان الميتا' })}</span>
					<input
						type="text"
						class="input"
						bind:value={formData.meta_title}
						placeholder={t('meta_title_placeholder', $language, {
							default: 'عنوان الميتا لمحركات البحث'
						})}
					/>
				</label>

				<!-- Meta Description -->
				<label class="label">
					<span>{t('meta_description', $language, { default: 'وصف الميتا' })}</span>
					<textarea
						class="textarea"
						bind:value={formData.meta_description}
						rows="3"
						placeholder={t('meta_description_placeholder', $language, {
							default: 'وصف الميتا لمحركات البحث'
						})}
					></textarea>
				</label>
			</div>
		</div>
	</div>

	<!-- Form Actions -->
	<div class="flex justify-end gap-2">
		<button
			type="button"
			class="btn variant-ghost-surface"
			on:click={() => dispatch('cancel')}
			disabled={loading}
		>
			{t('cancel', $language, { default: 'إلغاء' })}
		</button>
		<button type="submit" class="btn variant-filled-primary" disabled={loading}>
			{#if loading}
				<div class="spinner-icon mr-2"></div>
			{/if}
			{property
				? t('update_property', $language, { default: 'تحديث العقار' })
				: t('create_property', $language, { default: 'إنشاء العقار' })}
		</button>
	</div>
</form>

<style>
	.spinner-icon {
		border: 2px solid #f3f3f3;
		border-top: 2px solid currentColor;
		border-radius: 50%;
		width: 1em;
		height: 1em;
		animation: spin 1s linear infinite;
		display: inline-block;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
