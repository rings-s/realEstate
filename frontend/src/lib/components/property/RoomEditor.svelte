<!-- src/lib/components/property/RoomEditor.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import { fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	// Props
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
	let showAllFeatures = false;

	// Room types
	const roomTypes = [
		{ value: 'bedroom', label: 'غرفة نوم' },
		{ value: 'bathroom', label: 'حمام' },
		{ value: 'kitchen', label: 'مطبخ' },
		{ value: 'living_room', label: 'غرفة معيشة' },
		{ value: 'dining_room', label: 'غرفة طعام' },
		{ value: 'office', label: 'مكتب' },
		{ value: 'garage', label: 'مرآب' },
		{ value: 'other', label: 'أخرى' }
	];

	// Add or update room
	function saveRoom() {
		// Validate room data
		if (!newRoom.name.trim()) {
			alert('اسم الغرفة مطلوب');
			return;
		}

		if (newRoom.size && isNaN(parseFloat(newRoom.size))) {
			alert('يجب أن تكون مساحة الغرفة رقماً');
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
		<div class="card space-y-4 rounded-lg bg-white p-4 shadow">
			<h3 class="flex items-center font-semibold">
				<i class="fas fa-home ml-2"></i>
				قائمة الغرف ({rooms.length})
			</h3>

			<div class="grid gap-4 md:grid-cols-2">
				{#each rooms as room, i}
					<div class="card rounded-lg border border-slate-300 bg-white p-3" transition:fade>
						<div class="flex items-start justify-between">
							<div>
								<h4 class="font-medium">{room.name}</h4>
								<div class="text-sm text-slate-600">
									<div>{getRoomTypeLabel(room.type)}</div>
									<div>
										<i class="fas fa-layer-group ml-1 inline-block h-4 w-4"></i>
										الطابق: {room.floor}
									</div>
									{#if room.size}
										<div>
											المساحة: {room.size} م²
										</div>
									{/if}
								</div>
							</div>

							<div class="flex gap-2">
								<button
									type="button"
									class="btn btn-sm rounded p-1 text-blue-600 hover:bg-blue-50"
									on:click={() => editRoom(i)}
									aria-label="تعديل الغرفة"
								>
									<i class="fas fa-edit"></i>
								</button>
								<button
									type="button"
									class="btn btn-sm rounded p-1 text-red-600 hover:bg-red-50"
									on:click={() => removeRoom(i)}
									aria-label="إزالة الغرفة"
								>
									<i class="fas fa-trash-alt"></i>
								</button>
							</div>
						</div>

						<!-- Room Features -->
						{#if room.features && room.features.length > 0}
							<div class="mt-2">
								<div class="text-xs font-medium">المميزات:</div>
								<div class="mt-1 flex flex-wrap gap-1">
									{#each room.features as feature}
										<span class="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-700"
											>{feature}</span
										>
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
	<div class="card space-y-4 rounded-lg bg-white p-4 shadow">
		<h3 class="font-semibold">
			{#if editMode}
				تعديل الغرفة
			{:else}
				إضافة غرفة
			{/if}
		</h3>

		<div class="grid gap-4 md:grid-cols-2">
			<!-- Room Name -->
			<div class="label">
				<span class="mb-1 block text-sm font-medium text-slate-700">اسم الغرفة *</span>
				<input
					type="text"
					class="input w-full rounded border border-slate-300 px-3 py-2"
					bind:value={newRoom.name}
					placeholder="مثال: غرفة النوم الرئيسية"
				/>
			</div>

			<!-- Room Type -->
			<div class="label">
				<span class="mb-1 block text-sm font-medium text-slate-700">نوع الغرفة *</span>
				<select
					class="input w-full rounded border border-slate-300 px-3 py-2"
					bind:value={newRoom.type}
				>
					{#each roomTypes as roomType}
						<option value={roomType.value}>{roomType.label}</option>
					{/each}
				</select>
			</div>

			<!-- Floor -->
			<div class="label">
				<span class="mb-1 block text-sm font-medium text-slate-700">الطابق *</span>
				<select
					class="input w-full rounded border border-slate-300 px-3 py-2"
					bind:value={newRoom.floor}
				>
					<option value="0">طابق سفلي</option>
					<option value="1">الطابق الأرضي</option>
					<option value="2">الطابق الأول</option>
					<option value="3">الطابق الثاني</option>
					<option value="4">الطابق الثالث</option>
					<option value="5">الطابق الرابع</option>
					<option value="other">طابق آخر</option>
				</select>
			</div>

			<!-- Room Size -->
			<div class="label">
				<span class="mb-1 block text-sm font-medium text-slate-700"> مساحة الغرفة (م²) </span>
				<input
					type="number"
					class="input w-full rounded border border-slate-300 px-3 py-2"
					bind:value={newRoom.size}
					min="0"
					step="0.01"
					placeholder="أدخل المساحة"
				/>
			</div>
		</div>

		<!-- Room Features -->
		<div>
			<span class="mb-1 block text-sm font-medium text-slate-700">مميزات الغرفة</span>
			<div class="flex">
				<input
					type="text"
					class="input flex-1 rounded rounded-l-none border border-l-0 border-slate-300 px-3 py-2"
					bind:value={newFeature}
					placeholder="مثال: شرفة، خزانة ملابسة بنية، إضاءة سقف"
					on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
				/>
				<button
					type="button"
					class="btn rounded-r-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
					on:click={addFeature}
				>
					<i class="fas fa-plus"></i>
				</button>
			</div>

			<!-- Features List -->
			{#if newRoom.features.length > 0}
				<div class="mt-2">
					<div class="flex flex-wrap gap-2">
						{#each newRoom.features as feature, i}
							<div class="flex items-center rounded-full bg-blue-100 px-3 py-1 text-blue-700">
								<span>{feature}</span>
								<button
									type="button"
									class="ml-2 text-blue-500 hover:text-blue-700"
									on:click={() => removeFeature(i)}
								>
									<i class="fas fa-times-circle"></i>
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
				<button
					type="button"
					class="btn-secondary rounded border border-slate-300 bg-white px-4 py-2 text-slate-700 hover:bg-slate-50"
					on:click={resetForm}
				>
					إلغاء
				</button>
				<button
					type="button"
					class="btn-primary rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
					on:click={saveRoom}
				>
					تحديث الغرفة
				</button>
			{:else}
				<button
					type="button"
					class="btn-primary rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
					on:click={saveRoom}
				>
					إضافة الغرفة
				</button>
			{/if}
		</div>
	</div>
</div>
