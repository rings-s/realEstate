<!--
  Modified properties/add/+page.svelte to fix authentication issues
  and improve form submission handling
-->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { hasPermission, PERMISSIONS } from '$lib/utils/permissions';
	import { isTokenExpired, getAccessToken } from '$lib/utils/tokenManager';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft } from 'lucide-svelte';

	// Local state
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;

	// Check if user has permission to create properties
	$: canCreateProperty = hasPermission($userRoles, PERMISSIONS.CREATE_PROPERTY);

	// Enhanced authentication check
	function checkAuthentication() {
		console.log('Checking authentication status...');

		// First check if we have the auth store value
		if (!$isAuthenticated) {
			console.log('Not authenticated according to store');

			// Double-check with token directly as a fallback
			const token = getAccessToken();
			if (token && !isTokenExpired()) {
				console.log('Token exists and is valid, setting authenticated');
				// We have a valid token despite the store saying otherwise
				isAuthenticated.set(true);
				return true;
			}

			console.log('No valid token found, redirecting to login');
			goto('/auth/login?redirect=/properties/add');
			return false;
		}

		console.log('User is authenticated');
		return true;
	}

	onMount(() => {
		// Check if user is authenticated
		if (!checkAuthentication()) {
			return;
		}

		// Check if user has permission to create properties
		if (!canCreateProperty) {
			console.log('User lacks permission to create properties');
			unauthorized = true;
		}

		initialCheckDone = true;
	});

	// Handle form submission
	async function handleSubmit(event) {
		try {
			const propertyData = event.detail;
			loading = true;
			error = null;

			console.log('Submitting property data:', propertyData);

			// Create new property
			const newProperty = await properties.createProperty(propertyData);
			console.log('Property created successfully:', newProperty);

			// Show success message
			addToast(
				t('property_created', $language, {
					default: 'تم إنشاء العقار بنجاح'
				}),
				'success'
			);

			// Redirect to property detail page
			goto(`/properties/${newProperty.slug}`);
		} catch (err) {
			console.error('Error creating property:', err);
			error =
				err.message ||
				t('create_property_error', $language, {
					default: 'حدث خطأ أثناء إنشاء العقار'
				});
			loading = false;
		}
	}

	// Handle property image upload
	async function handleImageUpload(event) {
		const { propertyId, formData, imageIndex } = event.detail;

		try {
			// In the add page, we don't have propertyId yet, handle this differently
			console.log('Image will be uploaded after property creation');
		} catch (err) {
			console.error('Error handling image:', err);
			addToast(
				t('image_upload_error', $language, {
					default: 'فشل في تحميل الصورة'
				}),
				'error'
			);
		}
	}

	// Handle cancel
	function handleCancel() {
		goto('/properties');
	}
</script>

<div class="container mx-auto px-4 py-6">
	<div class="flex justify-between items-center mb-6">
		<h1 class="h2 {$isRTL ? 'text-right' : 'text-left'}">
			<Building class="inline-block w-8 h-8 {$isRTL ? 'ml-2' : 'mr-2'} text-primary-500" />
			{t('add_property', $language, { default: 'إضافة عقار' })}
		</h1>

		<a href="/properties" class="btn variant-ghost">
			<ArrowLeft class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('back_to_properties', $language, { default: 'العودة إلى العقارات' })}
		</a>
	</div>

	{#if !initialCheckDone}
		<!-- Loading state while checking authentication -->
		<div class="card p-6 text-center">
			<div class="spinner-icon mx-auto mb-4"></div>
			<p>{t('loading', $language, { default: 'جاري التحميل...' })}</p>
		</div>
	{:else if unauthorized}
		<div class="card p-6 text-center">
			<Alert
				type="error"
				message={t('no_permission', $language, { default: 'ليس لديك صلاحية لإضافة عقار' })}
			/>
			<div class="mt-4">
				<a href="/properties" class="btn variant-filled">
					{t('back_to_properties', $language, { default: 'العودة إلى العقارات' })}
				</a>
			</div>
		</div>
	{:else}
		<!-- Property Form -->
		<div class="card p-6 mb-6">
			<PropertyForm
				{loading}
				{error}
				on:submit={handleSubmit}
				on:uploadImage={handleImageUpload}
				on:cancel={handleCancel}
			/>
		</div>
	{/if}
</div>

<style>
	.spinner-icon {
		border: 4px solid rgba(0, 0, 0, 0.1);
		border-left-color: var(--color-primary-500);
		border-radius: 50%;
		width: 36px;
		height: 36px;
		animation: spin 1s linear infinite;
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
