<!-- src/routes/properties/add/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { propertiesStore } from '$lib/stores/properties';
	import { auth } from '$lib/stores/auth';
	import { ROLES, PERMISSIONS, hasRole, hasPermission } from '$lib/utils/permissions';
	import { uiStore } from '$lib/stores/ui';
	import { formatValidationErrors } from '$lib/utils/formatting';
	import { prepareEntityData, PROPERTY_JSON_FIELDS } from '$lib/utils/jsonFields';
	import { validateImageFiles } from '$lib/services/upload';
	import PropertyForm from '$lib/components/properties/PropertyForm.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Alert from '$lib/components/common/Alert.svelte';

	// Page state
	let isLoading = true;
	let isSubmitting = false;
	let error = null;
	let validationErrors = {};
	let isSearchingCoordinates = false;
	let pendingImageFiles = [];
	let uploadProgress = 0;

	// Available city options for dropdown - matching Saudi cities from the backend
	const cities = [
		'الرياض',
		'جدة',
		'مكة',
		'المدينة المنورة',
		'الدمام',
		'الخبر',
		'تبوك',
		'القصيم',
		'حائل',
		'أبها',
		'الطائف',
		'جازان',
		'نجران',
		'الباحة',
		'سكاكا',
		'عرعر'
	];

	/**
	 * Process form data and create a clean property object for submission
	 * with proper JSON field handling for Django v5 compatibility
	 */
	function preparePropertyData(formData) {
		// Create a base object with direct field mappings
		const baseData = {
			title: formData.title || '',
			description: formData.description || '',
			property_type: formData.property_type || 'apartment',
			condition: formData.condition || 'good',
			status: formData.status || 'draft',
			city: formData.city || '',
			district: formData.district || '',
			address: formData.address || '',
			postal_code: formData.postal_code || '',
			country: formData.country || 'Saudi Arabia',
			area: formData.area ? Number(formData.area) : 0,
			built_up_area: formData.built_up_area ? Number(formData.built_up_area) : null,
			estimated_value: formData.estimated_value ? Number(formData.estimated_value) : 0,
			asking_price: formData.asking_price ? Number(formData.asking_price) : null,
			bedrooms: formData.bedrooms !== undefined ? Number(formData.bedrooms) : 0,
			bathrooms: formData.bathrooms !== undefined ? Number(formData.bathrooms) : 0,
			floor_number: formData.floor_number !== undefined ? Number(formData.floor_number) : null,
			total_floors: formData.total_floors !== undefined ? Number(formData.total_floors) : null,
			year_built: formData.year_built ? Number(formData.year_built) : null,
			is_published: Boolean(formData.is_published),
			deed_date: formData.deed_date || null,
			deed_number: formData.deed_number || '',
			facing_direction: formData.facing_direction || '',
			current_usage: formData.current_usage || '',
			optimal_usage: formData.optimal_usage || ''
		};

		// Handle JSON fields properly for Django v5
		// These fields need to be initialized correctly for the backend
		baseData.location = formData.location || {};
		baseData.rooms = Array.isArray(formData.rooms) ? formData.rooms : [];
		baseData.features = Array.isArray(formData.features) ? formData.features : [];
		baseData.amenities = Array.isArray(formData.amenities) ? formData.amenities : [];
		baseData.outdoor_spaces = Array.isArray(formData.outdoor_spaces) ? formData.outdoor_spaces : [];
		baseData.videos = Array.isArray(formData.videos) ? formData.videos : [];
		baseData.documents = Array.isArray(formData.documents) ? formData.documents : [];

		// Initialize images as empty array - we'll upload separately
		baseData.images = [];

		// Handle text fields that might contain JSON or plain text
		baseData.street_details = formData.street_details || '';
		baseData.rental_details = formData.rental_details || '';
		baseData.parking = formData.parking || '';
		baseData.building_services = formData.building_services || '';
		baseData.infrastructure = formData.infrastructure || '';
		baseData.surroundings = formData.surroundings || '';

		return baseData;
	}

	/**
	 * Upload images to a property with direct Django integration
	 * @param {string} propertyId - The property ID
	 * @param {FileList|File[]} files - The files to upload
	 * @returns {Promise} - Promise resolving to the upload result
	 */
	async function uploadImagesToProperty(propertyId, files) {
		if (!propertyId || !files || files.length === 0) {
			throw new Error('Property ID and files are required for upload');
		}

		console.log(`Uploading ${files.length} images to property ID: ${propertyId}`);

		// Create form data for Django's handling
		const formData = new FormData();

		// Add each file individually with the same field name
		// This matches Django's request.FILES['images'] expectation
		Array.from(files).forEach((file) => {
			formData.append('images', file);
		});

		// Django also needs to know which property to attach these to
		formData.append('property_id', propertyId);

		try {
			// Set the progress indicator
			uploadProgress = 10; // Start progress

			// Get the API URL - directly use the upload endpoint for properties
			const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
			const uploadUrl = `${API_BASE_URL}/properties/${propertyId}/uploads/`;

			// Get authentication token
			const token = localStorage.getItem('access_token');
			if (!token) {
				throw new Error('Authentication token required');
			}

			// Update progress
			uploadProgress = 30;

			// Send the request
			const response = await fetch(uploadUrl, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${token}`
					// Let browser set Content-Type with boundary
				},
				body: formData
			});

			uploadProgress = 70;

			if (!response.ok) {
				const errorText = await response.text();
				console.error('Upload failed:', response.status, errorText);
				throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
			}

			uploadProgress = 90;

			// Parse the response
			const result = await response.json();

			uploadProgress = 100;

			console.log('Upload successful. Server response:', result);
			return result;
		} catch (error) {
			console.error('Error during image upload:', error);
			uploadProgress = 0;
			throw error;
		}
	}

	/**
	 * Handle form submission with improved media handling for Django integration
	 */
	/**
	 * Handle form submission with explicit image handling to ensure it's saved in DB
	 */
	async function handleSubmit(event) {
		const formData = event.detail;
		isSubmitting = true;
		error = null;
		validationErrors = {};
		uploadProgress = 0;

		try {
			console.log('Form data received:', formData);

			// Store pending images for later upload
			if (formData.imageFiles && formData.imageFiles.length) {
				pendingImageFiles = formData.imageFiles;
				console.log(
					`${pendingImageFiles.length} images pending for upload after property creation`
				);
			}

			// Prepare data
			const propertyData = preparePropertyData(formData);

			// Properly prepare JSON fields for Django
			// This uses the prepareEntityData utility to stringify JSON fields
			const preparedData = prepareEntityData(propertyData, PROPERTY_JSON_FIELDS);

			console.log('Saving property data to API...', preparedData);
			uiStore.startLoading('جاري حفظ بيانات العقار...');

			const result = await propertiesStore.createProperty(preparedData);
			console.log('Property created successfully:', result);

			uiStore.stopLoading();
			uiStore.addToast('تم إنشاء العقار بنجاح', 'success');

			// Now handle image uploads if needed
			if (pendingImageFiles.length > 0 && result && result.id) {
				try {
					console.log(
						`Starting upload of ${pendingImageFiles.length} images to property ID: ${result.id}`
					);
					uiStore.addToast('جاري رفع الصور...', 'info');

					// Upload the images
					const uploadResult = await uploadPropertyImages(result.id, pendingImageFiles, {
						onProgress: (progress) => {
							uploadProgress = progress;
						}
					});

					console.log('Image upload response:', uploadResult);

					// Parse and format the image data
					let imageData = [];
					if (uploadResult && uploadResult.images) {
						imageData =
							typeof uploadResult.images === 'string'
								? JSON.parse(uploadResult.images)
								: uploadResult.images;
					} else if (uploadResult && uploadResult.image_urls) {
						imageData =
							typeof uploadResult.image_urls === 'string'
								? JSON.parse(uploadResult.image_urls)
								: uploadResult.image_urls;
					}

					// If we got images back, explicitly update the property record
					if (imageData && imageData.length > 0) {
						// Format images properly
						const formattedImages = imageData.map((img) => {
							if (typeof img === 'string') {
								return {
									url: img,
									path: img,
									is_primary: false,
									uploaded_at: new Date().toISOString()
								};
							} else {
								return {
									id: img.id || undefined,
									url: img.url || img.path || '',
									path: img.path || img.url || '',
									is_primary: img.is_primary || false,
									uploaded_at: img.uploaded_at || new Date().toISOString()
								};
							}
						});

						console.log('Formatted images to save:', formattedImages);

						// Explicitly update the property with the new images
						try {
							const updateResult = await propertiesStore.updateProperty(result.id, {
								images: formattedImages
							});

							console.log('Property updated with images:', updateResult);
							uiStore.addToast('تم رفع وحفظ الصور بنجاح', 'success');

							// Navigate to property detail page after successful creation and image upload
							goto(`/properties/${updateResult.slug || result.slug}`);
							return;
						} catch (updateError) {
							console.error('Error updating property with images:', updateError);
							uiStore.addToast('تم رفع الصور ولكن حدث خطأ في تحديث بيانات العقار', 'warning');
						}
					}
				} catch (uploadError) {
					console.error('Error uploading images:', uploadError);
					uiStore.addToast(`خطأ في رفع الصور: ${uploadError.message}`, 'error');
				}
			}

			// Navigate to property detail page
			goto(`/properties/${result.slug}`);
		} catch (err) {
			uiStore.stopLoading();
			error = err;
			console.error('Property creation error:', err);

			// Handle validation errors
			if (err.data?.error_code === 'validation_error') {
				validationErrors = formatValidationErrors(err.data.error);
				console.log('Validation errors:', validationErrors);

				const errorFields = Object.keys(validationErrors);
				if (errorFields.length > 0) {
					const errorMessage = `حدث خطأ أثناء حفظ العقار: ${errorFields.join('، ')}`;
					uiStore.addToast(errorMessage, 'error');
				}
			} else {
				uiStore.addToast(`حدث خطأ أثناء حفظ العقار: ${err.message || 'خطأ غير معروف'}`, 'error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	/**
	 * Handle pending uploads with validation and improved error handling
	 * @param {Object} event - The event object containing files
	 */
	function handlePendingUploads(event) {
		const files = event.detail.files;

		if (!files || files.length === 0) {
			console.log('No files received for pending uploads');
			pendingImageFiles = [];
			return;
		}

		console.log(`Received ${files.length} files for pending upload`);

		// Validate files early
		const validation = validateImageFiles(files, {
			maxFiles: 10,
			maxSize: 5 * 1024 * 1024 // 5MB limit
		});

		// Show any warnings
		validation.warnings.forEach((warning) => {
			uiStore.addToast(warning, 'warning');
		});

		// Update pending files to only include valid ones
		pendingImageFiles = validation.validFiles;

		console.log(
			`${pendingImageFiles.length} valid images ready for upload after property creation`
		);

		// If we had invalid files, show a summary
		if (validation.invalidFiles.length > 0) {
			uiStore.addToast(`تم استبعاد ${validation.invalidFiles.length} ملفات غير صالحة`, 'warning');
		}
	}

	/**
	 * Handle image uploads with explicit property update to ensure images are saved in DB
	 * @param {Object} event - The upload event with propertyId and files
	 */
	async function handleImagesUpload(event) {
		const { propertyId, files } = event.detail;

		if (!propertyId || !files || files.length === 0) {
			uiStore.addToast('معلومات غير كافية لرفع الصور', 'error');
			return;
		}

		console.log(`Uploading ${files.length} images to property ID: ${propertyId}`);

		try {
			uiStore.startLoading('جاري رفع الصور...');
			uploadProgress = 0;

			// Step 1: Upload the images to the server's file storage
			const uploadResult = await uploadPropertyImages(propertyId, files, {
				onProgress: (progress) => {
					uploadProgress = progress;
				}
			});

			console.log('Upload response:', uploadResult);

			// Step 2: Explicitly update the property with the new image data
			if (uploadResult && (uploadResult.images || uploadResult.image_urls)) {
				// Parse the image data from the response
				let imageData = [];

				if (uploadResult.images) {
					// If the server returned images array
					imageData =
						typeof uploadResult.images === 'string'
							? JSON.parse(uploadResult.images)
							: uploadResult.images;
				} else if (uploadResult.image_urls) {
					// If the server returned image_urls array
					imageData =
						typeof uploadResult.image_urls === 'string'
							? JSON.parse(uploadResult.image_urls)
							: uploadResult.image_urls;
				}

				console.log('Parsed image data:', imageData);

				if (imageData.length > 0) {
					// Create a formatted image array with required properties
					const formattedImages = imageData.map((img) => {
						// Handle different response formats
						if (typeof img === 'string') {
							// If just a URL was returned
							return {
								url: img,
								path: img,
								is_primary: false,
								uploaded_at: new Date().toISOString()
							};
						} else {
							// If an object was returned
							return {
								id: img.id || undefined,
								url: img.url || img.path || '',
								path: img.path || img.url || '',
								is_primary: img.is_primary || false,
								uploaded_at: img.uploaded_at || new Date().toISOString()
							};
						}
					});

					console.log('Formatted images to save:', formattedImages);

					// Step 3: Explicitly update the property record with the new images
					// This ensures the images array is saved in the JSON field
					try {
						const propertyUpdateData = {
							images: formattedImages
						};

						// First try to update via API
						const updateResult = await propertiesStore.updateProperty(
							propertyId,
							propertyUpdateData
						);
						console.log('Property updated with new images:', updateResult);

						// Also update in the store
						if (propertiesStore.updatePropertyInStore) {
							propertiesStore.updatePropertyInStore(propertyId, { images: formattedImages });
						}

						uiStore.addToast(`تم رفع وحفظ ${files.length} صور بنجاح`, 'success');
					} catch (updateError) {
						console.error('Error updating property with new images:', updateError);
						uiStore.addToast('تم رفع الصور ولكن حدث خطأ في تحديث بيانات العقار', 'warning');
					}
				} else {
					uiStore.addToast('تم رفع الصور ولكن لم يتم استلام معلومات الصور من الخادم', 'warning');
				}
			} else {
				uiStore.addToast('تم رفع الصور ولكن لم ترجع أي بيانات من الخادم', 'warning');
			}

			uiStore.stopLoading();
		} catch (error) {
			uiStore.stopLoading();
			console.error('Error uploading images:', error);
			uiStore.addToast(`خطأ في رفع الصور: ${error.message}`, 'error');
		}
	}

	// Handle cancel action
	function handleCancel() {
		uiStore.showConfirmDialog({
			title: 'إلغاء إضافة العقار',
			message: 'هل أنت متأكد من إلغاء إضافة العقار؟ سيتم فقدان جميع البيانات المدخلة.',
			confirmText: 'نعم، إلغاء',
			cancelText: 'لا، استمرار',
			type: 'warning',
			onConfirm: () => {
				goto('/properties');
			}
		});
	}

	/**
	 * Check if user has permission to add a property
	 */
	function checkAddPropertyPermission() {
		// Must be authenticated
		if (!$auth.isAuthenticated) {
			return false;
		}

		// Staff users bypass role checks
		if ($auth.user?.is_staff || $auth.user?.is_superuser) {
			return true;
		}

		// Check user roles
		if (
			hasRole(ROLES.SELLER) ||
			hasRole(ROLES.AGENT) ||
			hasPermission(PERMISSIONS.CREATE_PROPERTY)
		) {
			return true;
		}

		return false;
	}

	onMount(async () => {
		try {
			// Check authentication first
			if (!$auth.isAuthenticated) {
				uiStore.addToast('يجب تسجيل الدخول أولاً', 'warning');
				goto('/login?redirect=/properties/add');
				return;
			}

			// Verify permissions against backend requirements
			const hasPermission = checkAddPropertyPermission();

			if (!hasPermission) {
				uiStore.addToast('ليس لديك الصلاحية لإضافة عقار. يجب أن تكون بائع أو وكيل عقاري.', 'error');
				goto('/properties');
				return;
			}
		} catch (err) {
			error = err;
			console.error('Error checking permissions:', err);
		} finally {
			isLoading = false;
		}
	});
</script>

<svelte:head>
	<title>إضافة عقار جديد | نظام المزادات العقارية</title>
	<meta name="description" content="إضافة عقار جديد للبيع أو المزاد في منصة المزادات العقارية" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">إضافة عقار جديد</h1>
		<p class="mt-2 text-gray-600 dark:text-gray-400">
			قم بإدخال معلومات العقار الجديد للنشر في المنصة. يرجى ملء الحقول المطلوبة بعلامة النجمة (*).
		</p>
	</div>

	{#if isLoading}
		<div class="flex min-h-[50vh] items-center justify-center">
			<Loader size="lg" />
		</div>
	{:else if error && !Object.keys(validationErrors).length}
		<Alert
			type="error"
			title="خطأ في حفظ العقار"
			message={error.message || 'حدث خطأ أثناء حفظ العقار. يرجى المحاولة مرة أخرى.'}
		/>
		<div class="mt-6 flex justify-end">
			<button
				type="button"
				class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
				on:click={() => (error = null)}
			>
				حاول مرة أخرى
			</button>
		</div>
	{:else}
		<!-- Upload Progress -->
		{#if uploadProgress > 0}
			<div class="dark:bg-opacity-20 mb-4 rounded-lg bg-blue-50 p-4 dark:bg-blue-900">
				<h4 class="font-medium text-blue-700 dark:text-blue-300">
					جاري رفع الصور ({uploadProgress}%)
				</h4>
				<div class="mt-2 h-2 w-full overflow-hidden rounded-full bg-blue-200 dark:bg-blue-700">
					<div
						class="h-full rounded-full bg-blue-600 dark:bg-blue-400"
						style="width: {uploadProgress}%"
					></div>
				</div>
			</div>
		{/if}

		<PropertyForm
			property={null}
			{cities}
			{isSubmitting}
			{isSearchingCoordinates}
			editMode={false}
			on:submit={handleSubmit}
			on:cancel={handleCancel}
			on:pendingUploads={handlePendingUploads}
			on:imagesUpload={handleImagesUpload}
		/>

		<!-- Validation errors -->
		{#if Object.keys(validationErrors).length > 0}
			<div class="dark:bg-opacity-20 mt-6 rounded-md bg-red-50 p-4 dark:bg-red-900">
				<div class="flex">
					<div class="flex-shrink-0">
						<svg
							class="h-5 w-5 text-red-400"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							aria-hidden="true"
						>
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class="mr-3">
						<h3 class="text-sm font-medium text-red-800 dark:text-red-200">
							يوجد {Object.keys(validationErrors).length} أخطاء في النموذج
						</h3>
						<div class="mt-2 text-sm text-red-700 dark:text-red-300">
							<ul class="list-disc space-y-1 pr-5">
								{#each Object.entries(validationErrors) as [field, errors]}
									<li>
										<strong>{field}:</strong>
										{Array.isArray(errors) ? errors.join(', ') : errors}
									</li>
								{/each}
							</ul>
						</div>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>
