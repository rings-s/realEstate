<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { hasPermission } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
	import PropertyForm from '$lib/components/property/PropertyForm.svelte';

	let loading = false;

	onMount(() => {
		if (!hasPermission('create_property')) {
			addToast('ليس لديك صلاحية لإضافة عقار', 'error');
			goto('/properties');
		}
	});

	async function handleSubmit(event) {
		loading = true;
		try {
			const propertyData = event.detail;
			// Handle property creation
			addToast('تم إضافة العقار بنجاح', 'success');
			goto('/properties');
		} catch (error) {
			addToast('حدث خطأ أثناء إضافة العقار', 'error');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>إضافة عقار جديد | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
	<div class="mb-6">
		<a href="/properties" class="text-slate-600 hover:text-blue-600">
			<i class="fas fa-arrow-right ml-2"></i>
			العودة إلى العقارات
		</a>
	</div>

	<div class="rounded-xl bg-white shadow-sm">
		<div class="border-b p-6">
			<h1 class="text-2xl font-bold text-slate-900">إضافة عقار جديد</h1>
			<p class="mt-1 text-slate-600">قم بإدخال بيانات العقار بشكل كامل</p>
		</div>

		<div class="p-6">
			<PropertyForm {loading} on:submit={handleSubmit} />
		</div>
	</div>
</div>
