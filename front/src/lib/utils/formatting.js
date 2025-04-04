/**
 * Data formatting utilities for the Arabic real estate auction platform
 */

// Format dates to Arabic locale with Gregorian calendar
const ARABIC_LOCALE = 'ar-SA';
const ENGLISH_NUMERALS_LOCALE = 'ar-EG-u-nu-latn'; // Arabic locale with Latin numerals

/**
 * Format date in Arabic format
 * @param {Date|string|number} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted date
 */
export const formatDate = (date, options = {}, useEnglishNumerals = true) => {
	if (!date) return '';

	const dateObj = typeof date === 'object' ? date : new Date(date);

	if (isNaN(dateObj.getTime())) {
		console.warn('Invalid date:', date);
		return '';
	}

	const defaultOptions = {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		calendar: 'gregory'
	};

	const mergedOptions = { ...defaultOptions, ...options };
	const locale = useEnglishNumerals ? ENGLISH_NUMERALS_LOCALE : ARABIC_LOCALE;

	try {
		return new Intl.DateTimeFormat(locale, mergedOptions).format(dateObj);
	} catch (error) {
		console.error('Error formatting date:', error);
		return '';
	}
};

/**
 * Format date and time in Arabic format
 * @param {Date|string|number} date - Date to format
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted date and time
 */
export const formatDateTime = (date, useEnglishNumerals = true) => {
	return formatDate(
		date,
		{
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: 'numeric',
			minute: 'numeric',
			calendar: 'gregory'
		},
		useEnglishNumerals
	);
};

/**
 * Format a short date (day/month/year)
 * @param {Date|string|number} date - Date to format
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted short date
 */
export const formatShortDate = (date, useEnglishNumerals = true) => {
	return formatDate(
		date,
		{
			year: 'numeric',
			month: 'numeric',
			day: 'numeric',
			calendar: 'gregory'
		},
		useEnglishNumerals
	);
};

/**
 * Format time
 * @param {Date|string|number} date - Date to format
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted time
 */
export const formatTime = (date, useEnglishNumerals = true) => {
	return formatDate(
		date,
		{
			hour: 'numeric',
			minute: 'numeric',
			calendar: 'gregory'
		},
		useEnglishNumerals
	);
};

/**
 * Format relative time (e.g., "منذ 5 دقائق")
 * @param {Date|string|number} date - Date to format
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted relative time
 */
export const formatRelativeTime = (date, useEnglishNumerals = true) => {
	if (!date) return '';

	const dateObj = typeof date === 'object' ? date : new Date(date);

	if (isNaN(dateObj.getTime())) {
		console.warn('Invalid date:', date);
		return '';
	}

	const now = new Date();
	const diffMs = now - dateObj;
	const diffSecs = Math.floor(diffMs / 1000);
	const diffMins = Math.floor(diffSecs / 60);
	const diffHours = Math.floor(diffMins / 60);
	const diffDays = Math.floor(diffHours / 24);

	// Format the number based on locale
	const formatNum = (num) => {
		if (useEnglishNumerals) return num.toString();
		return new Intl.NumberFormat(ARABIC_LOCALE).format(num);
	};

	if (diffSecs < 60) {
		return 'الآن';
	} else if (diffMins < 60) {
		return `منذ ${formatNum(diffMins)} ${getPluralForm(diffMins, 'دقيقة', 'دقيقتان', 'دقائق')}`;
	} else if (diffHours < 24) {
		return `منذ ${formatNum(diffHours)} ${getPluralForm(diffHours, 'ساعة', 'ساعتان', 'ساعات')}`;
	} else if (diffDays < 30) {
		return `منذ ${formatNum(diffDays)} ${getPluralForm(diffDays, 'يوم', 'يومان', 'أيام')}`;
	} else {
		return formatDate(date, undefined, useEnglishNumerals);
	}
};

/**
 * Format remaining time for auctions (e.g., "متبقي 2 ساعة و 15 دقيقة")
 * @param {Date|string|number} endDate - End date
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted remaining time
 */
export const formatRemainingTime = (endDate, useEnglishNumerals = true) => {
	if (!endDate) return '';

	const end = typeof endDate === 'object' ? endDate : new Date(endDate);

	if (isNaN(end.getTime())) {
		console.warn('Invalid date:', endDate);
		return '';
	}

	const now = new Date();

	// If auction has ended
	if (now >= end) {
		return 'انتهى';
	}

	const diffMs = end - now;
	const diffSecs = Math.floor(diffMs / 1000);
	const diffMins = Math.floor(diffSecs / 60);
	const diffHours = Math.floor(diffMins / 60);
	const diffDays = Math.floor(diffHours / 24);

	// Format the number based on locale
	const formatNum = (num) => {
		if (useEnglishNumerals) return num.toString();
		return new Intl.NumberFormat(ARABIC_LOCALE).format(num);
	};

	// Calculate remaining hours, minutes, seconds
	const remainingHours = diffHours % 24;
	const remainingMins = diffMins % 60;
	const remainingSecs = diffSecs % 60;

	if (diffDays > 0) {
		return `${formatNum(diffDays)} ${getPluralForm(diffDays, 'يوم', 'يومان', 'أيام')} ${remainingHours > 0 ? ` و ${formatNum(remainingHours)} ${getPluralForm(remainingHours, 'ساعة', 'ساعتان', 'ساعات')}` : ''}`;
	} else if (diffHours > 0) {
		return `${formatNum(diffHours)} ${getPluralForm(diffHours, 'ساعة', 'ساعتان', 'ساعات')} ${remainingMins > 0 ? ` و ${formatNum(remainingMins)} ${getPluralForm(remainingMins, 'دقيقة', 'دقيقتان', 'دقائق')}` : ''}`;
	} else if (diffMins > 0) {
		return `${formatNum(diffMins)} ${getPluralForm(diffMins, 'دقيقة', 'دقيقتان', 'دقائق')} ${remainingSecs > 0 ? ` و ${formatNum(remainingSecs)} ${getPluralForm(remainingSecs, 'ثانية', 'ثانيتان', 'ثوان')}` : ''}`;
	} else {
		return `${formatNum(diffSecs)} ${getPluralForm(diffSecs, 'ثانية', 'ثانيتان', 'ثوان')}`;
	}
};

/**
 * Format currency in Saudi Riyal (SAR)
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: SAR)
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted currency
 */
export const formatCurrency = (amount, currency = 'SAR', useEnglishNumerals = true) => {
	if (amount === null || amount === undefined) return '';

	const locale = useEnglishNumerals ? ENGLISH_NUMERALS_LOCALE : ARABIC_LOCALE;

	try {
		return new Intl.NumberFormat(locale, {
			style: 'currency',
			currency,
			maximumFractionDigits: 2,
			minimumFractionDigits: 0
		}).format(amount);
	} catch (error) {
		console.error('Error formatting currency:', error);
		return '';
	}
};

/**
 * Format number with thousands separator
 * @param {number} number - Number to format
 * @param {number} fractionDigits - Number of decimal places
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted number
 */
export const formatNumber = (number, fractionDigits = 0, useEnglishNumerals = true) => {
	if (number === null || number === undefined) return '';

	const locale = useEnglishNumerals ? ENGLISH_NUMERALS_LOCALE : ARABIC_LOCALE;

	try {
		return new Intl.NumberFormat(locale, {
			maximumFractionDigits: fractionDigits,
			minimumFractionDigits: fractionDigits
		}).format(number);
	} catch (error) {
		console.error('Error formatting number:', error);
		return '';
	}
};

/**
 * Format a percentage
 * @param {number} value - Percentage value (e.g., 0.75)
 * @param {number} fractionDigits - Number of decimal places
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted percentage
 */
export const formatPercentage = (value, fractionDigits = 0, useEnglishNumerals = true) => {
	if (value === null || value === undefined) return '';

	const locale = useEnglishNumerals ? ENGLISH_NUMERALS_LOCALE : ARABIC_LOCALE;

	try {
		return new Intl.NumberFormat(locale, {
			style: 'percent',
			maximumFractionDigits: fractionDigits,
			minimumFractionDigits: fractionDigits
		}).format(value);
	} catch (error) {
		console.error('Error formatting percentage:', error);
		return '';
	}
};

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted file size
 */
export const formatFileSize = (bytes, useEnglishNumerals = true) => {
	if (bytes === 0) return '0 بايت';

	const k = 1024;
	const sizes = ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت', 'تيرابايت'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));

	return `${formatNumber(parseFloat((bytes / Math.pow(k, i)).toFixed(2)), 2, useEnglishNumerals)} ${sizes[i]}`;
};

/**
 * Format a phone number in Arabic style
 * @param {string} phoneNumber - Phone number to format
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber) => {
	if (!phoneNumber) return '';

	// Remove non-digit characters
	const digits = phoneNumber.replace(/\D/g, '');

	// Format based on length and country code
	if (digits.startsWith('966')) {
		// Saudi Arabian number
		if (digits.length === 12) {
			return `+${digits.slice(0, 3)} ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8)}`;
		}
	}

	// Default formatting (groups of 3-4 digits)
	if (digits.length === 10) {
		return `${digits.slice(0, 3)} ${digits.slice(3, 6)} ${digits.slice(6)}`;
	} else if (digits.length > 10) {
		return `+${digits.slice(0, digits.length - 9)} ${digits.slice(-9, -6)} ${digits.slice(-6, -3)} ${digits.slice(-3)}`;
	}

	// If no special formatting, just group in threes
	return digits.replace(/(\d{3})(?=\d)/g, '$1 ');
};

/**
 * Truncate text to a specific length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} length - Maximum length
 * @param {string} suffix - Suffix to add if truncated
 * @returns {string} Truncated text
 */
export const truncateText = (text, length = 100, suffix = '...') => {
	if (!text) return '';

	return text.length > length ? text.substring(0, length - suffix.length) + suffix : text;
};

/**
 * Get the appropriate Arabic plural form based on number
 * @param {number} number - The number
 * @param {string} singular - Singular form (1)
 * @param {string} dual - Dual form (2)
 * @param {string} plural - Plural form (3-10)
 * @param {string} manyPlural - Many plural form (11+)
 * @returns {string} The appropriate plural form
 */
export const getPluralForm = (number, singular, dual, plural, manyPlural = plural) => {
	if (number === 0) return plural;
	if (number === 1) return singular;
	if (number === 2) return dual;
	if (number >= 3 && number <= 10) return plural;
	return manyPlural; // For numbers 11+
};

/**
 * Format a location as a human-readable address
 * @param {Object} location - Location object with coordinates
 * @param {string} defaultText - Default text if location is missing
 * @returns {string} Formatted location
 */
export const formatLocation = (location, defaultText = 'لم يتم تحديد الموقع') => {
	if (!location) return defaultText;

	try {
		// If location is a string (JSON), parse it
		const locationObj = typeof location === 'string' ? JSON.parse(location) : location;

		if (locationObj.address) {
			return locationObj.address;
		}

		if (locationObj.latitude && locationObj.longitude) {
			return `${formatNumber(locationObj.latitude, 6)}, ${formatNumber(locationObj.longitude, 6)}`;
		}
	} catch (error) {
		console.error('Error formatting location:', error);
	}

	return defaultText;
};

/**
 * Format property area with unit
 * @param {number} area - Area value
 * @param {string} unit - Unit of measurement (default: m²)
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted area
 */
export const formatArea = (area, unit = 'م²', useEnglishNumerals = true) => {
	if (area === null || area === undefined) return '';
	return `${formatNumber(area, 2, useEnglishNumerals)} ${unit}`;
};

/**
 * Format property price per square meter
 * @param {number} price - Total price
 * @param {number} area - Area in square meters
 * @param {boolean} useEnglishNumerals - Whether to use English (Latin) numerals
 * @returns {string} Formatted price per square meter
 */
export const formatPricePerSqm = (price, area, useEnglishNumerals = true) => {
	if (!price || !area || area <= 0) return '';

	const pricePerSqm = price / area;
	return `${formatCurrency(pricePerSqm, 'SAR', useEnglishNumerals)}/م²`;
};

/**
 * Format a validation error message
 * @param {Object|string} error - Error object or message
 * @returns {string} Formatted error message
 */
export const formatValidationError = (error) => {
	if (!error) return '';

	if (typeof error === 'string') return error;

	if (typeof error === 'object') {
		// If error has a message property
		if (error.message) return error.message;

		// If error is a complex object, stringify it
		try {
			return JSON.stringify(error);
		} catch (e) {
			return 'خطأ في التحقق من الصحة';
		}
	}

	return 'خطأ في التحقق من الصحة';
};

/**
 * Format validation errors from backend response
 * @param {Object} errors - Validation errors object
 * @returns {Object} Formatted validation errors
 */
export const formatValidationErrors = (errors) => {
	if (!errors) return {};

	// If errors is already an object with field keys
	if (typeof errors === 'object' && !Array.isArray(errors)) {
		const formatted = {};
		for (const [field, message] of Object.entries(errors)) {
			formatted[field] = Array.isArray(message) ? message[0] : message;
		}
		return formatted;
	}

	// If errors is a string
	if (typeof errors === 'string') {
		return { general: errors };
	}

	// If errors is an array
	if (Array.isArray(errors)) {
		return { general: errors.join(', ') };
	}

	return {};
};

export default {
	formatDate,
	formatDateTime,
	formatShortDate,
	formatTime,
	formatRelativeTime,
	formatRemainingTime,
	formatCurrency,
	formatNumber,
	formatPercentage,
	formatFileSize,
	formatPhoneNumber,
	truncateText,
	getPluralForm,
	formatLocation,
	formatArea,
	formatPricePerSqm,
	formatValidationError,
	formatValidationErrors
};
