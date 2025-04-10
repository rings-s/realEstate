<!--
  Refactored Property Images Component
  A component for managing property images without external dependencies
-->
<script>
	import { t } from '$lib/config/translations';
	import { language, isRTL, addToast } from '$lib/stores/ui';
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import {
		ImagePlus,
		Star,
		StarOff,
		Trash2,
		Edit3,
		X,
		Loader,
		CheckCircle,
		AlertCircle,
		ArrowUp,
		ArrowDown
	} from 'lucide-svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Alert from '$lib/components/common/Alert.svelte';
	import {
		fileToBase64,
		formatFileSize,
		isAllowedFileType,
		isAllowedFileSize
	} from '$lib/utils/fileUtils';
	import { API_URL } from '$lib/config/constants';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Property ID
	export let propertyId = null;
	// Initial images array
	export let images = [];
	// Max number of images allowed
	export let maxImages = 10;
	// Whether the component is in loading state
	export let loading = false;
	// Whether to allow editing (setting primary, deleting, etc.)
	export let editable = true;
	// Image display size: sm, md, lg
	export let size = 'md';
	// Additional classes
	export let classes = '';

	// Internal state
	let selectedImage = null;
	let isEditModalOpen = false;
	let isConfirmDeleteModalOpen = false;
	let isUploading = false;
	let uploadProgress = 0;
	let uploadError = null;
	let reordering = false;
	let fileInput;

	// Form data for image editing
	let imageFormData = {
		caption: '',
		alt_text: '',
		is_primary: false
	};

	// Size classes for image container
	const sizeClasses = {
		sm: 'h-32',
		md: 'h-48',
		lg: 'h-64'
	};

	// Get headers for API requests
	function getHeaders() {
		const headers = {};
		const token = localStorage.getItem('auth_token');
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}
		return headers;
	}

	// Load property images
	async function loadImages() {
		if (!propertyId) return;

		loading = true;

		try {
			const response = await fetch(`${API_URL}/properties/${propertyId}/images/`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.error || 'Failed to load images');
			}

			const data = await response.json();
			images = data.results || [];

			// Sort images by order (and primary status as secondary sort)
			images.sort((a, b) => {
				if (a.is_primary && !b.is_primary) return -1;
				if (!a.is_primary && b.is_primary) return 1;
				return (a.order || 0) - (b.order || 0);
			});

			dispatch('update', { images });
		} catch (error) {
			console.error('Error loading images:', error);
			addToast(t('images_load_error', $language, { default: 'فشل تحميل الصور' }), 'error');
		} finally {
			loading = false;
		}
	}

	// Set primary image
	async function setPrimaryImage(imageId) {
		if (!editable) return;

		try {
			const response = await fetch(`${API_URL}/property-images/${imageId}/edit/`, {
				method: 'PATCH',
				headers: {
					...getHeaders(),
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ is_primary: true })
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.error || 'Failed to set primary image');
			}

			// Update local state
			images = images.map((img) => ({
				...img,
				is_primary: img.id === imageId
			}));

			addToast(
				t('primary_image_set', $language, { default: 'تم تعيين الصورة الرئيسية بنجاح' }),
				'success'
			);

			// Dispatch event
			dispatch('update', { images });
		} catch (error) {
			console.error('Error setting primary image:', error);
			addToast(
				t('primary_image_error', $language, { default: 'فشل تعيين الصورة الرئيسية' }),
				'error'
			);
		}
	}

	// Open edit modal
	function openEditModal(image) {
		selectedImage = image;
		imageFormData = {
			caption: image.caption || '',
			alt_text: image.alt_text || '',
			is_primary: image.is_primary || false
		};
		isEditModalOpen = true;
	}

	// Update image details
	async function updateImageDetails() {
		if (!selectedImage) return;

		try {
			const response = await fetch(`${API_URL}/property-images/${selectedImage.id}/edit/`, {
				method: 'PATCH',
				headers: {
					...getHeaders(),
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(imageFormData)
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.error || 'Failed to update image details');
			}

			const updatedImage = await response.json();

			// Update local state
			images = images.map((img) => (img.id === selectedImage.id ? updatedImage : img));

			// Close modal
			isEditModalOpen = false;

			addToast(
				t('image_updated', $language, { default: 'تم تحديث تفاصيل الصورة بنجاح' }),
				'success'
			);

			// If primary status changed, make sure only one is primary
			if (imageFormData.is_primary) {
				images = images.map((img) => ({
					...img,
					is_primary: img.id === selectedImage.id
				}));
			}

			// Dispatch event
			dispatch('update', { images });
		} catch (error) {
			console.error('Error updating image details:', error);
			addToast(t('image_update_error', $language, { default: 'فشل تحديث تفاصيل الصورة' }), 'error');
		}
	}

	// Open delete confirmation modal
	function openDeleteModal(image) {
		selectedImage = image;
		isConfirmDeleteModalOpen = true;
	}

	// Delete image
	async function deleteImage() {
		if (!selectedImage) return;

		try {
			const response = await fetch(`${API_URL}/property-images/${selectedImage.id}/delete/`, {
				method: 'DELETE',
				headers: getHeaders()
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.error || 'Failed to delete image');
			}

			// Update local state
			images = images.filter((img) => img.id !== selectedImage.id);

			// Close modal
			isConfirmDeleteModalOpen = false;

			addToast(t('image_deleted', $language, { default: 'تم حذف الصورة بنجاح' }), 'success');

			// Dispatch event
			dispatch('update', { images });
		} catch (error) {
			console.error('Error deleting image:', error);
			addToast(t('image_delete_error', $language, { default: 'فشل حذف الصورة' }), 'error');
		}
	}

	// Handle file selection from input
	async function handleFileSelect(event) {
		const files = event.target.files;
		if (files && files.length > 0) {
			await uploadImages(files);
			// Clear input value to allow selecting the same file again
			event.target.value = null;
		}
	}

	// Handle file drop from drag-and-drop
	function handleDrop(event) {
		event.preventDefault();
		const files = event.dataTransfer.files;
		if (files.length > 0) {
			uploadImages(files);
		}
		dropTarget.classList.remove('border-primary-500');
	}

	// Handle drag over for visual effects
	function handleDragOver(event) {
		event.preventDefault();
		dropTarget.classList.add('border-primary-500');
	}

	// Handle drag leave for visual effects
	function handleDragLeave(event) {
		event.preventDefault();
		dropTarget.classList.remove('border-primary-500');
	}

	// Element reference for drag and drop
	let dropTarget;

	// Upload images
	async function uploadImages(files) {
		// Check if maximum number of images reached
		if (images.length + files.length > maxImages) {
			addToast(
				t('max_images_reached', $language, {
					default: 'تم الوصول إلى الحد الأقصى للصور ({{max}})',
					max: maxImages
				}),
				'warning'
			);

			// Only upload up to the max allowed
			const remainingSlots = maxImages - images.length;
			if (remainingSlots <= 0) return;

			files = Array.from(files).slice(0, remainingSlots);
		}

		// Validate files
		const validFiles = Array.from(files).filter((file) => {
			const isValidType = isAllowedFileType(file, [
				'image/jpeg',
				'image/png',
				'image/gif',
				'image/webp'
			]);
			const isValidSize = isAllowedFileSize(file, 5); // 5MB max

			if (!isValidType) {
				addToast(
					t('invalid_file_type', $language, {
						default: 'نوع الملف غير صالح: {{filename}}. الأنواع المسموح بها: JPG، PNG، GIF، WEBP',
						filename: file.name
					}),
					'error'
				);
			}

			if (!isValidSize) {
				addToast(
					t('file_too_large', $language, {
						default: 'حجم الملف كبير جداً: {{filename}}. الحد الأقصى هو 5 ميجابايت',
						filename: file.name
					}),
					'error'
				);
			}

			return isValidType && isValidSize;
		});

		if (validFiles.length === 0) return;

		isUploading = true;
		uploadProgress = 0;
		uploadError = null;

		for (let i = 0; i < validFiles.length; i++) {
			const file = validFiles[i];
			const formData = new FormData();
			formData.append('image', file);

			// Set as primary if it's the first image
			if (images.length === 0 && i === 0) {
				formData.append('is_primary', 'true');
			}

			// Set the order based on current images length
			formData.append('order', images.length + i);

			try {
				// Simulate upload progress
				const updateProgress = () => {
					uploadProgress = Math.min(100, uploadProgress + 5);
					if (uploadProgress < 100 && isUploading) {
						setTimeout(updateProgress, 100);
					}
				};
				updateProgress();

				const response = await fetch(`${API_URL}/properties/${propertyId}/images/`, {
					method: 'POST',
					headers: getHeaders(),
					body: formData
				});

				if (!response.ok) {
					const error = await response.json();
					throw new Error(error.error || 'Failed to upload image');
				}

				const newImage = await response.json();

				// Update local state
				if (newImage.is_primary) {
					// Make sure only this image is primary
					images = images.map((img) => ({
						...img,
						is_primary: false
					}));
				}

				images = [...images, newImage];

				// Update progress
				uploadProgress = ((i + 1) / validFiles.length) * 100;
			} catch (error) {
				console.error('Error uploading image:', error);
				uploadError = error.message;
				addToast(
					t('image_upload_error', $language, {
						default: 'فشل تحميل الصورة: {{filename}}',
						filename: file.name
					}),
					'error'
				);
			}
		}

		isUploading = false;
		uploadProgress = 100;

		// Dispatch event
		dispatch('update', { images });
	}

	// Move image up in order
	async function moveImageUp(index) {
		if (index === 0) return; // Already at the top

		reordering = true;

		try {
			// Swap order values
			const newOrder = [...images];
			const temp = newOrder[index].order;
			newOrder[index].order = newOrder[index - 1].order;
			newOrder[index - 1].order = temp;

			// Swap positions in array
			[newOrder[index], newOrder[index - 1]] = [newOrder[index - 1], newOrder[index]];

			// Update UI immediately
			images = newOrder;

			// Save to server if we have IDs
			if (propertyId && images[index].id && images[index - 1].id) {
				await saveImageOrder();
			}
		} catch (error) {
			console.error('Error moving image:', error);
			addToast(t('image_order_error', $language, { default: 'فشل تغيير ترتيب الصور' }), 'error');
		} finally {
			reordering = false;
		}
	}

	// Move image down in order
	async function moveImageDown(index) {
		if (index >= images.length - 1) return; // Already at the bottom

		reordering = true;

		try {
			// Swap order values
			const newOrder = [...images];
			const temp = newOrder[index].order;
			newOrder[index].order = newOrder[index + 1].order;
			newOrder[index + 1].order = temp;

			// Swap positions in array
			[newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];

			// Update UI immediately
			images = newOrder;

			// Save to server if we have IDs
			if (propertyId && images[index].id && images[index + 1].id) {
				await saveImageOrder();
			}
		} catch (error) {
			console.error('Error moving image:', error);
			addToast(t('image_order_error', $language, { default: 'فشل تغيير ترتيب الصور' }), 'error');
		} finally {
			reordering = false;
		}
	}

	// Save image order to server
	async function saveImageOrder() {
		if (!propertyId) return;

		reordering = true;

		try {
			// Create an array of {id, order} objects
			const orderData = images.map((img, index) => ({
				id: img.id,
				order: index
			}));

			const response = await fetch(`${API_URL}/properties/${propertyId}/images/reorder/`, {
				method: 'POST',
				headers: {
					...getHeaders(),
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ images: orderData })
			});

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.error || 'Failed to save image order');
			}

			addToast(
				t('image_order_saved', $language, { default: 'تم حفظ ترتيب الصور بنجاح' }),
				'success'
			);

			// Dispatch event
			dispatch('update', { images });
		} catch (error) {
			console.error('Error saving image order:', error);
			addToast(t('image_order_error', $language, { default: 'فشل حفظ ترتيب الصور' }), 'error');
		} finally {
			reordering = false;
		}
	}

	// Size class based on size prop
	$: sizeClass = sizeClasses[size] || sizeClasses.md;

	// Load images on mount if propertyId is provided
	onMount(() => {
		if (propertyId) {
			loadImages();
		}
	});
</script>

<div class="w-full {classes}">
	<!-- Upload dropzone area -->
	{#if editable && images.length < maxImages}
		<div
			bind:this={dropTarget}
			class="card p-4 mb-4 border border-dashed border-surface-300-600-token cursor-pointer hover:bg-surface-hover-token transition-colors"
			on:click={() => fileInput.click()}
			on:keydown={(e) => e.key === 'Enter' && fileInput.click()}
			on:dragover={handleDragOver}
			on:dragleave={handleDragLeave}
			on:drop={handleDrop}
			role="button"
			tabindex="0"
			aria-label={t('add_images', $language, { default: 'إضافة صور' })}
		>
			<div class="flex flex-col items-center justify-center gap-2 p-6">
				<ImagePlus class="w-12 h-12 text-surface-500-400-token" />
				<h3 class="font-medium text-center">
					{t('add_property_images', $language, { default: 'إضافة صور للعقار' })}
				</h3>
				<p class="text-sm text-surface-600-300-token text-center">
					{t('drag_or_click', $language, { default: 'اسحب وأفلت الصور هنا أو انقر للاختيار' })}
				</p>
				<p class="text-xs text-surface-500-400-token text-center">
					{t('image_requirements', $language, {
						default: 'PNG، JPG، GIF حتى 5 ميجابايت | {{remaining}} صور متبقية',
						remaining: maxImages - images.length
					})}
				</p>

				<input
					bind:this={fileInput}
					type="file"
					accept="image/jpeg,image/png,image/gif,image/webp"
					multiple
					class="hidden"
					on:change={handleFileSelect}
					aria-hidden="true"
				/>
			</div>
		</div>
	{/if}

	<!-- Upload progress -->
	{#if isUploading}
		<div class="card p-4 mb-4" transition:fade>
			<div class="flex flex-col gap-2">
				<div class="flex items-center justify-between">
					<span class="font-medium"
						>{t('uploading_images', $language, { default: 'جاري تحميل الصور...' })}</span
					>
					<span class="text-sm">{Math.round(uploadProgress)}%</span>
				</div>
				<div class="progress">
					<div
						class="progress-bar bg-primary-500"
						style="width: {uploadProgress}%;"
						role="progressbar"
						aria-valuenow={uploadProgress}
						aria-valuemin="0"
						aria-valuemax="100"
					></div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Upload error -->
	{#if uploadError}
		<Alert
			type="error"
			message={uploadError}
			dismissible={true}
			classes="mb-4"
			on:dismiss={() => (uploadError = null)}
		/>
	{/if}

	<!-- No images message -->
	{#if images.length === 0 && !loading}
		<div class="card p-8 text-center">
			<p class="text-surface-500-400-token">
				{t('no_images', $language, {
					default: 'لا توجد صور للعقار. أضف بعض الصور لعرض العقار بشكل أفضل.'
				})}
			</p>
		</div>
	{:else if loading}
		<!-- Loading skeleton -->
		<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-4">
			{#each Array(4) as _, i}
				<div class="card p-2" transition:fade>
					<div class="placeholder animate-pulse {sizeClass} w-full mb-2 rounded"></div>
					<div class="placeholder animate-pulse h-4 w-2/3 mb-1 rounded"></div>
					<div class="placeholder animate-pulse h-3 w-1/2 rounded"></div>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Images grid with reordering controls -->
		<section
			class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-4 relative"
		>
			{#each images as image, i (image.id)}
				<div transition:fade>
					<div class="card p-2 h-full flex flex-col relative overflow-hidden group">
						<!-- Primary image badge -->
						{#if image.is_primary}
							<div class="absolute top-3 {$isRTL ? 'right-3' : 'left-3'} z-10">
								<span class="badge variant-filled-primary">
									{t('primary', $language, { default: 'الرئيسية' })}
								</span>
							</div>
						{/if}

						<!-- Image container -->
						<div class="relative {sizeClass} w-full overflow-hidden rounded mb-2">
							<img
								src={image.image_url}
								alt={image.alt_text || t('property_image', $language, { default: 'صورة العقار' })}
								class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
							/>

							<!-- Image controls overlay (visible on hover) -->
							{#if editable}
								<div
									class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2"
								>
									{#if !image.is_primary}
										<button
											class="btn btn-sm btn-icon variant-filled-primary"
											on:click={() => setPrimaryImage(image.id)}
											aria-label={t('set_as_primary', $language, { default: 'تعيين كصورة رئيسية' })}
											title={t('set_as_primary', $language, { default: 'تعيين كصورة رئيسية' })}
										>
											<Star class="w-4 h-4" />
										</button>
									{/if}

									<button
										class="btn btn-sm btn-icon variant-filled-surface"
										on:click={() => openEditModal(image)}
										aria-label={t('edit_image', $language, { default: 'تعديل الصورة' })}
										title={t('edit_image', $language, { default: 'تعديل الصورة' })}
									>
										<Edit3 class="w-4 h-4" />
									</button>

									<button
										class="btn btn-sm btn-icon variant-filled-error"
										on:click={() => openDeleteModal(image)}
										aria-label={t('delete_image', $language, { default: 'حذف الصورة' })}
										title={t('delete_image', $language, { default: 'حذف الصورة' })}
									>
										<Trash2 class="w-4 h-4" />
									</button>
								</div>
							{/if}
						</div>

						<!-- Image details -->
						<div class="flex-grow {$isRTL ? 'text-right' : 'text-left'}">
							{#if image.caption}
								<p class="font-medium text-sm line-clamp-1" title={image.caption}>
									{image.caption}
								</p>
							{/if}
							<p class="text-xs text-surface-500-400-token line-clamp-1">
								{formatFileSize(image.file_size * 1024 || 0)} •
								{image.width || 0}×{image.height || 0}
							</p>
						</div>

						<!-- Reordering controls -->
						{#if editable && images.length > 1}
							<div
								class="absolute bottom-2 {$isRTL
									? 'left-2'
									: 'right-2'} opacity-50 group-hover:opacity-100"
							>
								<div class="flex gap-1">
									{#if i > 0}
										<button
											class="btn btn-sm btn-icon variant-soft p-1"
											on:click={() => moveImageUp(i)}
											aria-label={t('move_up', $language, { default: 'نقل للأعلى' })}
											title={t('move_up', $language, { default: 'نقل للأعلى' })}
										>
											<ArrowUp class="w-3 h-3" />
										</button>
									{/if}

									{#if i < images.length - 1}
										<button
											class="btn btn-sm btn-icon variant-soft p-1"
											on:click={() => moveImageDown(i)}
											aria-label={t('move_down', $language, { default: 'نقل للأسفل' })}
											title={t('move_down', $language, { default: 'نقل للأسفل' })}
										>
											<ArrowDown class="w-3 h-3" />
										</button>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</section>

		{#if reordering}
			<div class="flex justify-center mb-4">
				<div class="flex items-center gap-2">
					<Loader class="w-5 h-5 animate-spin" />
					<span>{t('saving_order', $language, { default: 'جاري حفظ الترتيب...' })}</span>
				</div>
			</div>
		{/if}
	{/if}
</div>

<!-- Edit Image Modal -->
{#if isEditModalOpen && selectedImage}
	<Modal
		open={isEditModalOpen}
		title={t('edit_image', $language, { default: 'تعديل الصورة' })}
		on:close={() => (isEditModalOpen = false)}
		size="md"
	>
		<div class="grid grid-cols-1 gap-4">
			<!-- Image preview -->
			<div class="flex justify-center mb-2">
				<img
					src={selectedImage.image_url}
					alt={selectedImage.alt_text || t('property_image', $language, { default: 'صورة العقار' })}
					class="max-h-48 rounded"
				/>
			</div>

			<!-- Caption -->
			<label class="label">
				<span>{t('caption', $language, { default: 'التعليق' })}</span>
				<input
					type="text"
					class="input"
					bind:value={imageFormData.caption}
					placeholder={t('caption_placeholder', $language, { default: 'صالة المعيشة الرئيسية' })}
				/>
			</label>

			<!-- Alt text -->
			<label class="label">
				<span>{t('alt_text', $language, { default: 'النص البديل' })}</span>
				<input
					type="text"
					class="input"
					bind:value={imageFormData.alt_text}
					placeholder={t('alt_text_placeholder', $language, {
						default: 'صورة لصالة المعيشة الواسعة مع نوافذ كبيرة'
					})}
				/>
				<small class="text-surface-500-400-token">
					{t('alt_text_help', $language, {
						default: 'وصف الصورة للمستخدمين الذين لا يستطيعون رؤيتها (مهم لإمكانية الوصول)'
					})}
				</small>
			</label>

			<!-- Primary image checkbox -->
			<label class="flex items-center gap-2">
				<input type="checkbox" bind:checked={imageFormData.is_primary} />
				<span>{t('set_as_primary', $language, { default: 'تعيين كصورة رئيسية' })}</span>
			</label>

			<div class="flex justify-end gap-2 mt-4">
				<button
					type="button"
					class="btn variant-ghost-surface"
					on:click={() => (isEditModalOpen = false)}
				>
					{t('cancel', $language, { default: 'إلغاء' })}
				</button>
				<button type="button" class="btn variant-filled-primary" on:click={updateImageDetails}>
					{t('save', $language, { default: 'حفظ' })}
				</button>
			</div>
		</div>
	</Modal>
{/if}

<!-- Delete Confirmation Modal -->
{#if isConfirmDeleteModalOpen && selectedImage}
	<Modal
		open={isConfirmDeleteModalOpen}
		title={t('confirm_delete', $language, { default: 'تأكيد الحذف' })}
		on:close={() => (isConfirmDeleteModalOpen = false)}
		size="sm"
	>
		<div class="text-center">
			<AlertCircle class="w-12 h-12 text-error-500 mx-auto mb-4" />
			<p class="mb-4">
				{t('confirm_delete_image', $language, {
					default: 'هل أنت متأكد من حذف هذه الصورة؟ لا يمكن التراجع عن هذا الإجراء.'
				})}
			</p>

			<div class="flex justify-center mb-2">
				<img
					src={selectedImage.image_url}
					alt={selectedImage.alt_text || t('property_image', $language, { default: 'صورة العقار' })}
					class="max-h-32 rounded"
				/>
			</div>

			<div class="flex justify-end gap-2 mt-4">
				<button
					type="button"
					class="btn variant-ghost-surface"
					on:click={() => (isConfirmDeleteModalOpen = false)}
				>
					{t('cancel', $language, { default: 'إلغاء' })}
				</button>
				<button type="button" class="btn variant-filled-error" on:click={deleteImage}>
					{t('delete', $language, { default: 'حذف' })}
				</button>
			</div>
		</div>
	</Modal>
{/if}
