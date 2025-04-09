/**
 * Application Constants
 */

// API URL - adjust based on your environment
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Authentication
export const TOKEN_KEY = 'auth_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';
export const TOKEN_EXPIRY_KEY = 'token_expiry';
export const USER_KEY = 'user_data';

// Property Types
export const PROPERTY_TYPES = [
	{ value: 'residential', label: 'سكني' },
	{ value: 'commercial', label: 'تجاري' },
	{ value: 'land', label: 'أرض' },
	{ value: 'industrial', label: 'صناعي' },
	{ value: 'mixed_use', label: 'متعدد الاستخدام' }
];

// Property Status
export const PROPERTY_STATUS = [
	{ value: 'available', label: 'متاح' },
	{ value: 'under_contract', label: 'تحت العقد' },
	{ value: 'sold', label: 'مباع' },
	{ value: 'off_market', label: 'خارج السوق' },
	{ value: 'auction', label: 'في المزاد' }
];

// Auction Types
export const AUCTION_TYPES = [
	{ value: 'english', label: 'مزاد إنجليزي' },
	{ value: 'dutch', label: 'مزاد هولندي' },
	{ value: 'sealed', label: 'مزاد العطاءات المغلقة' },
	{ value: 'reserve', label: 'مزاد بحد أدنى' },
	{ value: 'no_reserve', label: 'مزاد بدون حد أدنى' }
];

// Auction Status
export const AUCTION_STATUS = [
	{ value: 'draft', label: 'مسودة' },
	{ value: 'scheduled', label: 'مجدول' },
	{ value: 'live', label: 'مباشر' },
	{ value: 'ended', label: 'منتهي' },
	{ value: 'cancelled', label: 'ملغي' },
	{ value: 'completed', label: 'مكتمل' }
];

// User Roles
export const USER_ROLES = [
	{ value: 'admin', label: 'المشرف' },
	{ value: 'seller', label: 'بائع العقارات' },
	{ value: 'buyer', label: 'مشتري العقارات' },
	{ value: 'inspector', label: 'مفتش العقارات' },
	{ value: 'legal', label: 'ممثل قانوني' },
	{ value: 'agent', label: 'وكيل عقارات' }
];

// Bid Status
export const BID_STATUS = [
	{ value: 'pending', label: 'قيد الانتظار' },
	{ value: 'accepted', label: 'مقبول' },
	{ value: 'rejected', label: 'مرفوض' },
	{ value: 'outbid', label: 'تمت المزايدة بأعلى' },
	{ value: 'winning', label: 'فائز' }
];

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGINATION_SIZES = [10, 20, 50, 100];

// Default sorting options
export const SORT_OPTIONS = [
	{ value: 'created_at', label: 'الأحدث أولاً', direction: 'desc' },
	{ value: '-created_at', label: 'الأقدم أولاً', direction: 'asc' },
	{ value: 'price', label: 'السعر: من الأقل إلى الأعلى', direction: 'asc' },
	{ value: '-price', label: 'السعر: من الأعلى إلى الأقل', direction: 'desc' }
];

// Format currency helper
export const formatCurrency = (amount, currency = 'SAR') => {
	if (amount === undefined || amount === null) return '';

	return new Intl.NumberFormat('ar-SA', {
		style: 'currency',
		currency: currency,
		maximumFractionDigits: 0
	}).format(amount);
};

// Format date helper
export const formatDate = (dateString, locale = 'ar-SA') => {
	if (!dateString) return '';

	return new Date(dateString).toLocaleDateString(locale, {
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	});
};

// Format time helper
export const formatTime = (dateString, locale = 'ar-SA') => {
	if (!dateString) return '';

	return new Date(dateString).toLocaleTimeString(locale, {
		hour: '2-digit',
		minute: '2-digit'
	});
};

// Format datetime helper
export const formatDateTime = (dateString, locale = 'ar-SA') => {
	if (!dateString) return '';

	return new Date(dateString).toLocaleString(locale, {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	});
};
