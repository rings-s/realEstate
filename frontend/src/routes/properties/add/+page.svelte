<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { createProperty } from '$lib/services/properties';
  import { addToast } from '$lib/stores/ui';
  import PropertyForm from '$lib/components/property/PropertyForm.svelte';

  let loading = false;
  let error = '';

  async function handleSubmit(event) {
    loading = true;
    error = '';

    try {
      const formData = event.detail;
      
      if (!(formData instanceof FormData)) {
        throw new Error('Expected FormData object but received different data type');
      }
      
      // Debug what we're sending
      console.log("Sending property data to API...");
      for (let [key, value] of formData.entries()) {
        if (typeof value === 'string' && (key === 'location' || key === 'features' || 
            key === 'amenities' || key === 'rooms' || key === 'specifications' || 
            key === 'pricing_details' || key === 'highQualityStreets')) {
          console.log(`${key}: ${value.substring(0, 100)}${value.length > 100 ? '...' : ''}`);
        } else if (value instanceof File) {
          console.log(`${key}: File (${value.name}, ${value.size} bytes)`);
        } else {
          console.log(`${key}: ${value}`);
        }
      }
      
      const result = await createProperty(formData);
      
      if (result.success) {
        addToast('تم إضافة العقار بنجاح', 'success');
        goto('/properties/' + result.data.slug);
      } else {
        throw new Error(result.error || 'Failed to create property');
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
