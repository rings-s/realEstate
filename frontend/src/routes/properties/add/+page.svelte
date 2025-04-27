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
      
      // Validate required fields
      if (!propertyData.title) {
        throw new Error('عنوان العقار مطلوب');
      }
      if (!propertyData.property_type) {
        throw new Error('نوع العقار مطلوب');
      }
      if (!propertyData.city) {
        throw new Error('المدينة مطلوبة');
      }

      const result = await createProperty(propertyData);

      if (result.success) {
        addToast('تم إضافة العقار بنجاح', 'success');
        goto('/properties/' + result.data.slug);
      } else {
        throw new Error(result.error || 'فشل في إنشاء العقار');
      }
    } catch (err) {
      console.error('Property creation error:', err);
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