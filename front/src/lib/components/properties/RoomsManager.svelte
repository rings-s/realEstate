<!-- src/lib/components/properties/RoomsManager.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	// Props
	export let rooms = []; // Array of room objects

	// State
	let newRoom = {
		type: 'bedroom', // Default type
		name: '',
		size: '', // in square meters
		description: '',
		features: []
	};
	let editingIndex = -1; // -1 means we're not editing any room
	let featureInput = '';

	// Room type options
	const ROOM_TYPES = [
		{ value: 'bedroom', label: 'غرفة نوم' },
		{ value: 'living_room', label: 'غرفة معيشة' },
		{ value: 'dining_room', label: 'غرفة طعام' },
		{ value: 'kitchen', label: 'مطبخ' },
		{ value: 'bathroom', label: 'حمام' },
		{ value: 'office', label: 'مكتب' },
		{ value: 'game_room', label: 'غرفة ألعاب' },
		{ value: 'storage', label: 'غرفة تخزين' },
		{ value: 'hall', label: 'صالة' },
		{ value: 'balcony', label: 'شرفة' },
		{ value: 'gym', label: 'صالة رياضية' },
		{ value: 'laundry', label: 'غرفة غسيل' },
		{ value: 'other', label: 'أخرى' }
	];

	// Common room features for suggestions
	const COMMON_FEATURES = [
		'نافذة كبيرة',
		'إضاءة جيدة',
		'تكييف',
		'أرضيات خشبية',
		'دولاب ملابس',
		'تلفزيون',
		'اتصال إنترنت',
		'إطلالة',
		'سجاد',
		'ستائر',
		'مرآة'
	];

	// Event dispatcher for notifying parent component of changes
	const dispatch = createEventDispatcher();

	// Add a new room
	function addRoom() {
		// Validate required fields
		if (!newRoom.name.trim() || !newRoom.type) {
			alert('يرجى إدخال نوع الغرفة واسمها على الأقل');
			return;
		}

		// Convert size to number if it's a valid number
		const roomToAdd = {
			...newRoom,
			size: newRoom.size ? parseFloat(newRoom.size) : '',
			features: [...newRoom.features] // Make a copy to avoid reference issues
		};

		// If we're editing an existing room, update it
		if (editingIndex >= 0) {
			rooms[editingIndex] = roomToAdd;
			rooms = [...rooms]; // Create a new array to trigger reactivity
			editingIndex = -1; // Reset editing state
		} else {
			// Otherwise add a new room
			rooms = [...rooms, roomToAdd];
		}

		// Notify parent component of the change
		dispatch('update', rooms);

		// Reset form
		resetForm();
	}

	// Remove a room
	function removeRoom(index) {
		rooms = rooms.filter((_, i) => i !== index);
		dispatch('update', rooms);

		// If we were editing this room, reset the form
		if (editingIndex === index) {
			resetForm();
		} else if (editingIndex > index) {
			// Adjust editing index if we remove a room before the one we're editing
			editingIndex--;
		}
	}

	// Edit a room
	function editRoom(index) {
		editingIndex = index;
		newRoom = { ...rooms[index] }; // Copy room data to form
	}

	// Reset the form
	function resetForm() {
		newRoom = {
			type: 'bedroom',
			name: '',
			size: '',
			description: '',
			features: []
		};
		editingIndex = -1;
	}

	// Cancel editing
	function cancelEdit() {
		resetForm();
	}

	// Add a feature to the room being edited
	function addFeature() {
		if (featureInput.trim()) {
			newRoom.features = [...newRoom.features, featureInput.trim()];
			featureInput = '';
		}
	}

	// Remove a feature
	function removeFeature(index) {
		newRoom.features = newRoom.features.filter((_, i) => i !== index);
	}

	// Function to get room type label from value
	function getRoomTypeLabel(value) {
		const roomType = ROOM_TYPES.find((type) => type.value === value);
		return roomType ? roomType.label : value;
	}
</script>

<div class="space-y-6">
	<div class="mb-6">
		<div
			class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
		>
			<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">
				{editingIndex >= 0 ? 'تعديل غرفة' : 'إضافة غرفة جديدة'}
			</h3>

			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<!-- Room Type -->
				<div>
					<label
						for="room-type"
						class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						نوع الغرفة <span class="text-red-500">*</span>
					</label>
					<select
						id="room-type"
						class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
						bind:value={newRoom.type}
						required
					>
						{#each ROOM_TYPES as type}
							<option value={type.value}>{type.label}</option>
						{/each}
					</select>
				</div>

				<!-- Room Name -->
				<div>
					<label
						for="room-name"
						class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						اسم الغرفة <span class="text-red-500">*</span>
					</label>
					<input
						type="text"
						id="room-name"
						placeholder="مثال: غرفة النوم الرئيسية"
						class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
						bind:value={newRoom.name}
						required
					/>
				</div>

				<!-- Room Size -->
				<div>
					<label
						for="room-size"
						class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						المساحة (م²)
					</label>
					<input
						type="number"
						id="room-size"
						placeholder="المساحة بالمتر المربع"
						class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
						bind:value={newRoom.size}
						min="0"
						step="0.01"
					/>
				</div>

				<!-- Room Features -->
				<div>
					<label
						for="room-features"
						class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						المميزات
					</label>
					<div class="flex">
						<input
							type="text"
							id="room-features"
							placeholder="أضف ميزة للغرفة"
							class="flex-1 rounded-l-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
							bind:value={featureInput}
							on:keydown={(e) => e.key === 'Enter' && addFeature()}
						/>
						<button
							type="button"
							class="rounded-r-md bg-blue-600 px-3 py-2 text-white transition hover:bg-blue-700"
							on:click={addFeature}
						>
							+
						</button>
					</div>

					<!-- Feature suggestions -->
					<div class="mt-2 flex flex-wrap gap-1">
						{#each COMMON_FEATURES.slice(0, 5) as feature}
							<button
								type="button"
								class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700 transition hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
								on:click={() => {
									featureInput = feature;
									addFeature();
								}}
							>
								{feature}
							</button>
						{/each}
					</div>

					<!-- Feature tags -->
					{#if newRoom.features.length > 0}
						<div class="mt-2 flex flex-wrap gap-1">
							{#each newRoom.features as feature, index}
								<div
									class="flex items-center rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800 dark:bg-blue-900 dark:text-blue-200"
								>
									<span>{feature}</span>
									<button
										type="button"
										class="ml-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
										on:click={() => removeFeature(index)}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-3 w-3"
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
					{/if}
				</div>
			</div>

			<!-- Room Description -->
			<div class="mt-4">
				<label
					for="room-description"
					class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>
					وصف الغرفة
				</label>
				<textarea
					id="room-description"
					rows="3"
					placeholder="أضف وصفاً تفصيلياً للغرفة"
					class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
					bind:value={newRoom.description}
				></textarea>
			</div>

			<!-- Action buttons -->
			<div class="mt-4 flex justify-end space-x-3 space-x-reverse rtl:space-x-reverse">
				{#if editingIndex >= 0}
					<button
						type="button"
						class="rounded-md border border-gray-300 px-4 py-2 text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
						on:click={cancelEdit}
					>
						إلغاء
					</button>
				{/if}
				<button
					type="button"
					class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
					on:click={addRoom}
				>
					{editingIndex >= 0 ? 'تحديث الغرفة' : 'إضافة الغرفة'}
				</button>
			</div>
		</div>
	</div>

	<!-- List of rooms -->
	<div
		class="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="p-4">
			<h3 class="text-lg font-medium text-gray-900 dark:text-white">قائمة الغرف</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400">
				عدد الغرف: {rooms.length}
			</p>
		</div>

		{#if rooms.length > 0}
			<div class="overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead class="bg-gray-50 dark:bg-gray-700">
						<tr>
							<th
								scope="col"
								class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								نوع الغرفة
							</th>
							<th
								scope="col"
								class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								اسم الغرفة
							</th>
							<th
								scope="col"
								class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								المساحة
							</th>
							<th
								scope="col"
								class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								المميزات
							</th>
							<th scope="col" class="relative px-6 py-3">
								<span class="sr-only">الإجراءات</span>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
						{#each rooms as room, index}
							<tr
								class={editingIndex === index
									? 'dark:bg-opacity-20 bg-blue-50 dark:bg-blue-900'
									: ''}
							>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-900 dark:text-gray-100">
									{getRoomTypeLabel(room.type)}
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-900 dark:text-gray-100">
									{room.name}
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-900 dark:text-gray-100">
									{room.size ? `${room.size} م²` : '-'}
								</td>
								<td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
									{#if room.features && room.features.length > 0}
										<div class="flex flex-wrap gap-1">
											{#each room.features as feature}
												<span
													class="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800 dark:bg-blue-900 dark:text-blue-200"
												>
													{feature}
												</span>
											{/each}
										</div>
									{:else}
										<span class="text-gray-400 dark:text-gray-500">-</span>
									{/if}
								</td>
								<td class="px-6 py-4 text-right text-sm font-medium whitespace-nowrap">
									<button
										type="button"
										class="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
										on:click={() => editRoom(index)}
									>
										تعديل
									</button>
									<button
										type="button"
										class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
										on:click={() => removeRoom(index)}
									>
										حذف
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<div class="p-6 text-center">
				<p class="text-gray-500 dark:text-gray-400">لم تتم إضافة أي غرف بعد.</p>
			</div>
		{/if}
	</div>

	<!-- Empty state for properties that don't need room details -->
	{#if rooms.length === 0}
		<div
			class="rounded-lg border border-dashed border-gray-300 p-6 text-center dark:border-gray-600"
		>
			<svg
				class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
				xmlns="http://www.w3.org/2000/svg"
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
			<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">لا توجد غرف</h3>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				أضف غرف العقار للمساعدة في وصفه بشكل أفضل
			</p>
			<div class="mt-6">
				<button
					type="button"
					class="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
					on:click={() => {
						// Focus on first input field
						document.getElementById('room-type')?.focus();
					}}
				>
					<svg
						class="-mr-1 ml-2 h-5 w-5"
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						aria-hidden="true"
					>
						<path
							fill-rule="evenodd"
							d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
							clip-rule="evenodd"
						/>
					</svg>
					إضافة غرفة جديدة
				</button>
			</div>
		</div>
	{/if}
</div>
