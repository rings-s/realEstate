<!-- Fix for PropertyForm.svelte -->
<script>
	// PropertyForm.svelte - Script Section
	import { onMount, createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { PROPERTY_TYPES, PROPERTY_STATUS } from '$lib/config/constants';
	import { fade } from 'svelte/transition';
	import Alert from '$lib/components/common/Alert.svelte';
	import Map from './Map.svelte';
	import Tabs from '$lib/components/common/Tabs.svelte';
	import PropertyImages from '$lib/components/property/PropertyImages.svelte';
	import {
		validateProperty,
		validateNumeric,
		hasErrors,
		getErrorMessage
	} from '$lib/utils/validators';
	import {
		Building,
		MapPin,
		Star,
		Tag,
		Info,
		Plus,
		Trash2,
		X,
		Home,
		Image,
		Settings,
		Camera,
		Loader,
		ArrowRight,
		ArrowLeft,
		Save,
		ChevronRight,
		ChevronLeft
	} from 'lucide-svelte';
	import { formatPropertyData } from '$lib/services/propertyService';

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
	// Max text field lengths
	export let maxTitleLength = 100;
	export let maxDescriptionLength = 2000;

	// Form data
	let formData = {
		title: '',
		property_type: 'residential',
		status: 'available',
		location: {
			latitude: null,
			longitude: null,
			city: '',
			address: '',
			postal_code: '',
			state: '',
			country: 'المملكة العربية السعودية'
		},
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
	let locationError = null;
	let activeTab = 'basic-info';
	let mapLoaded = false;
	let fetchingAddress = false;
	let tabs = [
		{
			id: 'basic-info',
			label: $language === 'ar' ? 'المعلومات الأساسية' : 'Basic Information',
			icon: Building
		},
		{ id: 'location', label: $language === 'ar' ? 'الموقع' : 'Location', icon: MapPin },
		{ id: 'details', label: $language === 'ar' ? 'تفاصيل العقار' : 'Property Details', icon: Info },
		{
			id: 'features',
			label: $language === 'ar' ? 'المميزات والمرافق' : 'Features & Amenities',
			icon: Star
		},
		{ id: 'images', label: $language === 'ar' ? 'الصور' : 'Images', icon: Image },
		{ id: 'publishing', label: $language === 'ar' ? 'النشر' : 'Publishing', icon: Settings }
	];

	// Field-specific error handling
	let fieldErrors = {};

	// Extract field errors from the error message
	$: {
		fieldErrors = {};
		if (error) {
			// Handle ApiError objects with details
			if (error.details && typeof error.details === 'object') {
				fieldErrors = error.details;
			}
			// Handle string error messages that might contain field errors
			else if (typeof error === 'string') {
				// Try to extract field: message format
				const fieldErrorRegex = /(\w+):\s+(.+?)(?=\.\s+\w+:|$)/g;
				let match;

				while ((match = fieldErrorRegex.exec(error)) !== null) {
					const [, field, message] = match;
					fieldErrors[field] = message;
				}
			}
		}
	}

	// Function to get field error
	function getFieldError(fieldName) {
		if (!fieldErrors || !fieldName) return null;

		// Check for direct match
		if (fieldErrors[fieldName]) {
			return fieldErrors[fieldName];
		}

		// Check for case insensitive match
		const lowerFieldName = fieldName.toLowerCase();
		for (const [key, value] of Object.entries(fieldErrors)) {
			if (key.toLowerCase() === lowerFieldName) {
				return value;
			}
		}

		return null;
	}

	// Initialize form with existing property data
	$: if (property) {
		formData = {
			title: property.title || '',
			property_type: property.property_type || 'residential',
			status: property.status || 'available',
			location: property.location || {
				latitude: null,
				longitude: null,
				city: '',
				address: '',
				postal_code: '',
				state: '',
				country: 'المملكة العربية السعودية'
			},
			address: property.address || '',
			city: property.city || '',
			state: property.state || '',
			postal_code: property.postal_code || '',
			country: property.country || 'المملكة العربية السعودية',
			description: property.description || '',
			features: Array.isArray(property.features) ? property.features : [],
			amenities: Array.isArray(property.amenities) ? property.amenities : [],
			rooms: Array.isArray(property.rooms) ? property.rooms : [],
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

	// Update location when address fields change
	$: {
		formData.location.address = formData.address;
		formData.location.city = formData.city;
		formData.location.state = formData.state;
		formData.location.postal_code = formData.postal_code;
		formData.location.country = formData.country;
	}

	// Set map loaded when location tab is active
	$: if (activeTab === 'location') {
		mapLoaded = true;
	}

	// Move to next tab
	function goToNextTab() {
		const currentIndex = tabs.findIndex((tab) => tab.id === activeTab);
		if (currentIndex < tabs.length - 1) {
			// Basic validation before moving to next tab
			let canProceed = true;

			// Validate basic-info tab
			if (activeTab === 'basic-info' && !formData.title.trim()) {
				addToast(t('title_required', $language, { default: 'العنوان مطلوب' }), 'warning');
				canProceed = false;
			}

			// Validate location tab
			if (activeTab === 'location' && (!formData.address.trim() || !formData.city.trim())) {
				addToast(
					t('address_city_required', $language, { default: 'العنوان والمدينة مطلوبان' }),
					'warning'
				);
				canProceed = false;
			}

			// Validate details tab
			if (activeTab === 'details' && !formData.description.trim()) {
				addToast(t('description_required', $language, { default: 'الوصف مطلوب' }), 'warning');
				canProceed = false;
			}

			if (canProceed) {
				activeTab = tabs[currentIndex + 1].id;
			}
		}
	}

	// Move to previous tab
	function goToPrevTab() {
		const currentIndex = tabs.findIndex((tab) => tab.id === activeTab);
		if (currentIndex > 0) {
			activeTab = tabs[currentIndex - 1].id;
		}
	}

	// Set location in form data from Map component event
	async function handleLocationChange(event) {
		const { latitude, longitude } = event.detail;
		formData.location.latitude = latitude;
		formData.location.longitude = longitude;

		// Clear any previous location errors
		locationError = null;

		// Try to fetch address information for these coordinates
		fetchAddressFromCoordinates(latitude, longitude);
	}

	// Fetch address information from coordinates using Nominatim
	async function fetchAddressFromCoordinates(lat, lng) {
		if (!lat || !lng) return;

		fetchingAddress = true;
		try {
			const response = await fetch(
				`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
			);

			if (!response.ok) {
				throw new Error('Failed to fetch address information');
			}

			const data = await response.json();

			// Update form data with address details
			if (data.address) {
				// Only update fields that are empty or when explicitly asked to update
				if (!formData.address || formData.address.trim() === '') {
					const road = data.address.road || '';
					const houseNumber = data.address.house_number || '';
					formData.address = [road, houseNumber].filter(Boolean).join(', ');
				}

				if (!formData.city || formData.city.trim() === '') {
					formData.city = data.address.city || data.address.town || data.address.village || '';
				}

				if (!formData.state || formData.state.trim() === '') {
					formData.state = data.address.state || data.address.province || '';
				}

				if (!formData.postal_code || formData.postal_code.trim() === '') {
					formData.postal_code = data.address.postcode || '';
				}

				if (!formData.country || formData.country === 'المملكة العربية السعودية') {
					formData.country = data.address.country || 'المملكة العربية السعودية';
				}
			}
		} catch (error) {
			console.error('Error fetching address:', error);
		} finally {
			fetchingAddress = false;
		}
	}

	// Clear location data
	function clearLocation() {
		formData.location.latitude = null;
		formData.location.longitude = null;
	}

	// Handle tab change
	function handleTabChange(event) {
		activeTab = event.detail.id;
	}

	// Validate required fields
	function validate() {
		submitAttempted = true;

		// Check for required fields
		if (!formData.title.trim()) {
			activeTab = 'basic-info';
			return false;
		}

		if (!formData.address.trim() || !formData.city.trim()) {
			activeTab = 'location';
			return false;
		}

		if (!formData.description.trim()) {
			activeTab = 'details';
			return false;
		}

		return isValid;
	}

	// Handle form submission
	async function handleSubmit() {
		// Enable detailed logging
		console.log('Form Submission Started');
		console.log('Form Data:', JSON.parse(JSON.stringify(formData)));

		try {
			// Set submit attempted to true for validation
			submitAttempted = true;

			// Explicit validation
			if (!formData.title || !formData.title.trim()) {
				activeTab = 'basic-info';
				addToast(t('title_required', $language, { default: 'العنوان مطلوب' }), 'error');
				return;
			}

			if (!formData.address || !formData.address.trim()) {
				activeTab = 'location';
				addToast(t('address_required', $language, { default: 'العنوان مطلوب' }), 'error');
				return;
			}

			if (!formData.city || !formData.city.trim()) {
				activeTab = 'location';
				addToast(t('city_required', $language, { default: 'المدينة مطلوبة' }), 'error');
				return;
			}

			if (!formData.description || !formData.description.trim()) {
				activeTab = 'details';
				addToast(t('description_required', $language, { default: 'الوصف مطلوب' }), 'error');
				return;
			}

			// Start loading state
			loading = true;
			error = null;

			// Prepare data for submission
			const propertyData = {
				title: formData.title,
				property_type: formData.property_type,
				status: formData.status,
				address: formData.address,
				city: formData.city,
				state: formData.state,
				postal_code: formData.postal_code,
				country: formData.country,
				description: formData.description,

				// Convert numeric fields safely
				size_sqm: formData.size_sqm ? Number(formData.size_sqm) : null,
				bedrooms: formData.bedrooms ? Number(formData.bedrooms) : null,
				bathrooms: formData.bathrooms ? Number(formData.bathrooms) : null,
				parking_spaces: formData.parking_spaces ? Number(formData.parking_spaces) : null,
				year_built: formData.year_built ? Number(formData.year_built) : null,
				market_value: formData.market_value ? Number(formData.market_value) : null,
				minimum_bid: formData.minimum_bid ? Number(formData.minimum_bid) : null,

				// JSON fields
				location: formData.location || {},
				features: formData.features || [],
				amenities: formData.amenities || [],
				rooms: formData.rooms || [],
				specifications: formData.specifications || {},
				pricing_details: formData.pricing_details || {},
				metadata: formData.metadata || {},

				// Publishing options
				is_published: formData.is_published || false,
				is_featured: formData.is_featured || false,
				meta_title: formData.meta_title || '',
				meta_description: formData.meta_description || ''
			};

			// Log the prepared data
			console.log('Prepared Property Data:', JSON.parse(JSON.stringify(propertyData)));

			// Format data for API
			const formattedData = formatPropertyData(propertyData);
			console.log('Formatted Property Data:', JSON.parse(JSON.stringify(formattedData)));

			// Dispatch submission event
			dispatch('submit', {
				property: formattedData,
				images
			});
		} catch (err) {
			// Set error and loading states
			error = err.message || 'An error occurred';
			loading = false;

			// Log detailed error
			console.error('Form submission error:', err);

			// Show error toast
			addToast(error, 'error');
		}
	}

	// Handle image updates from PropertyImages component
	function handleImagesUpdate(event) {
		images = event.detail.images;
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

	// File input reference
	let fileInput;
	// Drop target reference
	let dropTarget;

	// FIXED IMAGE HANDLING: removed duplicated functions and kept only one version

	// Validate image file before adding it
	function validateImageFile(file) {
		const errors = [];

		// Check file type
		const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
		if (!allowedTypes.includes(file.type)) {
			errors.push(
				t('invalid_file_type', $language, {
					default: 'نوع الملف غير صالح: {{filename}}. الأنواع المسموح بها: JPG، PNG، GIF، WEBP',
					filename: file.name
				})
			);
		}

		// Check file size
		if (file.size > maxFileSize * 1024 * 1024) {
			errors.push(
				t('file_too_large', $language, {
					default: 'حجم الملف كبير جداً: {{filename}}. الحد الأقصى هو {{max}}MB',
					filename: file.name,
					max: maxFileSize
				})
			);
		}

		return { valid: errors.length === 0, errors };
	}

	// Handle file selection from input
	function handleFileSelection(files) {
		if (!files || files.length === 0) return;

		// Check if maximum number of images reached
		if (images.length >= maxImages) {
			addToast(
				t('max_images_reached', $language, {
					default: 'تم الوصول إلى الحد الأقصى للصور ({{max}})',
					max: maxImages
				}),
				'warning'
			);
			return;
		}

		// Calculate how many more images can be added
		const remainingSlots = maxImages - images.length;
		const filesToProcess = Array.from(files).slice(0, remainingSlots);

		let errorCount = 0;

		// Process each file with validation
		filesToProcess.forEach((file) => {
			const validation = validateImageFile(file);

			if (validation.valid) {
				// Create a preview URL for the valid image
				const url = URL.createObjectURL(file);

				// Add to images array
				images = [
					...images,
					{
						id: null,
						file,
						url,
						is_primary: images.length === 0, // First image is primary by default
						caption: '',
						alt_text: '',
						uploaded: false,
						progress: 0
					}
				];
			} else {
				// Report validation errors
				validation.errors.forEach((error) => {
					addToast(error, 'error');
				});
				errorCount++;
			}
		});

		// If we have errors, report summary
		if (errorCount > 0) {
			console.warn(`${errorCount} image(s) failed validation`);
		}
	}

	// Handle file input change
	function handleFileInputChange(event) {
		const files = event.target.files;
		handleFileSelection(files);
		// Reset input value to allow selecting the same file again
		event.target.value = null;
	}

	// Improved drag and drop handling
	function handleDrop(event) {
		event.preventDefault();
		const files = event.dataTransfer.files;
		handleFileSelection(files);
		dropTarget.classList.remove('border-primary-500', 'bg-primary-500/10');
	}

	// Handle drag over for visual effects
	function handleDragOver(event) {
		event.preventDefault();
		dropTarget.classList.add('border-primary-500', 'bg-primary-500/10');
	}

	// Handle drag leave for visual effects
	function handleDragLeave(event) {
		event.preventDefault();
		dropTarget.classList.remove('border-primary-500', 'bg-primary-500/10');
	}

	// Remove image from preview
	function removeImage(index) {
		const imageToRemove = images[index];

		// Revoke object URL if this is a local preview
		if (imageToRemove.url && !imageToRemove.uploaded) {
			URL.revokeObjectURL(imageToRemove.url);
		}

		// Remove the image
		images = images.filter((_, i) => i !== index);

		// If we removed the primary image, set the first one as primary
		if (imageToRemove.is_primary && images.length > 0) {
			images = images.map((img, idx) => ({
				...img,
				is_primary: idx === 0
			}));
		}
	}

	// Set an image as primary
	function setImageAsPrimary(index) {
		images = images.map((img, i) => ({
			...img,
			is_primary: i === index
		}));
	}

	// Handle cancel
	function handleCancel() {
		dispatch('cancel');
	}

	// Get current year for year_built validation
	const currentYear = new Date().getFullYear();

	onMount(() => {
		// Set default tab based on URL hash if present
		const hash = window.location.hash.replace('#', '');
		if (hash && tabs.some((tab) => tab.id === hash)) {
			activeTab = hash;
		}
	});
</script>

<form
	on:submit|preventDefault={handleSubmit}
	class="space-y-6 {$isRTL ? 'text-right' : 'text-left'}"
>
	<!-- Form error display -->
	{#if error}
		<Alert type="error" message={error} dismissible={true} />
	{/if}

	<!-- Tabs Navigation -->
	<Tabs
		{tabs}
		bind:activeTab
		on:change={handleTabChange}
		variant="ghost-hover"
		border="border-b"
		classes="mb-4"
	>
		<!-- Tab 1: Basic Information -->
		{#if activeTab === 'basic-info'}
			<div class="card p-4 animate-in fade-in duration-300">
				<h2 class="h3 mb-4 flex items-center">
					<Building class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('basic_information', $language, { default: 'المعلومات الأساسية' })}
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<!-- Title -->
					<label class="label md:col-span-2">
						<span>
							{t('title', $language, { default: 'العنوان' })}
							<span class="text-error-500">*</span>
						</span>
						<input
							type="text"
							class="input {getFieldError('title') || (!formData.title && submitAttempted)
								? 'input-error'
								: ''}"
							bind:value={formData.title}
							maxlength={maxTitleLength}
							required
							placeholder={t('title_placeholder', $language, { default: 'أدخل عنوان العقار' })}
						/>
						<span class="text-sm text-surface-500-400-token {$isRTL ? 'text-left' : 'text-right'}">
							{formData.title.length}/{maxTitleLength}
						</span>
						{#if getFieldError('title')}
							<span class="text-error-500 text-sm">
								{getFieldError('title')}
							</span>
						{:else if !formData.title && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>

					<!-- Property Type -->
					<label class="label">
						<span>
							{t('property_type', $language, { default: 'نوع العقار' })}
							<span class="text-error-500">*</span>
						</span>
						<select
							class="select {getFieldError('property_type') ||
							(!formData.property_type && submitAttempted)
								? 'select-error'
								: ''}"
							bind:value={formData.property_type}
							required
						>
							{#each PROPERTY_TYPES as type}
								<option value={type.value}
									>{t(type.value, $language, { default: type.label })}</option
								>
							{/each}
						</select>
						{#if getFieldError('property_type')}
							<span class="text-error-500 text-sm">
								{getFieldError('property_type')}
							</span>
						{:else if !formData.property_type && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>

					<!-- Status -->
					<label class="label">
						<span>
							{t('status', $language, { default: 'الحالة' })}
							<span class="text-error-500">*</span>
						</span>
						<select
							class="select {getFieldError('status') || (!formData.status && submitAttempted)
								? 'select-error'
								: ''}"
							bind:value={formData.status}
							required
						>
							{#each PROPERTY_STATUS as status}
								<option value={status.value}>
									{t(status.value, $language, { default: status.label })}
								</option>
							{/each}
						</select>
						{#if getFieldError('status')}
							<span class="text-error-500 text-sm">
								{getFieldError('status')}
							</span>
						{:else if !formData.status && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>
				</div>
			</div>
		{/if}

		<!-- Tab 2: Location -->
		{#if activeTab === 'location'}
			<div class="card p-4 animate-in fade-in duration-300">
				<h2 class="h3 mb-4 flex items-center">
					<MapPin class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('location', $language, { default: 'الموقع' })}
				</h2>

				<!-- Map Container -->
				<div class="mb-4">
					<div class="flex justify-between items-center mb-2">
						<h3 class="h4">
							{t('map_location', $language, { default: 'تحديد الموقع على الخريطة' })}
						</h3>
						<div class="flex gap-2">
							<button
								type="button"
								class="btn btn-sm variant-ghost-error"
								on:click={clearLocation}
								disabled={!formData.location.latitude}
							>
								<X class="w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
								{t('clear_location', $language, { default: 'مسح الموقع' })}
							</button>
						</div>
					</div>

					{#if locationError}
						<Alert type="warning" message={locationError} class="mb-2" />
					{/if}

					<!-- Use the Map component -->
					{#if mapLoaded}
						<Map
							latitude={formData.location.latitude}
							longitude={formData.location.longitude}
							height="400px"
							width="100%"
							showMarker={true}
							draggableMarker={true}
							showLocationButton={true}
							interactive={true}
							on:locationchange={handleLocationChange}
							classes="mb-4"
						/>
					{:else}
						<div
							class="h-[400px] w-full bg-surface-200-700-token rounded-lg flex items-center justify-center mb-4"
						>
							<button
								type="button"
								class="btn variant-filled-primary"
								on:click={() => (mapLoaded = true)}
							>
								<MapPin class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
								{t('load_map', $language, { default: 'تحميل الخريطة' })}
							</button>
						</div>
					{/if}

					<p class="text-sm text-surface-500-400-token mt-1">
						{t('map_instructions', $language, {
							default:
								'انقر على الخريطة لتحديد موقع العقار أو استخدم زر تحديد الموقع للكشف عن موقعك الحالي'
						})}
					</p>
				</div>

				<!-- Latitude and Longitude Fields -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
					<label class="label">
						<span>{t('latitude', $language, { default: 'خط العرض' })}</span>
						<input
							type="number"
							class="input {getFieldError('location.latitude') ? 'input-error' : ''}"
							bind:value={formData.location.latitude}
							step="any"
							placeholder={t('latitude_placeholder', $language, { default: 'مثال: 24.774265' })}
						/>
						{#if getFieldError('location.latitude')}
							<span class="text-error-500 text-sm">
								{getFieldError('location.latitude')}
							</span>
						{/if}
					</label>

					<label class="label">
						<span>{t('longitude', $language, { default: 'خط الطول' })}</span>
						<input
							type="number"
							class="input {getFieldError('location.longitude') ? 'input-error' : ''}"
							bind:value={formData.location.longitude}
							step="any"
							placeholder={t('longitude_placeholder', $language, { default: 'مثال: 46.738586' })}
						/>
						{#if getFieldError('location.longitude')}
							<span class="text-error-500 text-sm">
								{getFieldError('location.longitude')}
							</span>
						{/if}
					</label>
				</div>

				<!-- Address Information -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<!-- Address -->
					<label class="label md:col-span-2">
						<span>
							{t('address', $language, { default: 'العنوان' })}
							<span class="text-error-500">*</span>
						</span>
						<div class="relative">
							<input
								type="text"
								class="input {getFieldError('address') || (!formData.address && submitAttempted)
									? 'input-error'
									: ''}"
								bind:value={formData.address}
								required
								placeholder={t('address_placeholder', $language, {
									default: 'أدخل عنوان العقار الكامل'
								})}
							/>
							{#if fetchingAddress}
								<div class="absolute {$isRTL ? 'left-3' : 'right-3'} top-1/2 -translate-y-1/2">
									<Loader class="w-5 h-5 animate-spin text-primary-500" />
								</div>
							{/if}
						</div>
						{#if getFieldError('address')}
							<span class="text-error-500 text-sm">
								{getFieldError('address')}
							</span>
						{:else if !formData.address && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>

					<!-- City -->
					<label class="label">
						<span>
							{t('city', $language, { default: 'المدينة' })}
							<span class="text-error-500">*</span>
						</span>
						<div class="relative">
							<input
								type="text"
								class="input {getFieldError('city') || (!formData.city && submitAttempted)
									? 'input-error'
									: ''}"
								bind:value={formData.city}
								required
								placeholder={t('city_placeholder', $language, { default: 'أدخل اسم المدينة' })}
							/>
							{#if fetchingAddress}
								<div class="absolute {$isRTL ? 'left-3' : 'right-3'} top-1/2 -translate-y-1/2">
									<Loader class="w-5 h-5 animate-spin text-primary-500" />
								</div>
							{/if}
						</div>
						{#if getFieldError('city')}
							<span class="text-error-500 text-sm">
								{getFieldError('city')}
							</span>
						{:else if !formData.city && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>

					<!-- State/Province -->
					<label class="label">
						<span>{t('state', $language, { default: 'المنطقة/المحافظة' })}</span>
						<input
							type="text"
							class="input {getFieldError('state') ? 'input-error' : ''}"
							bind:value={formData.state}
							placeholder={t('state_placeholder', $language, {
								default: 'أدخل اسم المنطقة أو المحافظة'
							})}
						/>
						{#if getFieldError('state')}
							<span class="text-error-500 text-sm">
								{getFieldError('state')}
							</span>
						{/if}
					</label>

					<!-- Postal Code -->
					<label class="label">
						<span>{t('postal_code', $language, { default: 'الرمز البريدي' })}</span>
						<input
							type="text"
							class="input {getFieldError('postal_code') ? 'input-error' : ''}"
							bind:value={formData.postal_code}
							placeholder={t('postal_code_placeholder', $language, {
								default: 'أدخل الرمز البريدي'
							})}
						/>
						{#if getFieldError('postal_code')}
							<span class="text-error-500 text-sm">
								{getFieldError('postal_code')}
							</span>
						{/if}
					</label>

					<!-- Country -->
					<label class="label">
						<span>{t('country', $language, { default: 'الدولة' })}</span>
						<input
							type="text"
							class="input {getFieldError('country') ? 'input-error' : ''}"
							bind:value={formData.country}
							placeholder={t('country_placeholder', $language, { default: 'أدخل اسم الدولة' })}
						/>
						{#if getFieldError('country')}
							<span class="text-error-500 text-sm">
								{getFieldError('country')}
							</span>
						{/if}
					</label>
				</div>
			</div>
		{/if}

		<!-- Tab 3: Property Details -->
		{#if activeTab === 'details'}
			<div class="card p-4 animate-in fade-in duration-300">
				<h2 class="h3 mb-4 flex items-center">
					<Info class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('property_details', $language, { default: 'تفاصيل العقار' })}
				</h2>

				<div class="mb-4">
					<!-- Description -->
					<label class="label">
						<span>
							{t('description', $language, { default: 'الوصف' })}
							<span class="text-error-500">*</span>
						</span>
						<textarea
							class="textarea {getFieldError('description') ||
							(!formData.description && submitAttempted)
								? 'textarea-error'
								: ''}"
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
						{#if getFieldError('description')}
							<span class="text-error-500 text-sm">
								{getFieldError('description')}
							</span>
						{:else if !formData.description && submitAttempted}
							<span class="text-error-500 text-sm">
								{t('required_field', $language, { default: 'هذا الحقل مطلوب' })}
							</span>
						{/if}
					</label>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<!-- Size -->
					<label class="label">
						<span>{t('size_sqm', $language, { default: 'المساحة (متر مربع)' })}</span>
						<input
							type="number"
							class="input {getFieldError('size_sqm') ? 'input-error' : ''}"
							bind:value={formData.size_sqm}
							min="0"
							step="0.01"
							placeholder={t('size_placeholder', $language, { default: 'أدخل المساحة' })}
						/>
						{#if getFieldError('size_sqm')}
							<span class="text-error-500 text-sm">
								{getFieldError('size_sqm')}
							</span>
						{/if}
					</label>

					<!-- Bedrooms -->
					<label class="label">
						<span>{t('bedrooms', $language, { default: 'غرف النوم' })}</span>
						<input
							type="number"
							class="input {getFieldError('bedrooms') ? 'input-error' : ''}"
							bind:value={formData.bedrooms}
							min="0"
							step="1"
							placeholder={t('bedrooms_placeholder', $language, { default: 'عدد غرف النوم' })}
						/>
						{#if getFieldError('bedrooms')}
							<span class="text-error-500 text-sm">
								{getFieldError('bedrooms')}
							</span>
						{/if}
					</label>

					<!-- Bathrooms -->
					<label class="label">
						<span>{t('bathrooms', $language, { default: 'الحمامات' })}</span>
						<input
							type="number"
							class="input {getFieldError('bathrooms') ? 'input-error' : ''}"
							bind:value={formData.bathrooms}
							min="0"
							step="1"
							placeholder={t('bathrooms_placeholder', $language, { default: 'عدد الحمامات' })}
						/>
						{#if getFieldError('bathrooms')}
							<span class="text-error-500 text-sm">
								{getFieldError('bathrooms')}
							</span>
						{/if}
					</label>

					<!-- Parking Spaces -->
					<label class="label">
						<span>{t('parking_spaces', $language, { default: 'مواقف السيارات' })}</span>
						<input
							type="number"
							class="input {getFieldError('parking_spaces') ? 'input-error' : ''}"
							bind:value={formData.parking_spaces}
							min="0"
							step="1"
							placeholder={t('parking_placeholder', $language, { default: 'عدد المواقف' })}
						/>
						{#if getFieldError('parking_spaces')}
							<span class="text-error-500 text-sm">
								{getFieldError('parking_spaces')}
							</span>
						{/if}
					</label>

					<!-- Year Built -->
					<label class="label">
						<span>{t('year_built', $language, { default: 'سنة البناء' })}</span>
						<input
							type="number"
							class="input {getFieldError('year_built') ? 'input-error' : ''}"
							bind:value={formData.year_built}
							min="1900"
							max={currentYear}
							step="1"
							placeholder={t('year_built_placeholder', $language, { default: 'سنة بناء العقار' })}
						/>
						{#if getFieldError('year_built')}
							<span class="text-error-500 text-sm">
								{getFieldError('year_built')}
							</span>
						{/if}
					</label>

					<!-- Market Value -->
					<label class="label">
						<span>{t('market_value', $language, { default: 'القيمة السوقية' })}</span>
						<input
							type="number"
							class="input {getFieldError('market_value') ? 'input-error' : ''}"
							bind:value={formData.market_value}
							min="0"
							step="0.01"
							placeholder={t('market_value_placeholder', $language, {
								default: 'القيمة السوقية للعقار'
							})}
						/>
						{#if getFieldError('market_value')}
							<span class="text-error-500 text-sm">
								{getFieldError('market_value')}
							</span>
						{/if}
					</label>

					<!-- Minimum Bid -->
					<label class="label">
						<span>{t('minimum_bid', $language, { default: 'الحد الأدنى للمزايدة' })}</span>
						<input
							type="number"
							class="input {getFieldError('minimum_bid') ? 'input-error' : ''}"
							bind:value={formData.minimum_bid}
							min="0"
							step="0.01"
							placeholder={t('minimum_bid_placeholder', $language, {
								default: 'الحد الأدنى للمزايدة'
							})}
						/>
						{#if getFieldError('minimum_bid')}
							<span class="text-error-500 text-sm">
								{getFieldError('minimum_bid')}
							</span>
						{/if}
					</label>
				</div>
			</div>
		{/if}

		<!-- Tab 4: Features and Amenities -->
		{#if activeTab === 'features'}
			<div class="card p-4 animate-in fade-in duration-300">
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
								class="input {$isRTL ? 'rounded-l-none border-l-0' : 'rounded-r-none border-r-0'}"
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
		{/if}

		<!-- Tab 5: Images -->
		{#if activeTab === 'images'}
			<div class="card p-4 animate-in fade-in duration-300">
				<h2 class="h3 mb-4 flex items-center">
					<Image class="w-6 h-6 {$isRTL ? 'ml-2' : 'mr-2'}" />
					{t('images', $language, { default: 'الصور' })}
				</h2>

				{#if property && property.id}
					<!-- Use PropertyImages component for existing properties -->
					<PropertyImages
						propertyId={property.id}
						{images}
						{maxImages}
						on:update={handleImagesUpdate}
					/>
				{:else}
					<!-- Image upload area -->
					<div class="mb-4">
						<label
							bind:this={dropTarget}
							for="property-images"
							class="block w-full h-40 border-2 border-dashed border-surface-300-600-token rounded-token cursor-pointer hover:bg-surface-hover-token transition-colors"
							on:dragover={handleDragOver}
							on:dragleave={handleDragLeave}
							on:drop={handleDrop}
						>
							<div class="flex flex-col items-center justify-center h-full">
								<Camera class="w-12 h-12 text-surface-500-400-token mb-2" />
								<h3 class="font-medium text-center">
									{t('add_property_images', $language, { default: 'إضافة صور للعقار' })}
								</h3>
								<p class="text-sm text-surface-600-300-token text-center">
									{t('drag_or_click', $language, {
										default: 'اسحب وأفلت الصور هنا أو انقر للاختيار'
									})}
								</p>
								<p class="text-xs text-surface-500-400-token text-center">
									{t('image_requirements', $language, {
										default: 'PNG، JPG، GIF حتى {{max}}MB | {{remaining}} صور متبقية',
										max: maxFileSize,
										remaining: maxImages - images.length
									})}
								</p>
							</div>
						</label>
						<input
							id="property-images"
							bind:this={fileInput}
							type="file"
							accept="image/jpeg,image/png,image/gif,image/webp"
							multiple
							class="hidden"
							on:change={handleFileInputChange}
						/>
						<p class="text-sm text-surface-500-400-token mt-2 text-center">
							{t('image_count', $language, {
								default: '{{current}}/{{max}} صور',
								current: images.length,
								max: maxImages
							})}
						</p>
					</div>

					<!-- Image previews -->
					{#if images.length > 0}
						<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
							{#each images as image, i}
								<div class="relative group" transition:fade>
									<!-- Image preview -->
									<div
										class="aspect-square bg-cover bg-center rounded-token overflow-hidden border {image.is_primary
											? 'border-primary-500'
											: 'border-surface-300-600-token'}"
										style="background-image: url('{image.url}')"
									>
										<!-- Primary badge -->
										{#if image.is_primary}
											<div class="absolute top-2 {$isRTL ? 'right-2' : 'left-2'} z-10">
												<span class="badge variant-filled-primary text-xs">
													{t('primary', $language, { default: 'الرئيسية' })}
												</span>
											</div>
										{/if}
									</div>

									<!-- Image actions -->
									<div
										class="absolute bottom-0 inset-x-0 p-2 bg-black bg-opacity-70 opacity-0 group-hover:opacity-100 transition-opacity flex justify-between"
									>
										<!-- Set as primary button -->
										{#if !image.is_primary}
											<button
												type="button"
												class="btn btn-sm variant-ghost-primary p-1"
												on:click={() => setImageAsPrimary(i)}
												aria-label={t('set_as_primary', $language, {
													default: 'تعيين كصورة رئيسية'
												})}
											>
												<Star class="w-4 h-4" />
											</button>
										{:else}
											<div></div>
										{/if}

										<!-- Remove button -->
										<button
											type="button"
											class="btn btn-sm variant-ghost-error p-1"
											on:click={() => removeImage(i)}
											aria-label={t('remove_image', $language, { default: 'إزالة الصورة' })}
										>
											<Trash2 class="w-4 h-4" />
										</button>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{/if}
			</div>
		{/if}

		<!-- Tab 6: Publishing Options -->
		{#if activeTab === 'publishing'}
			<div class="card p-4 animate-in fade-in duration-300">
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
								class="input {getFieldError('meta_title') ? 'input-error' : ''}"
								bind:value={formData.meta_title}
								placeholder={t('meta_title_placeholder', $language, {
									default: 'عنوان الميتا لمحركات البحث'
								})}
							/>
							{#if getFieldError('meta_title')}
								<span class="text-error-500 text-sm">
									{getFieldError('meta_title')}
								</span>
							{/if}
						</label>

						<!-- Meta Description -->
						<label class="label">
							<span>{t('meta_description', $language, { default: 'وصف الميتا' })}</span>
							<textarea
								class="textarea {getFieldError('meta_description') ? 'textarea-error' : ''}"
								bind:value={formData.meta_description}
								rows="3"
								placeholder={t('meta_description_placeholder', $language, {
									default: 'وصف الميتا لمحركات البحث'
								})}
							></textarea>
							{#if getFieldError('meta_description')}
								<span class="text-error-500 text-sm">
									{getFieldError('meta_description')}
								</span>
							{/if}
						</label>
					</div>
				</div>
			</div>
		{/if}
	</Tabs>

	<!-- Tab Navigation Buttons -->
	<div class="flex justify-between mb-4">
		<!-- Previous button -->
		<button
			type="button"
			class="btn variant-ghost"
			on:click={goToPrevTab}
			disabled={tabs.findIndex((tab) => tab.id === activeTab) === 0}
		>
			{#if $isRTL}
				<ChevronRight class="w-5 h-5 mr-1" />
			{:else}
				<ChevronLeft class="w-5 h-5 mr-1" />
			{/if}
			{t('previous', $language, { default: 'السابق' })}
		</button>

		<!-- Next button -->
		{#if tabs.findIndex((tab) => tab.id === activeTab) < tabs.length - 1}
			<button type="button" class="btn variant-filled-primary" on:click={goToNextTab}>
				{t('next', $language, { default: 'التالي' })}
				{#if $isRTL}
					<ChevronLeft class="w-5 h-5 ml-1" />
				{:else}
					<ChevronRight class="w-5 h-5 ml-1" />
				{/if}
			</button>
		{/if}
	</div>

	<!-- Form Actions -->
	<div class="flex justify-end gap-2">
		<button
			type="button"
			class="btn variant-ghost-surface"
			on:click={handleCancel}
			disabled={loading}
		>
			{t('cancel', $language, { default: 'إلغاء' })}
		</button>
		<button type="submit" class="btn variant-filled-primary" disabled={loading}>
			{#if loading}
				<div class="spinner-icon {$isRTL ? 'ml-2' : 'mr-2'}"></div>
			{:else}
				<Save class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
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
