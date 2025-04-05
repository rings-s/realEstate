<!-- src/lib/components/properties/PropertyForm.svelte -->
<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import {
		parseLocationData,
		getSaudiArabiaCenter,
		formatCoordinates,
		validateCoordinates
	} from '$lib/utils/geocoding';
	import PropertyMap from './PropertyMap.svelte';
	import RoomsManager from './RoomsManager.svelte';
	import AmenitiesSelector from './AmenitiesSelector.svelte';
	import { uiStore } from '$lib/stores/ui';

	// Props
	export let property = null;
	export let cities = [];
	export let isSubmitting = false;
	export let editMode = false;
	export let imageUploadUrl = '/api/properties/upload-images/';
	export let isSearchingCoordinates = false;

	// Constants
	const PROPERTY_TYPES = [
		{ value: 'land', label: 'أرض' },
		{ value: 'apartment', label: 'شقة' },
		{ value: 'villa', label: 'فيلا' },
		{ value: 'commercial', label: 'تجاري' },
		{ value: 'building', label: 'مبنى' },
		{ value: 'farm', label: 'مزرعة' },
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
		{ value: 'inactive', label: 'غير نشط' },
		{ value: 'rejected', label: 'مرفوض' }
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

	// State
	let activeTab = 'basic'; // basic, details, location, features, rooms, images
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
		rooms: [], // Will contain array of {type, name, description, size}
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
		virtual_tours: [],
		documents: [],
		floor_plans: [],
		building_services: [],
		infrastructure: [],
		current_usage: '',
		optimal_usage: '',
		surroundings: '',
		reference_ids: []
	};

	// Feature management
	let featureInput = '';
	let amenityInput = '';

	// Image management
	let imageFiles = [];
	let imagePreviewUrls = [];
	let uploadProgress = 0;
	let uploadError = '';

	// Tab indicators for form completion
	let tabCompletion = {
		basic: false,
		details: false,
		location: false,
		features: false,
		rooms: false,
		images: false
	};

	// Mobile view status
	let isMobileView = false;

	// Map instance reference for direct control
	let mapInstance = null;
	let markerInstance = null;

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Initialize from property if provided
	$: {
		if (property) {
			try {
				// Clone property to form
				form = { ...form, ...property };

				// Parse JSON fields if needed
				if (property.location) {
					form.location = parseLocationData(property.location);
				}

				if (property.features && typeof property.features === 'string') {
					form.features = JSON.parse(property.features);
				}

				if (property.amenities && typeof property.amenities === 'string') {
					form.amenities = JSON.parse(property.amenities);
				}

				if (property.rooms && typeof property.rooms === 'string') {
					form.rooms = JSON.parse(property.rooms);
				} else if (!property.rooms) {
					form.rooms = [];
				}

				if (property.outdoor_spaces && typeof property.outdoor_spaces === 'string') {
					form.outdoor_spaces = JSON.parse(property.outdoor_spaces);
				}

				if (property.building_services && typeof property.building_services === 'string') {
					form.building_services = JSON.parse(property.building_services);
				}

				if (property.infrastructure && typeof property.infrastructure === 'string') {
					form.infrastructure = JSON.parse(property.infrastructure);
				}

				if (property.images && typeof property.images === 'string') {
					form.images = JSON.parse(property.images);

					// Set image previews
					imagePreviewUrls = form.images.map((img) => img.path);
				}

				// Update tab completion indicators
				updateTabCompletion();
			} catch (error) {
				console.error('Error initializing form from property:', error);
			}
		}
	}

	// Check screen size
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

	// Handle tab change
	function setTab(tab) {
		activeTab = tab;
	}

	// Handle rooms update from RoomsManager component
	function handleRoomsUpdate(event) {
		form.rooms = event.detail;
	}

	// Update tab completion status
	function updateTabCompletion() {
		// Basic tab
		tabCompletion.basic = !!form.title && !!form.property_type;

		// Details tab
		tabCompletion.details = !!form.area && !!form.estimated_value;

		// Location tab
		tabCompletion.location = !!form.city && !!form.district && !!form.address;

		// Features tab - always considered complete
		tabCompletion.features = true;

		// Rooms tab - consider complete if at least one room defined or property doesn't need rooms
		tabCompletion.rooms = form.property_type === 'land' || form.rooms.length > 0;

		// Images tab - consider complete if at least one image
		tabCompletion.images = form.images.length > 0 || imageFiles.length > 0;
	}

	// Handle form changes
	$: {
		// Update tab completion whenever form changes
		updateTabCompletion();
	}

	// Function to update map from coordinates in the form
	function updateMapFromCoordinates() {
		// Validate coordinates using utility function
		if (form.location && validateCoordinates(form.location.latitude, form.location.longitude)) {
			// If we have direct map references, we could update it directly
			if (mapInstance && markerInstance) {
				mapInstance.setView([form.location.latitude, form.location.longitude], 15);
				markerInstance.setLatLng([form.location.latitude, form.location.longitude]);
			}
			// Otherwise PropertyMap will reactively update based on form.location
		}
	}

	// Handle location update from map
	function handleLocationChange(event) {
		// Format coordinates using utility
		form.location = formatCoordinates(event.detail);
	}

	// Map ready event handler
	function handleMapReady(event) {
		// Store references to map and marker for direct control if needed
		mapInstance = event.detail.map;
		markerInstance = event.detail.marker;
	}

	// Handle form submission
	function handleSubmit() {
		try {
			const formData = { ...form };

			// Convert string numeric values to actual numbers
			formData.area = formData.area ? Number(formData.area) : null;
			formData.built_up_area = formData.built_up_area ? Number(formData.built_up_area) : null;
			formData.estimated_value = formData.estimated_value ? Number(formData.estimated_value) : null;
			formData.asking_price = formData.asking_price ? Number(formData.asking_price) : null;
			formData.bedrooms = formData.bedrooms ? Number(formData.bedrooms) : null;
			formData.bathrooms = formData.bathrooms ? Number(formData.bathrooms) : null;
			formData.floor_number = formData.floor_number ? Number(formData.floor_number) : null;
			formData.total_floors = formData.total_floors ? Number(formData.total_floors) : null;
			formData.year_built = formData.year_built ? Number(formData.year_built) : null;

			// Store image files for later upload (after property creation)
			if (imageFiles.length > 0) {
				formData.imageFiles = imageFiles;
			}

			// Ensure rooms is an array
			if (!Array.isArray(formData.rooms)) {
				formData.rooms = [];
			}

			// Make sure all JSON fields are properly handled
			// We'll let the parent component handle stringification to keep this component pure

			// Dispatch the data to the parent component
			dispatch('submit', formData);
		} catch (error) {
			console.error('Error preparing form data:', error);
		}
	}

	// Add feature
	function addFeature() {
		if (featureInput.trim()) {
			form.features = [...form.features, featureInput.trim()];
			featureInput = '';
		}
	}

	// Remove feature
	function removeFeature(index) {
		form.features = form.features.filter((_, i) => i !== index);
	}

	// Add amenity
	function addAmenity() {
		if (amenityInput.trim()) {
			form.amenities = [...form.amenities, amenityInput.trim()];
			amenityInput = '';
		}
	}

	// Remove amenity
	function removeAmenity(index) {
		form.amenities = form.amenities.filter((_, i) => i !== index);
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
	}

	// Upload images
	async function uploadImages() {
		if (!imageFiles.length) return;

		try {
			uploadProgress = 0;
			uploadError = '';

			// For existing properties, upload directly
			if (property && property.id) {
				const formData = new FormData();

				// Use 'files' instead of 'images' to match backend expectations
				imageFiles.forEach((file) => {
					formData.append('files', file);
				});

				// Use XHR for progress tracking
				const xhr = new XMLHttpRequest();

				xhr.upload.addEventListener('progress', (e) => {
					if (e.lengthComputable) {
						uploadProgress = Math.round((e.loaded / e.total) * 100);
					}
				});

				xhr.addEventListener('load', () => {
					if (xhr.status === 200 || xhr.status === 201) {
						try {
							const response = JSON.parse(xhr.responseText);
							console.log('Upload response:', response);

							// Add uploaded images to form.images
							if (response.files && Array.isArray(response.files)) {
								form.images = [...form.images, ...response.files];
							} else if (response.images && Array.isArray(response.images)) {
								form.images = [...form.images, ...response.images];
							}

							// Clear uploaded files
							imageFiles = [];
							uploadProgress = 0;

							dispatch('imagesUploaded', { success: true, images: form.images });
						} catch (error) {
							console.error('Error processing upload response:', error);
							uploadError = 'Error processing server response';
							uploadProgress = 0;
						}
					} else {
						console.error('Upload failed with status:', xhr.status, xhr.responseText);
						uploadError = `Failed to upload images: ${xhr.status} ${xhr.statusText}`;
						uploadProgress = 0;
					}
				});

				xhr.addEventListener('error', () => {
					console.error('XHR error occurred during upload');
					uploadError = 'Network error occurred during upload.';
					uploadProgress = 0;
				});

				// Construct URL with property ID
				// Important: Make sure there are no double slashes in the URL
				const url = `${imageUploadUrl.replace(/\/$/, '')}/${property.id}/`;
				console.log('Upload URL:', url);

				xhr.open('POST', url);

				// Add authorization header
				const token = localStorage.getItem('access_token');
				if (token) {
					xhr.setRequestHeader('Authorization', `Bearer ${token}`);
				}

				xhr.send(formData);
			} else {
				// For new properties, we need to store the files and upload after property creation
				console.log('New property - storing files for later upload');
				dispatch('pendingUploads', { files: imageFiles });
			}
		} catch (error) {
			console.error('Error preparing upload:', error);
			uploadError = 'An error occurred preparing the upload.';
			uploadProgress = 0;
		}
	}

	// Handle form fields that should be numeric
	function ensureNumber(value) {
		if (value === '' || value === null || isNaN(Number(value))) return null;
		return Number(value);
	}

	// Navigate to next tab
	function nextTab() {
		const tabs = ['basic', 'details', 'location', 'features', 'rooms', 'images'];
		const currentIndex = tabs.indexOf(activeTab);
		if (currentIndex < tabs.length - 1) {
			setTab(tabs[currentIndex + 1]);
		}
	}

	// Navigate to previous tab
	function prevTab() {
		const tabs = ['basic', 'details', 'location', 'features', 'rooms', 'images'];
		const currentIndex = tabs.indexOf(activeTab);
		if (currentIndex > 0) {
			setTab(tabs[currentIndex - 1]);
		}
	}

	// Handle deed date change
	function formatDeedDate(event) {
		const value = event.target.value;
		form.deed_date = value; // It will be in YYYY-MM-DD format
	}
</script>

<div class="w-full overflow-hidden rounded-lg bg-white shadow-lg dark:bg-gray-800">
	<!-- Tab Navigation -->
	<div
		class="relative sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="no-scrollbar overflow-x-auto">
			<div class="flex w-full min-w-full md:w-auto">
				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'basic'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('basic')}
					aria-selected={activeTab === 'basic'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">المعلومات الأساسية</span>
						<span class="md:hidden">أساسي</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.basic}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'basic'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>

				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'details'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('details')}
					aria-selected={activeTab === 'details'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">تفاصيل العقار</span>
						<span class="md:hidden">تفاصيل</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.details}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'details'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>

				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'location'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('location')}
					aria-selected={activeTab === 'location'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">الموقع</span>
						<span class="md:hidden">الموقع</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.location}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'location'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>

				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'features'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('features')}
					aria-selected={activeTab === 'features'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">المميزات والمرافق</span>
						<span class="md:hidden">المميزات</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.features}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'features'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>

				<!-- New Rooms Tab -->
				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'rooms'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('rooms')}
					aria-selected={activeTab === 'rooms'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">الغرف</span>
						<span class="md:hidden">الغرف</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.rooms}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'rooms'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>

				<button
					class="relative flex-1 px-3 py-3 text-sm font-medium whitespace-nowrap transition-all duration-200 md:flex-initial md:px-6 {activeTab ===
					'images'
						? 'text-blue-600 dark:text-blue-400'
						: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					on:click={() => setTab('images')}
					aria-selected={activeTab === 'images'}
					role="tab"
				>
					<div class="flex items-center justify-center gap-2">
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
						<span class="hidden md:inline">الصور</span>
						<span class="md:hidden">الصور</span>
					</div>

					<!-- Completion Indicator -->
					{#if tabCompletion.images}
						<span
							class="absolute top-2 right-2 h-2 w-2 rounded-full bg-green-500 md:top-3 md:right-3"
						></span>
					{/if}

					<!-- Active Indicator -->
					<div
						class={activeTab === 'images'
							? 'absolute inset-x-0 bottom-0 h-0.5 bg-blue-600 dark:bg-blue-400'
							: ''}
					></div>
				</button>
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
								on:input={() => (form.floor_number = ensureNumber(form.floor_number))}
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
								on:input={() => (form.total_floors = ensureNumber(form.total_floors))}
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
								on:input={() => (form.year_built = ensureNumber(form.year_built))}
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
									<option value={city.value || city}>{city.label || city}</option>
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
											// Format to 6 decimal places
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
											// Format to 6 decimal places
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
								on:click={async () => {
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
											uiStore.addToast(
												'يرجى إدخال العنوان والمدينة أولاً للبحث عن الإحداثيات',
												'warning'
											);
										}
									} catch (error) {
										uiStore.stopLoading();
										uiStore.addToast(error.message || 'حدث خطأ في البحث عن الإحداثيات', 'error');
									} finally {
										isSearchingCoordinates = false;
									}
								}}
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
									// Use the Saudi Arabia center utility function
									form.location = getSaudiArabiaCenter(); // Riyadh center
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

						<!-- Upload Action -->
						{#if imageFiles.length > 0}
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
					{#if imagePreviewUrls.length > 0 || form.images.length > 0}
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
