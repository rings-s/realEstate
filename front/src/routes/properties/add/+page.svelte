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

	// Handle form submission
	async function handleSubmit(event) {
		const formData = event.detail;
		isSubmitting = true;
		error = null;
		validationErrors = {};

		try {
			console.log('Received form data:', formData);

			// The data should already be properly formatted by PropertyForm
			// No need to transform JSON fields - the backend will handle the serialization

			// Create property - this will use IsSellerPermission from backend
			const result = await propertiesStore.createProperty(formData);

			// Navigate to property detail page after successful creation
			goto(`/properties/${result.slug}`);
			uiStore.addToast('تم إضافة العقار بنجاح', 'success');
		} catch (err) {
			error = err;
			console.error('Property creation error:', err);

			// Handle validation errors from backend
			if (err.data?.error_code === 'validation_error') {
				validationErrors = formatValidationErrors(err.data.error);

				// Log specific validation errors for debugging
				console.log('Validation errors:', validationErrors);
			}

			uiStore.addToast('حدث خطأ أثناء حفظ العقار. يرجى التحقق من البيانات المدخلة.', 'error');
		} finally {
			isSubmitting = false;
		}
	}

	// Handle cancel
	function handleCancel() {
		goto('/properties');
	}

	/**
	 * Check if user has permission to add a property
	 * This matches the backend IsSellerPermission class:
	 * - User must be authenticated AND
	 * - User must have SELLER or AGENT role OR be staff
	 *
	 * @returns {boolean} True if user has permission
	 */
	function checkAddPropertyPermission() {
		// Must be authenticated
		if (!$auth.isAuthenticated) {
			return false;
		}

		// Staff users bypass role checks (same as backend)
		if ($auth.user?.is_staff || $auth.user?.is_superuser) {
			return true;
		}

		// Check user roles - must match IsSellerPermission class from backend
		// "return request.user.is_authenticated and (
		//     request.user.has_role(Role.SELLER)
		//     or request.user.has_role(Role.AGENT)
		//     or request.user.is_staff
		// )"

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
			قم بإدخال معلومات العقار الجديد للنشر في المنصة
		</p>
	</div>

	{#if isLoading}
		<div class="flex min-h-[50vh] items-center justify-center">
			<Loader size="lg" />
		</div>
	{:else if error && !validationErrors.length}
		<Alert
			type="error"
			title="خطأ في حفظ العقار"
			message={error.message || 'حدث خطأ أثناء حفظ العقار. يرجى المحاولة مرة أخرى.'}
		/>
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
		/>
	{/if}
</div>
