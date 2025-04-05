<!-- src/lib/components/properties/AmenitiesSelector.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let selected = [];

	// Event dispatcher
	const dispatch = createEventDispatcher();

	// Custom amenity input
	let customAmenity = '';

	// Predefined common amenities
	const commonAmenities = [
		{ id: 'parking', label: 'موقف سيارات' },
		{ id: 'elevator', label: 'مصعد' },
		{ id: 'pool', label: 'مسبح' },
		{ id: 'garden', label: 'حديقة' },
		{ id: 'security', label: 'أمن وحراسة' },
		{ id: 'gym', label: 'صالة رياضية' },
		{ id: 'central_ac', label: 'تكييف مركزي' },
		{ id: 'balcony', label: 'شرفة' },
		{ id: 'storage', label: 'غرفة تخزين' },
		{ id: 'maid_room', label: 'غرفة خادمة' },
		{ id: 'driver_room', label: 'غرفة سائق' },
		{ id: 'mosque', label: 'مسجد قريب' },
		{ id: 'hospital', label: 'مستشفى قريب' },
		{ id: 'gas_station', label: 'محطة وقود' },
		{ id: 'school', label: 'مدرسة قريبة' },
		{ id: 'supermarket', label: 'سوبرماركت' },
		{ id: 'mall', label: 'مركز تسوق' },
		{ id: 'pharmacy', label: 'صيدلية' },
		{ id: 'furnished', label: 'مفروش' },
		{ id: 'kitchen_appliances', label: 'أجهزة مطبخ' },
		{ id: 'private_entrance', label: 'مدخل خاص' },
		{ id: 'covered_parking', label: 'موقف مغطى' },
		{ id: 'electricity_backup', label: 'مولد كهرباء احتياطي' },
		{ id: 'water_heater', label: 'سخان مياه' }
	];

	// Toggle an amenity selection
	function toggleAmenity(amenityId) {
		if (selected.includes(amenityId)) {
			selected = selected.filter((id) => id !== amenityId);
		} else {
			selected = [...selected, amenityId];
		}

		dispatch('change', selected);
	}

	// Add custom amenity
	function addCustomAmenity() {
		if (!customAmenity.trim()) return;

		const newAmenity = customAmenity.trim();

		// Check if already exists in selected
		if (!selected.includes(newAmenity)) {
			selected = [...selected, newAmenity];
			dispatch('change', selected);
		}

		// Reset input
		customAmenity = '';
	}

	// Remove selected amenity
	function removeAmenity(amenity) {
		selected = selected.filter((a) => a !== amenity);
		dispatch('change', selected);
	}

	// Handle enter key on custom input
	function handleKeydown(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addCustomAmenity();
		}
	}
</script>

<div>
	<!-- Common Amenities -->
	<div class="mb-6">
		<h4 class="mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">المرافق الشائعة</h4>
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
			{#each commonAmenities as amenity}
				<div class="flex items-center">
					<input
						type="checkbox"
						id={amenity.id}
						checked={selected.includes(amenity.id)}
						on:change={() => toggleAmenity(amenity.id)}
						class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
					/>
					<label for={amenity.id} class="mr-2 text-sm text-gray-700 dark:text-gray-300">
						{amenity.label}
					</label>
				</div>
			{/each}
		</div>
	</div>

	<!-- Custom Amenity Input -->
	<div class="mb-4">
		<h4 class="mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">إضافة مرافق مخصصة</h4>
		<div class="flex">
			<input
				type="text"
				bind:value={customAmenity}
				placeholder="أضف مرفق جديد"
				on:keydown={handleKeydown}
				class="flex-1 rounded-md rounded-r-none border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
			/>
			<button
				type="button"
				on:click={addCustomAmenity}
				class="rounded-md rounded-l-none bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
			>
				إضافة
			</button>
		</div>
	</div>

	<!-- Selected Amenities -->
	{#if selected.length > 0}
		<div>
			<h4 class="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">المرافق المختارة</h4>
			<div class="flex flex-wrap gap-2">
				{#each selected as amenity}
					<div
						class="flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800 dark:bg-blue-900 dark:text-blue-200"
					>
						<span>{commonAmenities.find((a) => a.id === amenity)?.label || amenity}</span>
						<button
							type="button"
							class="mr-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
							on:click={() => removeAmenity(amenity)}
							aria-label="إزالة المرفق"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
