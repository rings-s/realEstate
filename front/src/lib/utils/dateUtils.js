/**
 * Date utility functions for formatting, parsing, and calculations
 */

// Import any Hijri calendar conversion library if needed
// import { toHijri, toGregorian } from '@hijri/hijri-date';

/**
 * Format date to locale string
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date
 */
export function formatDate(date, locale = 'ar-SA', options = {}) {
	if (!date) return '';

	// Default options
	const defaultOptions = {
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	};

	// Merge options
	const formatterOptions = { ...defaultOptions, ...options };

	// Create date object if string
	const dateObj = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	return new Intl.DateTimeFormat(locale, formatterOptions).format(dateObj);
}

/**
 * Format time to locale string
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted time
 */
export function formatTime(date, locale = 'ar-SA', options = {}) {
	if (!date) return '';

	// Default options
	const defaultOptions = {
		hour: '2-digit',
		minute: '2-digit'
	};

	// Merge options
	const formatterOptions = { ...defaultOptions, ...options };

	// Create date object if string
	const dateObj = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	return new Intl.DateTimeFormat(locale, formatterOptions).format(dateObj);
}

/**
 * Format date and time to locale string
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date and time
 */
export function formatDateTime(date, locale = 'ar-SA', options = {}) {
	if (!date) return '';

	// Default options
	const defaultOptions = {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	};

	// Merge options
	const formatterOptions = { ...defaultOptions, ...options };

	// Create date object if string
	const dateObj = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	return new Intl.DateTimeFormat(locale, formatterOptions).format(dateObj);
}

/**
 * Format relative time (e.g., "2 hours ago", "in 3 days")
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @returns {string} Relative time
 */
export function formatRelativeTime(date, locale = 'ar-SA') {
	if (!date) return '';

	// Create date objects
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	const now = new Date();

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	// Calculate difference in seconds
	const diffSeconds = Math.floor((dateObj - now) / 1000);
	const absDiffSeconds = Math.abs(diffSeconds);

	// Define time units in seconds
	const minute = 60;
	const hour = minute * 60;
	const day = hour * 24;
	const week = day * 7;
	const month = day * 30;
	const year = day * 365;

	// Initialize formatter
	const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

	// Format based on time difference
	if (absDiffSeconds < minute) {
		return rtf.format(diffSeconds, 'second');
	} else if (absDiffSeconds < hour) {
		return rtf.format(Math.floor(diffSeconds / minute), 'minute');
	} else if (absDiffSeconds < day) {
		return rtf.format(Math.floor(diffSeconds / hour), 'hour');
	} else if (absDiffSeconds < week) {
		return rtf.format(Math.floor(diffSeconds / day), 'day');
	} else if (absDiffSeconds < month) {
		return rtf.format(Math.floor(diffSeconds / week), 'week');
	} else if (absDiffSeconds < year) {
		return rtf.format(Math.floor(diffSeconds / month), 'month');
	} else {
		return rtf.format(Math.floor(diffSeconds / year), 'year');
	}
}

/**
 * Calculate time remaining until (or since) a date
 * @param {Date|string} targetDate - Target date
 * @returns {object} Time remaining as { days, hours, minutes, seconds, total, isNegative }
 */
export function getTimeRemaining(targetDate) {
	if (!targetDate) {
		return { days: 0, hours: 0, minutes: 0, seconds: 0, total: 0, isNegative: false };
	}

	// Create date objects
	const targetDateTime =
		typeof targetDate === 'string' ? new Date(targetDate).getTime() : targetDate.getTime();
	const now = new Date().getTime();

	// Calculate difference in milliseconds
	const difference = targetDateTime - now;
	const isNegative = difference < 0;
	const absDifference = Math.abs(difference);

	// Calculate time units
	const days = Math.floor(absDifference / (1000 * 60 * 60 * 24));
	const hours = Math.floor((absDifference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
	const minutes = Math.floor((absDifference % (1000 * 60 * 60)) / (1000 * 60));
	const seconds = Math.floor((absDifference % (1000 * 60)) / 1000);

	return {
		days,
		hours,
		minutes,
		seconds,
		total: absDifference,
		isNegative
	};
}

/**
 * Format the time remaining as a string
 * @param {object} timeRemaining - Time remaining object from getTimeRemaining()
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @returns {string} Formatted time remaining
 */
export function formatTimeRemaining(timeRemaining, locale = 'ar-SA') {
	if (!timeRemaining) return '';

	const { days, hours, minutes, seconds, isNegative } = timeRemaining;

	let result = '';

	// Add prefix for past times
	if (isNegative) {
		result += locale === 'ar-SA' ? 'منذ ' : 'Elapsed: ';
	}

	// Format different cases
	if (days > 0) {
		if (locale === 'ar-SA') {
			result += `${days} ${getPluralForm(days, 'يوم', 'يومان', 'أيام')}`;
			if (hours > 0) {
				result += ` و ${hours} ${getPluralForm(hours, 'ساعة', 'ساعتان', 'ساعات')}`;
			}
		} else {
			result += `${days} ${days === 1 ? 'day' : 'days'}`;
			if (hours > 0) {
				result += ` and ${hours} ${hours === 1 ? 'hour' : 'hours'}`;
			}
		}
	} else if (hours > 0) {
		if (locale === 'ar-SA') {
			result += `${hours} ${getPluralForm(hours, 'ساعة', 'ساعتان', 'ساعات')}`;
			if (minutes > 0) {
				result += ` و ${minutes} ${getPluralForm(minutes, 'دقيقة', 'دقيقتان', 'دقائق')}`;
			}
		} else {
			result += `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
			if (minutes > 0) {
				result += ` and ${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`;
			}
		}
	} else if (minutes > 0) {
		if (locale === 'ar-SA') {
			result += `${minutes} ${getPluralForm(minutes, 'دقيقة', 'دقيقتان', 'دقائق')}`;
			if (seconds > 0) {
				result += ` و ${seconds} ${getPluralForm(seconds, 'ثانية', 'ثانيتان', 'ثوان')}`;
			}
		} else {
			result += `${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`;
			if (seconds > 0) {
				result += ` and ${seconds} ${seconds === 1 ? 'second' : 'seconds'}`;
			}
		}
	} else {
		if (locale === 'ar-SA') {
			result += `${seconds} ${getPluralForm(seconds, 'ثانية', 'ثانيتان', 'ثوان')}`;
		} else {
			result += `${seconds} ${seconds === 1 ? 'second' : 'seconds'}`;
		}
	}

	return result;
}

/**
 * Helper function for Arabic plural forms
 * @param {number} count - Count
 * @param {string} singular - Singular form
 * @param {string} dual - Dual form
 * @param {string} plural - Plural form
 * @returns {string} Correct plural form
 */
function getPluralForm(count, singular, dual, plural) {
	if (count === 0) return plural;
	if (count === 1) return singular;
	if (count === 2) return dual;
	if (count >= 3 && count <= 10) return plural;
	return singular; // 11+ uses singular form with numbers in Arabic
}

/**
 * Add days to a date
 * @param {Date|string} date - Date object or string
 * @param {number} days - Number of days to add
 * @returns {Date} New date
 */
export function addDays(date, days) {
	const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
	dateObj.setDate(dateObj.getDate() + days);
	return dateObj;
}

/**
 * Add months to a date
 * @param {Date|string} date - Date object or string
 * @param {number} months - Number of months to add
 * @returns {Date} New date
 */
export function addMonths(date, months) {
	const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
	dateObj.setMonth(dateObj.getMonth() + months);
	return dateObj;
}

/**
 * Format date in Hijri calendar
 * Note: This requires a Hijri date conversion library
 * @param {Date|string} date - Date object or string
 * @param {string} format - Output format
 * @returns {string} Formatted Hijri date
 */
export function formatHijriDate(date, format = 'iYYYY/iMM/iDD') {
	// This is a placeholder implementation
	// To implement this properly, you would need to include a Hijri date library
	// such as moment-hijri or @hijri/hijri-date

	// Example implementation (uncomment if using a Hijri library):
	/*
  if (!date) return '';

  // Create date object if string
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  // Convert to Hijri using library
  const hijriDate = toHijri(dateObj);

  // Format based on specified format string
  let formatted = format;
  formatted = formatted.replace('iYYYY', hijriDate.year.toString());
  formatted = formatted.replace('iMM', hijriDate.month.toString().padStart(2, '0'));
  formatted = formatted.replace('iDD', hijriDate.date.toString().padStart(2, '0'));

  return formatted;
  */

	return 'Hijri date formatting requires a Hijri calendar library';
}

/**
 * Check if a date is within a range
 * @param {Date|string} date - Date to check
 * @param {Date|string} startDate - Start date of range
 * @param {Date|string} endDate - End date of range
 * @returns {boolean} True if date is within range
 */
export function isDateInRange(date, startDate, endDate) {
	// Convert to date objects if strings
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	const startObj = typeof startDate === 'string' ? new Date(startDate) : startDate;
	const endObj = typeof endDate === 'string' ? new Date(endDate) : endDate;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return false;

	// Check range
	if (startObj && !isNaN(startObj.getTime()) && dateObj < startObj) return false;
	if (endObj && !isNaN(endObj.getTime()) && dateObj > endObj) return false;

	return true;
}

/**
 * Get the first day of the month
 * @param {Date|string} date - Date object or string
 * @returns {Date} First day of the month
 */
export function getFirstDayOfMonth(date) {
	const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
	return new Date(dateObj.getFullYear(), dateObj.getMonth(), 1);
}

/**
 * Get the last day of the month
 * @param {Date|string} date - Date object or string
 * @returns {Date} Last day of the month
 */
export function getLastDayOfMonth(date) {
	const dateObj = typeof date === 'string' ? new Date(date) : new Date(date);
	return new Date(dateObj.getFullYear(), dateObj.getMonth() + 1, 0);
}

/**
 * Format date in custom format
 * @param {Date|string} date - Date object or string
 * @param {string} formatStr - Format string
 * @returns {string} Formatted date
 */
export function formatCustomDate(date, formatStr = 'YYYY-MM-DD') {
	if (!date) return '';

	// Create date object if string
	const d = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(d.getTime())) return '';

	// Get date components
	const year = d.getFullYear();
	const month = d.getMonth() + 1;
	const day = d.getDate();
	const hours = d.getHours();
	const minutes = d.getMinutes();
	const seconds = d.getSeconds();

	// Replace format placeholders
	let result = formatStr;
	result = result.replace('YYYY', year.toString());
	result = result.replace('YY', year.toString().slice(-2));
	result = result.replace('MM', month.toString().padStart(2, '0'));
	result = result.replace('M', month.toString());
	result = result.replace('DD', day.toString().padStart(2, '0'));
	result = result.replace('D', day.toString());
	result = result.replace('HH', hours.toString().padStart(2, '0'));
	result = result.replace('H', hours.toString());
	result = result.replace('mm', minutes.toString().padStart(2, '0'));
	result = result.replace('m', minutes.toString());
	result = result.replace('ss', seconds.toString().padStart(2, '0'));
	result = result.replace('s', seconds.toString());

	return result;
}

/**
 * Parse date from string
 * @param {string} dateStr - Date string
 * @param {string} format - Expected format (YYYY-MM-DD, etc.)
 * @returns {Date|null} Parsed date or null if invalid
 */
export function parseDate(dateStr, format = 'YYYY-MM-DD') {
	if (!dateStr) return null;

	try {
		// Simple implementation for common formats
		if (format === 'YYYY-MM-DD') {
			const [year, month, day] = dateStr.split('-').map(Number);
			return new Date(year, month - 1, day);
		}

		if (format === 'DD/MM/YYYY') {
			const [day, month, year] = dateStr.split('/').map(Number);
			return new Date(year, month - 1, day);
		}

		if (format === 'MM/DD/YYYY') {
			const [month, day, year] = dateStr.split('/').map(Number);
			return new Date(year, month - 1, day);
		}

		// Fallback to built-in parsing
		const date = new Date(dateStr);
		return isNaN(date.getTime()) ? null : date;
	} catch (error) {
		return null;
	}
}

/**
 * Calculate age from birthdate
 * @param {Date|string} birthdate - Birthdate
 * @returns {number} Age in years
 */
export function calculateAge(birthdate) {
	if (!birthdate) return 0;

	// Create date objects
	const birthDate = typeof birthdate === 'string' ? new Date(birthdate) : birthdate;
	const today = new Date();

	// Handle invalid dates
	if (isNaN(birthDate.getTime())) return 0;

	// Calculate age
	let age = today.getFullYear() - birthDate.getFullYear();
	const monthDiff = today.getMonth() - birthDate.getMonth();

	// Adjust age if birthday hasn't occurred yet this year
	if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
		age--;
	}

	return age;
}

/**
 * Check if a year is a leap year
 * @param {number} year - Year to check
 * @returns {boolean} True if leap year
 */
export function isLeapYear(year) {
	return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/**
 * Get the day of the week
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @returns {string} Day of the week name
 */
export function getDayOfWeek(date, locale = 'ar-SA') {
	if (!date) return '';

	// Create date object if string
	const dateObj = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	// Get day name using Intl.DateTimeFormat
	return new Intl.DateTimeFormat(locale, { weekday: 'long' }).format(dateObj);
}

/**
 * Get the month name
 * @param {Date|string} date - Date object or string
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @returns {string} Month name
 */
export function getMonthName(date, locale = 'ar-SA') {
	if (!date) return '';

	// Create date object if string
	const dateObj = typeof date === 'string' ? new Date(date) : date;

	// Handle invalid dates
	if (isNaN(dateObj.getTime())) return '';

	// Get month name using Intl.DateTimeFormat
	return new Intl.DateTimeFormat(locale, { month: 'long' }).format(dateObj);
}

/**
 * Format auction time remaining in a localized way
 * @param {string} endDate - Auction end date
 * @param {string} locale - Locale code (default: 'ar-SA')
 * @returns {object} Time remaining details and formatted string
 */
export function formatAuctionTimeRemaining(endDate, locale = 'ar-SA') {
	const timeRemaining = getTimeRemaining(endDate);

	// Return early if auction ended
	if (timeRemaining.isNegative) {
		return {
			...timeRemaining,
			formatted: locale === 'ar-SA' ? 'انتهى المزاد' : 'Auction ended'
		};
	}

	// Format the time string
	let formatted = '';

	if (timeRemaining.days > 0) {
		if (locale === 'ar-SA') {
			formatted = `${timeRemaining.days} ${getPluralForm(timeRemaining.days, 'يوم', 'يومان', 'أيام')} ${timeRemaining.hours} ${getPluralForm(timeRemaining.hours, 'ساعة', 'ساعتان', 'ساعات')}`;
		} else {
			formatted = `${timeRemaining.days}d ${timeRemaining.hours}h`;
		}
	} else if (timeRemaining.hours > 0) {
		if (locale === 'ar-SA') {
			formatted = `${timeRemaining.hours} ${getPluralForm(timeRemaining.hours, 'ساعة', 'ساعتان', 'ساعات')} ${timeRemaining.minutes} ${getPluralForm(timeRemaining.minutes, 'دقيقة', 'دقيقتان', 'دقائق')}`;
		} else {
			formatted = `${timeRemaining.hours}h ${timeRemaining.minutes}m`;
		}
	} else if (timeRemaining.minutes > 0) {
		if (locale === 'ar-SA') {
			formatted = `${timeRemaining.minutes} ${getPluralForm(timeRemaining.minutes, 'دقيقة', 'دقيقتان', 'دقائق')} ${timeRemaining.seconds} ${getPluralForm(timeRemaining.seconds, 'ثانية', 'ثانيتان', 'ثوان')}`;
		} else {
			formatted = `${timeRemaining.minutes}m ${timeRemaining.seconds}s`;
		}
	} else {
		if (locale === 'ar-SA') {
			formatted = `${timeRemaining.seconds} ${getPluralForm(timeRemaining.seconds, 'ثانية', 'ثانيتان', 'ثوان')}`;
		} else {
			formatted = `${timeRemaining.seconds}s`;
		}
	}

	return {
		...timeRemaining,
		formatted
	};
}
