<!-- src/lib/components/property/PropertyForm.svelte -->
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import PropertyMap from './PropertyMap.svelte';
	import RoomEditor from './RoomEditor.svelte';
	import { addToast } from '$lib/stores/ui';
	import { createEventDispatcher } from 'svelte';
  
	export let initialData = null;
	export let loading = false;
  
	const dispatch = createEventDispatcher();
  
	// Form state
	let formData = {
	  title: '',
	  property_type: 'residential',
	  description: '',
	  status: 'available',
	  deed_number: '',
	  location: {
		latitude: null,
		longitude: null,
	  },
	  address: '',
	  city: '',
	  state: '',
	  postal_code: '',
	  country: 'المملكة العربية السعودية',
	  highQualityStreets: [],
	  features: [],
	  amenities: [], // Added amenities array
	  rooms: [],
	  specifications: {},
	  size_sqm: '',
	  bedrooms: '',
	  bathrooms: '',
	  floors: '',
	  parking_spaces: '',
	  year_built: new Date().getFullYear(),
	  market_value: '',
	  minimum_bid: '',
	  pricing_details: {
		valuation_method: '',
		notes: ''
	  },
	  is_published: false,
	  is_featured: false,
	  is_verified: false,
	  media: [],
	  metadata: {}
	};
  
	// Available property types
	const propertyTypes = [
	  { value: 'residential', label: 'سكني', icon: 'home' },
	  { value: 'commercial', label: 'تجاري', icon: 'store' },
	  { value: 'land', label: 'أرض', icon: 'map' },
	  { value: 'industrial', label: 'صناعي', icon: 'industry' },
	  { value: 'mixed_use', label: 'متعدد الاستخدام', icon: 'building' }
	];
  
	// Major cities
	const cityOptions = [
	  'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة',
	  'الدمام', 'الخبر', 'الظهران', 'تبوك', 'أبها'
	];
  
	// Specifications fields
	const specificationsFields = [
	  {
		key: 'finishing_type',
		label: 'نوع التشطيب',
		placeholder: 'اختر نوع التشطيب',
		options: [
		  { value: 'luxury', label: 'فاخر' },
		  { value: 'standard', label: 'قياسي' },
		  { value: 'basic', label: 'أساسي' }
		]
	  },
	  {
		key: 'view',
		label: 'الإطلالة',
		placeholder: 'اختر الإطلالة',
		options: [
		  { value: 'sea', label: 'بحر' },
		  { value: 'city', label: 'مدينة' },
		  { value: 'garden', label: 'حديقة' },
		  { value: 'street', label: 'شارع' }
		]
	  },
	  {
		key: 'age',
		label: 'عمر العقار',
		placeholder: 'اختر عمر العقار',
		options: [
		  { value: 'new', label: 'جديد' },
		  { value: '0-5', label: '0-5 سنوات' },
		  { value: '6-10', label: '6-10 سنوات' },
		  { value: '10+', label: 'أكثر من 10 سنوات' },
		]
	  }
	];
  
	// Common amenities
	const commonAmenities = [
	  { id: 'pool', label: 'مسبح' },
	  { id: 'gym', label: 'صالة رياضية' },
	  { id: 'garden', label: 'حديقة' },
	  { id: 'security', label: 'حراسة أمنية' },
	  { id: 'elevator', label: 'مصعد' },
	  { id: 'parking', label: 'موقف سيارات' },
	  { id: 'central_ac', label: 'تكييف مركزي' },
	  { id: 'mosque', label: 'مسجد قريب' },
	  { id: 'playground', label: 'منطقة ألعاب أطفال' },
	  { id: 'wifi', label: 'شبكة واي فاي' }
	];
  
	// Form state management
	let currentStep = 1;
	let errors = {};
	let uploadedImages = [];
	let detectingLocation = false;
	let newFeature = '';
	let newAmenity = '';
  
	// Location detection
	async function detectLocation() {
	  detectingLocation = true;
	  errors.location = '';
  
	  try {
		if (!navigator.geolocation) {
		  throw new Error('المتصفح لا يدعم تحديد الموقع');
		}
  
		const position = await new Promise((resolve, reject) => {
		  navigator.geolocation.getCurrentPosition(resolve, reject, {
			enableHighAccuracy: true,
			timeout: 10000,
			maximumAge: 0
		  });
		});
  
		formData.location.latitude = position.coords.latitude;
		formData.location.longitude = position.coords.longitude;
  
		// Attempt Reverse Geocoding
		try {
		  const response = await fetch(
			`https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}&accept-language=ar&addressdetails=1`
		  );
  
		  if (!response.ok) {
			throw new Error(`فشل في الحصول على العنوان (HTTP ${response.status})`);
		  }
  
		  const data = await response.json();
  
		  if (data && data.address) {
			formData.address = data.display_name || formData.address;
			formData.city = data.address.city || data.address.town || data.address.village || formData.city || '';
			formData.state = data.address.state || formData.state || '';
			formData.postal_code = data.address.postcode || formData.postal_code || '';
			formData.country = data.address.country || formData.country;
			addToast('تم تحديد الموقع والعنوان بنجاح', 'success');
		  } else {
			addToast('تم تحديد الموقع ولكن لم يتم العثور على تفاصيل العنوان', 'warning');
		  }
		} catch (geoError) {
		  console.error('Reverse geocoding failed:', geoError);
		  addToast(`تم تحديد الموقع ولكن فشل في الحصول على العنوان: ${geoError.message}`, 'warning');
		}
  
	  } catch (error) {
		console.error('Location detection error:', error);
		let errorMsg = 'فشل في تحديد الموقع الحالي';
		if (error.code) {
		  if (error.code === 1) errorMsg = 'تم رفض إذن تحديد الموقع من المتصفح';
		  else if (error.code === 2) errorMsg = 'فشل في تحديد الموقع (مشكلة بالشبكة أو الأقمار الصناعية)';
		  else if (error.code === 3) errorMsg = 'انتهت مهلة تحديد الموقع';
		} else if (error.message) {
		  errorMsg = error.message;
		}
		errors.location = errorMsg;
		addToast(errorMsg, 'error');
	  } finally {
		detectingLocation = false;
	  }
	}
  
	// Image handling
	function handleImageUpload(event) {
	  const files = Array.from(event.target.files);
	  errors.media = '';
  
	  for (const file of files) {
		if (!file.type.startsWith('image/')) {
		  addToast(`الملف "${file.name}" ليس صورة صالحة.`, 'error');
		  continue;
		}
		if (file.size > 5 * 1024 * 1024) {
		  addToast(`حجم الصورة "${file.name}" يتجاوز 5 ميجابايت`, 'error');
		  continue;
		}
  
		const reader = new FileReader();
		reader.onload = (e) => {
		  if (!uploadedImages.some(img => img.file.name === file.name && img.file.size === file.size)) {
			uploadedImages = [
			  ...uploadedImages,
			  { file, preview: e.target.result }
			];
		  }
		};
		reader.onerror = () => {
		  addToast(`فشل في قراءة الملف "${file.name}"`, 'error');
		};
		reader.readAsDataURL(file);
	  }
	  event.target.value = null;
	}
  
	function removeImage(index) {
	  uploadedImages = uploadedImages.filter((_, i) => i !== index);
	}
  
	// Features handling
	function addFeature() {
	  const featureToAdd = newFeature.trim();
	  if (featureToAdd && !formData.features.includes(featureToAdd)) {
		formData.features = [...formData.features, featureToAdd];
		newFeature = '';
	  } else if (formData.features.includes(featureToAdd)) {
		addToast('هذه الميزة مضافة بالفعل', 'info');
	  }
	}
  
	function removeFeature(index) {
	  formData.features = formData.features.filter((_, i) => i !== index);
	}
  
	// Amenities handling
	function addAmenity() {
	  const amenityToAdd = newAmenity.trim();
	  if (amenityToAdd && !formData.amenities.includes(amenityToAdd)) {
		formData.amenities = [...formData.amenities, amenityToAdd];
		newAmenity = '';
	  } else if (formData.amenities.includes(amenityToAdd)) {
		addToast('هذا المرفق مضاف بالفعل', 'info');
	  }
	}
  
	function removeAmenity(index) {
	  formData.amenities = formData.amenities.filter((_, i) => i !== index);
	}
  
	function toggleAmenity(amenity) {
	  const index = formData.amenities.indexOf(amenity);
	  if (index === -1) {
		formData.amenities = [...formData.amenities, amenity];
	  } else {
		formData.amenities = formData.amenities.filter(a => a !== amenity);
	  }
	}
  
	// Form steps definition
	const steps = [
	  { id: 1, title: 'المعلومات الأساسية', icon: 'fas fa-info-circle', fields: ['title', 'property_type', 'description', 'deed_number', 'status'] },
	  { id: 2, title: 'الموقع والعنوان', icon: 'fas fa-map-marker-alt', fields: ['location', 'address', 'city', 'state', 'postal_code'] },
	  { id: 3, title: 'تفاصيل العقار', icon: 'fas fa-building', fields: ['size_sqm', 'bedrooms', 'bathrooms', 'floors', 'parking_spaces', 'year_built', 'specifications'] },
	  { id: 4, title: 'المميزات والمرافق', icon: 'fas fa-list', fields: ['features', 'amenities', 'rooms'] },
	  { id: 5, title: 'التسعير', icon: 'fas fa-money-bill', fields: ['market_value', 'minimum_bid', 'pricing_details'] },
	  { id: 6, title: 'الصور والنشر', icon: 'fas fa-images', fields: ['media', 'is_published', 'is_featured'] }
	];
  
	function validateStep(step) {
	  const currentFields = steps[step - 1].fields;
	  errors = {};
  
	  currentFields.forEach(field => {
		// General required fields check
		if (['title', 'property_type', 'description'].includes(field) && !formData[field]?.trim()) {
		  errors[field] = `هذا الحقل مطلوب`;
		}
  
		// Step-specific validation
		if (step === 2) {
		  // Location object validation
		  if (field === 'location' && (!formData.location.latitude || !formData.location.longitude)) {
			// Check if address/city were filled manually instead
			if (!formData.address?.trim() || !formData.city?.trim()) {
			  errors.location = 'يرجى تحديد الموقع على الخريطة أو إدخال العنوان والمدينة';
			}
		  }
		  // Address fields validation
		  if (field === 'city' && !formData.city?.trim()) {
			errors.city = 'يرجى اختيار أو إدخال المدينة';
		  }
		  if (field === 'address' && !formData.address?.trim()) {
			errors.address = 'يرجى إدخال العنوان التفصيلي';
		  }
		} else if (step === 3) {
		  if (field === 'size_sqm' && (formData.size_sqm === '' || formData.size_sqm == null || parseFloat(formData.size_sqm) <= 0)) {
			errors.size_sqm = 'يرجى إدخال مساحة صحيحة (أكبر من 0)';
		  }
		  if (field === 'year_built' && formData.year_built && (parseInt(formData.year_built) < 1800 || parseInt(formData.year_built) > new Date().getFullYear() + 1)) {
			errors.year_built = `سنة البناء يجب أن تكون بين 1800 و ${new Date().getFullYear() + 1}`;
		  }
		  // Validate number inputs are not negative
		  ['bedrooms', 'bathrooms', 'floors', 'parking_spaces'].forEach(numField => {
			if (field === numField && formData[numField] !== '' && formData[numField] != null && parseInt(formData[numField]) < 0) {
			  errors[numField] = 'القيمة يجب أن تكون صفر أو أكبر';
			}
		  });
		} else if (step === 5) {
		  // Pricing validation
		  if (field === 'market_value' && (formData.market_value === '' || formData.market_value == null || parseFloat(formData.market_value) <= 0)) {
			errors.market_value = 'يرجى إدخال القيمة السوقية (أكبر من 0)';
		  }
		  if (field === 'minimum_bid' && formData.minimum_bid !== '' && formData.minimum_bid != null && parseFloat(formData.minimum_bid) < 0) {
			errors.minimum_bid = 'الحد الأدنى للمزايدة لا يمكن أن يكون سالباً';
		  }
		}
	  });
  
	  // Image validation (Step 6)
	  if (step === 6 && uploadedImages.length === 0) {
		errors.media = 'يرجى إضافة صورة واحدة على الأقل';
	  }
  
	  const isValid = Object.keys(errors).length === 0;
	  if (!isValid) {
		console.log("Validation Errors:", errors);
	  }
	  return isValid;
	}
  
	// Handle step navigation
	function handleStepChange(direction) {
	  if (direction === 'next') {
		if (!validateStep(currentStep)) {
		  addToast('يرجى تصحيح الأخطاء أو إكمال الحقول المطلوبة للمتابعة', 'error');
		  errors = { ...errors };
		  return;
		}
		if (currentStep < steps.length) {
		  currentStep++;
		  errors = {};
		}
	  } else {
		if (currentStep > 1) {
		  currentStep--;
		  errors = {};
		}
	  }
	  window.scrollTo({ top: 0, behavior: 'smooth' });
	}
  
	// Initialize form data if initialData is provided
	onMount(() => {
	  if (initialData) {
		formData = {
		  ...formData,
		  ...initialData,
		  location: {
			...formData.location,
			...(initialData.location || {})
		  },
		  pricing_details: {
			...formData.pricing_details,
			...(initialData.pricing_details || {})
		  },
		  specifications: {
			...formData.specifications,
			...(initialData.specifications || {})
		  }
		};
		
		// Convert numbers from string if needed
		['size_sqm', 'bedrooms', 'bathrooms', 'floors', 'parking_spaces', 'year_built', 'market_value', 'minimum_bid'].forEach(key => {
		  if (formData[key] != null && formData[key] !== '') {
			formData[key] = Number(formData[key]);
		  } else {
			formData[key] = '';
		  }
		});
  
		// Handle media if it exists in initialData
		if (initialData.media && initialData.media.length > 0) {
		  uploadedImages = initialData.media.map(m => ({ 
			file: null, // We don't have the actual file objects for existing media
			preview: m.file_url,
			id: m.id // Keep track of existing media IDs
		  }));
		}
	  } else {
		formData.year_built = new Date().getFullYear();
	  }
	});
  
	// Form submission
	async function handleSubmit() {
	  if (!validateStep(currentStep)) {
		addToast('يرجى تصحيح الأخطاء في الخطوة الحالية قبل الحفظ', 'error');
		errors = { ...errors };
		return;
	  }
  
	  // Prepare final data for submission
	  const finalData = {
		...formData,
		// Ensure all required fields are properly formatted
		size_sqm: formData.size_sqm ? Number(formData.size_sqm) : null,
		bedrooms: formData.bedrooms ? Number(formData.bedrooms) : null,
		bathrooms: formData.bathrooms ? Number(formData.bathrooms) : null,
		floors: formData.floors ? Number(formData.floors) : null,
		parking_spaces: formData.parking_spaces ? Number(formData.parking_spaces) : null,
		year_built: formData.year_built ? Number(formData.year_built) : null,
		market_value: formData.market_value ? Number(formData.market_value) : null,
		minimum_bid: formData.minimum_bid ? Number(formData.minimum_bid) : null,
	  };
  
	  // Get existing media IDs if editing
	  const existingMediaIds = uploadedImages
		.filter(img => img.id)
		.map(img => img.id);
  
	  // Get new files to upload
	  const newFiles = uploadedImages
		.filter(img => img.file)
		.map(img => img.file);
  
	  // Dispatch the submit event with the form data and the image files
	  dispatch('submit', { 
		formData: finalData, 
		images: newFiles,
		existingMedia: existingMediaIds
	  });
	}
  </script>
  
  <div class="mb-8">
	<div class="flex justify-between items-start">
	  {#each steps as step, i}
		<div class="relative flex flex-1 flex-col items-center">
		  <div
			class="flex h-12 w-12 items-center justify-center rounded-full border-2 transition-colors duration-300 {currentStep > i + 1
			  ? 'border-green-600 bg-green-600 text-white'
			  : currentStep === i + 1
			  ? 'border-blue-600 bg-blue-600 text-white scale-110' : 'border-slate-300 bg-white text-slate-400'}"
		  >
			<i class="{step.icon} text-lg"></i>
		  </div>
		  <span
			class="mt-2 text-center text-xs sm:text-sm font-medium transition-colors duration-300 {currentStep > i + 1
			  ? 'text-green-600'
			  : currentStep === i + 1
			  ? 'text-blue-600 font-semibold' : 'text-slate-500'}"
		  >
			{step.title}
		  </span>
		</div>
  
		{#if i < steps.length - 1}
		  <div
			class="relative top-6 h-0.5 flex-1 mt-0 mx-1 transition-colors duration-300 {currentStep > i + 1 ? 'bg-green-600' : 'bg-slate-300'}"
		  ></div>
		{/if}
	  {/each}
	</div>
  </div>
  
  <div class="space-y-8">
	<form on:submit|preventDefault={handleSubmit} class="mt-8">
	  {#if currentStep === 1}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[0].title}</h2>
		  <div class="form-group">
			<label class="label required" for="title">عنوان العقار</label>
			<input
			  id="title"
			  type="text"
			  class="input {errors.title ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
			  bind:value={formData.title}
			  placeholder="أدخل عنواناً مميزاً للعقار"
			  aria-required="true"
			  aria-invalid={!!errors.title}
			/>
			{#if errors.title}
			  <span class="mt-1 text-sm text-red-600">{errors.title}</span>
			{/if}
		  </div>
  
		  <div class="form-group">
			<label class="label required" for="property_type">نوع العقار</label>
			<select
			  id="property_type"
			  class="input {errors.property_type ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
			  bind:value={formData.property_type}
			  aria-required="true"
			  aria-invalid={!!errors.property_type}
			>
			  {#each propertyTypes as type}
				<option value={type.value}>{type.label}</option>
			  {/each}
			</select>
			{#if errors.property_type}
			  <span class="mt-1 text-sm text-red-600">{errors.property_type}</span>
			{/if}
		  </div>
  
		  <div class="form-group">
			<label class="label required" for="description">الوصف</label>
			<textarea
			  id="description"
			  class="input {errors.description ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
			  bind:value={formData.description}
			  rows="4"
			  placeholder="أدخل وصفاً تفصيلياً للعقار..."
			  aria-required="true"
			  aria-invalid={!!errors.description}
			></textarea>
			{#if errors.description}
			  <span class="mt-1 text-sm text-red-600">{errors.description}</span>
			{/if}
		  </div>
  
		  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div class="form-group">
			  <label class="label" for="deed_number">رقم الصك</label>
			  <input
				id="deed_number"
				type="text"
				class="input focus:border-blue-500 focus:ring-blue-200 transition-colors"
				bind:value={formData.deed_number}
				placeholder="أدخل رقم الصك (اختياري)"
			  />
			</div>
  
			<div class="form-group">
			  <label class="label" for="status">حالة العقار</label>
			  <select id="status" bind:value={formData.status} class="input focus:border-blue-500 focus:ring-blue-200 transition-colors">
				<option value="available">متاح</option>
				<option value="under_contract">تحت العقد</option>
				<option value="sold">مباع</option>
				<option value="off_market">خارج السوق</option>
				<option value="auction">في المزاد</option>
			  </select>
			</div>
		  </div>
		</div>
  
	  {:else if currentStep === 2}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[1].title}</h2>
		  <div class="form-group">
			<label class="label required" for="address">العنوان التفصيلي</label>
			<input
			  id="address"
			  type="text"
			  class="input {errors.address ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
			  bind:value={formData.address}
			  placeholder="مثال: حي الملك فهد، شارع العليا العام"
			  aria-required="true"
			  aria-invalid={!!errors.address}
			/>
			{#if errors.address}
			  <span class="mt-1 text-sm text-red-600">{errors.address}</span>
			{/if}
		  </div>
  
		  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div class="form-group">
			  <label class="label required" for="city">المدينة</label>
			  <select
				id="city"
				class="input {errors.city ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.city}
				aria-required="true"
				aria-invalid={!!errors.city}
			  >
				<option value="">-- اختر المدينة --</option>
				{#each cityOptions as city}
				  <option value={city}>{city}</option>
				{/each}
			  </select>
			  {#if errors.city}
				<span class="mt-1 text-sm text-red-600">{errors.city}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="state">المنطقة / المحافظة</label>
			  <input
				id="state"
				type="text"
				class="input focus:border-blue-500 focus:ring-blue-200 transition-colors"
				bind:value={formData.state}
				placeholder="مثال: منطقة الرياض (اختياري)"
			  />
			</div>
  
			<div class="form-group">
			  <label class="label" for="postal_code">الرمز البريدي</label>
			  <input
				id="postal_code"
				type="text"
				class="input focus:border-blue-500 focus:ring-blue-200 transition-colors"
				bind:value={formData.postal_code}
				placeholder="مثال: 12345 (اختياري)"
				pattern="[0-9]{5}"
				title="أدخل 5 أرقام للرمز البريدي"
			  />
			</div>
  
			<div class="form-group">
			  <label class="label" for="country">الدولة</label>
			  <input
				id="country"
				type="text"
				class="input bg-slate-100 cursor-not-allowed"
				bind:value={formData.country}
				readonly
			  />
			</div>
		  </div>
  
		  <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 mt-4">
			<label class="label">الموقع على الخريطة (اختياري ولكن موصى به)</label>
  
			<div class="mb-4 flex flex-col sm:flex-row gap-4">
			  <button
				type="button"
				class="btn-secondary flex-1"
				on:click={detectLocation}
				disabled={detectingLocation}
			  >
				{#if detectingLocation}
				  <i class="fas fa-spinner fa-spin mr-2"></i>
				  جاري تحديد الموقع...
				{:else}
				  <i class="fas fa-map-marker-alt mr-2"></i>
				  تحديد موقعي الحالي تلقائياً
				{/if}
			  </button>
			</div>
  
			{#if errors.location}
			  <div class="mb-4 rounded bg-red-100 border border-red-300 p-3 text-sm text-red-800">
				<i class="fas fa-exclamation-circle mr-2"></i>
				{errors.location}
			  </div>
			{/if}
  
			<p class="text-sm text-slate-600 mb-3">يمكنك تحديد الموقع الدقيق بسحب العلامة على الخريطة، أو إدخال الإحداثيات:</p>
			<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
			  <div class="form-group">
				<label class="label text-xs" for="latitude">خط العرض (Latitude)</label>
				<input
				  id="latitude"
				  type="number"
				  class="input text-sm {errors.location ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				  bind:value={formData.location.latitude}
				  step="any"
				  placeholder="e.g. 24.7136"
				  aria-invalid={!!errors.location}
				/>
			  </div>
  
			  <div class="form-group">
				<label class="label text-xs" for="longitude">خط الطول (Longitude)</label>
				<input
				  id="longitude"
				  type="number"
				  class="input text-sm {errors.location ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				  bind:value={formData.location.longitude}
				  step="any"
				  placeholder="e.g. 46.6753"
				  aria-invalid={!!errors.location}
				/>
			  </div>
			</div>
  
			<div class="mt-4 h-[350px] rounded overflow-hidden border">
			  {#key formData.location.latitude + formData.location.longitude}
				<PropertyMap
				  bind:latitude={formData.location.latitude}
				  bind:longitude={formData.location.longitude}
				  editable={true}
				  on:locationchange={(e) => {
					if (e.detail.lat && e.detail.lng) {
					  formData.location.latitude = e.detail.lat;
					  formData.location.longitude = e.detail.lng;
					  errors.location = '';
					}
				  }}
				/>
			  {/key}
			</div>
		  </div>
		</div>
  
	  {:else if currentStep === 3}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[2].title}</h2>
		  <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
			<div class="form-group">
			  <label class="label required" for="size_sqm">المساحة (متر مربع)</label>
			  <input
				id="size_sqm"
				type="number"
				class="input {errors.size_sqm ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.size_sqm}
				min="0.01"
				step="0.01"
				placeholder="أدخل المساحة"
				aria-required="true"
				aria-invalid={!!errors.size_sqm}
			  />
			  {#if errors.size_sqm}
				<span class="mt-1 text-sm text-red-600">{errors.size_sqm}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="bedrooms">عدد غرف النوم</label>
			  <input
				id="bedrooms"
				type="number"
				class="input {errors.bedrooms ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.bedrooms}
				min="0"
				step="1"
				placeholder="أدخل عدد غرف النوم (0 إن لا يوجد)"
				aria-invalid={!!errors.bedrooms}
			  />
			  {#if errors.bedrooms}
				<span class="mt-1 text-sm text-red-600">{errors.bedrooms}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="bathrooms">عدد الحمامات</label>
			  <input
				id="bathrooms"
				type="number"
				class="input {errors.bathrooms ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.bathrooms}
				min="0"
				step="1"
				placeholder="أدخل عدد الحمامات (0 إن لا يوجد)"
				aria-invalid={!!errors.bathrooms}
			  />
			  {#if errors.bathrooms}
				<span class="mt-1 text-sm text-red-600">{errors.bathrooms}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="floors">عدد الطوابق</label>
			  <input
				id="floors"
				type="number"
				class="input {errors.floors ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.floors}
				min="0"
				step="1"
				placeholder="أدخل عدد الطوابق (0 إن أرض)"
				aria-invalid={!!errors.floors}
			  />
			  {#if errors.floors}
				<span class="mt-1 text-sm text-red-600">{errors.floors}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="parking_spaces">مواقف السيارات</label>
			  <input
				id="parking_spaces"
				type="number"
				class="input {errors.parking_spaces ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.parking_spaces}
				min="0"
				step="1"
				placeholder="أدخل عدد المواقف (0 إن لا يوجد)"
				aria-invalid={!!errors.parking_spaces}
			  />
			  {#if errors.parking_spaces}
				<span class="mt-1 text-sm text-red-600">{errors.parking_spaces}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="year_built">سنة البناء</label>
			  <input
				id="year_built"
				type="number"
				class="input {errors.year_built ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.year_built}
				min="1800"
				max={new Date().getFullYear() + 1}
				placeholder="أدخل سنة البناء (اختياري)"
				aria-invalid={!!errors.year_built}
			  />
			  {#if errors.year_built}
				<span class="mt-1 text-sm text-red-600">{errors.year_built}</span>
			  {/if}
			</div>
		  </div>
  
		  <div class="mt-6 border-t pt-6">
			<h3 class="mb-4 text-lg font-semibold">المواصفات الإضافية (اختياري)</h3>
			{#if specificationsFields && specificationsFields.length > 0}
			  <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each specificationsFields as field (field.key)}
				  <div class="form-group">
					<label class="label" for="spec_{field.key}">{field.label}</label>
					<select
					  id="spec_{field.key}"
					  bind:value={formData.specifications[field.key]}
					  class="input focus:border-blue-500 focus:ring-blue-200 transition-colors"
					>
					  <option value="">{field.placeholder || '-- اختر --'}</option>
					  {#each field.options as option}
						<option value={option.value}>{option.label}</option>
					  {/each}
					</select>
					{#if errors[`specifications.${field.key}`]}
					  <span class="mt-1 text-sm text-red-600">{errors[`specifications.${field.key}`]}</span>
					{/if}
				  </div>
				{/each}
			  </div>
			{:else}
			  <p class="text-slate-500">لا توجد حقول مواصفات معرفة.</p>
			{/if}
		  </div>
		</div>
  
	  {:else if currentStep === 4}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[3].title}</h2>
		  <div class="form-group">
			<label class="label" for="features">المميزات (اختياري)</label>
			<p class="text-sm text-slate-500 mb-2">أضف ميزات إضافية للعقار مثل (مسبح، حديقة، مصعد، إلخ).</p>
			<div class="flex gap-2 items-center">
			  <input
				id="features"
				type="text"
				class="input flex-1 focus:border-blue-500 focus:ring-blue-200 transition-colors"
				bind:value={newFeature}
				placeholder="اكتب ميزة واضغط Enter أو زر الإضافة"
				on:keydown={(e) => {if (e.key === 'Enter') { e.preventDefault(); addFeature(); }}}
			  />
			  <button type="button" class="btn-secondary px-4" on:click={addFeature} title="إضافة الميزة">
				<i class="fas fa-plus"></i>
				<span class="sr-only">إضافة</span>
			  </button>
			</div>
  
			<div class="mt-3 flex flex-wrap gap-2">
			  {#each formData.features as feature, i}
				<span class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1.5 text-sm font-medium text-blue-800">
				  {feature}
				  <button
					type="button"
					class="-mr-1 ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full text-blue-500 hover:bg-blue-200 hover:text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1"
					on:click={() => removeFeature(i)}
					title="إزالة {feature}"
				  >
					<span class="sr-only">إزالة</span>
					<i class="fas fa-times text-xs"></i>
				  </button>
				</span>
			  {:else}
				<p class="text-slate-400 text-sm italic">لم يتم إضافة مميزات بعد.</p>
			  {/each}
			</div>
		  </div>
  
		  <!-- Amenities Section (NEW) -->
		  <div class="form-group mt-6 border-t pt-6">
			<label class="label" for="amenities">المرافق والخدمات (اختياري)</label>
			<p class="text-sm text-slate-500 mb-2">اختر أو أضف المرافق والخدمات المتوفرة في العقار أو بالقرب منه.</p>
			
			<!-- Common amenities as checkboxes -->
			<div class="mb-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
			  {#each commonAmenities as amenity}
				<div class="flex items-center">
				  <input 
					type="checkbox" 
					id="amenity_{amenity.id}" 
					class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
					checked={formData.amenities.includes(amenity.label)}
					on:change={() => toggleAmenity(amenity.label)}
				  />
				  <label for="amenity_{amenity.id}" class="mr-2 text-sm text-slate-700">
					{amenity.label}
				  </label>
				</div>
			  {/each}
			</div>
			
			<!-- Custom amenity input -->
			<div class="flex gap-2 items-center">
			  <input
				id="amenities"
				type="text"
				class="input flex-1 focus:border-blue-500 focus:ring-blue-200 transition-colors"
				bind:value={newAmenity}
				placeholder="أضف مرافق أخرى غير مذكورة أعلاه"
				on:keydown={(e) => {if (e.key === 'Enter') { e.preventDefault(); addAmenity(); }}}
			  />
			  <button type="button" class="btn-secondary px-4" on:click={addAmenity} title="إضافة مرفق">
				<i class="fas fa-plus"></i>
				<span class="sr-only">إضافة</span>
			  </button>
			</div>
  
			<!-- Display selected/added custom amenities -->
			{#if formData.amenities.filter(a => !commonAmenities.map(ca => ca.label).includes(a)).length > 0}
			  <div class="mt-3">
				<p class="text-sm font-medium text-slate-700 mb-2">المرافق المضافة:</p>
				<div class="flex flex-wrap gap-2">
				  {#each formData.amenities.filter(a => !commonAmenities.map(ca => ca.label).includes(a)) as amenity, i}
					<span class="inline-flex items-center rounded-full bg-green-100 px-3 py-1.5 text-sm font-medium text-green-800">
					  {amenity}
					  <button
						type="button"
						class="-mr-1 ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full text-green-500 hover:bg-green-200 hover:text-green-700 focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-offset-1"
						on:click={() => removeAmenity(formData.amenities.indexOf(amenity))}
						title="إزالة {amenity}"
					  >
						<span class="sr-only">إزالة</span>
						<i class="fas fa-times text-xs"></i>
					  </button>
					</span>
				  {/each}
				</div>
			  </div>
			{/if}
		  </div>
  
		  <div class="mt-6 border-t pt-6">
			<h3 class="mb-2 text-lg font-semibold">تفاصيل الغرف (اختياري)</h3>
			<p class="text-sm text-slate-500 mb-4">أضف تفاصيل عن الغرف الموجودة بالعقار ومساحاتها.</p>
			<RoomEditor bind:rooms={formData.rooms} />
			{#if errors.rooms}
			  <span class="mt-1 text-sm text-red-600">{errors.rooms}</span>
			{/if}
		  </div>
		</div>
  
	  {:else if currentStep === 5}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[4].title}</h2>
		  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div class="form-group">
			  <label class="label required" for="market_value">القيمة السوقية المقدرة (ريال سعودي)</label>
			  <input
				id="market_value"
				type="number"
				class="input {errors.market_value ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.market_value}
				min="0"
				step="1"
				placeholder="أدخل القيمة السوقية"
				aria-required="true"
				aria-invalid={!!errors.market_value}
			  />
			  {#if errors.market_value}
				<span class="mt-1 text-sm text-red-600">{errors.market_value}</span>
			  {/if}
			</div>
  
			<div class="form-group">
			  <label class="label" for="minimum_bid">الحد الأدنى للمزايدة (إن وجد)</label>
			  <input
				id="minimum_bid"
				type="number"
				class="input {errors.minimum_bid ? 'border-red-500 focus:border-red-500 focus:ring-red-200' : 'focus:border-blue-500 focus:ring-blue-200'} transition-colors"
				bind:value={formData.minimum_bid}
				min="0"
				step="1"
				placeholder="أدخل الحد الأدنى (اختياري)"
				aria-invalid={!!errors.minimum_bid}
			  />
			  {#if errors.minimum_bid}
				<span class="mt-1 text-sm text-red-600">{errors.minimum_bid}</span>
			  {/if}
			</div>
		  </div>
  
		  <div class="form-group mt-4 border-t pt-6">
			<label class="label text-lg font-semibold">تفاصيل إضافية للتسعير (اختياري)</label>
			<div class="rounded-lg border border-slate-200 p-4 space-y-4 bg-slate-50">
			  <div class="form-group">
				<label class="label" for="valuation_method">طريقة التقييم المستخدمة</label>
				<select id="valuation_method" bind:value={formData.pricing_details.valuation_method} class="input focus:border-blue-500 focus:ring-blue-200 transition-colors">
				  <option value="">-- اختر طريقة التقييم --</option>
				  <option value="market_comparison">مقارنة السوق</option>
				  <option value="income_approach">نهج الدخل</option>
				  <option value="cost_approach">نهج التكلفة</option>
				  <option value="developer_price">سعر المطور</option>
				  <option value="bank_valuation">تقييم بنكي</option>
				  <option value="other">أخرى</option>
				</select>
			  </div>
  
			  <div class="form-group">
				<label class="label" for="pricing_notes">ملاحظات التسعير</label>
				<textarea
				  id="pricing_notes"
				  class="input focus:border-blue-500 focus:ring-blue-200 transition-colors"
				  bind:value={formData.pricing_details.notes}
				  rows="3"
				  placeholder="أضف أي ملاحظات حول السعر أو التقييم"
				></textarea>
			  </div>
			</div>
		  </div>
		</div>
  
	  {:else if currentStep === 6}
		<div class="space-y-6 animate-fade-in">
		  <h2 class="text-xl font-semibold mb-4 border-b pb-2">{steps[5].title}</h2>
		  <div class="form-group">
			<label class="label required" for="property-images">صور العقار (صورة واحدة على الأقل)</label>
			<div
			  class="rounded-lg border-2 border-dashed border-slate-300 p-6 text-center hover:border-blue-500 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-200 focus-within:ring-offset-2 transition-colors relative
				{errors.media ? 'border-red-500 hover:border-red-600' : ''}"
			>
			  <input
				type="file"
				accept="image/jpeg, image/png, image/webp, image/gif"
				multiple
				class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
				on:change={handleImageUpload}
				id="property-images"
				aria-required="true"
				aria-invalid={!!errors.media}
				aria-describedby="media-error media-hint"
			  />
			  <label for="property-images" class="cursor-pointer block">
				<i class="fas fa-cloud-upload-alt text-4xl text-slate-400 mb-2"></i>
				<p class="text-slate-600 font-medium">اسحب الصور إلى هنا أو انقر للاختيار</p>
				<p class="text-slate-500 text-sm mt-1" id="media-hint">الحد الأقصى 5 ميجابايت للصورة. الأنواع المسموحة: JPG, PNG, WEBP, GIF.</p>
			  </label>
			</div>
			{#if errors.media}
			  <span class="mt-1 text-sm text-red-600" id="media-error">{errors.media}</span>
			{/if}
		  </div>
  
		  {#if uploadedImages.length > 0}
			<div class="mt-4">
			  <h4 class="text-md font-semibold mb-2">الصور المرفوعة ({uploadedImages.length}):</h4>
			  <p class="text-sm text-slate-500 mb-3">الصورة الأولى ستكون الصورة الرئيسية للعقار. يمكنك إعادة ترتيب الصور بالسحب والإفلات (إذا تم تطبيق مكتبة لذلك).</p>
			  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
				{#each uploadedImages as image, i}
				  <div class="relative group border rounded-lg overflow-hidden shadow-sm aspect-square">
					<img
					  src={image.preview}
					  alt="معاينة العقار {i + 1}"
					  class="w-full h-full object-cover"
					  loading="lazy"
					/>
					<div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-opacity flex items-center justify-center">
					  <button
						type="button"
						class="absolute top-1 right-1 h-7 w-7 rounded-full bg-red-600 text-white opacity-0 group-hover:opacity-100 hover:bg-red-700 transition-all flex items-center justify-center shadow-md"
						on:click={() => removeImage(i)}
						title="إزالة الصورة"
					  >
						<i class="fas fa-times text-sm"></i>
						<span class="sr-only">إزالة الصورة</span>
					  </button>
					</div>
					{#if i === 0}
					  <div class="absolute bottom-0 left-0 bg-blue-600 rounded-tr-lg px-2 py-0.5 text-white text-xs font-medium shadow">
						رئيسية
					  </div>
					{/if}
					<div class="absolute bottom-0 right-0 bg-gray-700 bg-opacity-70 text-white text-xs px-1.5 py-0.5 rounded-tl-md">
					  {image.file ? (image.file.size / 1024 / 1024).toFixed(2) + ' MB' : 'موجود'}
					</div>
				  </div>
				{/each}
			  </div>
			</div>
		  {/if}
  
		  <div class="mt-6 border border-slate-200 rounded-lg p-4 space-y-5 bg-slate-50">
			<h3 class="text-lg font-semibold mb-3">إعدادات النشر</h3>
			<div class="flex items-center justify-between border-b pb-4">
			  <div>
				<label class="label mb-0 font-medium" for="is_published">نشر العقار على الموقع</label>
				<p class="text-sm text-slate-500">عند تفعيل هذا الخيار، سيصبح العقار ظاهراً للزوار.</p>
			  </div>
			  <div class="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
				<input type="checkbox" id="is_published" class="toggle-checkbox" bind:checked={formData.is_published}/>
				<label for="is_published" class="toggle-label"></label>
			  </div>
			</div>
  
			<div class="flex items-center justify-between">
			  <div>
				<label class="label mb-0 font-medium" for="is_featured">تمييز العقار</label>
				<p class="text-sm text-slate-500">عرض هذا العقار في قائمة العقارات المميزة (قد يتطلب صلاحيات خاصة).</p>
			  </div>
			  <div class="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
				<input type="checkbox" id="is_featured" class="toggle-checkbox" bind:checked={formData.is_featured}/>
				<label for="is_featured" class="toggle-label"></label>
			  </div>
			</div>
		  </div>
		</div>
	  {/if}
  
	  <div class="mt-10 pt-6 border-t flex justify-between items-center">
		{#if currentStep > 1}
		  <button type="button" class="btn btn-secondary" on:click={() => handleStepChange('prev')}>
			<i class="fas fa-arrow-right ml-2"></i> السابق
		  </button>
		{:else}
		  <div></div>
		{/if}
  
		{#if currentStep < steps.length}
		  <button type="button" class="btn btn-primary" on:click={() => handleStepChange('next')}>
			التالي
			<i class="fas fa-arrow-left mr-2"></i>
		  </button>
		{:else}
		  <button type="submit" class="btn btn-success" disabled={loading}>
			{#if loading}
			  <i class="fas fa-spinner fa-spin ml-2"></i>
			  جاري الحفظ...
			{:else}
			  <i class="fas fa-save mr-2"></i>
			  حفظ العقار
			{/if}
		  </button>
		{/if}
	  </div>
	</form>
  </div>
  
  <style>
	/* Add basic fade-in animation */
	@keyframes fadeIn {
	  from { opacity: 0; transform: translateY(10px); }
	  to { opacity: 1; transform: translateY(0); }
	}
	.animate-fade-in {
	  animation: fadeIn 0.5s ease-out forwards;
	}
  
	/* Scoped styles for form elements (preferred over global) */
	.label {
	  margin-bottom: 0.35rem;
	  display: block;
	  font-size: 0.875rem;
	  font-weight: 500;
	  color: rgb(51 65 85);
	}
  
	.label.required::after {
	  content: '*';
	  margin-right: 0.25rem;
	  margin-left: 0;
	  color: rgb(220 38 38);
	}
  
	.input, select, textarea {
	  width: 100%;
	  border-radius: 0.375rem;
	  border: 1px solid rgb(203 213 225);
	  padding: 0.6rem 0.8rem;
	  font-size: 0.875rem;
	  line-height: 1.25rem;
	  color: rgb(17 24 39);
	  background-color: white;
	  box-shadow: inset 0 1px 2px 0 rgb(0 0 0 / 0.05);
	}
	
	.input, select, textarea {
	  transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
	}
  
	.input:focus, select:focus, textarea:focus {
	  outline: none;
	  border-color: rgb(59 130 246);
	  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
	}
  
	.input.border-red-500, select.border-red-500, textarea.border-red-500 {
	  border-color: rgb(239 68 68);
	}
	
	.input.border-red-500:focus, select.border-red-500:focus, textarea.border-red-500:focus {
	  border-color: rgb(220 38 38);
	  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
	}
  
	/* Base Button Styles */
	.btn {
	  display: inline-flex;
	  align-items: center;
	  justify-content: center;
	  border-radius: 0.375rem;
	  padding: 0.6rem 1.2rem;
	  font-size: 0.875rem;
	  font-weight: 500;
	  border: 1px solid transparent;
	  cursor: pointer;
	  transition: background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
	  white-space: nowrap;
	}
	
	.btn:focus {
	  outline: none;
	  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
	}
	
	.btn:disabled {
	  opacity: 0.6;
	  cursor: not-allowed;
	}
  
	/* Primary Button */
	.btn-primary {
	  background-color: rgb(37 99 235);
	  color: white;
	}
	
	.btn-primary:hover:not(:disabled) {
	  background-color: rgb(29 78 216);
	}
	
	.btn-primary:focus {
	  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
	}
  
	/* Secondary Button */
	.btn-secondary {
	  border: 1px solid rgb(203 213 225);
	  background-color: white;
	  color: rgb(51 65 85);
	}
	
	.btn-secondary:hover:not(:disabled) {
	  background-color: rgb(249 250 251);
	  border-color: rgb(156 163 175);
	}
	
	.btn-secondary:focus {
	  border-color: rgb(59 130 246);
	  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
	}
  
	/* Success Button */
	.btn-success {
	  background-color: rgb(22 163 74);
	  color: white;
	}
	
	.btn-success:hover:not(:disabled) {
	  background-color: rgb(21 128 61);
	}
	
	.btn-success:focus {
	  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.3);
	}
  
	/* Toggle Switch Styles */
	.toggle-checkbox {
	  position: absolute;
	  opacity: 0;
	  cursor: pointer;
	  height: 0;
	  width: 0;
	}
  
	.toggle-label {
	  display: block;
	  overflow: hidden;
	  cursor: pointer;
	  border: 0 solid #bbb;
	  border-radius: 20px;
	  width: 2.5rem;
	  height: 1.25rem;
	  background-color: rgb(203 213 225);
	  position: relative;
	  transition: background-color 0.2s ease-in;
	}
  
	.toggle-label:before {
	  content: "";
	  position: absolute;
	  top: 2px;
	  left: 2px;
	  width: 1rem;
	  height: 1rem;
	  background-color: white;
	  border-radius: 50%;
	  transition: transform 0.2s ease-in;
	}
  
	.toggle-checkbox:checked + .toggle-label {
	  background-color: rgb(37 99 235);
	}
  
	.toggle-checkbox:checked + .toggle-label:before {
	  transform: translateX(1.25rem);
	}
	
	.toggle-checkbox:focus + .toggle-label {
	  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
	}
  </style>