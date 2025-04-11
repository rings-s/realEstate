/**
 * Comprehensive Validation Utilities for Real Estate Auction Platform
 * Mirrors backend Django model validations and adds frontend-specific checks
 */

/**
 * Validate required fields
 * @param {Object} data - Data object to validate
 * @param {string[]} requiredFields - Array of required field names
 * @returns {Object} Validation errors
 */
export function validateRequired(data, requiredFields) {
	const errors = {};
	requiredFields.forEach((field) => {
		if (!data[field] || (typeof data[field] === 'string' && data[field].trim() === '')) {
			errors[field] = `${field.replace('_', ' ').toUpperCase()} is required`;
		}
	});
	return errors;
}

/**
 * Validate string length
 * @param {Object} data - Data object to validate
 * @param {Object} lengthConstraints - Object with min and max length constraints
 * @returns {Object} Validation errors
 */
export function validateStringLength(data, lengthConstraints) {
	const errors = {};
	Object.entries(lengthConstraints).forEach(([field, { min, max }]) => {
		if (data[field]) {
			const length = data[field].length;
			if (min && length < min) {
				errors[field] =
					`${field.replace('_', ' ').toUpperCase()} must be at least ${min} characters`;
			}
			if (max && length > max) {
				errors[field] =
					`${field.replace('_', ' ').toUpperCase()} must be no more than ${max} characters`;
			}
		}
	});
	return errors;
}

/**
 * Validate numeric fields
 * @param {Object} data - Data object to validate
 * @param {Object} numericConstraints - Object with numeric validation constraints
 * @returns {Object} Validation errors
 */
export function validateNumeric(data, numericConstraints) {
	const errors = {};
	Object.entries(numericConstraints).forEach(([field, constraints]) => {
		const value = data[field];
		if (value !== undefined && value !== null) {
			const numValue = Number(value);

			// Check if value is a valid number
			if (isNaN(numValue)) {
				errors[field] = `${field.replace('_', ' ').toUpperCase()} must be a valid number`;
				return;
			}

			// Min value check
			if (constraints.min !== undefined && numValue < constraints.min) {
				errors[field] =
					`${field.replace('_', ' ').toUpperCase()} must be at least ${constraints.min}`;
			}

			// Max value check
			if (constraints.max !== undefined && numValue > constraints.max) {
				errors[field] =
					`${field.replace('_', ' ').toUpperCase()} must be no more than ${constraints.max}`;
			}

			// Decimal places check
			if (constraints.decimalPlaces !== undefined) {
				const decimalPlaces = (numValue.toString().split('.')[1] || '').length;
				if (decimalPlaces > constraints.decimalPlaces) {
					errors[field] =
						`${field.replace('_', ' ').toUpperCase()} can have at most ${constraints.decimalPlaces} decimal places`;
				}
			}
		}
	});
	return errors;
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {string|null} Error message or null
 */
export function validateEmail(email) {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	if (!email) return 'Email is required';
	if (!emailRegex.test(email)) return 'Invalid email format';
	return null;
}

/**
 * Validate phone number
 * @param {string} phone - Phone number to validate
 * @returns {string|null} Error message or null
 */
export function validatePhone(phone) {
	const phoneRegex = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;
	if (!phone) return 'Phone number is required';
	if (!phoneRegex.test(phone)) return 'Invalid phone number format';
	return null;
}

/**
 * Validate password
 * @param {string} password - Password to validate
 * @param {Object} options - Password validation options
 * @returns {string|null} Error message or null
 */
export function validatePassword(password, options = {}) {
	const {
		minLength = 8,
		requireUppercase = true,
		requireLowercase = true,
		requireNumbers = true
		// requireSpecialChars = true
	} = options;

	if (!password) return 'Password is required';

	const errors = [];

	if (password.length < minLength) {
		errors.push(`Password must be at least ${minLength} characters long`);
	}

	if (requireUppercase && !/[A-Z]/.test(password)) {
		errors.push('Password must contain at least one uppercase letter');
	}

	if (requireLowercase && !/[a-z]/.test(password)) {
		errors.push('Password must contain at least one lowercase letter');
	}

	if (requireNumbers && !/[0-9]/.test(password)) {
		errors.push('Password must contain at least one number');
	}

	// if (requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
	// 	errors.push('Password must contain at least one special character');
	// }

	return errors.length > 0 ? errors.join('. ') : null;
}

/**
 * Validate property data
 * @param {Object} propertyData - Property data to validate
 * @returns {Object} Validation errors
 */
export function validateProperty(propertyData) {
	const errors = {
		...validateRequired(propertyData, ['title', 'property_type', 'address', 'city']),
		...validateStringLength(propertyData, {
			title: { min: 5, max: 255 },
			description: { max: 2000 }
		}),
		...validateNumeric(propertyData, {
			size_sqm: { min: 0, max: 100000, decimalPlaces: 2 },
			bedrooms: { min: 0, max: 100 },
			bathrooms: { min: 0, max: 50 },
			year_built: { min: 1800, max: new Date().getFullYear() },
			market_value: { min: 0, decimalPlaces: 2 }
		})
	};

	return errors;
}

/**
 * Validate auction data
 * @param {Object} auctionData - Auction data to validate
 * @returns {Object} Validation errors
 */
export function validateAuction(auctionData) {
	const errors = {
		...validateRequired(auctionData, [
			'title',
			'auction_type',
			'start_date',
			'end_date',
			'starting_bid'
		]),
		...validateStringLength(auctionData, {
			title: { min: 5, max: 255 },
			description: { max: 2000 }
		}),
		...validateNumeric(auctionData, {
			starting_bid: { min: 0, decimalPlaces: 2 },
			reserve_price: { min: 0, decimalPlaces: 2 },
			minimum_increment: { min: 0, decimalPlaces: 2 }
		})
	};

	// Date validations
	const startDate = new Date(auctionData.start_date);
	const endDate = new Date(auctionData.end_date);

	if (startDate > endDate) {
		errors['date_range'] = 'Start date must be before end date';
	}

	return errors;
}

/**
 * Validate bid data
 * @param {Object} bidData - Bid data to validate
 * @returns {Object} Validation errors
 */
export function validateBid(bidData) {
	const errors = {
		...validateRequired(bidData, ['bid_amount', 'auction']),
		...validateNumeric(bidData, {
			bid_amount: { min: 0, decimalPlaces: 2 }
		})
	};

	return errors;
}

/**
 * Validate contract data
 * @param {Object} contractData - Contract data to validate
 * @returns {Object} Validation errors
 */
export function validateContract(contractData) {
	const errors = {
		...validateRequired(contractData, ['total_amount', 'contract_date', 'buyer', 'seller']),
		...validateNumeric(contractData, {
			total_amount: { min: 0, decimalPlaces: 2 },
			down_payment: { min: 0, decimalPlaces: 2 }
		})
	};

	// Date validations
	const contractDate = new Date(contractData.contract_date);
	const effectiveDate = new Date(contractData.effective_date);
	const expiryDate = new Date(contractData.expiry_date);

	if (effectiveDate && contractDate > effectiveDate) {
		errors['effective_date'] = 'Effective date must be after contract date';
	}

	if (expiryDate && effectiveDate > expiryDate) {
		errors['expiry_date'] = 'Expiry date must be after effective date';
	}

	return errors;
}

/**
 * Combine multiple validation error objects
 * @param {...Object} errorObjects - Validation error objects to combine
 * @returns {Object} Combined validation errors
 */
export function combineErrors(...errorObjects) {
	return errorObjects.reduce((combined, errors) => {
		return { ...combined, ...errors };
	}, {});
}

/**
 * Check if an errors object has any errors
 * @param {Object} errors - Validation errors object
 * @returns {boolean} Whether there are any errors
 */
export function hasErrors(errors) {
	return Object.keys(errors).length > 0;
}

/**
 * Get a user-friendly error message from an errors object
 * @param {Object} errors - Validation errors object
 * @returns {string} Combined error message
 */
export function getErrorMessage(errors) {
	return Object.values(errors)
		.filter((error) => error) // Remove any falsy errors
		.join('. ');
}
