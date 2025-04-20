<!-- front/src/lib/components/property/RoomEditor.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import { t } from '$lib/config/translations';
	import { language, isRTL } from '$lib/stores/ui';
	import { fade, slide } from 'svelte/transition';
	import { Trash2, Plus, Home, Layers } from 'lucide-svelte';

	const dispatch = createEventDispatcher();

	/**
	 * Props
	 */
	// Rooms array
	export let rooms = [];

	// Local state
	let newRoom = {
		name: '',
		type: 'bedroom',
		floor: '1',
		size: '',
		features: []
	};

	let newFeature = '';
	let editMode = false;
	let editIndex = -1;

	// Room types
	const roomTypes = [
		{ value: 'bedroom', label: t('bedroom', $language, { default: 'غرفة نوم' }) },
		{ value: 'bathroom', label: t('bathroom', $language, { default: 'حمام' }) },
		{ value: 'kitchen', label: t('kitchen', $language, { default: 'مطبخ' }) },
		{ value: 'living_room', label: t('living_room', $language, { default: 'غرفة معيشة' }) },
		{ value: 'dining_room', label: t('dining_room', $language, { default: 'غرفة طعام' }) },
		{ value: 'office', label: t('office', $language, { default: 'مكتب' }) },
		{ value: 'garage', label: t('garage', $language, { default: 'مرآب' }) },
		{ value: 'other', label: t('other', $language, { default: 'أخرى' }) }
	];

	// Add or update room
	function saveRoom() {
		// Validate room data
		if (!newRoom.name.trim()) {
			alert(t('room_name_required', $language, { default: 'اسم الغرفة مطلوب' }));
			return;
		}

		if (newRoom.size && isNaN(parseFloat(newRoom.size))) {
			alert(t('room_size_number', $language, { default: 'يجب أن تكون مساحة الغرفة رقماً' }));
			return;
		}

		// Create a clean copy of the room data
		const roomData = {
			name: newRoom.name.trim(),
			type: newRoom.type,
			floor: newRoom.floor,
			size: newRoom.size ? parseFloat(newRoom.size) : null,
			features: [...newRoom.features]
		};

		if (editMode && editIndex >= 0) {
			// Update existing room
			rooms[editIndex] = roomData;
			rooms = [...rooms]; // Trigger reactivity
		} else {
			// Add new room
			rooms = [...rooms, roomData];
		}

		// Reset form
		resetForm();

		// Notify parent
		dispatch('update', { rooms });
	}

	// Remove room
	function removeRoom(index) {
		rooms = rooms.filter((_, i) => i !== index);
		dispatch('update', { rooms });
	}

	// Edit room
	function editRoom(index) {
		editMode = true;
		editIndex = index;

		// Clone room data to avoid modifying the original
		newRoom = {
			name: rooms[index].name,
			type: rooms[index].type,
			floor: rooms[index].floor || '1',
			size: rooms[index].size?.toString() || '',
			features: [...(rooms[index].features || [])]
		};
	}

	// Reset form
	function resetForm() {
		newRoom = {
			name: '',
			type: 'bedroom',
			floor: '1',
			size: '',
			features: []
		};
		newFeature = '';
		editMode = false;
		editIndex = -1;
	}

	// Add feature to current room
	function addFeature() {
		if (newFeature.trim()) {
			newRoom.features = [...newRoom.features, newFeature.trim()];
			newFeature = '';
		}
	}

	// Remove feature from current room
	function removeFeature(index) {
		newRoom.features = newRoom.features.filter((_, i) => i !== index);
	}

	// Get room type display name
	function getRoomTypeLabel(type) {
		const roomType = roomTypes.find((rt) => rt.value === type);
		return roomType ? roomType.label : type;
	}
</script>

<div class="room-editor space-y-4">
	<!-- Room List -->
	{#if rooms.length > 0}
		<div class="card p-4 space-y-4">
			<h3 class="font-semibold flex items-center">
				<Home class="w-5 h-5 {$isRTL ? 'ml-2' : 'mr-2'}" />
				{t('rooms_list', $language, { default: 'قائمة الغرف' })} ({rooms.length})
			</h3>

			<div class="grid gap-4 md:grid-cols-2">
				{#each rooms as room, i}
					<div class="card p-3 border border-surface-300-600-token" transition:fade>
						<div class="flex justify-between items-start">
							<div>
								<h4 class="font-medium">{room.name}</h4>
								<div class="text-sm text-surface-600-300-token">
									<div>{getRoomTypeLabel(room.type)}</div>
									<div>
										<Layers class="inline-block w-4 h-4 {$isRTL ? 'ml-1' : 'mr-1'}" />
										{t('floor', $language, { default: 'الطابق' })}: {room.floor}
									</div>
									{#if room.size}
										<div>
											{t('size', $language, { default: 'المساحة' })}: {room.size}
											{t('sqm', $language, { default: 'م²' })}
										</div>
									{/if}
								</div>
							</div>

							<div class="flex gap-2">
								<button
									type="button"
									class="btn btn-sm btn-icon variant-soft-primary p-1"
									on:click={() => editRoom(i)}
									aria-label={t('edit_room', $language, { default: 'تعديل الغرفة' })}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 24 24"
										width="16"
										height="16"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
										<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
									</svg>
								</button>
								<button
									type="button"
									class="btn btn-sm btn-icon variant-soft-error p-1"
									on:click={() => removeRoom(i)}
									aria-label={t('remove_room', $language, { default: 'إزالة الغرفة' })}
								>
									<Trash2 class="w-4 h-4" />
								</button>
							</div>
						</div>

						<!-- Room Features -->
						{#if room.features && room.features.length > 0}
							<div class="mt-2">
								<div class="text-xs font-medium">
									{t('features', $language, { default: 'المميزات' })}:
								</div>
								<div class="flex flex-wrap gap-1 mt-1">
									{#each room.features as feature}
										<span class="badge variant-soft-primary text-xs">{feature}</span>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Room Form -->
	<div class="card p-4 space-y-4">
		<h3 class="font-semibold">
			{#if editMode}
				{t('edit_room', $language, { default: 'تعديل الغرفة' })}
			{:else}
				{t('add_room', $language, { default: 'إضافة غرفة' })}
			{/if}
		</h3>

		<div class="grid gap-4 md:grid-cols-2">
			<!-- Room Name -->
			<label class="label">
				<span>{t('room_name', $language, { default: 'اسم الغرفة' })} *</span>
				<input
					type="text"
					class="input"
					bind:value={newRoom.name}
					placeholder={t('room_name_placeholder', $language, {
						default: 'مثال: غرفة النوم الرئيسية'
					})}
				/>
			</label>

			<!-- Room Type -->
			<label class="label">
				<span>{t('room_type', $language, { default: 'نوع الغرفة' })} *</span>
				<select class="select" bind:value={newRoom.type}>
					{#each roomTypes as roomType}
						<option value={roomType.value}>{roomType.label}</option>
					{/each}
				</select>
			</label>

			<!-- Floor -->
			<label class="label">
				<span>{t('floor', $language, { default: 'الطابق' })} *</span>
				<select class="select" bind:value={newRoom.floor}>
					<option value="0">{t('basement', $language, { default: 'طابق سفلي' })}</option>
					<option value="1">{t('ground_floor', $language, { default: 'الطابق الأرضي' })}</option>
					<option value="2">{t('first_floor', $language, { default: 'الطابق الأول' })}</option>
					<option value="3">{t('second_floor', $language, { default: 'الطابق الثاني' })}</option>
					<option value="4">{t('third_floor', $language, { default: 'الطابق الثالث' })}</option>
					<option value="5">{t('fourth_floor', $language, { default: 'الطابق الرابع' })}</option>
					<option value="other">{t('other_floor', $language, { default: 'طابق آخر' })}</option>
				</select>
			</label>

			<!-- Room Size -->
			<label class="label">
				<span
					>{t('room_size', $language, { default: 'مساحة الغرفة' })} ({t('sqm', $language, {
						default: 'م²'
					})})</span
				>
				<input
					type="number"
					class="input"
					bind:value={newRoom.size}
					min="0"
					step="0.01"
					placeholder={t('room_size_placeholder', $language, { default: 'أدخل المساحة' })}
				/>
			</label>
		</div>

		<!-- Room Features -->
		<div>
			<label class="label">
				<span>{t('room_features', $language, { default: 'مميزات الغرفة' })}</span>
				<div class="flex">
					<input
						type="text"
						class="input {$isRTL ? 'rounded-l-none border-l-0' : 'rounded-r-none border-r-0'}"
						bind:value={newFeature}
						placeholder={t('feature_placeholder', $language, {
							default: 'مثال: شرفة، خزانة ملابسة بنية، إضاءة سقف'
						})}
						on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
					/>
					<button
						type="button"
						class="btn variant-filled-primary {$isRTL ? 'rounded-r-token' : 'rounded-l-token'}"
						on:click={addFeature}
					>
						<Plus class="w-5 h-5" />
					</button>
				</div>
			</label>

			<!-- Features List -->
			{#if newRoom.features.length > 0}
				<div class="mt-2">
					<div class="flex flex-wrap gap-2">
						{#each newRoom.features as feature, i}
							<div class="badge variant-soft-primary flex gap-1 items-center p-2">
								<span>{feature}</span>
								<button
									type="button"
									class="text-surface-50-900-token"
									on:click={() => removeFeature(i)}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="16"
										height="16"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="w-3 h-3"
									>
										<path d="M18 6L6 18"></path>
										<path d="M6 6l12 12"></path>
									</svg>
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- Form Buttons -->
		<div class="flex justify-end gap-2">
			{#if editMode}
				<button type="button" class="btn variant-ghost" on:click={resetForm}>
					{t('cancel', $language, { default: 'إلغاء' })}
				</button>
				<button type="button" class="btn variant-filled-primary" on:click={saveRoom}>
					{t('update_room', $language, { default: 'تحديث الغرفة' })}
				</button>
			{:else}
				<button type="button" class="btn variant-filled-primary" on:click={saveRoom}>
					{t('add_room', $language, { default: 'إضافة الغرفة' })}
				</button>
			{/if}
		</div>
	</div>
</div>
