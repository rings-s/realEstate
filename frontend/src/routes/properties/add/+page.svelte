// src/routes/properties/add/+page.svelte

<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { hasPermission, isAuthenticated } from '$lib/stores/auth';
  import { addToast } from '$lib/stores/ui';
  import { createProperty } from '$lib/stores/properties';
  import PropertyForm from '$lib/components/property/PropertyForm.svelte';
  import Alert from '$lib/components/ui/Alert.svelte';

  let loading = false;
  let errorMessage = '';
  let canCreateProperty = false;

  onMount(() => {
    // Check if user can create properties
    canCreateProperty = isAuthenticated && hasPermission('create_property');

    if (!canCreateProperty) {
      errorMessage = 'ليس لديك صلاحية لإضافة عقار جديد. يرجى تسجيل الدخول كمالك أو وكيل عقاري.';
    }
  });

  async function handleSubmit(event) {
    const propertyData = event.detail;
    loading = true;

    try {
      console.log('Received property data object:', propertyData);

      // Call the API with the property data object, letting the store handle FormData and media files
      const result = await createProperty(propertyData);

      if (result.success) {
        addToast('تم إضافة العقار بنجاح', 'success');
        goto('/properties');
      } else {
        throw new Error(result.error || 'فشل في إنشاء العقار');
      }
    } catch (error) {
      console.error('Property creation error:', error);
      addToast(error.message || 'حدث خطأ أثناء إضافة العقار', 'error');
      
      // Format the error message for display
      errorMessage = error.message || 'حدث خطأ أثناء إضافة العقار، يرجى المحاولة مرة أخرى.';
      
      // Replace line breaks with <br> tags for proper display in Alert component
      if (errorMessage.includes('\n')) {
        const lines = errorMessage.split('\n');
        errorMessage = lines.join('<br>');
      }
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

  {#if errorMessage}
    <Alert type="error" message={errorMessage} dismissible={true} />
  {/if}

  {#if !canCreateProperty}
    <div class="rounded-xl bg-white p-8 shadow-sm">
      <div class="text-center">
        <div class="mb-4 text-amber-500">
          <i class="fas fa-exclamation-triangle text-5xl"></i>
        </div>
        <h1 class="text-2xl font-bold text-slate-900">لا يمكنك إضافة عقار</h1>
        <p class="mt-2 mb-6 text-slate-600">
          يجب أن تكون مسجلاً كمالك عقار أو وكيل عقاري ومفعلاً للحساب لإضافة عقار جديد.
        </p>

        <div class="flex justify-center gap-4">
          <a href="/login" class="btn-primary">
            <i class="fas fa-sign-in-alt ml-2"></i>
            تسجيل الدخول
          </a>
          <a href="/register" class="btn-secondary">
            <i class="fas fa-user-plus ml-2"></i>
            إنشاء حساب جديد
          </a>
        </div>
      </div>
    </div>
  {:else}
    <div class="rounded-xl bg-white shadow-sm">
      <div class="border-b p-6">
        <h1 class="text-2xl font-bold text-slate-900">إضافة عقار جديد</h1>
        <p class="mt-1 text-slate-600">قم بإدخال بيانات العقار بشكل كامل</p>
      </div>

      <div class="p-6">
        <PropertyForm {loading} on:submit={handleSubmit} />
      </div>
    </div>
  {/if}
</div>