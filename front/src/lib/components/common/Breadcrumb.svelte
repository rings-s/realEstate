<script>
	/**
	 * Breadcrumb navigation component
	 * @component
	 */
	export let items = []; // Array of { label, href, icon? } objects
	export let separator = 'chevron'; // chevron, slash, dot, arrow
	export let home = true; // Show home icon at the beginning

	// Separator icons
	const separators = {
		chevron: `<svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
               <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
              </svg>`,
		slash: `<svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
             <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z"></path>
            </svg>`,
		dot: `<svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
           <circle cx="10" cy="10" r="2"></circle>
          </svg>`,
		arrow: `<svg class="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
             <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>`
	};

	// Home icon
	const homeIcon = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                     <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
                    </svg>`;
</script>

<nav class="flex" aria-label="مسار التنقل">
	<ol
		class="inline-flex flex-wrap items-center space-x-1 space-x-reverse rounded-md bg-white px-2 py-3 text-gray-500"
	>
		{#if home}
			<li class="inline-flex items-center">
				<a href="/" class="hover:text-primary-600 inline-flex items-center text-gray-700">
					{@html homeIcon}
					<span class="sr-only ml-1.5">الرئيسية</span>
				</a>
			</li>
			<li aria-hidden="true" class="mx-1">
				{@html separators[separator]}
			</li>
		{/if}

		{#each items as item, index}
			<li class="inline-flex items-center">
				{#if item.href && index < items.length - 1}
					<a
						href={item.href}
						class="hover:text-primary-600 inline-flex items-center text-sm text-gray-700"
					>
						{#if item.icon}
							<span class="ml-1.5">{@html item.icon}</span>
						{/if}
						<span>{item.label}</span>
					</a>
				{:else}
					<span class="flex items-center text-sm text-gray-500">
						{#if item.icon}
							<span class="ml-1.5">{@html item.icon}</span>
						{/if}
						<span>{item.label}</span>
					</span>
				{/if}
			</li>

			{#if index < items.length - 1}
				<li aria-hidden="true" class="mx-1">
					{@html separators[separator]}
				</li>
			{/if}
		{/each}
	</ol>
</nav>
