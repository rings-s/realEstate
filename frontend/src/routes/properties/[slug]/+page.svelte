<!-- src/routes/properties/[slug]/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { fetchPropertyBySlug } from '$lib/services/properties';

  let property = null;
  let loading = true;
  let error = null;
  let activeImageIndex = 0;
  let showAllFeatures = false;
  let map = null;

  const { slug } = $page.params;

  async function loadProperty() {
    loading = true;
    error = null;

    try {
      const data = await fetchPropertyBySlug(slug);
      property = data;

      // Initialize map after data is loaded
      if (property && property.location?.latitude && property.location?.longitude) {
        initMap();
      }
    } catch (err) {
      error = err.message || 'حدث خطأ أثناء تحميل بيانات العقار';
      console.error(error);
    } finally {
      loading = false;
    }
  }

  function initMap() {
    if (!property || !property.location?.latitude || !property.location?.longitude) return;

    // Wait for Leaflet to be available
    if (typeof L === 'undefined') {
      setTimeout(initMap, 100);
      return;
    }

    if (!map) {
      map = L.map('property-map').setView(
        [property.location.latitude, property.location.longitude],
        15
      );

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(map);

      L.marker([property.location.latitude, property.location.longitude])
        .addTo(map)
        .bindPopup(property.title);
    }
  }

  onMount(() => {
    loadProperty();

    // Load Leaflet from CDN
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
    script.integrity = 'sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA==';
    script.crossOrigin = '';

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css';
    link.integrity = 'sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMAS6/keqq/sMZMZ19scR4PsZChSR7A==';
    link.crossOrigin = '';

    document.head.appendChild(link);
    document.body.appendChild(script);

    return () => {
      if (map) {
        map.remove();
        map = null;
      }
    };
  });
</script>

<svelte:head>
  <title>{property ? property.title : 'تحميل العقار...'} | منصة المزادات العقارية</title>
</svelte:head>

{#if loading}
  <div class="flex justify-center items-center h-64">
    <div class="text-center">
      <i class="fas fa-spinner fa-spin text-blue-600 text-3xl mb-4"></i>
      <p class="text-slate-500">جاري تحميل بيانات العقار...</p>
    </div>
  </div>
{:else if error}
  <div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
    <i class="fas fa-exclamation-circle text-red-500 mt-0.5 ml-3"></i>
    <div>
      <h3 class="font-medium text-red-800">حدث خطأ</h3>
      <p class="text-red-700 text-sm mt-1">{error}</p>
      <button on:click={loadProperty} class="text-red-700 font-medium text-sm mt-2 hover:underline">
        إعادة المحاولة
      </button>
    </div>
  </div>
{:else if property}
  <div>
    <!-- Back button -->
    <div class="mb-4">
      <a href="/properties" class="inline-flex items-center text-slate-600 hover:text-blue-600">
        <i class="fas fa-arrow-right ml-2"></i>
        العودة إلى العقارات
      </a>
    </div>

    <!-- Property header -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
      <div>
        <h1 class="text-3xl font-bold text-slate-900">{property.title}</h1>
        <p class="text-slate-600 mt-1 flex items-center">
          <i class="fas fa-map-marker-alt ml-2"></i>
          {property.address}, {property.city}
        </p>
      </div>

      <div class="flex flex-col items-end">
        <div class="text-2xl font-bold text-blue-600">
          {#if property.market_value}
            {property.market_value.toLocaleString()} ريال
          {:else}
            السعر عند الطلب
          {/if}
        </div>
        <div class="flex items-center mt-2">
          <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium {property.status === 'available' ? 'bg-green-100 text-green-800' : property.status === 'auction' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-800'}">
            {property.status_display}
          </span>
          {#if property.is_verified}
            <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 mr-2">
              <i class="fas fa-check-circle ml-1"></i>
              تم التحقق
            </span>
          {/if}
        </div>
      </div>
    </div>

    <!-- Gallery -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="md:col-span-2 relative rounded-lg overflow-hidden h-80">
        {#if property.media && property.media.length > 0}
          <img
            src={property.media[activeImageIndex]?.file_url || '/images/property-placeholder.jpg'}
            alt={property.title}
            class="w-full h-full object-cover"
          />

          {#if property.media.length > 1}
            <button
              class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white bg-opacity-70 flex items-center justify-center text-slate-700 hover:bg-opacity-100"
              on:click={() => {
                activeImageIndex = (activeImageIndex + 1) % property.media.length;
              }}
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <button
              class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white bg-opacity-70 flex items-center justify-center text-slate-700 hover:bg-opacity-100"
              on:click={() => {
                activeImageIndex = (activeImageIndex - 1 + property.media.length) % property.media.length;
              }}
            >
              <i class="fas fa-chevron-right"></i>
            </button>
          {/if}
        {:else}
          <div class="w-full h-full bg-slate-200 flex items-center justify-center">
            <i class="fas fa-home text-4xl text-slate-400"></i>
          </div>
        {/if}
      </div>

      <div class="grid grid-cols-2 gap-2 h-80 overflow-hidden">
        {#if property.media && property.media.length > 1}
          {#each property.media.slice(0, 4) as image, i}
            {#if i !== activeImageIndex}
              <button
                class="relative rounded-lg overflow-hidden hover:opacity-75 transition-opacity"
                on:click={() => (activeImageIndex = i)}
              >
                <img
                  src={image.file_url}
                  alt={property.title}
                  class="w-full h-full object-cover"
                />
              </button>
            {:else}
              <div class="relative rounded-lg overflow-hidden bg-blue-100 border-2 border-blue-500">
                <img
                  src={image.file_url}
                  alt={property.title}
                  class="w-full h-full object-cover opacity-50"
                />
                <div class="absolute inset-0 flex items-center justify-center">
                  <div class="bg-white bg-opacity-80 rounded-full w-8 h-8 flex items-center justify-center">
                    <i class="fas fa-check text-blue-500"></i>
                  </div>
                </div>
              </div>
            {/if}
          {/each}

          {#if property.media.length > 4}
            <button
              class="relative rounded-lg overflow-hidden bg-slate-800 text-white flex items-center justify-center text-sm font-medium"
              on:click={() => {
                // Logic to show all images in a gallery modal
              }}
            >
              +{property.media.length - 4} صورة أخرى
            </button>
          {/if}
        {:else}
          <div class="col-span-2 bg-slate-200 rounded-lg flex items-center justify-center">
            <p class="text-slate-500">لا توجد صور إضافية</p>
          </div>
        {/if}
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Property details -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-bold mb-4 text-slate-900">تفاصيل العقار</h2>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {#if property.property_type}
              <div class="text-center p-3 border rounded-lg">
                <div class="text-blue-600 mb-1">
                  <i class="fas fa-home text-xl"></i>
                </div>
                <div class="text-sm text-slate-500">نوع العقار</div>
                <div class="font-medium text-slate-800">{property.property_type_display}</div>
              </div>
            {/if}

            {#if property.size_sqm}
              <div class="text-center p-3 border rounded-lg">
                <div class="text-blue-600 mb-1">
                  <i class="fas fa-ruler-combined text-xl"></i>
                </div>
                <div class="text-sm text-slate-500">المساحة</div>
                <div class="font-medium text-slate-800">{property.size_sqm} م²</div>
              </div>
            {/if}

            {#if property.bedrooms}
              <div class="text-center p-3 border rounded-lg">
                <div class="text-blue-600 mb-1">
                  <i class="fas fa-bed text-xl"></i>
                </div>
                <div class="text-sm text-slate-500">غرف النوم</div>
                <div class="font-medium text-slate-800">{property.bedrooms}</div>
              </div>
            {/if}

            {#if property.bathrooms}
              <div class="text-center p-3 border rounded-lg">
                <div class="text-blue-600 mb-1">
                  <i class="fas fa-bath text-xl"></i>
                </div>
                <div class="text-sm text-slate-500">الحمامات</div>
                <div class="font-medium text-slate-800">{property.bathrooms}</div>
              </div>
            {/if}
          </div>

          <div class="prose max-w-none">
            <p>{property.description}</p>
          </div>
        </div>

        <!-- Features -->
        {#if property.features && property.features.length > 0}
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-bold mb-4 text-slate-900">المميزات</h2>

            <div class="grid grid-cols-2 md:grid-cols-3 gap-y-3">
              {#each showAllFeatures ? property.features : property.features.slice(0, 6) as feature}
                <div class="flex items-center">
                  <i class="fas fa-check-circle text-green-500 ml-2"></i>
                  <span>{feature}</span>
                </div>
              {/each}
            </div>

            {#if property.features.length > 6}
              <button
                class="mt-4 text-blue-600 hover:underline flex items-center"
                on:click={() => (showAllFeatures = !showAllFeatures)}
              >
                {#if showAllFeatures}
                  <i class="fas fa-chevron-up ml-1"></i>
                  عرض أقل
                {:else}
                  <i class="fas fa-chevron-down ml-1"></i>
                  عرض المزيد ({property.features.length - 6})
                {/if}
              </button>
            {/if}
          </div>
        {/if}

        <!-- Specifications -->
        {#if property.specifications && Object.keys(property.specifications).length > 0}
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-bold mb-4 text-slate-900">المواصفات</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              {#each Object.entries(property.specifications) as [key, value]}
                <div class="border-b pb-2">
                  <span class="text-slate-500">{key}:</span>
                  <span class="font-medium mr-2">{value}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Location Map -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-bold mb-4 text-slate-900">الموقع</h2>

          {#if property.location?.latitude && property.location?.longitude}
            <div id="property-map" class="h-96 rounded-lg border"></div>
          {:else}
            <div class="h-64 rounded-lg border bg-slate-100 flex items-center justify-center">
              <p class="text-slate-500">لا تتوفر بيانات موقع دقيقة لهذا العقار</p>
            </div>
          {/if}

          <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {#if property.city}
              <div>
                <span class="text-slate-500">المدينة:</span>
                <span class="font-medium mr-2">{property.city}</span>
              </div>
            {/if}

            {#if property.state}
              <div>
                <span class="text-slate-500">المنطقة/المحافظة:</span>
                <span class="font-medium mr-2">{property.state}</span>
              </div>
            {/if}

            {#if property.postal_code}
              <div>
                <span class="text-slate-500">الرمز البريدي:</span>
                <span class="font-medium mr-2">{property.postal_code}</span>
              </div>
            {/if}

            {#if property.country}
              <div>
                <span class="text-slate-500">الدولة:</span>
                <span class="font-medium mr-2">{property.country}</span>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Auction info if available -->
        {#if property.active_auction}
          <div class="bg-white rounded-lg shadow p-6 border-2 border-amber-400">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-xl font-bold text-slate-900">المزاد الحالي</h2>
              <span class="px-2 py-1 bg-amber-100 text-amber-800 rounded text-sm font-medium">
                {property.active_auction.status === 'live' ? 'مزاد نشط' : 'مزاد مجدول'}
              </span>
            </div>

            <div class="space-y-3 mb-4">
              <div class="flex justify-between">
                <span class="text-slate-500">المزايدة الحالية:</span>
                <span class="font-bold text-blue-600">
                  {property.active_auction.current_bid ? property.active_auction.current_bid.toLocaleString() + ' ريال' : 'لا توجد مزايدات'}
                </span>
              </div>

              <div class="flex justify-between">
                <span class="text-slate-500">تاريخ البدء:</span>
                <span class="font-medium">
                  {new Date(property.active_auction.start_date).toLocaleDateString('ar-SA')}
                </span>
              </div>

              <div class="flex justify-between">
                <span class="text-slate-500">تاريخ الإنتهاء:</span>
                <span class="font-medium">
                  {new Date(property.active_auction.end_date).toLocaleDateString('ar-SA')}
                </span>
              </div>
            </div>

            <a
              href={`/auctions/${property.active_auction.id}`}
              class="btn-primary w-full"
            >
              الذهاب إلى المزاد
            </a>
          </div>
        {/if}

        <!-- Contact owner/agent -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-bold mb-4 text-slate-900">تواصل مع المالك</h2>

          {#if property.owner_details}
            <div class="flex items-center mb-4">
              <img
                src={property.owner_details.avatar_url || '/images/default-avatar.jpg'}
                alt="صورة المالك"
                class="w-12 h-12 rounded-full object-cover border"
              />
              <div class="mr-3">
                <div class="font-medium">
                  {property.owner_details.first_name} {property.owner_details.last_name || ''}
                </div>
                <div class="text-sm text-slate-500">
                  {property.owner_details.primary_role?.name || 'مالك العقار'}
                </div>
              </div>
            </div>
          {/if}

          <div class="space-y-3 mb-4">
            {#if property.owner_details?.phone_number}
              <a href={`tel:${property.owner_details.phone_number}`} class="flex items-center text-slate-700 hover:text-blue-600">
                <i class="fas fa-phone ml-3 text-blue-600"></i>
                <span>{property.owner_details.phone_number}</span>
              </a>
            {/if}

            {#if property.owner_details?.email}
              <a href={`mailto:${property.owner_details.email}`} class="flex items-center text-slate-700 hover:text-blue-600">
                <i class="fas fa-envelope ml-3 text-blue-600"></i>
                <span>{property.owner_details.email}</span>
              </a>
            {/if}
          </div>

          <button class="btn-secondary w-full">
            <i class="fas fa-comment-alt ml-2"></i>
            إرسال رسالة
          </button>
        </div>

        <!-- Interested / Share -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex flex-col space-y-3">
            <button class="btn-primary">
              <i class="fas fa-star ml-2"></i>
              إضافة إلى المفضلة
            </button>

            <button class="btn-secondary">
              <i class="fas fa-share-alt ml-2"></i>
              مشاركة العقار
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Leaflet styles */
  :global(#property-map) {
    height: 400px;
    width: 100%;
  }
</style>
