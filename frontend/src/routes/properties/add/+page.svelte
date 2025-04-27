<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { createProperty } from '$lib/stores/properties';
	import { addToast } from '$lib/stores/ui';
	import PropertyForm from '$lib/components/property/PropertyForm.svelte';

	let loading = false;
	let error = '';

  async function handleSubmit(event) {
    loading = true;
    error = '';

    try {
      const propertyData = event.detail;
      console.log("Received property data from form:", propertyData);
      
      // Validate required fields
      const requiredFields = {
        'title': 'عنوان العقار',
        'property_type': 'نوع العقار', 
        'description': 'وصف العقار',
        'city': 'المدينة'
      };
      
      for (const [field, label] of Object.entries(requiredFields)) {
        if (!propertyData[field]) {
          throw new Error(`${label} مطلوب`);
        }
      }
      
      // Ensure numeric fields are valid numbers
      if (propertyData.market_value && isNaN(parseFloat(propertyData.market_value))) {
        throw new Error('القيمة السوقية يجب أن تكون رقمًا');
      }
      
      // Ensure location structure
      if (!propertyData.location || typeof propertyData.location !== 'object') {
        propertyData.location = {}; 
      }
      
      // Make sure arrays and objects are initialized properly
      ['features', 'amenities', 'rooms', 'highQualityStreets'].forEach(field => {
        if (!Array.isArray(propertyData[field])) {
          propertyData[field] = [];
        }
      });
      
      ['specifications', 'pricing_details'].forEach(field => {
        if (!propertyData[field] || typeof propertyData[field] !== 'object') {
          propertyData[field] = {};
        }
      });
      
      // Validate media files
      if (!propertyData.media || !propertyData.media.length) {
        throw new Error('يجب إضافة صورة واحدة على الأقل');
      }

      console.log("Submitting property with validated data...");
      const result = await createProperty(propertyData);

      if (result.success) {
        addToast('تم إضافة العقار بنجاح', 'success');
        goto('/properties/' + result.data.slug);
      } else {
        throw new Error(result.error || 'فشل في إنشاء العقار');
      }
    } catch (err) {
      console.error('Submit error:', err);
      error = err.message;
      addToast(error, 'error');
    } finally {
      loading = false;
    }
  }
</script>

<div class="mx-auto max-w-5xl px-4 py-8">
	<div class="rounded-xl bg-white shadow">
		<div class="border-b p-6">
			<h1 class="text-2xl font-bold">إضافة عقار جديد</h1>
			<p class="mt-1 text-slate-600">قم بإدخال بيانات العقار بشكل كامل</p>
		</div>

		{#if error}
			<div class="mx-6 mt-6 rounded-lg bg-red-50 p-4 text-red-700">
				<i class="fas fa-exclamation-circle ml-2"></i>
				{error}
			</div>
		{/if}

		<div class="p-6">
			<PropertyForm {loading} on:submit={handleSubmit} />
		</div>
	</div>
</div>
