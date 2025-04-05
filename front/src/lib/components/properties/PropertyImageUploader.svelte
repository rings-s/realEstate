<!-- src/lib/components/properties/PropertyImageUploader.svelte -->
<script>
	import { createEventDispatcher, onDestroy } from 'svelte';
	import { uploadPropertyImages, validateImageFiles } from '$lib/services/imageUpload';
	import Button from '$lib/components/common/Button.svelte';

	// Props
	export let propertyId = null;
	export let existingImages = [];
	export let disabled = false;
	export let maxFiles = 10;
	export let maxSize = 5 * 1024 * 1024; // 5MB

	// State
	let selectedFiles = [];
	let uploadProgress = 0;
	let isUploading = false;
	let error = null;
	let currentUploadXHR = null; // To allow cancellation

	// Combined images (existing + new ones)
	$: previewImages = [
		...existingImages,
		...Array.from(selectedFiles).map((file) => ({
			file,
			url: URL.createObjectURL(file),
			isNew: true
		}))
	];

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Handle file selection
	function handleFileSelect(event) {
		if (disabled) return;

		const files = event.target.files;
		if (!files || !files.length) return;

		// Validate selected files
		const validation = validateImageFiles(files, {
			maxFiles: maxFiles - existingImages.length,
			maxSize
		});

		// Show warnings if any
		validation.warnings.forEach((warning) => {
			dispatch('warning', { message: warning });
		});

		// Add only valid files
		if (validation.validFiles.length > 0) {
			selectedFiles = [...selectedFiles, ...validation.validFiles];
			dispatch('select', { files: selectedFiles });
		}
	}

	// Remove a file from selection
	function removeFile(index) {
		if (disabled || isUploading) return;

		// Check if this is an existing image or a new one
		if (index < existingImages.length) {
			// This is an existing image - emit remove event for parent
			dispatch('removeExisting', { index });
		} else {
			// This is a new image - adjust index and remove from selectedFiles
			const newIndex = index - existingImages.length;
			selectedFiles = selectedFiles.filter((_, i) => i !== newIndex);
			dispatch('select', { files: selectedFiles });
		}
	}

	// Upload selected files
	async function uploadFiles() {
		if (!propertyId || !selectedFiles.length || isUploading) return;

		isUploading = true;
		uploadProgress = 0;
		error = null;

		try {
			dispatch('uploadStart');

			const result = await uploadPropertyImages(propertyId, selectedFiles, {
				onProgress: (percent) => {
					uploadProgress = percent;
					dispatch('progress', { progress: percent });
				}
			});

			dispatch('uploadComplete', { result });

			// Clear selected files after successful upload
			selectedFiles = [];

			return result;
		} catch (err) {
			error = err;
			dispatch('error', { error: err });
			return null;
		} finally {
			isUploading = false;
		}
	}

	// Cancel ongoing upload
	function cancelUpload() {
		if (currentUploadXHR && isUploading) {
			currentUploadXHR.abort();
			isUploading = false;
			uploadProgress = 0;
			dispatch('uploadCancel');
		}
	}

	// Clean up object URLs on destroy
	onDestroy(() => {
		// Revoke any object URLs we created to avoid memory leaks
		selectedFiles.forEach((file) => {
			if (file.objectURL) {
				URL.revokeObjectURL(file.objectURL);
			}
		});
	});
</script>

<div class="property-image-uploader">
	<!-- File Input Area -->
	<div
		class="relative mb-4 flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-6 transition-colors hover:border-gray-400 dark:border-gray-600 dark:hover:border-gray-500
               {disabled || isUploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}"
		on:click={() => !disabled && !isUploading && document.getElementById('file-input').click()}
		on:keydown={(e) =>
			e.key === 'Enter' &&
			!disabled &&
			!isUploading &&
			document.getElementById('file-input').click()}
		tabindex={disabled || isUploading ? -1 : 0}
		role="button"
		aria-label="اختيار صور للرفع"
	>
		<input
			type="file"
			id="file-input"
			accept="image/jpeg,image/png,image/gif,image/webp"
			multiple
			on:change={handleFileSelect}
			class="hidden"
			disabled={disabled || isUploading}
		/>

		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mb-3 h-12 w-12 text-gray-400"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
			/>
		</svg>

		<p class="mb-2 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
			انقر لتحديد الصور أو اسحب وأسقط الملفات هنا
		</p>

		<p class="text-center text-xs text-gray-500 dark:text-gray-400">
			PNG، JPG، GIF أو WEBP (الحد الأقصى: {maxFiles} صور، {maxSize / (1024 * 1024)} ميجابايت لكل صورة)
		</p>
	</div>

	<!-- Upload Progress -->
	{#if isUploading}
		<div class="dark:bg-opacity-20 mb-4 rounded-lg bg-blue-50 p-4 dark:bg-blue-900">
			<div class="flex items-center justify-between">
				<h4 class="font-medium text-blue-700 dark:text-blue-300">جاري الرفع...</h4>
				<button
					type="button"
					class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
					on:click={cancelUpload}
				>
					إلغاء
				</button>
			</div>

			<div class="mt-2 flex items-center gap-2">
				<div class="h-2 flex-1 overflow-hidden rounded-full bg-blue-200 dark:bg-blue-700">
					<div
						class="h-full rounded-full bg-blue-600 dark:bg-blue-400"
						style="width: {uploadProgress}%"
					></div>
				</div>
				<span class="text-sm font-medium text-blue-700 dark:text-blue-300">{uploadProgress}%</span>
			</div>
		</div>
	{/if}

	<!-- Error Message -->
	{#if error}
		<div class="dark:bg-opacity-20 mb-4 rounded-lg bg-red-50 p-4 dark:bg-red-900">
			<h4 class="font-medium text-red-700 dark:text-red-300">حدث خطأ أثناء الرفع</h4>
			<p class="mt-1 text-sm text-red-600 dark:text-red-400">{error.message}</p>
		</div>
	{/if}

	<!-- Selected Files Preview -->
	{#if previewImages.length > 0}
		<div class="mb-4">
			<h3 class="mb-2 font-medium text-gray-700 dark:text-gray-300">
				الصور المحددة ({previewImages.length})
			</h3>

			<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
				{#each previewImages as image, index}
					<div
						class="group relative h-32 overflow-hidden rounded-lg border border-gray-200 bg-gray-100 dark:border-gray-700 dark:bg-gray-800"
					>
						<img
							src={image.isNew ? image.url : image.path || image.url}
							alt="معاينة الصورة"
							class="h-full w-full object-cover"
						/>

						<!-- Image Actions Overlay -->
						<div
							class="bg-opacity-0 group-hover:bg-opacity-40 absolute inset-0 flex items-center justify-center bg-black opacity-0 transition-all group-hover:opacity-100"
						>
							<button
								type="button"
								class="rounded-full bg-red-600 p-1.5 text-white transition hover:bg-red-700"
								on:click={() => removeFile(index)}
								disabled={disabled || isUploading}
								aria-label="حذف الصورة"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M6 18L18 6M6 6l12 12"
									/>
								</svg>
							</button>
						</div>

						<!-- Tags -->
						{#if image.isNew}
							<span
								class="absolute top-1 left-1 rounded bg-blue-500 px-1.5 py-0.5 text-xs font-medium text-white"
							>
								جديدة
							</span>
						{/if}

						{#if image.is_primary}
							<span
								class="absolute bottom-1 left-1 rounded bg-green-500 px-1.5 py-0.5 text-xs font-medium text-white"
							>
								رئيسية
							</span>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- Upload Button -->
		{#if selectedFiles.length > 0 && propertyId}
			<div class="flex justify-end">
				<Button
					variant="primary"
					on:click={uploadFiles}
					disabled={isUploading || disabled}
					loading={isUploading}
				>
					رفع {selectedFiles.length} صور
				</Button>
			</div>
		{/if}
	{/if}
</div>
