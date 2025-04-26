<!-- src/lib/components/property/PropertyImages.svelte -->
<script>
	export let images = [];
	export let mainTitle = '';

	let activeIndex = 0;
	let lightboxOpen = false;

	function nextImage() {
		activeIndex = (activeIndex + 1) % images.length;
	}

	function prevImage() {
		activeIndex = (activeIndex - 1 + images.length) % images.length;
	}

	function openLightbox(index) {
		activeIndex = index;
		lightboxOpen = true;
	}
</script>

<div class="relative">
	<!-- Main Image Gallery -->
	<div class="grid grid-cols-1 gap-4 overflow-hidden rounded-xl md:grid-cols-12">
		<!-- Large Main Image -->
		<div
			class="relative h-[500px] transition-all duration-300 ease-in-out hover:opacity-95 md:col-span-8"
		>
			{#if images.length > 0}
				<img
					src={images[activeIndex].file_url}
					alt={mainTitle}
					class="h-full w-full cursor-pointer rounded-xl object-cover"
					on:click={() => openLightbox(activeIndex)}
				/>

				<!-- Navigation Arrows -->
				{#if images.length > 1}
					<div
						class="absolute inset-y-0 right-0 left-0 flex items-center justify-between px-4 opacity-0 transition-opacity hover:opacity-100"
					>
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
							on:click|stopPropagation={prevImage}
						>
							<i class="fas fa-chevron-right"></i>
						</button>
						<button
							class="flex h-10 w-10 items-center justify-center rounded-full bg-black/50 text-white backdrop-blur-sm transition hover:bg-black/70"
							on:click|stopPropagation={nextImage}
						>
							<i class="fas fa-chevron-left"></i>
						</button>
					</div>
				{/if}

				<!-- Image Counter -->
				<div
					class="absolute right-4 bottom-4 rounded-full bg-black/50 px-3 py-1 text-sm text-white backdrop-blur-sm"
				>
					{activeIndex + 1} / {images.length}
				</div>
			{:else}
				<div class="flex h-full w-full items-center justify-center rounded-xl bg-slate-100">
					<i class="fas fa-image text-4xl text-slate-400"></i>
				</div>
			{/if}
		</div>

		<!-- Thumbnails -->
		<div class="grid h-[500px] grid-cols-2 gap-4 md:col-span-4">
			{#each images.slice(0, 4) as image, i}
				{#if i !== activeIndex}
					<div
						class="relative h-[240px] cursor-pointer overflow-hidden rounded-xl transition-transform duration-300 hover:scale-[1.02]"
						on:click={() => (activeIndex = i)}
					>
						<img src={image.file_url} alt={mainTitle} class="h-full w-full object-cover" />
						{#if i === 3 && images.length > 4}
							<div
								class="absolute inset-0 flex items-center justify-center bg-black/50 text-white backdrop-blur-sm"
							>
								<span class="text-xl font-semibold">+{images.length - 4}</span>
							</div>
						{/if}
					</div>
				{/if}
			{/each}
		</div>
	</div>

	<!-- Lightbox -->
	{#if lightboxOpen}
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
			on:click={() => (lightboxOpen = false)}
			transition:fade
		>
			<div class="relative mx-auto max-w-4xl px-4">
				<img src={images[activeIndex].file_url} alt={mainTitle} class="max-h-[90vh] w-auto" />

				<!-- Navigation -->
				<div class="absolute inset-y-0 right-0 left-0 flex items-center justify-between px-4">
					<button
						class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition hover:bg-white/20"
						on:click|stopPropagation={prevImage}
					>
						<i class="fas fa-chevron-right"></i>
					</button>
					<button
						class="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition hover:bg-white/20"
						on:click|stopPropagation={nextImage}
					>
						<i class="fas fa-chevron-left"></i>
					</button>
				</div>

				<!-- Close Button -->
				<button
					class="absolute top-4 right-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition hover:bg-white/20"
					on:click|stopPropagation={() => (lightboxOpen = false)}
				>
					<i class="fas fa-times"></i>
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	/* Image hover effect */
	img {
		transition: transform 0.3s ease-in-out;
	}

	img:hover {
		transform: scale(1.02);
	}
</style>
