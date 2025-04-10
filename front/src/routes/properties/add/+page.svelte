<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { properties } from '$lib/stores/properties';
	import { isAuthenticated, currentUser, userRoles } from '$lib/stores/auth';
	import { hasPermission, PERMISSIONS } from '$lib/utils/permissions';

	import PropertyForm from '$lib/components/property/PropertyForm.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import { Building, ArrowLeft } from 'lucide-svelte';

	// Local state
	let loading = false;
	let error = null;
	let unauthorized = false;

	// Check if user has permission to create properties
	$: canCreateProperty = hasPermission($userRoles, PERMISSIONS.CREATE_PROPERTY);

	onMount(() => {
		// Check if user is authenticated
		if (!$isAuthenticated) {
			goto('/auth/login?redirect=/properties/add');
			return;
		}

		// Check if user has permission to create properties
		if (!canCreateProperty) {
			unauthorized = true;
		}
	});

	// Handle form submission
	async function handleSubmit(event) {
		try {
			const propertyData = event.detail;
			loading = true;
			error = null;

			// Create new property
			const newProperty = await properties.createProperty(propertyData);

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
			// Maybe store the images to be uploaded after property creation
			console.log('Image upload will be handled after property creation');
		} catch (err) {
			console.error('Error uploading image:', err);
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

	{#if unauthorized}
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
