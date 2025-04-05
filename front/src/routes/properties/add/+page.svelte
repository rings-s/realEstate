<!-- src/routes/properties/add/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { propertiesStore } from '$lib/stores/properties';
	import { auth } from '$lib/stores/auth';
	import { ROLES, PERMISSIONS, hasRole, hasPermission } from '$lib/utils/permissions';
	import { uiStore } from '$lib/stores/ui';
	import { formatValidationErrors } from '$lib/utils/formatting';
	import PropertyForm from '$lib/components/properties/PropertyForm.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Alert from '$lib/components/common/Alert.svelte';

	// Import our direct upload function
	import { uploadPropertyImages } from '$lib/services/directUpload';

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
	 * Create a simple clean object with just the required fields
	 */
	function createCleanPropertyData(data) {
		// Create a fresh object with only the fields we need
		const cleanData = {
			title: data.title || '',
			description: data.description || '',
			property_type: data.property_type || 'apartment',
			condition: data.condition || 'good',
			status: data.status || 'draft',
			city: data.city || '',
			district: data.district || '',
			address: data.address || '',
			postal_code: data.postal_code || '',
			country: data.country || 'Saudi Arabia',

			// Handle JSON fields - ensure they're all strings not objects
			location:
				typeof data.location === 'object' ? JSON.stringify(data.location) : data.location || '',
			rooms: typeof data.rooms === 'object' ? JSON.stringify(data.rooms) : data.rooms || '[]',
			features:
				typeof data.features === 'object' ? JSON.stringify(data.features) : data.features || '[]',
			amenities:
				typeof data.amenities === 'object'
					? JSON.stringify(data.amenities)
					: data.amenities || '[]',

			// Numeric fields
			area: data.area ? Number(data.area) : 0,
			built_up_area: data.built_up_area ? Number(data.built_up_area) : null,
			estimated_value: data.estimated_value ? Number(data.estimated_value) : 0,
			asking_price: data.asking_price ? Number(data.asking_price) : null,
			bedrooms: data.bedrooms !== undefined ? Number(data.bedrooms) : 0,
			bathrooms: data.bathrooms !== undefined ? Number(data.bathrooms) : 0,
			floor_number: data.floor_number !== undefined ? Number(data.floor_number) : null,
			total_floors: data.total_floors !== undefined ? Number(data.total_floors) : null,
			year_built: data.year_built ? Number(data.year_built) : null,

			// Boolean fields
			is_published: Boolean(data.is_published),

			// Date fields
			deed_date: data.deed_date || null,
			deed_number: data.deed_number || ''
		};

		// Log the prepared data for debugging
		console.log('Clean property data created for submission:', cleanData);
		return cleanData;
	}

	// Handle form submission
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

			// Create clean data object for API
			const cleanData = createCleanPropertyData(formData);

			// Save the property first
			console.log('Saving property data to API...');
			uiStore.startLoading('جاري حفظ بيانات العقار...');

			const result = await propertiesStore.createProperty(cleanData);
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

					// Use our direct upload function
					const uploadResult = await uploadPropertyImages(
						result.id,
						pendingImageFiles,
						(progress) => {
							uploadProgress = progress;
						}
					);

					console.log('Image upload complete:', uploadResult);
					uiStore.addToast('تم رفع الصور بنجاح', 'success');
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

	// Handle pending uploads - store files for later upload
	function handlePendingUploads(event) {
		pendingImageFiles = event.detail.files;
		console.log(`${pendingImageFiles.length} images pending for upload after property creation`);

		// Validate files early
		if (pendingImageFiles.length > 0) {
			let hasInvalidFiles = false;

			// Check file types
			pendingImageFiles.forEach((file) => {
				const isValidType = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(
					file.type
				);
				const isValidSize = file.size <= 5 * 1024 * 1024; // 5MB limit

				if (!isValidType) {
					console.warn(`Invalid file type: ${file.type} for file ${file.name}`);
					hasInvalidFiles = true;
				}

				if (!isValidSize) {
					console.warn(`File too large: ${file.size} bytes for file ${file.name}`);
					hasInvalidFiles = true;
				}
			});

			if (hasInvalidFiles) {
				uiStore.addToast(
					'بعض الملفات غير صالحة. تأكد من استخدام ملفات صور بحجم أقل من 5 ميجابايت',
					'warning'
				);
			}
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
			imageUploadUrl="/api/properties/upload-images/"
			on:submit={handleSubmit}
			on:cancel={handleCancel}
			on:pendingUploads={handlePendingUploads}
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
