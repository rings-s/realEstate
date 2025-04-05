<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import {
		parseLocationData,
		getSaudiArabiaCenter,
		formatCoordinates,
		validateCoordinates
	} from '$lib/utils/geocoding';
	import { uiStore } from '$lib/stores/ui';
	import PropertyMap from './PropertyMap.svelte';
	import RoomsManager from './RoomsManager.svelte';
	import AmenitiesSelector from './AmenitiesSelector.svelte';

	// Props
	export let property = null;
	export let cities = [];
	export let isSubmitting = false;
	export let editMode = false;
	export let isSearchingCoordinates = false;

	// Constants - moved here to reduce bloat in render code
	const PROPERTY_TYPES = [
		{ value: 'land', label: 'أرض' },
		{ value: 'apartment', label: 'شقة' },
		{ value: 'villa', label: 'فيلا' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'building', label: 'مبنى' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'office', label: 'مكتب' },
		{ value: 'retail', label: 'محل تجاري' },
		{ value: 'mixed_use', label: 'متعدد الاستخدامات' }
	];

	const PROPERTY_STATUS = [
		{ value: 'draft', label: 'مسودة' },
		{ value: 'pending_approval', label: 'قيد الموافقة' },
		{ value: 'active', label: 'نشط' },
		{ value: 'under_contract', label: 'تحت التعاقد' },
		{ value: 'sold', label: 'مباع' },
		{ value: 'inactive', label: 'غير نشط' }
	];

	const PROPERTY_CONDITION = [
		{ value: 'excellent', label: 'ممتاز' },
		{ value: 'very_good', label: 'جيد جدا' },
		{ value: 'good', label: 'جيد' },
		{ value: 'fair', label: 'مقبول' },
		{ value: 'poor', label: 'سيئ' },
		{ value: 'under_construction', label: 'تحت الإنشاء' },
		{ value: 'new', label: 'جديد' }
	];

	const FACING_DIRECTIONS = [
		{ value: 'north', label: 'شمال' },
		{ value: 'east', label: 'شرق' },
		{ value: 'south', label: 'جنوب' },
		{ value: 'west', label: 'غرب' },
		{ value: 'northeast', label: 'شمال شرق' },
		{ value: 'southeast', label: 'جنوب شرق' },
		{ value: 'southwest', label: 'جنوب غرب' },
		{ value: 'northwest', label: 'شمال غرب' }
	];

	const USAGE_TYPES = [
		{ value: 'residential', label: 'سكني' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'mixed', label: 'مختلط' },
		{ value: 'industrial', label: 'صناعي' },
		{ value: 'agricultural', label: 'زراعي' }
	];

	// Form state with default values
	let form = {
		title: '',
		description: '',
		property_type: 'apartment',
		condition: 'good',
		status: 'draft',
		city: '',
		district: '',
		address: '',
		postal_code: '',
		country: 'Saudi Arabia',
		location: getSaudiArabiaCenter(),
		facing_direction: '',
		area: '',
		built_up_area: '',
		bedrooms: 0,
		bathrooms: 0,
		rooms: [],
		floor_number: null,
		total_floors: null,
		year_built: null,
		estimated_value: '',
		asking_price: '',
		is_published: false,
		features: [],
		amenities: [],
		images: [],
		deed_number: '',
		deed_date: '',
		street_details: '',
		outdoor_spaces: [],
		rental_details: '',
		parking: '',
		videos: [],
		documents: [],
		building_services: [],
		infrastructure: [],
		current_usage: '',
		optimal_usage: '',
		surroundings: '',
		reference_ids: []
	};

	// State
	let activeTab = 'basic'; // basic, details, location, features, rooms, images
	let featureInput = '';
	let amenityInput = '';
	let imageFiles = [];
	let imagePreviewUrls = [];
	let uploadProgress = 0;
	let uploadError = '';
	let isMobileView = false;
	let mapInstance = null;
	let markerInstance = null;
	let tabCompletion = {
		basic: false,
		details: false,
		location: false,
		features: true, // Always considered complete
		rooms: false,
		images: false
	};

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Initialize form from property data if in edit mode
	$: {
		if (property) {
			initializeFormFromProperty(property);
		}
	}

	/**
	 * Initialize form data from property object
	 * @param {Object} propertyData - Property data from API
	 */
	function initializeFormFromProperty(propertyData) {
		try {
			// Start with a fresh form
			form = { ...form };

			// Basic fields
			Object.keys(form).forEach((key) => {
				if (propertyData[key] !== undefined) {
					form[key] = propertyData[key];
				}
			});

			// Handle JSON fields
			if (propertyData.location) {
				form.location = parseLocationData(propertyData.location);
			}

			// Parse JSON fields if they're strings
			[
				'features',
				'amenities',
				'rooms',
				'outdoor_spaces',
				'building_services',
				'infrastructure',
				'images',
				'videos',
				'documents'
			].forEach((field) => {
				if (propertyData[field]) {
					if (typeof propertyData[field] === 'string') {
						try {
							form[field] = JSON.parse(propertyData[field]);
						} catch (e) {
							console.error(`Error parsing ${field}:`, e);
							form[field] = [];
						}
					} else if (Array.isArray(propertyData[field])) {
						form[field] = [...propertyData[field]];
					}
				}
			});

			// Set image previews
			if (form.images && form.images.length) {
				imagePreviewUrls = form.images.map((img) => img.path || img.url);
			}

			// Update tab completion indicators
			updateTabCompletion();
		} catch (error) {
			console.error('Error initializing form from property:', error);
			uiStore.addToast('حدث خطأ أثناء تحميل بيانات العقار', 'error');
		}
	}

	onMount(() => {
		checkScreenSize();
		window.addEventListener('resize', checkScreenSize);

		// If no location is set, initialize with Saudi Arabia center
		if (!form.location || !validateCoordinates(form.location.latitude, form.location.longitude)) {
			form.location = getSaudiArabiaCenter();
		}

		return () => {
			window.removeEventListener('resize', checkScreenSize);
		};
	});

	function checkScreenSize() {
		isMobileView = window.innerWidth < 768;
	}

	// Tab navigation functions
	function setTab(tab) {
		activeTab = tab;
	}

	function handleRoomsUpdate(event) {
		form.rooms = event.detail;
		updateTabCompletion();
	}

	// Update tab completion status based on form state
	function updateTabCompletion() {
		// Basic tab
		tabCompletion.basic = Boolean(form.title && form.property_type);

		// Details tab
		tabCompletion.details = Boolean(form.area && form.estimated_value);

		// Location tab
		tabCompletion.location = Boolean(form.city && form.district && form.address);

		// Rooms tab - complete if property doesn't need rooms or has rooms
		tabCompletion.rooms = form.property_type === 'land' || form.rooms.length > 0;

		// Images tab - consider complete if any images exist
		tabCompletion.images = form.images.length > 0 || imageFiles.length > 0;
	}

	// Update map from coordinates in the form
	function updateMapFromCoordinates() {
		if (form.location && validateCoordinates(form.location.latitude, form.location.longitude)) {
			if (mapInstance && markerInstance) {
				mapInstance.setView([form.location.latitude, form.location.longitude], 15);
				markerInstance.setLatLng([form.location.latitude, form.location.longitude]);
			}
		}
	}

	// Handle location update from map
	function handleLocationChange(event) {
		form.location = formatCoordinates(event.detail);
		updateTabCompletion();
	}

	// Map ready event handler
	function handleMapReady(event) {
		mapInstance = event.detail.map;
		markerInstance = event.detail.marker;
	}

	// Form submission
	function handleSubmit() {
		// The form data is already properly structured
		dispatch('submit', form);
	}

	// Feature management
	function addFeature() {
		if (featureInput.trim()) {
			form.features = [...form.features, featureInput.trim()];
			featureInput = '';
			updateTabCompletion();
		}
	}

	function removeFeature(index) {
		form.features = form.features.filter((_, i) => i !== index);
		updateTabCompletion();
	}

	// Amenities management
	function addAmenity() {
		if (amenityInput.trim()) {
			form.amenities = [...form.amenities, amenityInput.trim()];
			amenityInput = '';
			updateTabCompletion();
		}
	}

	function removeAmenity(index) {
		form.amenities = form.amenities.filter((_, i) => i !== index);
		updateTabCompletion();
	}

	// Handle image selection
	function handleImageSelect(event) {
		const files = Array.from(event.target.files);
		if (!files.length) return;

		imageFiles = [...imageFiles, ...files];

		// Create preview URLs
		files.forEach((file) => {
			const reader = new FileReader();
			reader.onload = (e) => {
				imagePreviewUrls = [...imagePreviewUrls, e.target.result];
			};
			reader.readAsDataURL(file);
		});

		updateTabCompletion();
	}

	// Remove image preview
	function removeImagePreview(index) {
		// Check if this is an existing image or a new one
		if (index < form.images.length) {
			// Existing image - remove from form.images
			form.images = form.images.filter((_, i) => i !== index);
			imagePreviewUrls = imagePreviewUrls.filter((_, i) => i !== index);
		} else {
			// New image - calculate correct index in imageFiles array
			const fileIndex = index - form.images.length;
			imageFiles = imageFiles.filter((_, i) => i !== fileIndex);
			imagePreviewUrls = imagePreviewUrls.filter((_, i) => i !== index);
		}

		updateTabCompletion();
	}

	// Upload images
	async function uploadImages() {
		if (!imageFiles.length) return;

		try {
			uploadProgress = 0;
			uploadError = '';

			// For existing properties, upload directly
			if (property && property.id) {
				dispatch('imagesUpload', { propertyId: property.id, files: imageFiles });
			} else {
				// For new properties, store the files for later upload
				dispatch('pendingUploads', { files: imageFiles });
			}
		} catch (error) {
			console.error('Error preparing upload:', error);
			uploadError = 'حدث خطأ أثناء تحضير الملفات للرفع.';
			uploadProgress = 0;
		}
	}

	// Format deed date
	function formatDeedDate(event) {
		form.deed_date = event.target.value; // It will be in YYYY-MM-DD format
	}

	// Search for location using geocoding API
	async function searchAddressLocation() {
		if (isSearchingCoordinates) return;

		try {
			isSearchingCoordinates = true;

			if (form.address && form.city) {
				const fullAddress = `${form.address}, ${form.district || ''}, ${form.city}, ${
					form.country || 'المملكة العربية السعودية'
				}`;

				// Show loading indicator
				uiStore.startLoading('جاري البحث عن الإحداثيات...');

				// Import and use the geocoding utility
				const { getLocationFromAddress } = await import('$lib/utils/geocoding');
				const coordinates = await getLocationFromAddress(fullAddress);

				// Update form with coordinates from geocoding result
				form.location = {
					latitude: coordinates.latitude,
					longitude: coordinates.longitude
				};

				// Update map
				updateMapFromCoordinates();

				uiStore.stopLoading();
				uiStore.addToast('تم العثور على الإحداثيات بنجاح', 'success');
			} else {
				uiStore.addToast('يرجى إدخال العنوان والمدينة أولاً للبحث عن الإحداثيات', 'warning');
			}
		} catch (error) {
			uiStore.stopLoading();
			uiStore.addToast(error.message || 'حدث خطأ في البحث عن الإحداثيات', 'error');
		} finally {
			isSearchingCoordinates = false;
		}
	}

	// Tab navigation
	function nextTab() {
		const tabs = ['basic', 'details', 'location', 'features', 'rooms', 'images'];
		const currentIndex = tabs.indexOf(activeTab);
		if (currentIndex < tabs.length - 1) {
			setTab(tabs[currentIndex + 1]);
		}
	}

	function prevTab() {
		const tabs = ['basic', 'details', 'location', 'features', 'rooms', 'images'];
		const currentIndex = tabs.indexOf(activeTab);
		if (currentIndex > 0) {
			setTab(tabs[currentIndex - 1]);
		}
	}

	// Watch form changes to update completion status
	$: {
		updateTabCompletion();
	}
</script>

<div class="w-full overflow-hidden rounded-lg bg-white shadow-lg dark:bg-gray-800">
	<!-- Tab Navigation -->
	<div
		class="relative sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="no-scrollbar overflow-x-auto">
			<div class="flex w-full min-w-full md:w-auto">
				<!-- Tab buttons -->
				{#each ['basic', 'details', 'location', 'features', 'rooms', 'images'] as tab}
					<button
						class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
						tab
							? 'text-blue-600 dark:text-blue-400'
							: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
						on:click={() => setTab(tab)}
						aria-selected={activeTab === tab}
						role="tab"
					>
						<div class="flex items-center justify-center gap-2">
							<!-- Icon based on tab -->
							{#if tab === 'basic'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
									/>
								</svg>
							{:else if tab === 'details'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
									/>
								</svg>
							{:else if tab === 'location'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
									/>
								</svg>
							{:else if tab === 'features'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
									/>
								</svg>
							{:else if tab === 'rooms'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
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
							{:else if tab === 'images'}
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
									/>
								</svg>
							{/if}
							<span class="hidden md:inline"
								>{tab === 'basic'
									? 'المعلومات الأساسية'
									: tab === 'details'
										? 'تفاصيل العقار'
										: tab === 'location'
											? 'الموقع'
											: tab === 'features'
												? 'المميزات والمرافق'
												: tab === 'rooms'
													? 'الغرف'
													: tab === 'images'
														? 'الصور'
														: tab}</span
							>
							<span class="md:hidden"
								>{tab === 'basic'
									? 'أساسي'
									: tab === 'details'
										? 'تفاصيل'
										: tab === 'location'
											? 'الموقع'
											: tab === 'features'
												? 'المميزات'
												: tab === 'rooms'
													? 'الغرف'
													: tab === 'images'
														? 'الصور'
														: tab}</span
							>
						</div>

						<!-- Completion Indicator -->
						{#if tabCompletion[tab]}
							<span
								class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
							></span>
						{/if}

						<!-- Active Indicator -->
						<div
							class={activeTab === tab
								? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
								: ''}
						></div>
					</button>
				{/each}
			</div>
		</div>
	</div>

	<form on:submit|preventDefault={handleSubmit} class="w-full">
		<div class="w-full p-4 md:p-6">
			<!-- Tab Title -->
			<div class="mb-6">
				<h2 class="text-xl font-bold text-gray-900 dark:text-white">
					{#if activeTab === 'basic'}
						المعلومات الأساسية
					{:else if activeTab === 'details'}
						تفاصيل العقار
					{:else if activeTab === 'location'}
						موقع العقار
					{:else if activeTab === 'features'}
						المميزات والمرافق
					{:else if activeTab === 'rooms'}
						الغرف
					{:else if activeTab === 'images'}
						صور العقار
					{/if}
				</h2>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					{#if activeTab === 'basic'}
						أدخل المعلومات الأساسية للعقار.
					{:else if activeTab === 'details'}
						أضف التفاصيل الفنية للعقار.
					{:else if activeTab === 'location'}
						حدد موقع العقار على الخريطة.
					{:else if activeTab === 'features'}
						أضف ميزات العقار ومرافقه.
					{:else if activeTab === 'rooms'}
						أضف معلومات الغرف في العقار.
					{:else if activeTab === 'images'}
						أرفع صور العقار.
					{/if}
				</p>
			</div>

			<!-- Basic Information Tab -->
			{#if activeTab === 'basic'}
				<div class="space-y-6">
					<div class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-6">
						<!-- Title -->
						<div class="sm:col-span-6">
							<label
								for="title"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								عنوان العقار <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="title"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.title}
								required
							/>
						</div>

						<!-- Property Type -->
						<div class="sm:col-span-3">
							<label
								for="property_type"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								نوع العقار <span class="text-red-500">*</span>
							</label>
							<select
								id="property_type"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.property_type}
								required
							>
								{#each PROPERTY_TYPES as type}
									<option value={type.value}>{type.label}</option>
								{/each}
							</select>
						</div>

						<!-- Condition -->
						<div class="sm:col-span-3">
							<label
								for="condition"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								حالة العقار <span class="text-red-500">*</span>
							</label>
							<select
								id="condition"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.condition}
								required
							>
								{#each PROPERTY_CONDITION as condition}
									<option value={condition.value}>{condition.label}</option>
								{/each}
							</select>
						</div>

						<!-- Status -->
						<div class="sm:col-span-3">
							<label
								for="status"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								حالة القائمة <span class="text-red-500">*</span>
							</label>
							<select
								id="status"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.status}
								required
							>
								{#each PROPERTY_STATUS as status}
									<option value={status.value}>{status.label}</option>
								{/each}
							</select>
						</div>

						<!-- Published -->
						<div class="flex items-center sm:col-span-3">
							<label for="is_published" class="flex cursor-pointer items-center">
								<input
									type="checkbox"
									id="is_published"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:text-blue-500"
									bind:checked={form.is_published}
								/>
								<span class="mr-2 text-sm text-gray-700 dark:text-gray-300">نشر العقار</span>
							</label>
						</div>

						<!-- Deed Number -->
						<div class="sm:col-span-3">
							<label
								for="deed_number"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								رقم الصك
							</label>
							<input
								type="text"
								id="deed_number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.deed_number}
							/>
						</div>

						<!-- Deed Date -->
						<div class="sm:col-span-3">
							<label
								for="deed_date"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								تاريخ الصك
							</label>
							<input
								type="date"
								id="deed_date"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.deed_date}
								on:change={formatDeedDate}
							/>
						</div>

						<!-- Description -->
						<div class="sm:col-span-6">
							<label
								for="description"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الوصف التفصيلي
							</label>
							<textarea
								id="description"
								rows="5"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.description}
							></textarea>
						</div>
					</div>
				</div>
			{/if}

			<!-- Details Tab -->
			{#if activeTab === 'details'}
				<div class="space-y-6">
					<div class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-6">
						<!-- Area -->
						<div class="sm:col-span-3">
							<label
								for="area"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								المساحة (م²) <span class="text-red-500">*</span>
							</label>
							<input
								type="number"
								id="area"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.area}
								min="0"
								step="0.01"
								required
							/>
						</div>

						<!-- Built Up Area -->
						<div class="sm:col-span-3">
							<label
								for="built_up_area"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								المساحة المبنية (م²)
							</label>
							<input
								type="number"
								id="built_up_area"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.built_up_area}
								min="0"
								step="0.01"
							/>
						</div>

						<!-- Bedrooms & Bathrooms -->
						<div class="sm:col-span-3">
							<label
								for="bedrooms"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								عدد غرف النوم
							</label>
							<input
								type="number"
								id="bedrooms"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.bedrooms}
								min="0"
							/>
						</div>

						<div class="sm:col-span-3">
							<label
								for="bathrooms"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								عدد الحمامات
							</label>
							<input
								type="number"
								id="bathrooms"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.bathrooms}
								min="0"
							/>
						</div>

						<!-- Floors -->
						<div class="sm:col-span-3">
							<label
								for="floor_number"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								رقم الطابق
							</label>
							<input
								type="number"
								id="floor_number"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.floor_number}
								min="0"
							/>
						</div>

						<div class="sm:col-span-3">
							<label
								for="total_floors"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								إجمالي الطوابق
							</label>
							<input
								type="number"
								id="total_floors"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.total_floors}
								min="0"
							/>
						</div>

						<!-- Year Built & Direction -->
						<div class="sm:col-span-3">
							<label
								for="year_built"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								سنة البناء
							</label>
							<input
								type="number"
								id="year_built"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.year_built}
								min="1900"
								max={new Date().getFullYear()}
							/>
						</div>

						<div class="sm:col-span-3">
							<label
								for="facing_direction"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								اتجاه الواجهة
							</label>
							<select
								id="facing_direction"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.facing_direction}
							>
								<option value="">اختر الاتجاه</option>
								{#each FACING_DIRECTIONS as direction}
									<option value={direction.value}>{direction.label}</option>
								{/each}
							</select>
						</div>

						<!-- Usage -->
						<div class="sm:col-span-3">
							<label
								for="current_usage"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الاستخدام الحالي
							</label>
							<select
								id="current_usage"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.current_usage}
							>
								<option value="">اختر الاستخدام</option>
								{#each USAGE_TYPES as usage}
									<option value={usage.value}>{usage.label}</option>
								{/each}
							</select>
						</div>

						<div class="sm:col-span-3">
							<label
								for="optimal_usage"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الاستخدام الأمثل
							</label>
							<select
								id="optimal_usage"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.optimal_usage}
							>
								<option value="">اختر الاستخدام</option>
								{#each USAGE_TYPES as usage}
									<option value={usage.value}>{usage.label}</option>
								{/each}
							</select>
						</div>

						<!-- Pricing -->
						<div class="sm:col-span-3">
							<label
								for="estimated_value"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								القيمة التقديرية (ريال) <span class="text-red-500">*</span>
							</label>
							<div class="relative">
								<input
									type="number"
									id="estimated_value"
									class="w-full rounded-md border border-gray-300 bg-white py-2 pr-3 pl-12 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
									bind:value={form.estimated_value}
									min="0"
									step="0.01"
									required
								/>
								<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
									<span class="text-gray-500 dark:text-gray-400">ريال</span>
								</div>
							</div>
						</div>

						<div class="sm:col-span-3">
							<label
								for="asking_price"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								السعر المطلوب (ريال)
							</label>
							<div class="relative">
								<input
									type="number"
									id="asking_price"
									class="w-full rounded-md border border-gray-300 bg-white py-2 pr-3 pl-12 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
									bind:value={form.asking_price}
									min="0"
									step="0.01"
								/>
								<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
									<span class="text-gray-500 dark:text-gray-400">ريال</span>
								</div>
							</div>
						</div>

						<!-- Additional Details - Street Details -->
						<div class="sm:col-span-6">
							<label
								for="street_details"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								تفاصيل الشوارع
							</label>
							<textarea
								id="street_details"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.street_details}
							></textarea>
						</div>

						<!-- Rental Details -->
						<div class="sm:col-span-6">
							<label
								for="rental_details"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								تفاصيل الإيجار
							</label>
							<textarea
								id="rental_details"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.rental_details}
							></textarea>
						</div>

						<!-- Parking -->
						<div class="sm:col-span-6">
							<label
								for="parking"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								تفاصيل مواقف السيارات
							</label>
							<textarea
								id="parking"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.parking}
							></textarea>
						</div>
					</div>
				</div>
			{/if}

			<!-- Location Tab -->
			{#if activeTab === 'location'}
				<div class="space-y-6">
					<div class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-6">
						<!-- City & District -->
						<div class="sm:col-span-3">
							<label
								for="city"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								المدينة <span class="text-red-500">*</span>
							</label>
							<select
								id="city"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.city}
								required
							>
								<option value="">اختر المدينة</option>
								{#each cities as city}
									<option value={city}>{city}</option>
								{/each}
							</select>
						</div>

						<div class="sm:col-span-3">
							<label
								for="district"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الحي <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="district"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.district}
								required
							/>
						</div>

						<!-- Full Address -->
						<div class="sm:col-span-6">
							<label
								for="address"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								العنوان <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								id="address"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.address}
								required
							/>
						</div>

						<!-- Postal Code & Country -->
						<div class="sm:col-span-3">
							<label
								for="postal_code"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الرمز البريدي
							</label>
							<input
								type="text"
								id="postal_code"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.postal_code}
							/>
						</div>

						<div class="sm:col-span-3">
							<label
								for="country"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								الدولة
							</label>
							<input
								type="text"
								id="country"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								bind:value={form.country}
								placeholder="المملكة العربية السعودية"
							/>
						</div>

						<!-- Latitude and Longitude Fields -->
						<div class="sm:col-span-3">
							<label
								for="latitude"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								خط العرض (Latitude) <span class="text-red-500">*</span>
							</label>
							<div class="relative">
								<input
									type="number"
									id="latitude"
									class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
									bind:value={form.location.latitude}
									min="-90"
									max="90"
									step="0.000001"
									required
									on:input={() => {
										if (!isNaN(parseFloat(form.location.latitude))) {
											form.location.latitude = parseFloat(
												parseFloat(form.location.latitude).toFixed(6)
											);
											updateMapFromCoordinates();
										}
									}}
								/>
								<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
									خط العرض بين -90 و 90 درجة
								</p>
							</div>
						</div>

						<div class="sm:col-span-3">
							<label
								for="longitude"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								خط الطول (Longitude) <span class="text-red-500">*</span>
							</label>
							<div class="relative">
								<input
									type="number"
									id="longitude"
									class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
									bind:value={form.location.longitude}
									min="-180"
									max="180"
									step="0.000001"
									required
									on:input={() => {
										if (!isNaN(parseFloat(form.location.longitude))) {
											form.location.longitude = parseFloat(
												parseFloat(form.location.longitude).toFixed(6)
											);
											updateMapFromCoordinates();
										}
									}}
								/>
								<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
									خط الطول بين -180 و 180 درجة
								</p>
							</div>
						</div>

						<!-- Address to Coordinates Action -->
						<div class="flex flex-wrap gap-3 sm:col-span-6">
							<button
								type="button"
								class="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
								on:click={searchAddressLocation}
								disabled={isSearchingCoordinates}
							>
								{#if isSearchingCoordinates}
									<span
										class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
									></span>
									جاري البحث...
								{:else}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
										/>
									</svg>
									البحث من العنوان
								{/if}
							</button>

							<!-- Quick preset locations -->
							<button
								type="button"
								class="flex items-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-gray-700 transition hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
								on:click={() => {
									form.location = getSaudiArabiaCenter();
									updateMapFromCoordinates();
								}}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-5 w-5"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
									/>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
									/>
								</svg>
								وسط الرياض
							</button>
						</div>

						<p class="text-xs text-gray-500 sm:col-span-6 dark:text-gray-400">
							يمكنك تحديد الموقع على الخريطة مباشرة أو استخدام زر "تحديد موقعي الحالي" في الخريطة
							للحصول على الموقع الحالي.
						</p>
					</div>

					<!-- Map Location -->
					<div class="mt-6">
						<div class="mb-2 flex items-center justify-between">
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
								حدد الموقع على الخريطة <span class="text-red-500">*</span>
							</label>
							<div class="text-xs text-gray-500 dark:text-gray-400">
								الإحداثيات: {typeof form.location.latitude === 'number'
									? form.location.latitude.toFixed(6)
									: '0.000000'},
								{typeof form.location.longitude === 'number'
									? form.location.longitude.toFixed(6)
									: '0.000000'}
							</div>
						</div>
						<div class="overflow-hidden rounded-lg border border-gray-300 dark:border-gray-600">
							<PropertyMap
								location={form.location}
								height="400px"
								interactive={true}
								showControls={true}
								enableSearch={true}
								on:locationchange={handleLocationChange}
								on:mapready={handleMapReady}
							/>
						</div>
						<p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
							انقر على الخريطة لتحديد موقع العقار بدقة، أو اسحب العلامة إلى الموقع الصحيح، أو استخدم
							زر "تحديد موقعي الحالي".
						</p>
					</div>
				</div>
			{/if}

			<!-- Features Tab -->
			{#if activeTab === 'features'}
				<div class="space-y-6">
					<!-- Features Section -->
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">المميزات</h3>
						<div class="mb-3 flex gap-2">
							<input
								type="text"
								class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="أضف ميزة..."
								bind:value={featureInput}
								on:keyup={(e) => e.key === 'Enter' && addFeature()}
							/>
							<button
								type="button"
								class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
								on:click={addFeature}
							>
								إضافة
							</button>
						</div>

						<!-- Feature Tags -->
						{#if form.features.length > 0}
							<div class="mt-4 flex flex-wrap gap-2">
								{#each form.features as feature, index}
									<div
										class="flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800 dark:bg-blue-900 dark:text-blue-200"
									>
										<span>{feature}</span>
										<button
											type="button"
											class="mr-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
											on:click={() => removeFeature(index)}
											aria-label="حذف الميزة"
										>
											<svg
												xmlns="http://www.w3.org/2000/svg"
												class="h-4 w-4"
												viewBox="0 0 20 20"
												fill="currentColor"
											>
												<path
													fill-rule="evenodd"
													d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
													clip-rule="evenodd"
												/>
											</svg>
										</button>
									</div>
								{/each}
							</div>
						{:else}
							<div class="mt-3 rounded-md bg-gray-50 p-4 text-center dark:bg-gray-700">
								<p class="text-sm text-gray-500 dark:text-gray-400">لم تتم إضافة أي ميزات بعد.</p>
							</div>
						{/if}
					</div>

					<!-- Amenities Section -->
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">المرافق</h3>
						<AmenitiesSelector
							selected={form.amenities}
							on:change={(e) => (form.amenities = e.detail)}
						/>
					</div>

					<!-- Feature Suggestions -->
					<div class="mt-4">
						<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
							اقتراحات المميزات الشائعة:
						</h3>
						<div class="flex flex-wrap gap-2">
							{#each ['تكييف مركزي', 'حوض سباحة', 'حديقة خاصة', 'مطبخ مجهز', 'انترنت', 'موقف سيارات', 'أمن', 'مصعد'] as suggestion}
								<button
									type="button"
									class="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700 transition hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
									on:click={() => {
										featureInput = suggestion;
										addFeature();
									}}
								>
									{suggestion}
								</button>
							{/each}
						</div>
					</div>

					<!-- Building Services & Infrastructure -->
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">
							خدمات المبنى والبنية التحتية
						</h3>

						<!-- Building Services -->
						<div class="mb-4">
							<label
								for="building_services"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								خدمات المبنى
							</label>
							<textarea
								id="building_services"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="وصف خدمات المبنى مثل: الصيانة، الأمن، النظافة، إلخ..."
								bind:value={form.building_services}
							></textarea>
						</div>

						<!-- Infrastructure -->
						<div>
							<label
								for="infrastructure"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								البنية التحتية
							</label>
							<textarea
								id="infrastructure"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="وصف البنية التحتية المتوفرة مثل: شبكات المياه، الكهرباء، الاتصالات، إلخ..."
								bind:value={form.infrastructure}
							></textarea>
						</div>
					</div>

					<!-- Surroundings Section -->
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">المحيط</h3>
						<div>
							<label
								for="surroundings"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								وصف المحيط والخدمات القريبة
							</label>
							<textarea
								id="surroundings"
								rows="3"
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
								placeholder="وصف المنطقة المحيطة بالعقار والخدمات القريبة مثل: المدارس، المستشفيات، المراكز التجارية، إلخ..."
								bind:value={form.surroundings}
							></textarea>
						</div>
					</div>
				</div>
			{/if}

			<!-- Rooms Tab -->
			{#if activeTab === 'rooms'}
				<RoomsManager rooms={form.rooms} on:update={handleRoomsUpdate} />
			{/if}

			<!-- Images Tab -->
			{#if activeTab === 'images'}
				<div class="space-y-6">
					<!-- Image Upload Section -->
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">رفع الصور</h3>

						<!-- Uploader -->
						<div
							class="flex flex-col items-center rounded-md border-2 border-dashed border-gray-300 p-6 dark:border-gray-600"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="mb-2 h-12 w-12 text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
							<p class="mb-3 text-center text-sm text-gray-600 dark:text-gray-400">
								{#if isMobileView}
									التقط أو اختر صورًا من جهازك
								{:else}
									اسحب الصور هنا أو انقر للاختيار
								{/if}
							</p>
							<input
								type="file"
								id="images"
								accept="image/*"
								multiple
								class="hidden"
								on:change={handleImageSelect}
							/>
							<button
								type="button"
								class="rounded-md bg-blue-100 px-4 py-2 text-blue-700 transition hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800"
								on:click={() => document.getElementById('images').click()}
							>
								اختيار الصور
							</button>
						</div>

						<!-- Upload Progress -->
						{#if uploadProgress > 0 && uploadProgress < 100}
							<div class="mt-4">
								<div class="mb-1 flex justify-between text-sm text-gray-700 dark:text-gray-300">
									<span>جاري الرفع...</span>
									<span>{uploadProgress}%</span>
								</div>
								<div class="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
									<div
										class="h-2.5 rounded-full bg-blue-600"
										style="width: {uploadProgress}%"
									></div>
								</div>
							</div>
						{/if}

						<!-- Upload Error -->
						{#if uploadError}
							<div
								class="mt-4 rounded-md bg-red-100 p-3 text-red-700 dark:bg-red-900 dark:text-red-300"
							>
								<p>{uploadError}</p>
							</div>
						{/if}

						<!-- Upload Action for existing properties -->
						{#if property && property.id && imageFiles.length > 0}
							<div class="mt-4 flex justify-end">
								<button
									type="button"
									class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
									on:click={uploadImages}
								>
									رفع {imageFiles.length} صور
								</button>
							</div>
						{/if}
					</div>

					<!-- Image Preview Section -->
					{#if imagePreviewUrls.length > 0}
						<div
							class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
						>
							<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">معاينة الصور</h3>

							<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
								{#each imagePreviewUrls as url, index}
									<div
										class="group relative h-48 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700"
									>
										<img src={url} alt="معاينة الصورة" class="h-full w-full object-cover" />

										<!-- Overlay with actions -->
										<div
											class="bg-opacity-0 group-hover:bg-opacity-40 absolute inset-0 flex items-center justify-center bg-black opacity-0 transition-opacity group-hover:opacity-100"
										>
											<button
												type="button"
												class="rounded-full bg-red-600 p-2 text-white transition hover:bg-red-700"
												on:click={() => removeImagePreview(index)}
												aria-label="حذف الصورة"
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													class="h-5 w-5"
													viewBox="0 0 20 20"
													fill="currentColor"
												>
													<path
														fill-rule="evenodd"
														d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
														clip-rule="evenodd"
													/>
												</svg>
											</button>
										</div>

										<!-- Primary image indicator -->
										{#if index < form.images.length && form.images[index].is_primary}
											<div
												class="absolute bottom-2 left-2 rounded-full bg-green-600 px-2 py-0.5 text-xs text-white"
											>
												الصورة الرئيسية
											</div>
										{/if}

										<!-- Image status indicator -->
										{#if index >= form.images.length}
											<div
												class="absolute top-2 right-2 rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
											>
												بانتظار الرفع
											</div>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Navigation Buttons -->
			<div
				class="mt-8 flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-700"
			>
				<div>
					<button
						type="button"
						class="mr-3 rounded-md border border-gray-300 px-4 py-2 text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
						on:click={() => dispatch('cancel')}
					>
						إلغاء
					</button>

					{#if editMode && property && property.id}
						<button
							type="button"
							class="rounded-md bg-red-600 px-4 py-2 text-white transition hover:bg-red-700"
							on:click={() => dispatch('delete', property)}
						>
							حذف العقار
						</button>
					{/if}
				</div>

				<div class="flex gap-3">
					<!-- Previous Tab Button -->
					{#if activeTab !== 'basic'}
						<button
							type="button"
							class="flex items-center gap-1 rounded-md border border-gray-300 px-4 py-2 text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
							on:click={prevTab}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
									clip-rule="evenodd"
								/>
							</svg>
							السابق
						</button>
					{/if}

					<!-- Next Tab Button -->
					{#if activeTab !== 'images'}
						<button
							type="button"
							class="flex items-center gap-1 rounded-md bg-blue-100 px-4 py-2 text-blue-700 transition hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
							on:click={nextTab}
						>
							التالي
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					{:else}
						<!-- Submit Button (only on last tab) -->
						<button
							type="submit"
							class="flex items-center gap-2 rounded-md bg-blue-600 px-6 py-2 text-white transition hover:bg-blue-700"
							disabled={isSubmitting}
						>
							{#if isSubmitting}
								<div
									class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
								></div>
							{/if}
							{editMode ? 'تحديث العقار' : 'إضافة العقار'}
						</button>
					{/if}
				</div>
			</div>
		</div>
	</form>
</div>
