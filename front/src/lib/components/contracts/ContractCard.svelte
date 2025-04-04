<!-- Internal component for card content to avoid duplication -->
<script context="module">
	const ContractCardContent = {
		props: [
			'contract',
			'showStatus',
			'showActions',
			'truncate',
			'getStatusColor',
			'getStatusText',
			'getSigningStatusColor',
			'getSigningStatusText',
			'formatDate',
			'formatCurrency',
			'isSignedByBuyer',
			'isSignedBySeller',
			'isSignedByAgent',
			'isFullySigned'
		],
		events: ['view', 'sign'],

		render($$props, $$slots, $$render, $$createComponentInstance) {
			return `
      <div>
        <div class="flex justify-between items-start">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white ${$$props.truncate ? 'truncate' : ''}" title="${$$props.contract.title || ''}">
              ${$$props.contract.title || 'عقد بدون عنوان'}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              ${$$props.contract.contract_number || 'رقم العقد غير متوفر'}
            </p>
          </div>

          ${
						$$props.showStatus
							? `
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${$$props.getStatusColor($$props.contract.status)}">
            ${$$props.getStatusText($$props.contract.status)}
          </span>
          `
							: ''
					}
        </div>

        <div class="mt-4 space-y-1">
          <div class="flex justify-between">
            <span class="text-sm text-gray-500 dark:text-gray-400">تاريخ العقد:</span>
            <span class="text-sm text-gray-900 dark:text-white">${$$props.formatDate($$props.contract.contract_date)}</span>
          </div>

          <div class="flex justify-between">
            <span class="text-sm text-gray-500 dark:text-gray-400">قيمة العقد:</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">${$$props.formatCurrency($$props.contract.contract_amount)}</span>
          </div>

          <div class="flex justify-between">
            <span class="text-sm text-gray-500 dark:text-gray-400">الأطراف:</span>
            <span class="text-sm text-gray-900 dark:text-white ${$$props.truncate ? 'truncate max-w-[60%]' : ''}" title="البائع: ${$$props.contract.seller_name || ''} | المشتري: ${$$props.contract.buyer_name || ''}">
              ${$$props.contract.seller_name || 'البائع'} و ${$$props.contract.buyer_name || 'المشتري'}
            </span>
          </div>
        </div>

        <div class="mt-4 flex justify-between items-center">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${$$props.getSigningStatusColor()}">
            ${$$props.getSigningStatusText()}
          </span>

          ${
						$$props.showActions
							? `
          <div class="flex space-x-2 space-x-reverse">
            <button type="button"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    on:click|stopPropagation="$$props.dispatch('view', { contract: $$props.contract })">
              عرض التفاصيل
            </button>

            ${
							!$$props.isFullySigned
								? `
            <button type="button"
                    class="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
                    on:click|stopPropagation="$$props.dispatch('sign', { contract: $$props.contract })">
              توقيع
            </button>
            `
								: ''
						}
          </div>
          `
							: ''
					}
        </div>

        ${
					$$props.contract.expiry_date
						? `
        <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500 dark:text-gray-400">تاريخ انتهاء الصلاحية:</span>
            <span class="text-sm ${new Date($$props.contract.expiry_date) < new Date() ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}">
              ${$$props.formatDate($$props.contract.expiry_date)}
            </span>
          </div>
        </div>
        `
						: ''
				}
      </div>
      `;
		}
	};
</script>

<script>
	/**
	 * Contract summary card component
	 * Used for displaying contract information in lists and grids
	 * @component
	 */
	import { createEventDispatcher } from 'svelte';
	import { fade } from 'svelte/transition';
	import { format } from 'date-fns';
	import { ar } from 'date-fns/locale';

	// Props
	export let contract = {}; // Contract data object
	export let variant = 'default'; // default, compact, elevated, bordered
	export let interactive = true; // Whether card is clickable/interactive
	export let showActions = true; // Show action buttons
	export let showStatus = true; // Show status badge
	export let truncate = true; // Truncate long text
	export let loading = false; // Loading state
	export let href = undefined; // Direct link (if card should be a link)

	const dispatch = createEventDispatcher();

	// Local properties
	$: isSignedByBuyer = contract.buyer_signed;
	$: isSignedBySeller = contract.seller_signed;
	$: isSignedByAgent = contract.agent_signed || !contract.agent;
	$: isFullySigned = isSignedByBuyer && isSignedBySeller && isSignedByAgent;

	// Format date
	function formatDate(date) {
		if (!date) return 'غير محدد';
		return format(new Date(date), 'dd MMMM yyyy', { locale: ar });
	}

	// Format currency
	function formatCurrency(amount) {
		if (!amount && amount !== 0) return 'غير محدد';
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

	// Get signing status color
	function getSigningStatusColor() {
		if (isFullySigned)
			return 'bg-green-100 text-green-800 dark:bg-green-900 dark:bg-opacity-30 dark:text-green-400';
		if (isSignedByBuyer || isSignedBySeller)
			return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:bg-opacity-30 dark:text-yellow-400';
		return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
	}

	// Get signing status text
	function getSigningStatusText() {
		if (isFullySigned) return 'موقع بالكامل';
		if (isSignedByBuyer && !isSignedBySeller) return 'موقع من المشتري';
		if (!isSignedByBuyer && isSignedBySeller) return 'موقع من البائع';
		if (isSignedByBuyer || isSignedBySeller) return 'موقع جزئياً';
		return 'غير موقع';
	}

	// Handle card click
	function handleClick() {
		if (!interactive || href) return;
		dispatch('click', { contract });
	}

	// Handle view action
	function handleView(e) {
		e.stopPropagation();
		dispatch('view', { contract });
	}

	// Handle sign action
	function handleSign(e) {
		e.stopPropagation();
		dispatch('sign', { contract });
	}

	// Variant classes
	const variantClasses = {
		default: 'bg-white border border-gray-200 dark:bg-gray-800 dark:border-gray-700',
		compact: 'bg-white border border-gray-200 dark:bg-gray-800 dark:border-gray-700',
		elevated: 'bg-white border border-gray-200 shadow-md dark:bg-gray-800 dark:border-gray-700',
		bordered: 'bg-white border-2 border-gray-300 dark:bg-gray-800 dark:border-gray-600'
	};

	// Computed classes
	$: cardClasses = [
		'rounded-lg overflow-hidden transition-all duration-200',
		variantClasses[variant],
		interactive ? 'hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-md' : '',
		interactive && !href ? 'cursor-pointer' : '',
		variant === 'compact' ? 'p-4' : 'p-6',
		$$props.class || ''
	].join(' ');
</script>

{#if loading}
	<div class={cardClasses} aria-busy="true" transition:fade={{ duration: 200 }}>
		<div class="animate-pulse">
			<div class="flex items-start justify-between">
				<div class="w-1/2">
					<div class="mb-3 h-6 rounded bg-gray-200 dark:bg-gray-700"></div>
					<div class="mb-2 h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700"></div>
				</div>
				<div class="h-8 w-24 rounded bg-gray-200 dark:bg-gray-700"></div>
			</div>

			<div class="mt-4 space-y-2">
				<div class="h-4 rounded bg-gray-200 dark:bg-gray-700"></div>
				<div class="h-4 rounded bg-gray-200 dark:bg-gray-700"></div>
				<div class="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700"></div>
			</div>

			<div class="mt-6 flex items-center justify-between">
				<div class="h-5 w-24 rounded bg-gray-200 dark:bg-gray-700"></div>
				<div class="h-9 w-32 rounded bg-gray-200 dark:bg-gray-700"></div>
			</div>
		</div>
	</div>
{:else if href}
	<a {href} class={cardClasses}>
		<ContractCardContent
			{contract}
			{showStatus}
			{showActions}
			{truncate}
			{getStatusColor}
			{getStatusText}
			{getSigningStatusColor}
			{getSigningStatusText}
			{formatDate}
			{formatCurrency}
			{isSignedByBuyer}
			{isSignedBySeller}
			{isSignedByAgent}
			{isFullySigned}
			on:view={handleView}
			on:sign={handleSign}
		/>
	</a>
{:else}
	<div
		class={cardClasses}
		on:click={handleClick}
		on:keydown={(e) => e.key === 'Enter' && handleClick()}
		tabindex={interactive ? '0' : undefined}
		role={interactive ? 'button' : undefined}
	>
		<ContractCardContent
			{contract}
			{showStatus}
			{showActions}
			{truncate}
			{getStatusColor}
			{getStatusText}
			{getSigningStatusColor}
			{getSigningStatusText}
			{formatDate}
			{formatCurrency}
			{isSignedByBuyer}
			{isSignedBySeller}
			{isSignedByAgent}
			{isFullySigned}
			on:view={handleView}
			on:sign={handleSign}
		/>
	</div>
{/if}
