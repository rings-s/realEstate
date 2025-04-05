<!-- src/routes/properties/add/+page.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { propertiesStore } from '$lib/stores/properties';
	import { auth, roles } from '$lib/stores/auth';
	import { ROLES, PERMISSIONS, hasRole, hasPermission } from '$lib/utils/permissions';
	import { uiStore } from '$lib/stores/ui';
	import { formatValidationErrors } from '$lib/utils/formatting';
	import PropertyForm from '$lib/components/properties/PropertyForm.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Alert from '$lib/components/common/Alert.svelte';

	let isLoading = true;
	let isSubmitting = false;
	let error = null;
	let validationErrors = {};
	let isSearchingCoordinates = false;

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

	// Temporary file storage for uploading after property creation
	let pendingImageFiles = [];

	/**
	 * Create a simple clean object with just the required fields
	 * This approach avoids any issues with complex objects or circular references
	 * @param {Object} data - Form data
	 * @returns {Object} Clean data object ready for API
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

			// Convert all JSON fields to strings with defaults
			location: JSON.stringify(data.location || { latitude: 0, longitude: 0 }),
			rooms: JSON.stringify(data.rooms || []),
			features: JSON.stringify(data.features || []),
			amenities: JSON.stringify(data.amenities || []),
			images: JSON.stringify(data.images || []),
			videos: JSON.stringify(data.videos || []),
			outdoor_spaces: JSON.stringify(data.outdoor_spaces || []),
			street_details: JSON.stringify(data.street_details || ''),
			rental_details: JSON.stringify(data.rental_details || ''),
			parking: JSON.stringify(data.parking || ''),
			building_services: JSON.stringify(data.building_services || ''),
			infrastructure: JSON.stringify(data.infrastructure || ''),
			surroundings: JSON.stringify(data.surroundings || ''),
			reference_ids: JSON.stringify(data.reference_ids || []),

			// Numeric fields
			area: data.area ? Number(data.area) : 0,
			built_up_area: data.built_up_area ? Number(data.built_up_area) : null,
			estimated_value: data.estimated_value ? Number(data.estimated_value) : 0,
			asking_price: data.asking_price ? Number(data.asking_price) : null,
			bedrooms: data.bedrooms ? Number(data.bedrooms) : 0,
			bathrooms: data.bathrooms ? Number(data.bathrooms) : 0,
			floor_number: data.floor_number ? Number(data.floor_number) : null,
			total_floors: data.total_floors ? Number(data.total_floors) : null,
			year_built: data.year_built ? Number(data.year_built) : null,

			// Boolean fields
			is_published: Boolean(data.is_published),
			is_featured: Boolean(data.is_featured),
			is_verified: Boolean(data.is_verified),

			// Date fields
			deed_date: data.deed_date || null,
			deed_number: data.deed_number || ''
		};

		// Log the prepared data
		console.log('Clean property data created:', cleanData);
		return cleanData;
	}

	// Handle form submission
	async function handleSubmit(event) {
		const formData = event.detail;
		isSubmitting = true;
		error = null;
		validationErrors = {};

		try {
			console.log('Raw form data:', formData);

			// Create a clean object with just the needed fields
			const cleanData = createCleanPropertyData(formData);
			console.log('Cleaned data for submission:', cleanData);

			// Store any pending image files for upload after property creation
			if (formData.imageFiles && formData.imageFiles.length) {
				pendingImageFiles = formData.imageFiles;
			}

			// Create property
			const result = await propertiesStore.createProperty(cleanData);

			// If we have pending images to upload, do it now
			if (pendingImageFiles.length > 0 && result && result.id) {
				try {
					uiStore.addToast('تم إنشاء العقار بنجاح، جاري رفع الصور...', 'info');

					// Prepare FormData for image upload
					const imageFormData = new FormData();
					pendingImageFiles.forEach((file) => {
						imageFormData.append('files', file);
					});

					// Upload images to the newly created property
					await propertiesStore.uploadPropertyImages(result.id, pendingImageFiles);

					uiStore.addToast('تم رفع الصور بنجاح', 'success');
				} catch (uploadError) {
					console.error('Error uploading images:', uploadError);
					uiStore.addToast('تم إنشاء العقار ولكن حدث خطأ أثناء رفع الصور', 'warning');
				}
			}

			// Navigate to property detail page after successful creation
			goto(`/properties/${result.slug}`);
			uiStore.addToast('تم إضافة العقار بنجاح', 'success');
		} catch (err) {
			error = err;
			console.error('Property creation error:', err);

			// Handle validation errors from backend
			if (err.data?.error_code === 'validation_error') {
				validationErrors = formatValidationErrors(err.data.error);
				console.log('Validation errors:', validationErrors);

				let errorMessage = 'حدث خطأ أثناء حفظ العقار. يرجى التحقق من البيانات المدخلة:';
				const errorFields = Object.keys(validationErrors);
				if (errorFields.length > 0) {
					errorMessage += ' ' + errorFields.join('، ');
				}

				uiStore.addToast(errorMessage, 'error');
			} else {
				uiStore.addToast('حدث خطأ أثناء حفظ العقار: ' + (err.message || 'خطأ غير معروف'), 'error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	// Handle pending uploads that will be processed after property creation
	function handlePendingUploads(event) {
		pendingImageFiles = event.detail.files;
		console.log(`${pendingImageFiles.length} images pending for upload after property creation`);
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
