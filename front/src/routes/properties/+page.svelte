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

	// Configuration constants
	const MAX_AUTH_ATTEMPTS = 3;
	const AUTH_RETRY_DELAY = 1000; // 1 second
	const DEFAULT_REDIRECT = '/properties/add';

	// Local state management
	let loading = false;
	let error = null;
	let unauthorized = false;
	let initialCheckDone = false;
	let selectedImages = [];
	let authAttempts = 0;

	// Comprehensive safe permission check
	function safeHasPermission(roles, permission) {
		// Validate input parameters
		if (!permission) {
			console.warn('No permission specified for check');
			return false;
		}

		// Handle undefined or non-array roles
		if (!roles || !Array.isArray(roles)) {
			console.warn('Invalid roles provided', { roles, permission });
			return false;
		}

		// Empty roles check
		if (roles.length === 0) {
			console.warn('Empty roles array', { permission });
			return false;
		}

		// Predefined admin roles with full access
		const adminRoles = [ROLES.ADMIN, ROLES.SELLER, ROLES.AGENT];

		// Check for admin roles first
		const hasAdminRole = roles.some((role) => adminRoles.includes(role));

		if (hasAdminRole) {
			console.log('Admin role detected, granting full access');
			return true;
		}

		// Fallback to specific permission check with error handling
		try {
			const permissionResult = hasPermission(roles, permission);
			console.log(`Permission check for ${permission}:`, permissionResult);
			return permissionResult;
		} catch (checkError) {
			console.error('Permission check failed:', checkError, {
				roles,
				permission
			});
			return false;
		}
	}

	// Reactive permission check with fallback
	$: canCreateProperty = safeHasPermission($userRoles || [], PERMISSIONS.CREATE_PROPERTY);

	// Enhanced authentication with comprehensive error handling
	async function checkAuthentication() {
		// Prevent concurrent checks and limit attempts
		if (loading || authAttempts >= MAX_AUTH_ATTEMPTS) {
			console.warn(`Authentication check blocked. Loading: ${loading}, Attempts: ${authAttempts}`);
			return false;
		}

		try {
			loading = true;
			authAttempts++;

			// Explicit authentication flow
			const token = getAccessToken();

			// Token validation
			if (!token || isTokenExpired()) {
				console.log('Invalid or expired token');
				goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
				return false;
			}

			// Fetch user information from token
			const userInfo = getUserFromToken();

			// Validate user information
			if (!userInfo || !userInfo.roles) {
				console.warn('No user information found in token');
				goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
				return false;
			}

			// Update authentication stores
			isAuthenticated.set(true);
			userRoles.set(userInfo.roles);
			currentUser.set(userInfo);

			return true;
		} catch (error) {
			console.error('Authentication verification failed:', error);

			// Notify user of authentication failure
			addToast(
				t('auth_verification_failed', $language, {
					default: 'فشل التحقق من صحة المصادقة'
				}),
				'error'
			);

			// Redirect on authentication failure
			goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
			return false;
		} finally {
			loading = false;
			initialCheckDone = true;

			// Reset auth attempts if needed
			if (authAttempts >= MAX_AUTH_ATTEMPTS) {
				authAttempts = 0;
			}
		}
	}

	// Robust image upload handler
	async function uploadPropertyImages(propertyId, images) {
		// Validate inputs
		if (!propertyId || !images?.length) {
			console.warn('No images to upload or invalid property ID');
			return [];
		}

		// Parallel image upload with comprehensive error handling
		const uploadResults = await Promise.allSettled(
			images.map((image, index) => {
				// Validate individual image
				if (!image.file) {
					console.warn(`Skipping invalid image at index ${index}`);
					return Promise.reject(new Error('Invalid image'));
				}

				return propertyService.uploadPropertyImage(propertyId, image.file, {
					isPrimary: image.is_primary || false,
					caption: image.caption || '',
					order: index
				});
			})
		);

		// Process upload results
		const successfulUploads = uploadResults.filter((result) => result.status === 'fulfilled');

		const failedUploads = uploadResults.filter((result) => result.status === 'rejected');

		// Notify upload results
		if (successfulUploads.length > 0) {
			addToast(
				t('images_uploaded', $language, {
					default: 'تم رفع {{count}} صور بنجاح',
					count: successfulUploads.length
				}),
				'success'
			);
		}

		if (failedUploads.length > 0) {
			addToast(
				t('some_images_failed', $language, {
					default: 'فشل رفع {{count}} صور',
					count: failedUploads.length
				}),
				'error'
			);

			// Log specific upload errors
			failedUploads.forEach((result, index) => {
				console.error(`Image upload ${index} failed:`, result.reason);
			});
		}

		return successfulUploads;
	}

	// Comprehensive form submission handler
	async function handleSubmit(event) {
		// Validate event data
		if (!event.detail) {
			console.error('Invalid submit event');
			return;
		}

		const { property: propertyData, images } = event.detail;

		try {
			loading = true;
			error = null;

			// Comprehensive authentication check
			if (!$isAuthenticated) {
				const authResult = await checkAuthentication();
				if (!authResult) {
					throw new Error(
						t('auth_required', $language, {
							default: 'يرجى تسجيل الدخول لإنشاء عقار'
						})
					);
				}
			}

			// Validate property data
			if (!propertyData) {
				throw new Error(
					t('invalid_property_data', $language, {
						default: 'بيانات العقار غير صالحة'
					})
				);
			}

			// Create property with error handling
			let newProperty;
			try {
				newProperty = await properties.createProperty(propertyData);
			} catch (createError) {
				console.error('Property creation failed:', createError);
				throw new Error(
					t('create_property_error', $language, {
						default: 'فشل إنشاء العقار'
					})
				);
			}

			// Upload images if present
			if (images?.length) {
				await uploadPropertyImages(newProperty.id, images);
			}

			// Success notification
			addToast(
				t('property_created', $language, {
					default: 'تم إنشاء العقار بنجاح'
				}),
				'success'
			);

			// Navigate to new property
			goto(`/properties/${newProperty.slug}`);
		} catch (err) {
			console.error('Property submission error:', err);

			// Set user-friendly error message
			error =
				err.message ||
				t('unexpected_error', $language, {
					default: 'حدث خطأ غير متوقع'
				});

			// Handle specific authentication errors
			if (err.message?.includes('authentication') || err.status === 401) {
				addToast(
					t('auth_required', $language, {
						default: 'يرجى تسجيل الدخول لإنشاء عقار'
					}),
					'error'
				);

				// Delayed redirect to prevent race conditions
				setTimeout(() => goto('/auth/login?redirect=' + DEFAULT_REDIRECT), 1500);
			}
		} finally {
			loading = false;
		}
	}

	// Safe mount handler
	onMount(async () => {
		// Prevent multiple initializations
		if (initialCheckDone) return;

		try {
			// Perform initial authentication
			const authResult = await checkAuthentication();

			if (authResult) {
				// Delayed permission check
				setTimeout(() => {
					// Validate create property permission
					if (!canCreateProperty) {
						console.warn('Insufficient permissions', {
							roles: $userRoles || []
						});
						unauthorized = true;
					}
				}, 200);
			}
		} catch (error) {
			console.error('Initialization error:', error);
			// Redirect on initialization failure
			goto('/auth/login?redirect=' + DEFAULT_REDIRECT);
		}
	});

	// Simple cancellation handler
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
