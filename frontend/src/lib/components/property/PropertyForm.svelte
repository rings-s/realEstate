<!-- src/lib/components/property/PropertyForm.svelte -->
<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import PropertyMap from './PropertyMap.svelte';
  import RoomEditor from './RoomEditor.svelte';

  export let initialData = null;
  export let loading = false;

  // Initialize form data with all model fields
  let formData = {
    title: '',
    property_type: 'residential',
    description: '',
    status: 'available',
    deed_number: '',

    // Location
    location: {
      latitude: null,
      longitude: null,
      city: '',
      address: '',
      state: '',
      postal_code: '',
      country: 'المملكة العربية السعودية'
    },
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'المملكة العربية السعودية',
    highQualityStreets: [],

    // Property details
    features: [],
    amenities: [],
    rooms: [],
    specifications: {},
    size_sqm: '',
    bedrooms: '',
    bathrooms: '',
    floors: '',
    parking_spaces: '',
    year_built: new Date().getFullYear(),

    // Financial
    market_value: '',
    minimum_bid: '',
    pricing_details: {},

    // Status
    is_published: false,
    is_featured: false,
    is_verified: false,

    // Media
    media: [],

    // Additional metadata
    metadata: {}
  };

  // Form steps
  const steps = [
    {
      id: 1,
      title: 'المعلومات الأساسية',
      icon: 'fas fa-info-circle',
      fields: ['title', 'property_type', 'description', 'deed_number', 'status']
    },
    {
      id: 2,
      title: 'الموقع والعنوان',
      icon: 'fas fa-map-marker-alt',
      fields: ['location', 'address', 'city', 'state', 'postal_code', 'highQualityStreets']
    },
    {
      id: 3,
      title: 'تفاصيل العقار',
      icon: 'fas fa-building',
      fields: ['size_sqm', 'bedrooms', 'bathrooms', 'floors', 'parking_spaces', 'year_built', 'specifications']
    },
    {
      id: 4,
      title: 'المميزات والمرافق',
      icon: 'fas fa-list',
      fields: ['features', 'amenities', 'rooms']
    },
    {
      id: 5,
      title: 'التسعير',
      icon: 'fas fa-money-bill',
      fields: ['market_value', 'minimum_bid', 'pricing_details']
    },
    {
      id: 6,
      title: 'الصور والمرفقات',
      icon: 'fas fa-images',
      fields: ['media']
    }
  ];

  let currentStep = 1;
  let errors = {};
  let uploadedImages = [];
  let detectingLocation = false;

  // Property types
  const propertyTypes = [
    { value: 'residential', label: 'سكني', icon: 'home' },
    { value: 'commercial', label: 'تجاري', icon: 'store' },
    { value: 'land', label: 'أرض', icon: 'map' },
    { value: 'industrial', label: 'صناعي', icon: 'industry' },
    { value: 'mixed_use', label: 'متعدد الاستخدام', icon: 'building' }
  ];

  // Cities
  const cityOptions = [
    'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة',
    'الدمام', 'الخبر', 'الظهران', 'تبوك', 'أبها'
  ];

  onMount(() => {
    if (initialData) {
      formData = { ...formData, ...initialData };
    }
  });

  // Step validation
  function validateStep(step) {
    const stepFields = steps[step - 1].fields;
    errors = {};

    stepFields.forEach(field => {
      // Required fields validation
      if (['title', 'property_type', 'description', 'deed_number', 'address', 'city'].includes(field)) {
        if (!formData[field]?.trim()) {
          errors[field] = `${field} مطلوب`;
        }
      }

      // Numeric fields validation
      if (['size_sqm', 'bedrooms', 'bathrooms', 'floors', 'parking_spaces', 'market_value', 'minimum_bid'].includes(field)) {
        if (formData[field] && isNaN(parseFloat(formData[field]))) {
          errors[field] = 'يجب أن يكون رقماً';
        }
      }

      // Location validation
      if (field === 'location' && currentStep === 2) {
        if (!formData.location.latitude || !formData.location.longitude) {
          errors.location = 'يرجى تحديد الموقع على الخريطة';
        }
      }

      // Media validation
      if (field === 'media' && currentStep === 6) {
        if (uploadedImages.length === 0) {
          errors.media = 'يرجى إضافة صورة واحدة على الأقل';
        }
      }
    });

    return Object.keys(errors).length === 0;
  }

  // Navigation
  function handleStep(direction) {
    if (direction === 'next') {
      if (!validateStep(currentStep)) return;
      if (currentStep < steps.length) currentStep++;
    } else {
      if (currentStep > 1) currentStep--;
    }
  }

  // Location detection
  async function detectLocation() {
    detectingLocation = true;
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });

      formData.location = {
        ...formData.location,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude
      };

      // Trigger reverse geocoding if needed
      await updateAddressFromCoordinates(position.coords.latitude, position.coords.longitude);
    } catch (error) {
      errors.location = 'فشل في تحديد الموقع الحالي';
    } finally {
      detectingLocation = false;
    }
  }

  // Image handling
  async function handleImageUpload(event) {
    const files = Array.from(event.target.files);
    
    for (const file of files) {
      if (file.size > 5 * 1024 * 1024) {
        errors.media = 'حجم الملف يتجاوز 5 ميجابايت';
        continue;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        uploadedImages = [
          ...uploadedImages,
          { file, preview: e.target.result }
        ];
      };
      reader.readAsDataURL(file);
    }
  }

  function removeImage(index) {
    uploadedImages = uploadedImages.filter((_, i) => i !== index);
  }

  // Form submission
  function handleSubmit() {
    if (!validateStep(currentStep)) return;

    const finalData = {
      ...formData,
      media: uploadedImages.map(img => img.file)
    };

    dispatch('submit', finalData);
  }
</script>

<div class="mb-8">
	<div class="flex justify-between">
	    {#each steps as step, i}
			<div class="relative flex flex-1 flex-col items-center">
		  <div
			class="flex h-12 w-12 items-center justify-center rounded-full border-2 {currentStep > i + 1
			  ? 'border-green-600 bg-green-600 text-white'
			  : currentStep === i + 1
			  ? 'border-blue-600 bg-blue-600 text-white'
			  : 'border-slate-200 bg-white text-slate-400'}"
		  >
			<i class="{step.icon} text-lg"></i>
		  </div>
		  <span
			class="mt-2 text-center text-sm font-medium {currentStep > i + 1
			  ? 'text-green-600'
			  : currentStep === i + 1
			  ? 'text-blue-600'
			  : 'text-slate-500'}"
		  >
			{step.title}
		  </span>
			</div>
   
			{#if i < steps.length - 1}
				<div
				class="relative top-6 h-0.5 flex-1 {currentStep > i + 1
				? 'bg-green-600'
				: 'bg-slate-200'}"
				>
				</div>
			{/if}
		{/each}
	</div>
</div>
   
<form>
	<div class="mt-12">
	  {#if currentStep === 1}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <div class="space-y-6">
			<!-- Basic Information Fields -->
			<div class="form-group">
			  <label class="label required">عنوان العقار</label>
			  <input
				type="text"
				class="input {errors.title ? 'border-red-500' : ''}"
				bind:value={formData.title}
				placeholder="أدخل عنواناً مميزاً للعقار"
			  />
			  {#if errors.title}
				<span class="text-sm text-red-500">{errors.title}</span>
			  {/if}
			</div>
   
			<div class="form-group">
			  <label class="label required">نوع العقار</label>
			  <select
				class="input {errors.property_type ? 'border-red-500' : ''}"
				bind:value={formData.property_type}
			  >
				{#each propertyTypes as type}
				  <option value={type.value}>{type.label}</option>
				{/each}
			  </select>
			  {#if errors.property_type}
				<span class="text-sm text-red-500">{errors.property_type}</span>
			  {/if}
			</div>
   
			<!-- Description -->
			<div class="mt-6">
			  <label for="description" class="mb-1 block text-sm font-medium text-slate-700">الوصف</label>
			  <textarea
				id="description"
				bind:value={formData.description}
				rows="4"
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.description ? 'border-red-500' : ''}"
				placeholder="أدخل وصفاً مفصلاً للعقار..."
			  />
			  {#if errors.description}
				<p class="mt-1 text-sm text-red-600">{errors.description}</p>
			  {/if}
			</div>
   
			<!-- Additional optional fields -->
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			  <div class="form-group">
				<label class="label">المساحة (متر مربع)</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.size_sqm}
				  placeholder="المساحة"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">السعر المتوقع</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.market_value}
				  placeholder="السعر بالريال"
				  min="0"
				/>
			  </div>
			</div>
		  </div>
		</div>
   
	  {#if currentStep === 2}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <!-- Location Fields -->
		  <div class="space-y-4">
			<!-- Address -->
			<div>
			  <label for="address" class="mb-1 block text-sm font-medium text-slate-700">العنوان</label>
			  <input
				type="text"
				id="address"
				bind:value={formData.address}
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.address ? 'border-red-500' : ''}"
				placeholder="مثال: شارع الملك فهد، حي العليا"
			  />
			  {#if errors.address}
				<p class="mt-1 text-sm text-red-600">{errors.address}</p>
			  {/if}
			</div>
   
			<!-- Location detection -->
			<div class="flex gap-4">
			  <button
				type="button"
				class="btn flex-1 bg-blue-600 text-white hover:bg-blue-700"
				on:click={detectLocation}
				disabled={detectingLocation}>
				{#if detectingLocation}
				  <i class="fas fa-spinner fa-spin ml-2"></i>
				  جاري تحديد الموقع...
				{:else}
				  <i class="fas fa-map-marker-alt ml-2"></i>
				  تحديد موقعي الحالي
				{/if}
			  </button>
			</div>
   
			<!-- Map Component -->
			<PropertyMap
			  bind:latitude={formData.location.latitude}
			  bind:longitude={formData.location.longitude}
			  editable={true}
			/>
   
			<!-- City -->
			<div>
			  <label for="city" class="mb-1 block text-sm font-medium text-slate-700">المدينة</label>
			  <select
				id="city"
				bind:value={formData.city}
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.city ? 'border-red-500' : ''}"
			  >
				<option value="" disabled>اختر مدينة</option>
				{#each cityOptions as city}
				  <option value={city}>{city}</option>
				{/each}
			  </select>
			  {#if errors.city}
				<p class="mt-1 text-sm text-red-600">{errors.city}</p>
			  {/if}
			</div>
   
			<!-- State -->
			<div>
			  <label for="state" class="mb-1 block text-sm font-medium text-slate-700">المنطقة</label>
			  <input
				type="text"
				id="state"
				bind:value={formData.state}
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.state ? 'border-red-500' : ''}"
				placeholder="مثال: منطقة الرياض"
			  />
			  {#if errors.state}
				<p class="mt-1 text-sm text-red-600">{errors.state}</p>
			  {/if}
			</div>
   
			<!-- Postal Code -->
			<div>
			  <label for="postal_code" class="mb-1 block text-sm font-medium text-slate-700">الرمز البريدي</label>
			  <input
				type="text"
				id="postal_code"
				bind:value={formData.postal_code}
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.postal_code ? 'border-red-500' : ''}"
				placeholder="مثال: 11564"
			  />
			</div>
   
			<!-- Deed Number -->
			<div>
			  <label for="deed_number" class="mb-1 block text-sm font-medium text-slate-700">رقم الصك</label>
			  <input
				type="text"
				id="deed_number"
				bind:value={formData.deed_number}
				class="w-full rounded-md border border-slate-300 p-2 focus:border-blue-500 focus:ring-blue-500 {errors.deed_number ? 'border-red-500' : ''}"
				placeholder="أدخل رقم الصك"
			  />
			  {#if errors.deed_number}
				<p class="mt-1 text-sm text-red-600">{errors.deed_number}</p>
			  {/if}
			</div>
		  </div>
		</div>
	  {/if}
   
	  {#if currentStep === 3}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <!-- Property Details -->
		  <div class="space-y-6">
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			  <div class="form-group">
				<label class="label">المساحة (متر مربع)</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.size_sqm}
				  placeholder="أدخل المساحة"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">عدد غرف النوم</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.bedrooms}
				  placeholder="عدد الغرف"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">عدد دورات المياه</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.bathrooms}
				  placeholder="عدد دورات المياه"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">عدد الطوابق</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.floors}
				  placeholder="عدد الطوابق"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">مواقف السيارات</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.parking_spaces}
				  placeholder="عدد المواقف"
				  min="0"
				/>
			  </div>
   
			  <div class="form-group">
				<label class="label">سنة البناء</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.year_built}
				  placeholder="سنة البناء"
				  min="1900"
				  max={new Date().getFullYear()}
				/>
			  </div>
			</div>
   
			<!-- Specifications -->
			<div class="mt-6">
			  <h3 class="mb-4 text-lg font-semibold">المواصفات</h3>
			  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
				{#each specificationsFields as field}
				  <div class="form-group">
					<label class="label">{field.label}</label>
					<select
					  class="input"
					  bind:value={formData.specifications[field.key]}>
					  <option value="">{field.placeholder}</option>
					  {#each field.options as option}
						<option value={option.value}>{option.label}</option>
					  {/each}
					</select>
				  </div>
				{/each}
			  </div>
			</div>
		  </div>
		</div>
	  {/if}
   
	  {#if currentStep === 4}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <!-- Features and Amenities -->
		  <div class="space-y-6">
			<!-- Features -->
			<div class="form-group">
			  <label class="label">المميزات</label>
			  <div class="flex gap-2">
				<input
				  type="text"
				  class="input flex-1"
				  bind:value={newFeature}
				  placeholder="أضف ميزة جديدة"
				  on:keydown={(e) => e.key === 'Enter' && addFeature()}
				/>
				<button type="button" class="btn-primary" on:click={addFeature}>
				  إضافة
				</button>
			  </div>
			  <div class="mt-2 flex flex-wrap gap-2">
				{#each formData.features as feature, i}
				  <span class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-blue-700">
					{feature}
					<button
					  type="button"
					  class="ml-2 text-blue-400 hover:text-blue-600"
					  on:click={() => removeFeature(i)}
					>
					  <i class="fas fa-times"></i>
					</button>
				  </span>
				{/each}
			  </div>
			</div>
   
			<!-- Amenities -->
			<div class="form-group">
			  <label class="label">المرافق</label>
			  <div class="flex gap-2">
				<input
				  type="text"
				  class="input flex-1"
				  bind:value={newAmenity}
				  placeholder="أضف مرفق جديد"
				  on:keydown={(e) => e.key === 'Enter' && addAmenity()}
				/>
				<button type="button" class="btn-primary" on:click={addAmenity}>
				  إضافة
				</button>
			  </div>
			  <div class="mt-2 flex flex-wrap gap-2">
				{#each formData.amenities as amenity, i}
				  <span class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-blue-700">
					{amenity}
					<button
					  type="button"
					  class="ml-2 text-blue-400 hover:text-blue-600"
					  on:click={() => removeAmenity(i)}
					>
					  <i class="fas fa-times"></i>
					</button>
				  </span>
				{/each}
			  </div>
			</div>
   
			<!-- Rooms -->
			<RoomEditor bind:rooms={formData.rooms} />
		  </div>
		</div>
	  {/if}
   
	  {#if currentStep === 5}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <!-- Pricing -->
		  <div class="space-y-6">
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			  <div class="form-group">
				<label class="label required">القيمة السوقية</label>
				<input
				  type="number"
				  class="input {errors.market_value ? 'border-red-500' : ''}"
				  bind:value={formData.market_value}
				  placeholder="أدخل القيمة السوقية"
				  min="0"
				/>
				{#if errors.market_value}
				  <span class="text-sm text-red-500">{errors.market_value}</span>
				{/if}
			  </div>
   
			  <div class="form-group">
				<label class="label">الحد الأدنى للمزايدة</label>
				<input
				  type="number"
				  class="input"
				  bind:value={formData.minimum_bid}
				  placeholder="أدخل الحد الأدنى للمزايدة"
				  min="0"
				/>
			  </div>
			</div>
   
			<!-- Pricing Details -->
			<div class="form-group">
			  <label class="label">تفاصيل التسعير</label>
			  <div class="rounded-lg border border-slate-200 p-4 space-y-4">
				<div class="form-group">
				  <label class="label">طريقة التقييم</label>
				  <select
					class="input"
					bind:value={formData.pricing_details.valuation_method}>
					<option value="">اختر طريقة التقييم</option>
					<option value="market">تقييم سوقي</option>
					<option value="income">تقييم الدخل</option>
					<option value="cost">تقييم التكلفة</option>
				  </select>
				</div>
   
				<div class="form-group">
				  <label class="label">ملاحظات التسعير</label>
				  <textarea
					class="input"
					bind:value={formData.pricing_details.notes}
					placeholder="أضف ملاحظات حول التسعير"
					rows="3"
				  ></textarea>
				</div>
			  </div>
			</div>
		  </div>
		</div>
	  {/if}
   
	  {#if currentStep === 6}
		<div in:fly={{ y: 20, duration: 300 }} out:fade>
		  <!-- Media -->
		  <div class="space-y-6">
			<div class="form-group">
			  <label class="label required">صور العقار</label>
			  <div
				class="rounded-lg border-2 border-dashed border-slate-300 p-6 text-center hover:border-blue-500 transition-colors relative
				  {errors.media ? 'border-red-500' : ''}"
			  >
				<input
				  type="file"
				  accept="image/*"
				  multiple
				  class="hidden"
				  on:change={handleImageUpload}
				  id="property-images"
				/>
				<label for="property-images" class="cursor-pointer block">
				  <i class="fas fa-cloud-upload-alt text-4xl text-slate-400 mb-2"></i>
				  <p class="text-slate-600">اسحب الصور هنا أو انقر للاختيار</p>
				  <p class="text-slate-500 text-sm mt-1">الحد الأقصى 5 ميجابايت للصورة</p>
				</label>
			  </div>
			  {#if errors.media}
				<span class="text-sm text-red-500">{errors.media}</span>
			  {/if}
			</div>
   
			{#if uploadedImages.length > 0}
			  <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
				{#each uploadedImages as image, i}
				  <div class="relative group">
					<img
					  src={image.preview}
					  alt=""
					  class="w-full h-40 object-cover rounded-lg"
					/>
					<button
					  type="button"
					  class="absolute top-2 right-2 h-8 w-8 rounded-full bg-red-500 text-white opacity-0 group-hover:opacity-100 transition-opacity"
					  on:click={() => removeImage(i)}
					>
					  <i class="fas fa-times"></i>
					</button>
					{#if i === 0}
					  <div class="absolute top-2 left-2 bg-blue-500 rounded px-2 py-1 text-white text-xs">
						الصورة الرئيسية
					  </div>
					{/if}
				  </div>
				{/each}
			  </div>
			{/if}
   
			<!-- Publishing Settings -->
			<div class="mt-6 border border-slate-200 rounded-lg p-4 space-y-4">
			  <div class="flex items-center justify-between">
				<div>
				  <label class="label mb-0">نشر العقار</label>
				  <p class="text-sm text-slate-500">اجعل العقار متاحاً للمشاهدة</p>
				</div>
				<div class="relative inline-block w-12 select-none">
				  <input
					type="checkbox"
					class="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
					bind:checked={formData.is_published}
				  />
				  <div class="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300"></div>
				</div>
			  </div>
   
			  <div class="flex items-center justify-between">
				<div>
				  <label class="label mb-0">عقار مميز</label>
				  <p class="text-sm text-slate-500">عرض العقار في القائمة المميزة</p>
				</div>
				<div class="relative inline-block w-12 select-none">
				  <input
					type="checkbox"
					class="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
					bind:checked={formData.is_featured}
				  />
				  <div class="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300"></div>
				</div>
			  </div>
			</div>
		  </div>
		</div>
	  {/if}
   
	  <!-- Navigation Buttons -->
	  <div class="mt-8 flex justify-between">
		{#if currentStep > 1}
		  <button
			type="button"
			class="btn-secondary"
			on:click={() => handleStep('prev')}>
			<i class="fas fa-arrow-right ml-2"></i>
			السابق
		  </button>
		{:else}
		  <div></div>
		{/if}
   
		{#if currentStep < steps.length}
		  <button
			type="button"
			class="btn-primary"
			on:click={() => handleStep('next')}>
			التالي
			<i class="fas fa-arrow-left mr-2"></i>
		  </button>
		{:else}
		  <button
			type="submit"
			class="btn-primary"
			disabled={loading}
			on:click|preventDefault={handleSubmit}>
			{loading ? 'جاري الحفظ...' : 'حفظ العقار'}
			<i class="fas fa-save mr-2"></i>
		  </button>
		{/if}
	  </div>
	</div>
</form>
   
<style>
	.label {
	  @apply mb-1 block text-sm font-medium text-slate-700;
	}
   
	.label.required::after {
	  content: '*';
	  @apply mr-1 text-red-500;
	}
   
	.input {
	  @apply w-full rounded-md border border-slate-300 px-3 py-2 focus:border-blue-500 focus:ring-blue-500;
	}
   
	.btn-primary {
	  @apply flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50;
	}
   
	.btn-secondary {
	  @apply flex items-center justify-center px-4 py-2 border border-slate-300 text-slate-700 bg-white rounded-md hover:bg-slate-50;
	}
   
	/* Toggle Checkbox Styles */
	.toggle-checkbox:checked {
	  @apply right-0 border-blue-600;
	}
	.toggle-checkbox:checked + .toggle-label {
	  @apply bg-blue-600;
	}
</style>