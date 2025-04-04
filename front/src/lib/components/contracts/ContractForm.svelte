<script>
	/**
	 * Contract creation/editing form component
	 * Handles both creating new contracts and editing existing ones
	 * @component
	 */
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { createForm } from '$lib/utils/validation';

	// Import components
	import DatePicker from '../common/DatePicker.svelte';
	import Button from '../common/Button.svelte';
	import Input from '../common/Input.svelte';
	import Select from '../common/Select.svelte';
	import Textarea from '../common/Textarea.svelte';
	import Alert from '../common/Alert.svelte';
	import Loader from '../common/Loader.svelte';

	// Import utilities for formatting
	import { formatCurrency } from '$lib/utils/formatting';

	// Props
	export let contract = null; // Existing contract for editing
	export let isEditing = false; // Whether we're editing an existing contract
	export let properties = []; // Available properties
	export let auctions = []; // Available auctions
	export let buyers = []; // Available buyers
	export let sellers = []; // Available sellers
	export let agents = []; // Available agents
	export let loading = false; // Loading state
	export let saving = false; // Saving state
	export let autoSave = false; // Enable auto-save
	export let showCancelButton = true; // Show cancel button
	export let error = null; // Error message

	const dispatch = createEventDispatcher();

	// Form state
	const initialData = {
		title: contract?.title || '',
		related_property: contract?.related_property || '',
		auction: contract?.auction || '',
		buyer: contract?.buyer || '',
		seller: contract?.seller || '',
		agent: contract?.agent || '',
		contract_date: contract?.contract_date
			? new Date(contract.contract_date).toISOString().split('T')[0]
			: new Date().toISOString().split('T')[0],
		effective_date: contract?.effective_date
			? new Date(contract.effective_date).toISOString().split('T')[0]
			: '',
		expiry_date: contract?.expiry_date
			? new Date(contract.expiry_date).toISOString().split('T')[0]
			: '',
		contract_amount: contract?.contract_amount || '',
		total_amount: contract?.total_amount || '',
		payment_method: contract?.payment_method || 'cash',
		payment_terms: contract?.payment_terms || '',
		description: contract?.description || '',
		status: contract?.status || 'draft'
	};

	// Create form with validation
	const form = createForm(initialData, {
		title: [
			(value) => !!value || 'عنوان العقد مطلوب',
			(value) => value.length >= 5 || 'عنوان العقد يجب أن يكون 5 أحرف على الأقل',
			(value) => value.length <= 100 || 'عنوان العقد يجب أن لا يتجاوز 100 حرف'
		],
		buyer: [(value) => !!value || 'المشتري مطلوب'],
		seller: [(value) => !!value || 'البائع مطلوب'],
		contract_date: [(value) => !!value || 'تاريخ العقد مطلوب'],
		contract_amount: [
			(value) => !!value || 'قيمة العقد مطلوبة',
			(value) => !isNaN(parseFloat(value)) || 'يجب أن تكون قيمة العقد رقمًا',
			(value) => parseFloat(value) > 0 || 'يجب أن تكون قيمة العقد أكبر من صفر'
		],
		total_amount: [
			(value) => !!value || 'إجمالي المبلغ مطلوب',
			(value) => !isNaN(parseFloat(value)) || 'يجب أن يكون إجمالي المبلغ رقمًا',
			(value) => parseFloat(value) > 0 || 'يجب أن يكون إجمالي المبلغ أكبر من صفر',
			(value, formData) =>
				!formData.contract_amount ||
				parseFloat(value) >= parseFloat(formData.contract_amount) ||
				'يجب أن يكون إجمالي المبلغ أكبر من أو يساوي قيمة العقد'
		],
		effective_date: [
			(value, formData) =>
				!value ||
				!formData.contract_date ||
				new Date(value) >= new Date(formData.contract_date) ||
				'يجب أن يكون تاريخ السريان بعد تاريخ العقد أو مساويًا له'
		],
		expiry_date: [
			(value, formData) =>
				!value ||
				!formData.effective_date ||
				new Date(value) > new Date(formData.effective_date) ||
				'يجب أن يكون تاريخ انتهاء الصلاحية بعد تاريخ السريان'
		]
	});

	// Local state
	let formKey = 1; // For form reset
	let auctionSelected = !!form.data.auction;
	let propertyFromAuction = false;
	let autoSaveTimeout;
	let lastSavedData = JSON.stringify(form.data);
	let saveButtonState = 'idle'; // idle, saving, saved, error
	let errorMessage = '';
	let formSections = {
		basic: true,
		parties: true,
		financial: true,
		details: true
	};

	// Reset form
	function resetForm() {
		form.reset();
		formKey++;
		auctionSelected = false;
		propertyFromAuction = false;
		saveButtonState = 'idle';
		errorMessage = '';
		lastSavedData = JSON.stringify(form.data);
	}

	// Handle auction selection
	function handleAuctionChange(e) {
		const auctionId = e.target.value;
		auctionSelected = !!auctionId;

		if (auctionId) {
			const selectedAuction = auctions.find((a) => a.id === auctionId);
			if (selectedAuction && selectedAuction.related_property) {
				form.data.related_property = selectedAuction.related_property;
				propertyFromAuction = true;

				// If auction has seller and buyer, set them
				if (selectedAuction.seller) {
					form.data.seller = selectedAuction.seller;
				}
				// If auction has a winning bidder, set as buyer
				if (selectedAuction.winning_bidder) {
					form.data.buyer = selectedAuction.winning_bidder;
				}

				// Set contract amount from winning bid
				if (selectedAuction.winning_bid) {
					form.data.contract_amount = selectedAuction.winning_bid;
					form.data.total_amount = selectedAuction.winning_bid;
				}
			}
		} else {
			propertyFromAuction = false;
		}

		// Validate affected fields
		form.validateField('related_property');
		form.validateField('seller');
		form.validateField('buyer');
		form.validateField('contract_amount');
		form.validateField('total_amount');
	}

	// Handle property selection
	function handlePropertyChange(e) {
		const propertyId = e.target.value;

		if (propertyId && !propertyFromAuction) {
			const selectedProperty = properties.find((p) => p.id === propertyId);
			if (selectedProperty && selectedProperty.owner) {
				form.data.seller = selectedProperty.owner;
				form.validateField('seller');
			}
		}
	}

	// Update contract amount
	function handleContractAmountChange(e) {
		const amount = parseFloat(e.target.value);

		// If total amount is empty or less than contract amount, update it
		if (!form.data.total_amount || parseFloat(form.data.total_amount) < amount) {
			form.data.total_amount = amount.toString();
			form.validateField('total_amount');
		}
	}

	// Toggle section visibility
	function toggleSection(section) {
		formSections[section] = !formSections[section];
	}

	// Handle form submission
	async function handleSubmit() {
		if (!form.validate()) {
			// Scroll to first error
			const firstErrorField = document.querySelector('.error-message');
			if (firstErrorField) {
				firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
			}
			return;
		}

		try {
			saveButtonState = 'saving';

			// Get data from form
			const formData = { ...form.data };

			// Format some fields
			if (formData.contract_amount) {
				formData.contract_amount = parseFloat(formData.contract_amount);
			}
			if (formData.total_amount) {
				formData.total_amount = parseFloat(formData.total_amount);
			}

			// Trim text fields
			['title', 'description', 'payment_terms'].forEach((field) => {
				if (formData[field]) {
					formData[field] = formData[field].trim();
				}
			});

			dispatch('submit', { data: formData, isEditing });

			// Update last saved data
			lastSavedData = JSON.stringify(formData);
			saveButtonState = 'saved';

			// Reset to idle after delay
			setTimeout(() => {
				saveButtonState = 'idle';
			}, 2000);
		} catch (error) {
			saveButtonState = 'error';
			errorMessage = error.message || 'حدث خطأ أثناء حفظ العقد';

			// Reset to idle after delay
			setTimeout(() => {
				saveButtonState = 'idle';
			}, 3000);
		}
	}

	// Handle cancel button
	function handleCancel() {
		dispatch('cancel');
	}

	// Auto save
	function setupAutoSave() {
		if (!autoSave) return;

		if (autoSaveTimeout) {
			clearTimeout(autoSaveTimeout);
		}

		autoSaveTimeout = setTimeout(() => {
			const currentData = JSON.stringify(form.data);
			if (currentData !== lastSavedData && form.isValid()) {
				handleSubmit();
			}
		}, 5000); // Auto save after 5 seconds of inactivity
	}

	// Cleanup on unmount
	onMount(() => {
		return () => {
			if (autoSaveTimeout) {
				clearTimeout(autoSaveTimeout);
			}
		};
	});

	// Watch for changes in form data for auto save
	$: {
		// Using this reactive block to trigger auto save
		const _ = JSON.stringify(form.data);
		setupAutoSave();
	}

	// Get button state classes
	function getButtonStateClasses(state) {
		switch (state) {
			case 'saving':
				return 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
			case 'saved':
				return 'bg-green-600 hover:bg-green-700 focus:ring-green-500';
			case 'error':
				return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
			default:
				return 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-500';
		}
	}

	// Get button text
	function getButtonText(state) {
		switch (state) {
			case 'saving':
				return 'جاري الحفظ...';
			case 'saved':
				return 'تم الحفظ';
			case 'error':
				return 'حدث خطأ';
			default:
				return isEditing ? 'حفظ التغييرات' : 'إنشاء العقد';
		}
	}
</script>

{#if loading}
	<div class="rounded-lg bg-white p-6 shadow-md dark:bg-gray-800">
		<Loader text="جاري تحميل النموذج..." />
	</div>
{:else}
	<div class="rounded-lg bg-white p-6 shadow-md dark:bg-gray-800" in:fly={{ y: 20, duration: 300 }}>
		<form key={formKey} on:submit|preventDefault={handleSubmit}>
			<div class="mb-6">
				<h2 class="flex items-center text-xl font-bold text-gray-900 dark:text-white">
					{isEditing ? 'تعديل العقد' : 'إنشاء عقد جديد'}
					{#if autoSave}
						<span
							class="mr-2 rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-500 dark:bg-gray-700 dark:text-gray-400"
						>
							حفظ تلقائي
						</span>
					{/if}
				</h2>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					قم بتعبئة البيانات المطلوبة لإنشاء عقد جديد. الحقول المميزة بـ * إلزامية.
				</p>
			</div>

			{#if error}
				<Alert type="error" message={error} class="mb-6" />
			{/if}

			<!-- Basic Contract Information Section -->
			<div class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700">
				<button
					type="button"
					class="flex w-full items-center justify-between p-4 text-right text-lg font-medium text-gray-900 dark:text-white"
					on:click={() => toggleSection('basic')}
				>
					<span>معلومات العقد الأساسية</span>
					<svg
						class="h-5 w-5 transform text-gray-500 transition-transform duration-200 dark:text-gray-400 {formSections.basic
							? 'rotate-180'
							: ''}"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 9l-7 7-7-7"
						/>
					</svg>
				</button>

				{#if formSections.basic}
					<div
						class="grid grid-cols-1 gap-6 p-4 pt-0 md:grid-cols-2"
						transition:fade={{ duration: 200 }}
					>
						<!-- Title -->
						<div class="col-span-1 md:col-span-2">
							<Input
								id="title"
								label="عنوان العقد"
								placeholder="أدخل عنوان العقد"
								required={true}
								bind:value={form.data.title}
								error={form.errors.title}
								on:input={() => form.validateField('title')}
								disabled={saving}
							/>
						</div>

						<!-- Auction Selection -->
						<div>
							<Select
								id="auction"
								label="المزاد المرتبط"
								bind:value={form.data.auction}
								on:change={handleAuctionChange}
								disabled={saving || isEditing}
								helpText="اختياري - حدد المزاد المرتبط بهذا العقد"
							>
								<option value="">- اختر المزاد -</option>
								{#each auctions as auction}
									<option value={auction.id}>{auction.title}</option>
								{/each}
							</Select>
						</div>

						<!-- Property Selection -->
						<div>
							<Select
								id="related_property"
								label="العقار المرتبط"
								bind:value={form.data.related_property}
								on:change={handlePropertyChange}
								disabled={saving || (auctionSelected && propertyFromAuction) || isEditing}
								error={form.errors.related_property}
								helpText="اختياري - حدد العقار المرتبط بهذا العقد"
							>
								<option value="">- اختر العقار -</option>
								{#each properties as property}
									<option value={property.id}>{property.title}</option>
								{/each}
							</Select>
						</div>

						<!-- Contract Date -->
						<div>
							<DatePicker
								id="contract_date"
								label="تاريخ العقد"
								bind:value={form.data.contract_date}
								error={form.errors.contract_date}
								on:change={() => {
									form.validateField('contract_date');
									form.validateField('effective_date');
								}}
								required={true}
								disabled={saving}
							/>
						</div>

						<!-- Contract Status -->
						<div>
							<Select
								id="status"
								label="حالة العقد"
								bind:value={form.data.status}
								disabled={saving}
							>
								<option value="draft">مسودة</option>
								<option value="pending">قيد الانتظار</option>
								<option value="active">نشط</option>
								{#if isEditing}
									<option value="completed">مكتمل</option>
									<option value="cancelled">ملغي</option>
									<option value="expired">منتهي الصلاحية</option>
								{/if}
							</Select>
						</div>

						<!-- Effective Date -->
						<div>
							<DatePicker
								id="effective_date"
								label="تاريخ السريان"
								bind:value={form.data.effective_date}
								error={form.errors.effective_date}
								on:change={() => {
									form.validateField('effective_date');
									form.validateField('expiry_date');
								}}
								helpText="اختياري - التاريخ الذي يبدأ فيه سريان العقد"
								disabled={saving}
							/>
						</div>

						<!-- Expiry Date -->
						<div>
							<DatePicker
								id="expiry_date"
								label="تاريخ انتهاء الصلاحية"
								bind:value={form.data.expiry_date}
								error={form.errors.expiry_date}
								on:change={() => form.validateField('expiry_date')}
								helpText="اختياري - التاريخ الذي ينتهي فيه العقد"
								disabled={saving}
							/>
						</div>
					</div>
				{/if}
			</div>

			<!-- Contract Parties Section -->
			<div class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700">
				<button
					type="button"
					class="flex w-full items-center justify-between p-4 text-right text-lg font-medium text-gray-900 dark:text-white"
					on:click={() => toggleSection('parties')}
				>
					<span>أطراف العقد</span>
					<svg
						class="h-5 w-5 transform text-gray-500 transition-transform duration-200 dark:text-gray-400 {formSections.parties
							? 'rotate-180'
							: ''}"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 9l-7 7-7-7"
						/>
					</svg>
				</button>

				{#if formSections.parties}
					<div
						class="grid grid-cols-1 gap-6 p-4 pt-0 md:grid-cols-2"
						transition:fade={{ duration: 200 }}
					>
						<!-- Buyer Selection -->
						<div>
							<Select
								id="buyer"
								label="المشتري"
								bind:value={form.data.buyer}
								on:change={() => form.validateField('buyer')}
								error={form.errors.buyer}
								required={true}
								disabled={saving}
							>
								<option value="">- اختر المشتري -</option>
								{#each buyers as buyer}
									<option value={buyer.id}
										>{buyer.name || `${buyer.first_name} ${buyer.last_name}`}</option
									>
								{/each}
							</Select>
						</div>

						<!-- Seller Selection -->
						<div>
							<Select
								id="seller"
								label="البائع"
								bind:value={form.data.seller}
								on:change={() => form.validateField('seller')}
								error={form.errors.seller}
								required={true}
								disabled={saving}
							>
								<option value="">- اختر البائع -</option>
								{#each sellers as seller}
									<option value={seller.id}
										>{seller.name || `${seller.first_name} ${seller.last_name}`}</option
									>
								{/each}
							</Select>
						</div>

						<!-- Agent Selection -->
						<div class="col-span-1 md:col-span-2">
							<Select
								id="agent"
								label="الوكيل العقاري"
								bind:value={form.data.agent}
								disabled={saving}
								helpText="اختياري - حدد الوكيل العقاري لهذا العقد"
							>
								<option value="">- اختر الوكيل -</option>
								{#each agents as agent}
									<option value={agent.id}
										>{agent.name || `${agent.first_name} ${agent.last_name}`}</option
									>
								{/each}
							</Select>
						</div>
					</div>
				{/if}
			</div>

			<!-- Financial Details Section -->
			<div class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700">
				<button
					type="button"
					class="flex w-full items-center justify-between p-4 text-right text-lg font-medium text-gray-900 dark:text-white"
					on:click={() => toggleSection('financial')}
				>
					<span>التفاصيل المالية</span>
					<svg
						class="h-5 w-5 transform text-gray-500 transition-transform duration-200 dark:text-gray-400 {formSections.financial
							? 'rotate-180'
							: ''}"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 9l-7 7-7-7"
						/>
					</svg>
				</button>

				{#if formSections.financial}
					<div
						class="grid grid-cols-1 gap-6 p-4 pt-0 md:grid-cols-2"
						transition:fade={{ duration: 200 }}
					>
						<!-- Contract Amount -->
						<div>
							<Input
								id="contract_amount"
								label="قيمة العقد"
								type="number"
								min="0"
								step="0.01"
								placeholder="0.00"
								prefix="ر.س"
								required={true}
								bind:value={form.data.contract_amount}
								error={form.errors.contract_amount}
								on:input={handleContractAmountChange}
								disabled={saving}
							/>
						</div>

						<!-- Total Amount -->
						<div>
							<Input
								id="total_amount"
								label="إجمالي المبلغ"
								type="number"
								min="0"
								step="0.01"
								placeholder="0.00"
								prefix="ر.س"
								required={true}
								bind:value={form.data.total_amount}
								error={form.errors.total_amount}
								on:input={() => form.validateField('total_amount')}
								helpText="إجمالي المبلغ المستحق بما في ذلك الرسوم والضرائب"
								disabled={saving}
							/>
						</div>

						<!-- Payment Method -->
						<div>
							<Select
								id="payment_method"
								label="طريقة الدفع"
								bind:value={form.data.payment_method}
								disabled={saving}
							>
								<option value="cash">نقدي</option>
								<option value="bank_transfer">تحويل بنكي</option>
								<option value="cheque">شيك</option>
								<option value="credit_card">بطاقة ائتمان</option>
								<option value="installment">تقسيط</option>
							</Select>
						</div>

						<!-- Payment Terms -->
						<div class="col-span-1 md:col-span-2">
							<Textarea
								id="payment_terms"
								label="شروط الدفع"
								placeholder="أدخل شروط الدفع للعقد"
								bind:value={form.data.payment_terms}
								rows={3}
								helpText="اختياري - وصف لشروط وجدول الدفع"
								disabled={saving}
							/>
						</div>
					</div>
				{/if}
			</div>

			<!-- Additional Details Section -->
			<div class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700">
				<button
					type="button"
					class="flex w-full items-center justify-between p-4 text-right text-lg font-medium text-gray-900 dark:text-white"
					on:click={() => toggleSection('details')}
				>
					<span>تفاصيل إضافية</span>
					<svg
						class="h-5 w-5 transform text-gray-500 transition-transform duration-200 dark:text-gray-400 {formSections.details
							? 'rotate-180'
							: ''}"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M19 9l-7 7-7-7"
						/>
					</svg>
				</button>

				{#if formSections.details}
					<div class="p-4 pt-0" transition:fade={{ duration: 200 }}>
						<!-- Description -->
						<Textarea
							id="description"
							label="تفاصيل العقد"
							placeholder="أدخل وصفًا للعقد وأي تفاصيل إضافية"
							bind:value={form.data.description}
							rows={5}
							disabled={saving}
						/>
					</div>
				{/if}
			</div>

			<!-- Form Actions -->
			<div class="mt-8 flex flex-wrap justify-end gap-3">
				{#if showCancelButton}
					<Button type="button" variant="secondary" on:click={handleCancel} disabled={saving}>
						إلغاء
					</Button>
				{/if}

				<Button
					type="submit"
					variant="primary"
					class={getButtonStateClasses(saveButtonState)}
					disabled={saving}
					loading={saveButtonState === 'saving'}
				>
					{getButtonText(saveButtonState)}
				</Button>
			</div>

			{#if errorMessage}
				<Alert type="error" message={errorMessage} class="mt-4" />
			{/if}
		</form>
	</div>
{/if}
