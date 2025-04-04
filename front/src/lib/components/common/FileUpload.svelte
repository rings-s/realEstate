<!-- src/lib/components/common/FileUpload.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let label = 'رفع الملفات';
	export let accept = '*';
	export let multiple = false;
	export let maxFiles = 10;
	export let error = '';

	// State
	let fileInput;
	let isDragging = false;
	let files = [];
	let uploading = false;
	let uploadProgress = 0;

	// Event Dispatcher
	const dispatch = createEventDispatcher();

	// Handle file selection
	function handleFileSelect(event) {
		const selectedFiles = Array.from(event.target.files || []);

		// Check max files limit
		if (selectedFiles.length > maxFiles) {
			error = `الحد الأقصى لعدد الملفات هو ${maxFiles}`;
			return;
		}

		files = selectedFiles;
		simulateUpload();
	}

	// Simulate uploading files
	function simulateUpload() {
		if (files.length === 0) return;

		uploading = true;
		uploadProgress = 0;

		// Simulate file processing and upload
		const interval = setInterval(() => {
			uploadProgress += 5;

			if (uploadProgress >= 100) {
				clearInterval(interval);
				uploading = false;

				// Process files to get URLs
				const uploadedFiles = files.map((file) => ({
					name: file.name,
					size: file.size,
					type: file.type,
					// In a real app, this would be a server URL
					url: URL.createObjectURL(file)
				}));

				// Dispatch event with uploaded files
				dispatch('filesUploaded', { files: uploadedFiles });

				// Reset the input
				if (fileInput) {
					fileInput.value = '';
				}

				files = [];
			}
		}, 100);
	}

	// Handle file drag events
	function handleDragOver(event) {
		event.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function handleDrop(event) {
		event.preventDefault();
		isDragging = false;

		const droppedFiles = Array.from(event.dataTransfer.files || []);

		// Check if file types match the accept attribute
		if (accept !== '*') {
			const acceptTypes = accept.split(',').map((type) => type.trim());
			const validFiles = droppedFiles.filter((file) => {
				return acceptTypes.some((acceptType) => {
					if (acceptType.startsWith('.')) {
						return file.name.endsWith(acceptType);
					} else if (acceptType.includes('/*')) {
						const mainType = acceptType.split('/')[0];
						return file.type.startsWith(mainType);
					} else {
						return file.type === acceptType;
					}
				});
			});

			if (validFiles.length !== droppedFiles.length) {
				error = 'بعض الملفات غير مدعومة';
				return;
			}
		}

		// Check max files limit
		if (droppedFiles.length > maxFiles) {
			error = `الحد الأقصى لعدد الملفات هو ${maxFiles}`;
			return;
		}

		files = droppedFiles;
		simulateUpload();
	}
</script>

<div class="mb-4">
	<p class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">{label}</p>

	<!-- Drop Zone - Added role="button" and aria attributes for accessibility -->
	<div
		class="flex flex-col items-center justify-center rounded-md border-2 border-dashed p-6
			{isDragging
			? 'border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-900/20'
			: 'border-gray-300 dark:border-gray-600'}
			transition-colors duration-150"
		on:dragover={handleDragOver}
		on:dragleave={handleDragLeave}
		on:drop={handleDrop}
		role="button"
		tabindex="0"
		aria-label="منطقة إسقاط الملفات"
		on:keydown={(e) => e.key === 'Enter' && fileInput.click()}
	>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mb-2 h-10 w-10 text-gray-400 dark:text-gray-500"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
			/>
		</svg>

		<p class="mb-2 text-center text-sm text-gray-600 dark:text-gray-400">
			اسحب الملفات هنا أو انقر للاختيار
		</p>

		<input
			bind:this={fileInput}
			type="file"
			{accept}
			{multiple}
			class="hidden"
			on:change={handleFileSelect}
		/>

		<button
			type="button"
			class="rounded-md bg-blue-600 px-4 py-2 text-sm text-white transition hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
			on:click={() => fileInput.click()}
			disabled={uploading}
		>
			اختيار الملفات
		</button>
	</div>

	<!-- Upload Progress -->
	{#if uploading}
		<div class="mt-3">
			<div class="flex justify-between text-xs text-gray-600 dark:text-gray-400">
				<span>جاري الرفع...</span>
				<span>{uploadProgress}%</span>
			</div>
			<div class="mt-1 h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
				<div
					class="h-2 rounded-full bg-blue-600 dark:bg-blue-500"
					style="width: {uploadProgress}%"
				></div>
			</div>
		</div>
	{/if}

	<!-- File List -->
	{#if files.length > 0 && !uploading}
		<ul
			class="mt-3 divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-700 dark:border-gray-700"
		>
			{#each files as file}
				<li class="flex items-center justify-between px-3 py-2 text-sm">
					<div class="flex items-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="ml-2 h-5 w-5 text-gray-400"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							/>
						</svg>
						<span class="truncate">{file.name}</span>
					</div>
					<span class="text-xs text-gray-500">
						{Math.round(file.size / 1024)} كيلوبايت
					</span>
				</li>
			{/each}
		</ul>
	{/if}

	<!-- Error Message -->
	{#if error}
		<p class="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
	{/if}
</div>
