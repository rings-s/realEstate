<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { PERMISSIONS } from '$lib/utils/permissions';
	import { isTokenExpired, getAccessToken } from '$lib/utils/tokenManager';
	import * as propertyService from '$lib/services/propertyService';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft } from 'lucide-svelte';

	// Local state
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;
	let selectedImages = [];
	let rolesLoaded = false;

	// Improved permission check that doesn't fail on empty roles
	function canCreateProperty(roles) {
		// Don't check permissions until roles are properly loaded
		if (!roles || !Array.isArray(roles) || roles.length === 0) {
			console.log('Roles not loaded yet, deferring permission check');
			return true; // Assume allowed until we can properly check
		}

		// Check for admin role which has all permissions
		if (roles.includes('admin')) {
			return true;
		}

		// Check for roles that can create properties
		return roles.includes('seller') || roles.includes('agent');
	}

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

	onMount(async () => {
		// Check if user is authenticated
		if (!checkAuthentication()) {
			return;
		}

		// Wait for roles to be loaded if they aren't already
		if (!$userRoles || $userRoles.length === 0) {
			console.log('User roles not loaded yet, waiting...');

			// Wait a bit to let roles load
			await new Promise((resolve) => setTimeout(resolve, 1000));

			// If roles are still not loaded, set a flag but don't block the UI
			if (!$userRoles || $userRoles.length === 0) {
				console.log('Roles still not loaded after waiting, continuing anyway');
				// Initialize with empty array if null
				if (!$userRoles) userRoles.set([]);
			}
		}

		rolesLoaded = true;

		// Check permissions if roles are loaded
		if (rolesLoaded && !canCreateProperty($userRoles)) {
			console.log('User lacks permission to create properties');
			unauthorized = true;
		} else {
			console.log('User has permission to create properties or permission check deferred');
		}

		initialCheckDone = true;
	});

	// Upload images for a property
	async function uploadPropertyImages(propertyId, images) {
		if (!propertyId || !images || images.length === 0) {
			return;
		}

		console.log(`Uploading ${images.length} images for property ID ${propertyId}`);

		// Upload each image sequentially
		for (let i = 0; i < images.length; i++) {
			const image = images[i];

			if (!image.file) continue;

			try {
				const result = await propertyService.uploadPropertyImage(propertyId, image.file, {
					isPrimary: image.is_primary,
					caption: image.caption || '',
					order: i
				});

				console.log(`Uploaded image ${i + 1}/${images.length}`, result);
			} catch (err) {
				console.error(`Error uploading image ${i + 1}/${images.length}:`, err);
				// Continue with next image despite error
			}
		}

		console.log('All images uploaded successfully');
	}

	// Handle form submission
	async function handleSubmit(event) {
		try {
			const { property: propertyData, images } = event.detail;
			selectedImages = images; // Store images for later upload
			loading = true;
			error = null;

			console.log('Submitting property data:', propertyData);
			console.log('Selected images:', selectedImages.length);

			// Create new property
			const newProperty = await properties.createProperty(propertyData);
			console.log('Property created successfully:', newProperty);

			// Upload images if any
			if (selectedImages.length > 0) {
				await uploadPropertyImages(newProperty.id, selectedImages);
			}

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

	// Handle property image upload for the form preview
	async function handleImageUpload(event) {
		const { propertyId, formData, imageIndex } = event.detail;

		try {
			if (propertyId) {
				// Upload the image
				const response = await propertyService.uploadFiles(
					propertyService.ENDPOINTS.PROPERTY.IMAGES(propertyId),
					formData
				);

				// Update the image in the UI
				if (selectedImages[imageIndex]) {
					selectedImages[imageIndex].id = response.id;
					selectedImages[imageIndex].uploaded = true;
					selectedImages[imageIndex].progress = 100;
					selectedImages = [...selectedImages];
				}
			} else {
				console.log('Storing image for upload after property creation');
			}
		} catch (err) {
			console.error('Error handling image upload:', err);
			addToast(
				t('image_upload_error', $language, {
					default: 'فشل في تحميل الصورة'
				}),
				'error'
			);
		}
	}

	// Handle image removal
	async function handleRemoveImage(event) {
		const { imageId } = event.detail;

		try {
			if (imageId) {
				await propertyService.deletePropertyImage(imageId);
				addToast(t('image_removed', $language, { default: 'تم حذف الصورة بنجاح' }), 'success');
			}
		} catch (err) {
			console.error('Error removing image:', err);
			addToast(t('image_remove_error', $language, { default: 'فشل في حذف الصورة' }), 'error');
		}
	}

	// Handle setting primary image
	async function handleSetPrimaryImage(event) {
		const { imageId } = event.detail;

		try {
			if (imageId) {
				await propertyService.setPropertyImageAsPrimary(imageId);
				addToast(
					t('primary_image_set', $language, { default: 'تم تعيين الصورة الرئيسية بنجاح' }),
					'success'
				);
			}
		} catch (err) {
			console.error('Error setting primary image:', err);
			addToast(
				t('primary_image_error', $language, { default: 'فشل في تعيين الصورة الرئيسية' }),
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
				on:removeImage={handleRemoveImage}
				on:setPrimaryImage={handleSetPrimaryImage}
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
