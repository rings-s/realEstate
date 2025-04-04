<script>
	/**
	 * Detailed contract view component
	 * Displays comprehensive contract information with actions
	 * @component
	 */
	import { createEventDispatcher, onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { format } from 'date-fns';
	import { ar } from 'date-fns/locale';
	import SignatureArea from './SignatureArea.svelte';

	// Props
	export let contract = {}; // Contract data object
	export let showSignatures = true; // Show signature area
	export let showPayments = true; // Show payments section
	export let showDocuments = true; // Show documents section
	export let loading = false; // Loading state
	export let canSign = false; // Can current user sign
	export let userRole = 'buyer'; // Current user role: buyer, seller, agent
	export let expanded = true; // Whether details are expanded
	export let printMode = false; // Print-friendly mode
	export let status = null; // Override contract status for display

	const dispatch = createEventDispatcher();

	// Local state
	let activeTab = 'details'; // Active tab: details, payments, documents

	// Local properties
	$: contractStatus = status || contract.status || 'draft';
	$: isSignedByBuyer = contract.buyer_signed;
	$: isSignedBySeller = contract.seller_signed;
	$: isSignedByAgent = contract.agent_signed || !contract.agent;
	$: isFullySigned = isSignedByBuyer && isSignedBySeller && isSignedByAgent;
	$: remainingAmount = (contract.total_amount || 0) - (contract.payments_total || 0);
	$: completionPercentage = contract.total_amount
		? Math.min(100, Math.round(((contract.payments_total || 0) / contract.total_amount) * 100))
		: 0;

	// Format date
	function formatDate(date) {
		if (!date) return 'غير محدد';
		return format(new Date(date), 'dd MMMM yyyy', { locale: ar });
	}

	// Format datetime
	function formatDateTime(date) {
		if (!date) return 'غير محدد';
		return format(new Date(date), 'dd MMMM yyyy - hh:mm a', { locale: ar });
	}

	// Format currency
	function formatCurrency(amount) {
		if (amount === undefined || amount === null) return 'غير محدد';
		return new Intl.NumberFormat('ar-SA', {
			style: 'currency',
			currency: 'SAR',
			maximumFractionDigits: 0
		}).format(amount);
	}

	// Get status color
	function getStatusColor(status) {
		switch (status) {
			case 'draft':
				return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
			case 'pending':
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:bg-opacity-30 dark:text-yellow-400';
			case 'active':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:bg-opacity-30 dark:text-green-400';
			case 'completed':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:bg-opacity-30 dark:text-blue-400';
			case 'cancelled':
				return 'bg-red-100 text-red-800 dark:bg-red-900 dark:bg-opacity-30 dark:text-red-400';
			case 'expired':
				return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	// Get status text
	function getStatusText(status) {
		switch (status) {
			case 'draft':
				return 'مسودة';
			case 'pending':
				return 'قيد الانتظار';
			case 'active':
				return 'نشط';
			case 'completed':
				return 'مكتمل';
			case 'cancelled':
				return 'ملغي';
			case 'expired':
				return 'منتهي الصلاحية';
			default:
				return status;
		}
	}

	// Handle sign action
	function handleSign(signature) {
		dispatch('sign', { contract, signature, role: userRole });
	}

	// Handle actions
	function handleEdit() {
		dispatch('edit', { contract });
	}

	function handlePrint() {
		dispatch('print', { contract });
	}

	function handleDownload() {
		dispatch('download', { contract });
	}

	function handlePayment() {
		dispatch('payment', { contract });
	}

	function handleUploadDocument() {
		dispatch('uploadDocument', { contract });
	}

	function handleCancel() {
		dispatch('cancel', { contract });
	}

	function handleViewPayment(payment) {
		dispatch('viewPayment', { payment, contract });
	}

	function handleViewDocument(document) {
		dispatch('viewDocument', { document, contract });
	}

	function toggleExpand() {
		expanded = !expanded;
		dispatch('expand', { expanded });
	}

	// Change active tab
	function setActiveTab(tab) {
		activeTab = tab;
	}

	// Can user sign
	$: canUserSign =
		canSign &&
		((userRole === 'buyer' && !isSignedByBuyer) ||
			(userRole === 'seller' && !isSignedBySeller) ||
			(userRole === 'agent' && !isSignedByAgent));

	onMount(() => {
		// Initialize component
		if (contract.payments?.length && !showSignatures) {
			activeTab = 'payments';
		}
	});
</script>

{#if loading}
	<div class="animate-pulse rounded-lg bg-white p-6 shadow-md dark:bg-gray-800">
		<div class="mb-4 h-8 w-3/4 rounded bg-gray-200 dark:bg-gray-700"></div>
		<div class="space-y-3">
			<div class="h-4 rounded bg-gray-200 dark:bg-gray-700"></div>
			<div class="h-4 w-5/6 rounded bg-gray-200 dark:bg-gray-700"></div>
			<div class="h-4 w-4/6 rounded bg-gray-200 dark:bg-gray-700"></div>
		</div>
		<div class="mt-6 flex space-x-3 space-x-reverse">
			<div class="h-9 w-24 rounded bg-gray-200 dark:bg-gray-700"></div>
			<div class="h-9 w-24 rounded bg-gray-200 dark:bg-gray-700"></div>
		</div>
	</div>
{:else}
	<div
		class="rounded-lg bg-white shadow-md dark:bg-gray-800 {printMode ? 'p-0' : 'p-6'}"
		in:fly={{ y: 20, duration: 300 }}
	>
		<!-- Header -->
		<div
			class="flex flex-col items-start justify-between sm:flex-row sm:items-center {printMode
				? 'px-6 pb-6'
				: ''}"
		>
			<div>
				<div class="flex items-center">
					<h2 class="text-xl font-bold text-gray-900 dark:text-white">
						{contract.title || 'عقد بدون عنوان'}
					</h2>

					{#if !printMode}
						<button
							type="button"
							class="focus:ring-primary-500 mr-2 rounded-md p-1 text-gray-400 hover:text-gray-600 focus:ring-2 focus:outline-none dark:text-gray-500 dark:hover:text-gray-300"
							on:click={toggleExpand}
							aria-label={expanded ? 'طي التفاصيل' : 'عرض التفاصيل'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 transform transition-transform duration-200 {expanded
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
					{/if}
				</div>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					{contract.contract_number || 'رقم العقد غير متوفر'}
				</p>
			</div>

			<div class="mt-3 flex flex-wrap gap-2 sm:mt-0">
				<span
					class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {getStatusColor(
						contractStatus
					)}"
				>
					{getStatusText(contractStatus)}
				</span>

				{#if contract.is_verified}
					<span
						class="dark:bg-opacity-30 inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-400"
					>
						<svg class="ml-1 h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
								clip-rule="evenodd"
							/>
						</svg>
						موثق
					</span>
				{/if}
			</div>
		</div>

		{#if expanded}
			{#if !printMode}
				<!-- Tabs -->
				<div class="mt-4 border-b border-gray-200 dark:border-gray-700">
					<nav class="-mb-px flex space-x-6 space-x-reverse">
						<button
							class="border-b-2 px-1 py-3 text-sm font-medium {activeTab === 'details'
								? 'border-primary-500 text-primary-600 dark:text-primary-400'
								: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'}"
							on:click={() => setActiveTab('details')}
							aria-current={activeTab === 'details' ? 'page' : undefined}
						>
							تفاصيل العقد
						</button>

						{#if showPayments && contract.payments?.length > 0}
							<button
								class="border-b-2 px-1 py-3 text-sm font-medium {activeTab === 'payments'
									? 'border-primary-500 text-primary-600 dark:text-primary-400'
									: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'}"
								on:click={() => setActiveTab('payments')}
								aria-current={activeTab === 'payments' ? 'page' : undefined}
							>
								<div class="flex items-center">
									المدفوعات
									<span
										class="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-gray-100 text-xs dark:bg-gray-700"
										>{contract.payments?.length || 0}</span
									>
								</div>
							</button>
						{/if}

						{#if showDocuments && contract.documents?.length > 0}
							<button
								class="border-b-2 px-1 py-3 text-sm font-medium {activeTab === 'documents'
									? 'border-primary-500 text-primary-600 dark:text-primary-400'
									: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'}"
								on:click={() => setActiveTab('documents')}
								aria-current={activeTab === 'documents' ? 'page' : undefined}
							>
								<div class="flex items-center">
									المستندات
									<span
										class="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-gray-100 text-xs dark:bg-gray-700"
										>{contract.documents?.length || 0}</span
									>
								</div>
							</button>
						{/if}
					</nav>
				</div>
			{/if}

			<!-- Content -->
			<div class="mt-6 {printMode ? 'px-6' : ''}">
				{#if activeTab === 'details' || printMode}
					<!-- Details Tab -->
					<div class="grid grid-cols-1 gap-8 md:grid-cols-2">
						<!-- Contract Info -->
						<div>
							<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">بيانات العقد</h3>
							<dl class="space-y-3">
								<div class="grid grid-cols-3 gap-1">
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">تاريخ العقد</dt>
									<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
										{formatDate(contract.contract_date)}
									</dd>
								</div>

								<div class="grid grid-cols-3 gap-1">
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
										تاريخ السريان
									</dt>
									<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
										{formatDate(contract.effective_date)}
									</dd>
								</div>

								{#if contract.expiry_date}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											تاريخ انتهاء الصلاحية
										</dt>
										<dd
											class="col-span-2 text-sm text-gray-900 dark:text-white {new Date(
												contract.expiry_date
											) < new Date()
												? 'text-red-600 dark:text-red-400'
												: ''}"
										>
											{formatDate(contract.expiry_date)}
										</dd>
									</div>
								{/if}

								<div class="grid grid-cols-3 gap-1">
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">قيمة العقد</dt>
									<dd class="col-span-2 text-sm font-medium text-gray-900 dark:text-white">
										{formatCurrency(contract.contract_amount)}
									</dd>
								</div>

								{#if contract.total_amount !== contract.contract_amount}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											إجمالي المبلغ
										</dt>
										<dd class="col-span-2 text-sm font-medium text-gray-900 dark:text-white">
											{formatCurrency(contract.total_amount)}
										</dd>
									</div>
								{/if}

								<div class="grid grid-cols-3 gap-1">
									<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">طريقة الدفع</dt>
									<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
										{contract.payment_method_display || 'غير محدد'}
									</dd>
								</div>

								{#if contract.payment_terms}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">شروط الدفع</dt>
										<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
											{contract.payment_terms}
										</dd>
									</div>
								{/if}

								{#if contract.related_property}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											العقار المرتبط
										</dt>
										<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
											{#if contract.property_details}
												<a
													href="/properties/{contract.property_details.slug}"
													class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
												>
													{contract.property_details.title}
												</a>
											{:else}
												{contract.property_title || 'العقار المرتبط'}
											{/if}
										</dd>
									</div>
								{/if}

								{#if contract.auction}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											المزاد المرتبط
										</dt>
										<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
											{#if contract.auction_details}
												<a
													href="/auctions/{contract.auction_details.slug}"
													class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
												>
													{contract.auction_details.title}
												</a>
											{:else}
												{contract.auction_title || 'المزاد المرتبط'}
											{/if}
										</dd>
									</div>
								{/if}

								{#if contract.is_verified}
									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											تم التوثيق بواسطة
										</dt>
										<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
											{contract.verification_authority || 'غير محدد'}
										</dd>
									</div>

									<div class="grid grid-cols-3 gap-1">
										<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
											تاريخ التوثيق
										</dt>
										<dd class="col-span-2 text-sm text-gray-900 dark:text-white">
											{formatDate(contract.verification_date)}
										</dd>
									</div>
								{/if}
							</dl>

							{#if contract.payments_total !== undefined && contract.total_amount !== undefined}
								<!-- Payment Progress -->
								<div class="mt-6">
									<div class="mb-2 flex items-center justify-between">
										<span class="text-sm font-medium text-gray-500 dark:text-gray-400"
											>المدفوعات ({completionPercentage}%)</span
										>
										<span class="text-sm font-medium text-gray-900 dark:text-white">
											{formatCurrency(contract.payments_total)} / {formatCurrency(
												contract.total_amount
											)}
										</span>
									</div>
									<div class="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
										<div
											class="bg-primary-600 h-2.5 rounded-full"
											style="width: {completionPercentage}%"
										></div>
									</div>
									{#if remainingAmount > 0}
										<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
											المبلغ المتبقي: {formatCurrency(remainingAmount)}
										</p>
									{/if}
								</div>
							{/if}
						</div>

						<!-- Parties Info -->
						<div>
							<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">الأطراف</h3>

							<!-- Buyer -->
							<div class="mb-6">
								<h4 class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">المشتري</h4>
								<div class="rounded-md bg-gray-50 p-4 dark:bg-gray-700">
									<p class="font-medium text-gray-900 dark:text-white">
										{contract.buyer_name || 'غير محدد'}
									</p>

									{#if contract.buyer_details}
										<div class="mt-2 text-sm text-gray-500 dark:text-gray-400">
											{#if contract.buyer_details.email}
												<p>{contract.buyer_details.email}</p>
											{/if}
											{#if contract.buyer_details.phone_number}
												<p>{contract.buyer_details.phone_number}</p>
											{/if}
										</div>
									{/if}

									<div class="mt-3 flex items-center">
										<span
											class="text-xs font-medium {isSignedByBuyer
												? 'text-green-600 dark:text-green-400'
												: 'text-gray-500 dark:text-gray-400'}"
										>
											{isSignedByBuyer ? 'تم التوقيع' : 'لم يتم التوقيع بعد'}
										</span>
										{#if isSignedByBuyer && contract.buyer_signature_date}
											<span class="mx-1.5 text-gray-400 dark:text-gray-600">•</span>
											<span class="text-xs text-gray-500 dark:text-gray-400"
												>{formatDateTime(contract.buyer_signature_date)}</span
											>
										{/if}
									</div>
								</div>
							</div>

							<!-- Seller -->
							<div class="mb-6">
								<h4 class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">البائع</h4>
								<div class="rounded-md bg-gray-50 p-4 dark:bg-gray-700">
									<p class="font-medium text-gray-900 dark:text-white">
										{contract.seller_name || 'غير محدد'}
									</p>

									{#if contract.seller_details}
										<div class="mt-2 text-sm text-gray-500 dark:text-gray-400">
											{#if contract.seller_details.email}
												<p>{contract.seller_details.email}</p>
											{/if}
											{#if contract.seller_details.phone_number}
												<p>{contract.seller_details.phone_number}</p>
											{/if}
										</div>
									{/if}

									<div class="mt-3 flex items-center">
										<span
											class="text-xs font-medium {isSignedBySeller
												? 'text-green-600 dark:text-green-400'
												: 'text-gray-500 dark:text-gray-400'}"
										>
											{isSignedBySeller ? 'تم التوقيع' : 'لم يتم التوقيع بعد'}
										</span>
										{#if isSignedBySeller && contract.seller_signature_date}
											<span class="mx-1.5 text-gray-400 dark:text-gray-600">•</span>
											<span class="text-xs text-gray-500 dark:text-gray-400"
												>{formatDateTime(contract.seller_signature_date)}</span
											>
										{/if}
									</div>
								</div>
							</div>

							<!-- Agent (if applicable) -->
							{#if contract.agent || contract.agent_name}
								<div>
									<h4 class="mb-2 text-sm font-medium text-gray-500 dark:text-gray-400">
										الوكيل العقاري
									</h4>
									<div class="rounded-md bg-gray-50 p-4 dark:bg-gray-700">
										<p class="font-medium text-gray-900 dark:text-white">
											{contract.agent_name || 'غير محدد'}
										</p>

										{#if contract.agent_details}
											<div class="mt-2 text-sm text-gray-500 dark:text-gray-400">
												{#if contract.agent_details.email}
													<p>{contract.agent_details.email}</p>
												{/if}
												{#if contract.agent_details.phone_number}
													<p>{contract.agent_details.phone_number}</p>
												{/if}
											</div>
										{/if}

										<div class="mt-3 flex items-center">
											<span
												class="text-xs font-medium {isSignedByAgent
													? 'text-green-600 dark:text-green-400'
													: 'text-gray-500 dark:text-gray-400'}"
											>
												{isSignedByAgent ? 'تم التوقيع' : 'لم يتم التوقيع بعد'}
											</span>
											{#if isSignedByAgent && contract.agent_signature_date}
												<span class="mx-1.5 text-gray-400 dark:text-gray-600">•</span>
												<span class="text-xs text-gray-500 dark:text-gray-400"
													>{formatDateTime(contract.agent_signature_date)}</span
												>
											{/if}
										</div>
									</div>
								</div>
							{/if}
						</div>
					</div>

					{#if contract.description}
						<!-- Contract Description -->
						<div class="mt-8">
							<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">تفاصيل إضافية</h3>
							<div class="prose prose-sm dark:prose-invert max-w-none">
								<p class="text-gray-600 dark:text-gray-300">{contract.description}</p>
							</div>
						</div>
					{/if}

					{#if showSignatures && canUserSign && !printMode}
						<!-- Signature Area -->
						<div class="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
							<h3 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">التوقيع</h3>
							<SignatureArea on:sign={handleSign} {userRole} contractId={contract.id} />
						</div>
					{/if}
				{:else if activeTab === 'payments' && contract.payments?.length > 0}
					<!-- Payments Tab -->
					<div>
						<div class="mb-4 flex items-center justify-between">
							<h3 class="text-lg font-medium text-gray-900 dark:text-white">المدفوعات</h3>
							{#if contractStatus === 'active' && !printMode}
								<button
									type="button"
									class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 inline-flex items-center rounded-md border border-transparent px-3 py-2 text-sm leading-4 font-medium text-white shadow-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
									on:click={handlePayment}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="ml-1 h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M12 6v6m0 0v6m0-6h6m-6 0H6"
										/>
									</svg>
									إضافة دفعة
								</button>
							{/if}
						</div>

						<div class="overflow-x-auto">
							<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
								<thead class="bg-gray-50 dark:bg-gray-800">
									<tr>
										<th
											scope="col"
											class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
										>
											رقم الدفعة
										</th>
										<th
											scope="col"
											class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
										>
											نوع الدفعة
										</th>
										<th
											scope="col"
											class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
										>
											المبلغ
										</th>
										<th
											scope="col"
											class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
										>
											تاريخ الدفع
										</th>
										<th
											scope="col"
											class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
										>
											الحالة
										</th>
										{#if !printMode}
											<th
												scope="col"
												class="px-6 py-3 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
											>
												<span class="sr-only">إجراءات</span>
											</th>
										{/if}
									</tr>
								</thead>
								<tbody
									class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800"
								>
									{#each contract.payments as payment}
										<tr>
											<td
												class="px-6 py-4 text-sm font-medium whitespace-nowrap text-gray-900 dark:text-white"
											>
												{payment.payment_number}
											</td>
											<td
												class="px-6 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400"
											>
												{payment.payment_type_display || payment.payment_type || 'غير محدد'}
											</td>
											<td
												class="px-6 py-4 text-sm font-medium whitespace-nowrap text-gray-900 dark:text-white"
											>
												{formatCurrency(payment.amount)}
											</td>
											<td
												class="px-6 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400"
											>
												{formatDate(payment.payment_date)}
											</td>
											<td class="px-6 py-4 whitespace-nowrap">
												<span
													class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {payment.status ===
													'completed'
														? 'dark:bg-opacity-30 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-400'
														: 'dark:bg-opacity-30 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-400'}"
												>
													{payment.status === 'completed' ? 'مكتمل' : 'قيد التنفيذ'}
												</span>
											</td>
											{#if !printMode}
												<td
													class="px-6 py-4 text-left text-sm whitespace-nowrap text-gray-500 dark:text-gray-400"
												>
													<button
														type="button"
														class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
														on:click={() => handleViewPayment(payment)}
													>
														عرض
													</button>
												</td>
											{/if}
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else if activeTab === 'documents' && contract.documents?.length > 0}
					<!-- Documents Tab -->
					<div>
						<div class="mb-4 flex items-center justify-between">
							<h3 class="text-lg font-medium text-gray-900 dark:text-white">المستندات</h3>
							{#if !printMode}
								<button
									type="button"
									class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 inline-flex items-center rounded-md border border-transparent px-3 py-2 text-sm leading-4 font-medium text-white shadow-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
									on:click={handleUploadDocument}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="ml-1 h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
										/>
									</svg>
									رفع مستند
								</button>
							{/if}
						</div>

						<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
							{#each contract.documents as document}
								<div
									class="flex items-start justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-700"
								>
									<div>
										<h4 class="font-medium text-gray-900 dark:text-white">{document.title}</h4>
										<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
											{document.document_type_display || document.document_type}
										</p>
										<div class="mt-2 flex items-center text-xs text-gray-500 dark:text-gray-400">
											<span>{formatDate(document.created_at)}</span>
											<span class="mx-1.5 text-gray-400 dark:text-gray-600">•</span>
											<span
												class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium {document.verification_status
													? 'dark:bg-opacity-30 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-400'
													: 'dark:bg-opacity-30 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-400'}"
											>
												{document.verification_status ? 'موثق' : 'غير موثق'}
											</span>
										</div>
									</div>
									{#if !printMode}
										<button
											type="button"
											class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
											on:click={() => handleViewDocument(document)}
										>
											عرض
										</button>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}

		{#if !printMode}
			<!-- Actions -->
			<div
				class="mt-8 flex flex-wrap justify-end gap-3 border-t border-gray-200 pt-6 dark:border-gray-700"
			>
				{#if contract.status === 'draft'}
					<button
						type="button"
						class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 inline-flex items-center rounded-md border border-transparent px-4 py-2 text-sm font-medium text-white shadow-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
						on:click={handleEdit}
					>
						تعديل العقد
					</button>
				{/if}

				<button
					type="button"
					class="focus:ring-primary-500 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
					on:click={handlePrint}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-1.5 h-4 w-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
						/>
					</svg>
					طباعة
				</button>

				<button
					type="button"
					class="focus:ring-primary-500 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
					on:click={handleDownload}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="ml-1.5 h-4 w-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
						/>
					</svg>
					تحميل PDF
				</button>

				{#if contract.status === 'active' && !isFullySigned && canUserSign}
					<button
						type="button"
						class="bg-primary-600 hover:bg-primary-700 focus:ring-primary-500 inline-flex items-center rounded-md border border-transparent px-4 py-2 text-sm font-medium text-white shadow-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
						on:click={() =>
							document.getElementById('signature-section')?.scrollIntoView({ behavior: 'smooth' })}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="ml-1.5 h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
							/>
						</svg>
						توقيع العقد
					</button>
				{/if}

				{#if contract.status === 'active' && (userRole === 'admin' || (userRole === 'agent' && contract.agent === contract.agent_id))}
					<button
						type="button"
						class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-red-700 hover:bg-gray-50 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-red-400 dark:hover:bg-gray-600"
						on:click={handleCancel}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="ml-1.5 h-4 w-4"
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
						إلغاء العقد
					</button>
				{/if}
			</div>
		{/if}
	</div>
{/if}
