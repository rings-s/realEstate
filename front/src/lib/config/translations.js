/**
 * Translation files for the application
 * Default language: Arabic (ar)
 */

// Arabic translations
export const ar = {
	// General
	app_name: 'منصة مزادات العقارات',
	loading: 'جاري التحميل...',
	error: 'حدث خطأ',
	success: 'تم بنجاح',
	cancel: 'إلغاء',
	confirm: 'تأكيد',
	save: 'حفظ',
	edit: 'تعديل',
	delete: 'حذف',
	back: 'رجوع',
	next: 'التالي',
	previous: 'السابق',
	view: 'عرض',
	close: 'إغلاق',
	search: 'بحث',
	filter: 'تصفية',
	reset: 'إعادة ضبط',
	required_field: 'هذا الحقل مطلوب',
	no_results: 'لا توجد نتائج',

	// Auth
	login: 'تسجيل الدخول',
	logout: 'تسجيل الخروج',
	register: 'تسجيل حساب جديد',
	email: 'البريد الإلكتروني',
	password: 'كلمة المرور',
	confirm_password: 'تأكيد كلمة المرور',
	remember_me: 'تذكرني',
	forgot_password: 'نسيت كلمة المرور؟',
	reset_password: 'إعادة تعيين كلمة المرور',
	current_password: 'كلمة المرور الحالية',
	new_password: 'كلمة المرور الجديدة',
	verify_email: 'تأكيد البريد الإلكتروني',
	verification_code: 'رمز التحقق',
	resend_code: 'إعادة إرسال الرمز',
	first_name: 'الاسم الأول',
	last_name: 'اسم العائلة',
	phone_number: 'رقم الهاتف',
	date_of_birth: 'تاريخ الميلاد',

	// Navigation
	home: 'الرئيسية',
	dashboard: 'لوحة التحكم',
	properties: 'العقارات',
	auctions: 'المزادات',
	bids: 'المزايدات',
	contracts: 'العقود',
	documents: 'المستندات',
	messages: 'الرسائل',
	notifications: 'الإشعارات',
	profile: 'الملف الشخصي',
	settings: 'الإعدادات',
	admin: 'المشرف',
	users: 'المستخدمين',

	// Properties
	property: 'عقار',
	add_property: 'إضافة عقار',
	edit_property: 'تعديل العقار',
	property_details: 'تفاصيل العقار',
	property_type: 'نوع العقار',
	residential: 'سكني',
	commercial: 'تجاري',
	land: 'أرض',
	industrial: 'صناعي',
	mixed_use: 'متعدد الاستخدام',
	status: 'الحالة',
	available: 'متاح',
	under_contract: 'تحت العقد',
	sold: 'مباع',
	off_market: 'خارج السوق',
	in_auction: 'في المزاد',
	address: 'العنوان',
	city: 'المدينة',
	state: 'المحافظة',
	postal_code: 'الرمز البريدي',
	country: 'الدولة',
	description: 'الوصف',
	features: 'المميزات',
	amenities: 'المرافق',
	rooms: 'الغرف',
	size: 'المساحة',
	bedrooms: 'غرف النوم',
	bathrooms: 'الحمامات',
	parking: 'مواقف السيارات',
	year_built: 'سنة البناء',
	price: 'السعر',
	market_value: 'القيمة السوقية',
	minimum_bid: 'الحد الأدنى للمزايدة',
	is_published: 'منشور',
	is_featured: 'مميز',
	is_verified: 'موثق',
	location: 'الموقع',

	// Auctions
	auction: 'مزاد',
	create_auction: 'إنشاء مزاد',
	edit_auction: 'تعديل المزاد',
	auction_details: 'تفاصيل المزاد',
	auction_type: 'نوع المزاد',
	english_auction: 'مزاد إنجليزي (تصاعدي)',
	dutch_auction: 'مزاد هولندي (تنازلي)',
	sealed_bid_auction: 'مزاد العطاءات المغلقة',
	reserve_auction: 'مزاد بحد أدنى',
	no_reserve_auction: 'مزاد بدون حد أدنى',
	start_date: 'تاريخ البدء',
	end_date: 'تاريخ الانتهاء',
	registration_deadline: 'موعد انتهاء التسجيل',
	viewing_dates: 'مواعيد المعاينة',
	timeline: 'الجدول الزمني',
	starting_bid: 'المزايدة الأولية',
	reserve_price: 'السعر المحفوظ',
	minimum_increment: 'الحد الأدنى للزيادة',
	current_bid: 'المزايدة الحالية',
	estimated_value: 'القيمة التقديرية',
	bid_history: 'سجل المزايدات',
	financial_terms: 'الشروط المالية',
	buyer_premium: 'عمولة المشتري',
	registration_fee: 'رسوم التسجيل',
	deposit_required: 'التأمين المطلوب',
	is_private: 'مزاد خاص',
	terms_conditions: 'الشروط والأحكام',
	special_notes: 'ملاحظات خاصة',
	view_count: 'عدد المشاهدات',
	bid_count: 'عدد المزايدات',
	registered_bidders: 'المزايدين المسجلين',

	// Auction status
	draft: 'مسودة',
	scheduled: 'مجدول',
	live: 'مباشر',
	ended: 'منتهي',
	cancelled: 'ملغي',
	completed: 'مكتمل',
	time_remaining: 'الوقت المتبقي',
	days: 'أيام',
	hours: 'ساعات',
	minutes: 'دقائق',
	seconds: 'ثواني',

	// Bids
	place_bid: 'تقديم مزايدة',
	your_bid: 'مزايدتك',
	bid_amount: 'مبلغ المزايدة',
	bid_time: 'وقت المزايدة',
	bid_status: 'حالة المزايدة',
	bidder: 'المزايد',
	auto_bid: 'مزايدة تلقائية',
	max_auto_bid: 'الحد الأقصى للمزايدة التلقائية',
	bid_increment: 'زيادة المزايدة',
	bid_suggestions: 'اقتراحات المزايدة',
	outbid: 'تمت المزايدة بأعلى',
	winning_bid: 'المزايدة الفائزة',

	// Documents
	document: 'مستند',
	upload_document: 'تحميل مستند',
	document_type: 'نوع المستند',
	deed: 'صك ملكية',
	contract: 'عقد',
	certificate: 'شهادة',
	report: 'تقرير فحص',
	identity: 'وثيقة هوية',
	financial: 'وثيقة مالية',
	verification_status: 'حالة التحقق',
	pending: 'قيد الانتظار',
	verified: 'تم التحقق',
	rejected: 'مرفوض',
	issue_date: 'تاريخ الإصدار',
	expiry_date: 'تاريخ الانتهاء',
	file: 'ملف',

	// Contracts
	contract_details: 'تفاصيل العقد',
	create_contract: 'إنشاء عقد',
	contract_date: 'تاريخ العقد',
	effective_date: 'تاريخ السريان',
	buyer: 'المشتري',
	seller: 'البائع',
	total_amount: 'المبلغ الإجمالي',
	down_payment: 'الدفعة الأولى',
	payment_method: 'طريقة الدفع',
	payment_terms: 'شروط الدفع',
	full_payment: 'دفعة كاملة',
	installments: 'أقساط',
	mortgage: 'رهن عقاري',
	custom_payment: 'خطة دفع مخصصة',
	buyer_signed: 'توقيع المشتري',
	seller_signed: 'توقيع البائع',

	// Contract status
	active: 'نشط',
	fulfilled: 'تم الوفاء',
	expired: 'منتهي',
	disputed: 'متنازع عليه',

	// Messages
	new_message: 'رسالة جديدة',
	send_message: 'إرسال رسالة',
	reply: 'رد',
	subject: 'الموضوع',
	message: 'الرسالة',
	sender: 'المرسل',
	recipients: 'المستلمين',
	inbox: 'البريد الوارد',
	sent: 'المرسل',
	thread: 'المحادثة',

	// User roles
	role: 'الدور',
	roles: 'الأدوار',
	admin: 'المشرف',
	seller: 'بائع العقارات',
	buyer: 'مشتري العقارات',
	inspector: 'مفتش العقارات',
	legal: 'ممثل قانوني',
	agent: 'وكيل عقارات',
	appraiser: 'مثمن',

	// Profile
	profile_settings: 'إعدادات الملف الشخصي',
	change_password: 'تغيير كلمة المرور',
	personal_info: 'المعلومات الشخصية',
	account_settings: 'إعدادات الحساب',
	avatar: 'الصورة الشخصية',
	upload_avatar: 'تحميل صورة شخصية',
	company_name: 'اسم الشركة',
	company_registration: 'رقم تسجيل الشركة',
	tax_id: 'الرقم الضريبي',
	license_number: 'رقم الترخيص',
	license_expiry: 'تاريخ انتهاء الترخيص',

	// Dashboard
	welcome: 'مرحباً',
	summary: 'ملخص',
	analytics: 'إحصائيات',
	recent_activity: 'النشاط الأخير',
	properties_overview: 'نظرة عامة على العقارات',
	auctions_overview: 'نظرة عامة على المزادات',
	bids_overview: 'نظرة عامة على المزايدات',
	contracts_overview: 'نظرة عامة على العقود',
	total_properties: 'إجمالي العقارات',
	total_auctions: 'إجمالي المزادات',
	active_auctions: 'المزادات النشطة',
	total_bids: 'إجمالي المزايدات',
	pending_approvals: 'الموافقات المعلقة',

	// Settings
	language: 'اللغة',
	arabic: 'العربية',
	english: 'الإنجليزية',
	theme: 'المظهر',
	light: 'فاتح',
	dark: 'داكن',
	currency: 'العملة',
	notifications_settings: 'إعدادات الإشعارات',
	email_notifications: 'إشعارات البريد الإلكتروني',

	// Validation messages
	field_required: 'هذا الحقل مطلوب',
	invalid_email: 'البريد الإلكتروني غير صحيح',
	passwords_not_match: 'كلمات المرور غير متطابقة',
	password_too_short: 'كلمة المرور قصيرة جداً',
	invalid_phone: 'رقم الهاتف غير صحيح',
	invalid_date: 'التاريخ غير صحيح',
	amount_too_low: 'المبلغ منخفض جداً',
	number_required: 'يجب إدخال رقم',

	// Time and date
	today: 'اليوم',
	yesterday: 'الأمس',
	tomorrow: 'غداً',
	days_ago: 'منذ %{count} أيام',
	days_from_now: 'بعد %{count} أيام',

	// Error messages
	error_loading: 'حدث خطأ أثناء التحميل',
	error_saving: 'حدث خطأ أثناء الحفظ',
	session_expired: 'انتهت صلاحية الجلسة',
	no_permission: 'ليس لديك صلاحية للوصول',
	server_error: 'حدث خطأ في الخادم',
	connection_error: 'تعذر الاتصال بالخادم'
};

// English translations (abbreviated version, expand as needed)
export const en = {
	app_name: 'Real Estate Auction Platform',
	loading: 'Loading...',
	error: 'Error',
	success: 'Success'
	// Add more English translations as needed
};

// Default translations based on the selected language
export default {
	ar,
	en
};

/**
 * Get translation for a key
 * @param {string} key - Translation key
 * @param {string} lang - Language code
 * @param {Object} params - Replacement parameters
 * @returns {string} Translated text or key if not found
 */
export function t(key, lang = 'ar', params = {}) {
	// Get the translation object for the language
	const translations = lang === 'en' ? en : ar;

	// Get the translation or fall back to the key
	let translation = translations[key] || key;

	// Replace parameters in the format %{param}
	if (params && typeof translation === 'string') {
		Object.keys(params).forEach((param) => {
			translation = translation.replace(new RegExp(`%{${param}}`, 'g'), params[param]);
		});
	}

	return translation;
}
