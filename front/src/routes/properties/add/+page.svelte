<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { hasPermission, PERMISSIONS, ROLES } from '$lib/utils/permissions';
	import { isTokenExpired, getAccessToken, getUserFromToken } from '$lib/utils/tokenManager';
	import * as propertyService from '$lib/services/propertyService';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft, Save } from 'lucide-svelte';

	// Local state
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;
	let selectedImages = [];

	// Check permissions in a more robust way
	$: canCreateProperty =
		$userRoles &&
		($userRoles.includes(ROLES.ADMIN) ||
			$userRoles.includes(ROLES.SELLER) ||
			$userRoles.includes(ROLES.AGENT) ||
			hasPermission($userRoles, PERMISSIONS.CREATE_PROPERTY));

	// Enhanced authentication check with token validation
	async function checkAuthentication() {
		console.log('Checking authentication status...');

		// First check if we have the auth store value
		if (!$isAuthenticated) {
			console.log('Not authenticated according to store');

			// Double-check with token directly as a fallback
			const token = getAccessToken();
			if (token && !isTokenExpired()) {
				console.log('Token exists and is valid, setting authenticated');

				// Get user info from token
				const userInfo = getUserFromToken();
				if (userInfo && userInfo.roles) {
					// Update the stores manually since they might not be initialized yet
					isAuthenticated.set(true);
					userRoles.set(userInfo.roles);
					currentUser.set(userInfo);

					// Wait a moment for store updates to propagate
					await new Promise((resolve) => setTimeout(resolve, 100));
					return true;
				}
			}

			console.log('No valid token found, redirecting to login');
			goto('/auth/login?redirect=/properties/add');
			return false;
		}

		// Also check if user roles are loaded, which is required for permission check
		if (!$userRoles || $userRoles.length === 0) {
			console.log('User authenticated but roles not loaded');

			// Try to get roles from token
			const userInfo = getUserFromToken();
			if (userInfo && userInfo.roles && userInfo.roles.length > 0) {
				console.log('Setting roles from token:', userInfo.roles);
				userRoles.set(userInfo.roles);

				// Wait a moment for store updates to propagate
				await new Promise((resolve) => setTimeout(resolve, 100));
			} else {
				console.log('No roles found in token, will check permissions later');
			}
		}

		console.log('User is authenticated with roles:', $userRoles);
		return true;
	}

	// Initialize component on mount
	onMount(async () => {
		// Check if user is authenticated
		if (!(await checkAuthentication())) {
			return;
		}

		// Check if user has permission to create properties after a short delay
		// to ensure stores are properly updated
		setTimeout(() => {
			if (!canCreateProperty) {
				console.log('User lacks permission to create properties. Roles:', $userRoles);
				unauthorized = true;
			}
			initialCheckDone = true;
		}, 200);
	});

	// Upload images for a property
	async function uploadPropertyImages(propertyId, images) {
		if (!propertyId || !images || images.length === 0) {
			return;
		}

		console.log(`Uploading ${images.length} images for property ID ${propertyId}`);
		let successCount = 0;
		let errorCount = 0;

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
				successCount++;
			} catch (err) {
				console.error(`Error uploading image ${i + 1}/${images.length}:`, err);
				errorCount++;
			}
		}

		console.log(`Image upload complete: ${successCount} succeeded, ${errorCount} failed`);
		if (successCount > 0) {
			addToast(
				t('images_uploaded', $language, {
					default: 'تم رفع {{count}} صور بنجاح',
					count: successCount
				}),
				'success'
			);
		}

		if (errorCount > 0) {
			addToast(
				t('some_images_failed', $language, {
					default: 'فشل رفع {{count}} صور',
					count: errorCount
				}),
				'error'
			);
		}
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

			// Verify authentication before submission
			if (!$isAuthenticated) {
				if (!(await checkAuthentication())) {
					throw new Error(
						t('auth_required', $language, {
							default: 'يرجى تسجيل الدخول لإنشاء عقار'
						})
					);
				}
			}

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

			// If authentication error, redirect to login
			if (err.message?.includes('authentication') || err.status === 401) {
				addToast(
					t('auth_required', $language, {
						default: 'يرجى تسجيل الدخول لإنشاء عقار'
					}),
					'error'
				);

				setTimeout(() => {
					goto('/auth/login?redirect=/properties/add');
				}, 1500);
			}
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
		<!-- Enhanced Property Form with Tabs -->
		<div class="mb-6">
			<PropertyForm {loading} {error} on:submit={handleSubmit} on:cancel={handleCancel} />
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
