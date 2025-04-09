/**
 * Formatting Utilities
 * Functions for formatting different types of data
 */

/**
 * Format date to locale string
 * @param {string|Date} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDate = (date, options = {}) => {
	if (!date) return '';

	const defaultOptions = {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		...options
	};

	try {
		const dateObj = typeof date === 'string' ? new Date(date) : date;
		return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
	} catch (error) {
		console.error('Error formatting date:', error);
		return date.toString();
	}
};

/**
 * Format time to locale string
 * @param {string|Date} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted time string
 */
export const formatTime = (date, options = {}) => {
	if (!date) return '';

	const defaultOptions = {
		hour: 'numeric',
		minute: 'numeric',
		hour12: true,
		...options
	};

	try {
		const dateObj = typeof date === 'string' ? new Date(date) : date;
		return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
	} catch (error) {
		console.error('Error formatting time:', error);
		return date.toString();
	}
};

/**
 * Format date and time to locale string
 * @param {string|Date} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date and time string
 */
export const formatDateTime = (date, options = {}) => {
	if (!date) return '';

	const defaultOptions = {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: 'numeric',
		hour12: true,
		...options
	};

	try {
		const dateObj = typeof date === 'string' ? new Date(date) : date;
		return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
	} catch (error) {
		console.error('Error formatting date and time:', error);
		return date.toString();
	}
};

/**
 * Format currency amount
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: 'USD')
 * @param {Object} options - Intl.NumberFormat options
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'USD', options = {}) => {
	if (amount === null || amount === undefined) return '';

	const defaultOptions = {
		style: 'currency',
		currency,
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
		...options
	};

	try {
		return new Intl.NumberFormat('en-US', defaultOptions).format(amount);
	} catch (error) {
		console.error('Error formatting currency:', error);
		return `${currency} ${amount.toFixed(2)}`;
	}
};

/**
 * Format number with commas and decimal places
 * @param {number} number - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export const formatNumber = (number, decimals = 0) => {
	if (number === null || number === undefined) return '';

	try {
		return new Intl.NumberFormat('en-US', {
			minimumFractionDigits: decimals,
			maximumFractionDigits: decimals
		}).format(number);
	} catch (error) {
		console.error('Error formatting number:', error);
		return number.toFixed(decimals);
	}
};

/**
 * Format file size in bytes to human-readable format
 * @param {number} bytes - File size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted file size string
 */
export const formatFileSize = (bytes, decimals = 2) => {
	if (bytes === 0) return '0 Bytes';

	const k = 1024;
	const dm = decimals < 0 ? 0 : decimals;
	const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

	const i = Math.floor(Math.log(bytes) / Math.log(k));

	return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format percentage
 * @param {number} value - Percentage value (0-100)
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 0) => {
	if (value === null || value === undefined) return '';

	try {
		return new Intl.NumberFormat('en-US', {
			style: 'percent',
			minimumFractionDigits: decimals,
			maximumFractionDigits: decimals
		}).format(value / 100);
	} catch (error) {
		console.error('Error formatting percentage:', error);
		return `${value.toFixed(decimals)}%`;
	}
};

/**
 * Format phone number to readable format
 * @param {string} phoneNumber - Phone number to format
 * @returns {string} Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber) => {
	if (!phoneNumber) return '';

	// Remove all non-numeric characters
	const cleaned = ('' + phoneNumber).replace(/\D/g, '');

	// Format based on length
	if (cleaned.length === 10) {
		// US format: (XXX) XXX-XXXX
		return `(${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)}-${cleaned.substring(6, 10)}`;
	} else if (cleaned.length === 11 && cleaned.charAt(0) === '1') {
		// US with country code: +1 (XXX) XXX-XXXX
		return `+1 (${cleaned.substring(1, 4)}) ${cleaned.substring(4, 7)}-${cleaned.substring(7, 11)}`;
	} else if (cleaned.length > 10) {
		// International format with + prefix
		return `+${cleaned}`;
	}

	// Return original if can't format
	return phoneNumber;
};

/**
 * Format address components into a readable address
 * @param {Object} address - Address object
 * @param {string} address.address - Street address
 * @param {string} address.city - City
 * @param {string} address.state - State/province
 * @param {string} address.postal_code - Postal/zip code
 * @param {string} address.country - Country
 * @returns {string} Formatted address string
 */
export const formatAddress = (address) => {
	if (!address) return '';

	const { address: street, city, state, postal_code, country } = address;

	const parts = [];
	if (street) parts.push(street);

	const cityStateZip = [city, state, postal_code].filter(Boolean).join(', ');
	if (cityStateZip) parts.push(cityStateZip);

	if (country) parts.push(country);

	return parts.join('\n');
};

/**
 * Format auction status for display
 * @param {string} status - Status code
 * @returns {Object} Object with formatted status text and CSS class
 */
export const formatAuctionStatus = (status) => {
	if (!status) return { text: 'Unknown', className: 'text-gray-500' };

	const statusMap = {
		draft: { text: 'Draft', className: 'text-gray-500' },
		scheduled: { text: 'Scheduled', className: 'text-blue-500' },
		live: { text: 'Live', className: 'text-green-500' },
		ended: { text: 'Ended', className: 'text-orange-500' },
		cancelled: { text: 'Cancelled', className: 'text-red-500' },
		completed: { text: 'Completed', className: 'text-purple-500' }
	};

	return statusMap[status] || { text: status, className: 'text-gray-500' };
};

/**
 * Format property status for display
 * @param {string} status - Status code
 * @returns {Object} Object with formatted status text and CSS class
 */
export const formatPropertyStatus = (status) => {
	if (!status) return { text: 'Unknown', className: 'text-gray-500' };

	const statusMap = {
		available: { text: 'Available', className: 'text-green-500' },
		under_contract: { text: 'Under Contract', className: 'text-blue-500' },
		sold: { text: 'Sold', className: 'text-purple-500' },
		off_market: { text: 'Off Market', className: 'text-gray-500' },
		auction: { text: 'In Auction', className: 'text-orange-500' }
	};

	return statusMap[status] || { text: status, className: 'text-gray-500' };
};

/**
 * Format contract status for display
 * @param {string} status - Status code
 * @returns {Object} Object with formatted status text and CSS class
 */
export const formatContractStatus = (status) => {
	if (!status) return { text: 'Unknown', className: 'text-gray-500' };

	const statusMap = {
		draft: { text: 'Draft', className: 'text-gray-500' },
		pending: { text: 'Pending Approval', className: 'text-orange-500' },
		active: { text: 'Active', className: 'text-green-500' },
		fulfilled: { text: 'Fulfilled', className: 'text-purple-500' },
		cancelled: { text: 'Cancelled', className: 'text-red-500' },
		expired: { text: 'Expired', className: 'text-gray-500' },
		disputed: { text: 'Disputed', className: 'text-red-500' }
	};

	return statusMap[status] || { text: status, className: 'text-gray-500' };
};

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} length - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, length = 100) => {
	if (!text) return '';

	if (text.length <= length) return text;

	return text.substring(0, length) + '...';
};

/**
 * Convert a string to title case
 * @param {string} text - Text to convert
 * @returns {string} Title cased text
 */
export const toTitleCase = (text) => {
	if (!text) return '';

	return text
		.toLowerCase()
		.split(' ')
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
};

/**
 * Format full name from first and last name
 * @param {Object} user - User object
 * @param {string} user.first_name - First name
 * @param {string} user.last_name - Last name
 * @returns {string} Formatted full name
 */
export const formatFullName = (user) => {
	if (!user) return '';

	const { first_name, last_name } = user;

	if (first_name && last_name) {
		return `${first_name} ${last_name}`;
	} else if (first_name) {
		return first_name;
	} else if (last_name) {
		return last_name;
	}

	return user.email || 'Unknown User';
};
