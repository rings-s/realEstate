<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { hasPermission, PERMISSIONS } from '$lib/utils/permissions';
	import { getAccessToken, isTokenExpired } from '$lib/utils/tokenManager';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft } from 'lucide-svelte';

	// Local state
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;
	let uploadedImages = [];

	// Check permissions for creating properties
	// This looks at the role-based permissions structure to see if the user can create properties
	$: canCreateProperty = $isAuthenticated && hasPermission($userRoles, PERMISSIONS.CREATE_PROPERTY);

	// Enhanced authentication and permission check
	async function checkAuthAndPermissions() {
		console.log('Checking authentication and permissions...');

		// First check if store says we're authenticated
		if (!$isAuthenticated) {
			// Double-check with token as fallback
			const token = getAccessToken();
			if (token && !isTokenExpired()) {
				console.log('Token exists and is valid, updating authentication state');
				isAuthenticated.set(true);
				// Wait for the store to update
				await new Promise((resolve) => setTimeout(resolve, 50));
			} else {
				console.log('No valid authentication found, redirecting to login');
				goto('/auth/login?redirect=/properties/add');
				return false;
			}
		}

		// Now check if user has the CREATE_PROPERTY permission
		const hasCreatePermission = hasPermission($userRoles, PERMISSIONS.CREATE_PROPERTY);

		// Also look for SELLER or AGENT roles which should be able to create properties
		const isSellerOrAgent =
			$userRoles.includes('seller') || $userRoles.includes('agent') || $userRoles.includes('admin');

		if (!hasCreatePermission && !isSellerOrAgent) {
			console.log('User lacks permission to create properties');
			unauthorized = true;
			error = t('no_permission', $language, { default: 'ليس لديك صلاحية لإضافة عقار' });
			return false;
		}

		console.log('User has permission to create properties');
		return true;
	}

	onMount(async () => {
		// Check authentication and permissions
		const hasPermission = await checkAuthAndPermissions();
		initialCheckDone = true;

		if (!hasPermission) {
			console.log('Permission check failed');
			return;
		}
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

			// Handle any pending image uploads
			if (uploadedImages.length > 0 && newProperty.id) {
				for (const imageData of uploadedImages) {
					try {
						await properties.uploadImage(newProperty.id, imageData.file, {
							isPrimary: imageData.isPrimary,
							caption: imageData.caption
						});
					} catch (imgErr) {
						console.error('Error uploading image after property creation:', imgErr);
					}
				}
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

	// Handle property image selection before the property is created
	function handleImageUpload(event) {
		const { propertyId, formData, imageIndex } = event.detail;

		// Store image info for uploading after property creation
		if (!propertyId) {
			// Extract file and metadata from formData
			const file = formData.get('image');
			const isPrimary = formData.get('is_primary') === 'true';
			const caption = formData.get('caption') || '';

			// Add to pending uploads
			uploadedImages.push({
				file,
				isPrimary,
				caption
			});

			console.log('Image queued for upload after property creation:', {
				isPrimary,
				caption,
				fileName: file ? file.name : 'unknown'
			});

			addToast(
				t('image_queued', $language, {
					default: 'سيتم تحميل الصورة بعد إنشاء العقار'
				}),
				'info'
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
				message={t('no_permission', $language, {
					default: 'ليس لديك صلاحية لإضافة عقار. يجب أن تكون بائع عقارات أو وكيل عقاري للقيام بذلك.'
				})}
			/>
			<div class="mt-4">
				<a href="/properties" class="btn variant-filled">
					{t('back_to_properties', $language, { default: 'العودة إلى العقارات' })}
				</a>
			</div>
		</div>
	{:else}
		<!-- Property Form -->
		<div class="card">
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
