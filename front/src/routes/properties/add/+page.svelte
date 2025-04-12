<!-- Updated Property Add Page Component with robust image handling -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast, pageLoading } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import {
		isAuthenticated,
		currentUser,
		userRoles,
		checkAuth,
		refreshToken
	} from '$lib/stores/auth';
	import { canCreateProperty } from '$lib/utils/permissions';
	import { uploadMultiplePropertyImages } from '$lib/services/propertyService';
	import tokenManager from '$lib/utils/tokenManager';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft } from 'lucide-svelte';

	// Configuration constants
	const DEFAULT_REDIRECT = '/properties/add';

	// Local state management
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;
	let uploadProgress = { current: 0, total: 0, percentage: 0 };
	let isUploading = false;

	// Reactive permission check - ensure this has a default value of true until roles are loaded
	$: hasCreatePermission =
		$userRoles && $userRoles.length > 0 ? canCreateProperty($userRoles) : true;

	// Enhanced authentication check with expiry handling
	async function ensureAuthenticated() {
		// Set loading state
		loading = true;
		pageLoading.set(true);

		try {
			console.log('Checking authentication...');

			// First check current auth state
			if (!$isAuthenticated) {
				console.log('Not authenticated according to store. Checking token directly...');

				// Check if we have a token
				const token = tokenManager.getAccessToken();
				if (!token) {
					console.log('No token found, redirecting to login');
					goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
					return false;
				}

				// Check if token is expired
				if (tokenManager.isTokenExpired()) {
					// Try to refresh token
					const refreshResult = await refreshToken();

					if (!refreshResult) {
						console.log('Token refresh failed, redirecting to login');
						goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
						return false;
					}

					console.log('Token refreshed successfully');
				} else {
					// Token exists and is valid, set authenticated state
					isAuthenticated.set(true);
				}
			}

			// Validate that auth state is correct
			const isAuthValid = checkAuth();
			console.log('Auth check result:', isAuthValid);

			if (!isAuthValid) {
				console.log('Auth invalid, redirecting to login');
				goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
				return false;
			}

			console.log('Authentication confirmed. Roles:', $userRoles);
			return true;
		} catch (error) {
			console.error('Authentication check error:', error);
			goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
			return false;
		} finally {
			loading = false;
			pageLoading.set(false);
			initialCheckDone = true;
		}
	}

	// Parent component submit handler
	/**
	 * Enhanced handleSubmit for the Properties Add Page
	 */
	async function handleSubmit(event) {
		loading = true;
		error = null;

		try {
			const { property, images } = event.detail;

			console.log('Submitting Property Data:', property);
			console.log('Images to upload:', images?.length || 0);

			// Log image details for debugging
			if (images && images.length > 0) {
				images.forEach((img, index) => {
					console.log(`Image ${index + 1}:`, {
						fileName: img.file?.name,
						fileType: img.file?.type,
						fileSize: img.file?.size,
						isPrimary: img.is_primary,
						hasUrl: Boolean(img.url),
						uploaded: img.uploaded
					});
				});
			}

			if (!property) {
				throw new Error('No property data provided');
			}

			// Ensure user is authenticated
			if (!$isAuthenticated) {
				const authResult = await ensureAuthenticated();
				if (!authResult) {
					throw new Error('Authentication required');
				}
			}

			// Create property
			const newProperty = await properties.createProperty(property);
			console.log('Property created successfully:', newProperty);

			// Success notification
			addToast(t('property_created', $language, { default: 'تم إنشاء العقار بنجاح' }), 'success');

			// Upload images if any
			if (images && images.length > 0) {
				isUploading = true;
				console.log(`Starting upload of ${images.length} images for property ${newProperty.id}`);

				// Filter out any images without files
				const imagesToUpload = images.filter((img) => img.file && !img.uploaded);
				console.log(`${imagesToUpload.length} images have files to upload`);

				// Upload each image individually using fetch for better control
				for (let i = 0; i < imagesToUpload.length; i++) {
					const image = imagesToUpload[i];
					const formData = new FormData();

					// Add the image file
					formData.append('image', image.file);

					// Add metadata
					formData.append('is_primary', image.is_primary ? 'true' : 'false');
					formData.append('caption', image.caption || '');
					formData.append('alt_text', image.alt_text || image.file.name || '');
					formData.append('order', i.toString());

					// Log what we're uploading
					console.log(`Uploading image ${i + 1}/${imagesToUpload.length}:`, {
						fileName: image.file.name,
						fileSize: image.file.size,
						isPrimary: image.is_primary
					});

					try {
						// Update progress
						uploadProgress = {
							current: i + 1,
							total: imagesToUpload.length,
							percentage: ((i + 1) / imagesToUpload.length) * 100
						};

						// Get auth token
						const token = tokenManager.getAccessToken();

						// Make the fetch request
						const response = await fetch(`${API_URL}/properties/${newProperty.id}/images/`, {
							method: 'POST',
							headers: {
								Authorization: `Bearer ${token}`
								// Don't set Content-Type, let browser set it for multipart/form-data
							},
							body: formData
						});

						// Handle response
						if (!response.ok) {
							const errorText = await response.text();
							console.error(`Error uploading image ${i + 1}:`, errorText);
							throw new Error(`Error uploading image: ${errorText}`);
						}

						const responseData = await response.json();
						console.log(`Successfully uploaded image ${i + 1}:`, responseData);
					} catch (uploadError) {
						console.error(`Error uploading image ${i + 1}:`, uploadError);
						// Continue to next image
					}
				}

				isUploading = false;
				console.log('All image uploads attempted');
			}

			// Navigate to new property page
			goto(`/properties/${newProperty.slug}`);
		} catch (error) {
			// Log the detailed error
			console.error('Property Creation Error:', error);
			isUploading = false;

			// Handle API errors with details
			if (error.details && typeof error.details === 'object') {
				// Extract field-specific errors for form display
				const fieldErrors = [];

				Object.entries(error.details).forEach(([field, messages]) => {
					let fieldMessage;

					if (Array.isArray(messages)) {
						fieldMessage = messages.join(', ');
					} else if (typeof messages === 'string') {
						fieldMessage = messages;
					} else {
						fieldMessage = 'Invalid value';
					}

					fieldErrors.push(`${field}: ${fieldMessage}`);
				});

				// Set error for the form to display
				error = fieldErrors.join('. ');
			} else {
				// Use message from error object or default
				error = error.message || 'An unexpected error occurred';
			}

			// Show error toast
			addToast(error, 'error');
		} finally {
			loading = false;
		}
	}

	// Simple cancellation handler
	function handleCancel() {
		goto('/properties');
	}

	// Safe mount handler
	onMount(async () => {
		// Prevent multiple initializations
		if (initialCheckDone) return;

		try {
			pageLoading.set(true);
			console.log('Component mounted, checking authentication...');

			// Perform initial authentication check
			const authResult = await ensureAuthenticated();

			// Set as done after authentication check regardless of outcome
			initialCheckDone = true;

			if (authResult) {
				// Check if user can create properties
				console.log('Authentication successful, checking permissions...');
				console.log('User roles:', $userRoles);

				// Properly check permissions with a delay to ensure roles are loaded
				if ($userRoles && $userRoles.length > 0) {
					// Only check permissions if roles are loaded
					unauthorized = !canCreateProperty($userRoles);
					if (unauthorized) {
						console.warn('Insufficient permissions to create properties');
					}
				} else {
					// If roles aren't loaded yet, wait for them
					const checkPermissionsInterval = setInterval(() => {
						if ($userRoles && $userRoles.length > 0) {
							clearInterval(checkPermissionsInterval);
							unauthorized = !canCreateProperty($userRoles);
							if (unauthorized) {
								console.warn('Insufficient permissions to create properties');
							}
							pageLoading.set(false);
						}
					}, 250);

					// Safety timeout to prevent infinite waiting
					setTimeout(() => {
						clearInterval(checkPermissionsInterval);
						pageLoading.set(false);
					}, 5000);
				}
			} else {
				pageLoading.set(false);
			}
		} catch (error) {
			console.error('Initialization error:', error);
			pageLoading.set(false);
			initialCheckDone = true;
		}
	});
</script>

<div class="container mx-auto px-4 py-6">
	<div class="flex justify-between items-center mb-6">
		<h1 class="h2 flex items-center {$isRTL ? 'text-right' : 'text-left'}">
			<Building class="inline-block w-8 h-8 {$isRTL ? 'ml-2' : 'mr-2'} text-primary-500" />
			{t('add_property', $language, { default: 'إضافة عقار' })}
		</h1>

		<a href="/properties" class="btn variant-ghost">
			<ArrowLeft class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
			{t('back_to_properties', $language, { default: 'العودة إلى العقارات' })}
		</a>
	</div>

	{#if $pageLoading}
		<div class="card p-6 text-center animate-pulse">
			<div class="spinner-icon mx-auto mb-4"></div>
			<p>{t('loading', $language, { default: 'جاري التحميل...' })}</p>
		</div>
	{:else if !initialCheckDone}
		<!-- Loading state while checking authentication -->
		<div class="card p-6 text-center">
			<div class="spinner-icon mx-auto mb-4"></div>
			<p>{t('checking_permissions', $language, { default: 'جاري التحقق من الصلاحيات...' })}</p>
		</div>
	{:else if unauthorized}
		<div class="card p-6 text-center">
			<Alert
				type="error"
				message={t('no_permission', $language, { default: 'ليس لديك صلاحية لإضافة عقار' })}
				dismissible={false}
			/>
			<div class="mt-4">
				<a href="/properties" class="btn variant-filled">
					{t('back_to_properties', $language, { default: 'العودة إلى العقارات' })}
				</a>
			</div>
		</div>
	{:else}
		<!-- Enhanced Property Form with Tabs -->
		<div class="card variant-filled-surface p-0 overflow-hidden">
			<header class="bg-primary-500 text-white p-4">
				<h3 class="h3">{t('create_new_property', $language, { default: 'إنشاء عقار جديد' })}</h3>
				<p class="text-sm opacity-80">
					{t('property_form_description', $language, {
						default: 'أدخل معلومات العقار بالتفصيل. الحقول المطلوبة مميزة بعلامة *'
					})}
				</p>
			</header>

			{#if isUploading}
				<div class="p-4 bg-surface-200-700-token">
					<div class="flex flex-col gap-2">
						<div class="flex justify-between items-center">
							<span class="font-medium">
								{t('uploading_images', $language, { default: 'جاري رفع الصور...' })}
							</span>
							<span>
								{uploadProgress.current}/{uploadProgress.total}
								({Math.round(uploadProgress.percentage)}%)
							</span>
						</div>
						<div class="progress h-2">
							<div
								class="progress-bar bg-primary-500"
								style="width: {uploadProgress.percentage}%;"
							></div>
						</div>
					</div>
				</div>
			{/if}

			<div class="p-4">
				<PropertyForm {loading} {error} on:submit={handleSubmit} on:cancel={handleCancel} />
			</div>
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

	.progress {
		width: 100%;
		background-color: rgba(0, 0, 0, 0.1);
		border-radius: 0.25rem;
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		transition: width 0.3s ease;
	}
</style>
