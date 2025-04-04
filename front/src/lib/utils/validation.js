/**
 * Form validation utilities for Arabic-focused real estate auction platform
 */

// Regular expressions for validation
const patterns = {
	email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
	phone: /^(\+?[0-9]{1,3})?[0-9]{9,12}$/,
	password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
	number: /^\d+$/,
	decimal: /^\d+(\.\d{1,2})?$/,
	url: /^(https?:\/\/)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(\/[\w-_.~:/?#[\]@!$&'()*+,;=]*)?$/,
	arabicText: /^[\u0600-\u06FF\s.,!?؟،0-9]+$/,
	arabicName: /^[\u0600-\u06FF\s]+$/,
	alphaNumeric: /^[\u0600-\u06FFa-zA-Z0-9\s.,!?؟،]+$/
};

/**
 * Object with validation rules for common fields
 */
export const rules = {
	// Basic validations
	required: (value) => (!!value && value.toString().trim() !== '') || 'هذا الحقل مطلوب',
	email: (value) => !value || patterns.email.test(value) || 'البريد الإلكتروني غير صالح',
	password: (value) =>
		!value ||
		patterns.password.test(value) ||
		'كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل وتتضمن حرف كبير وحرف صغير ورقم ورمز خاص',
	phone: (value) => !value || patterns.phone.test(value) || 'رقم الهاتف غير صالح',
	url: (value) => !value || patterns.url.test(value) || 'الرابط غير صالح',

	// Text validations
	arabicText: (value) =>
		!value || patterns.arabicText.test(value) || 'يجب إدخال نص باللغة العربية فقط',
	arabicName: (value) =>
		!value || patterns.arabicName.test(value) || 'يجب إدخال اسم باللغة العربية فقط',
	alphaNumeric: (value) =>
		!value || patterns.alphaNumeric.test(value) || 'يجب إدخال حروف وأرقام فقط',

	// Number validations
	number: (value) => !value || patterns.number.test(value) || 'يجب إدخال أرقام فقط',
	decimal: (value) =>
		!value || patterns.decimal.test(value) || 'يجب إدخال رقم صحيح أو عشري بخانتين عشريتين',
	positive: (value) => !value || parseFloat(value) > 0 || 'يجب إدخال رقم موجب',
	min: (min) => (value) =>
		!value || parseFloat(value) >= min || `يجب إدخال رقم أكبر من أو يساوي ${min}`,
	max: (max) => (value) =>
		!value || parseFloat(value) <= max || `يجب إدخال رقم أصغر من أو يساوي ${max}`,

	// Length validations
	minLength: (min) => (value) =>
		!value || value.length >= min || `يجب أن يكون طول النص ${min} حرف على الأقل`,
	maxLength: (max) => (value) =>
		!value || value.length <= max || `يجب أن لا يتجاوز طول النص ${max} حرف`,

	// Date validations
	dateFormat: (value) => {
		if (!value) return true;
		const date = new Date(value);
		return !isNaN(date.getTime()) || 'تنسيق التاريخ غير صالح';
	},
	dateFuture: (value) => {
		if (!value) return true;
		const date = new Date(value);
		const now = new Date();
		return (!isNaN(date.getTime()) && date > now) || 'يجب إدخال تاريخ مستقبلي';
	},
	datePast: (value) => {
		if (!value) return true;
		const date = new Date(value);
		const now = new Date();
		return (!isNaN(date.getTime()) && date < now) || 'يجب إدخال تاريخ سابق';
	},

	// File validations
	fileType: (types) => (file) => {
		if (!file) return true;
		const fileExtension = file.name.split('.').pop().toLowerCase();
		return (
			types.includes(fileExtension) ||
			`نوع الملف غير مسموح به. الأنواع المسموح بها: ${types.join(', ')}`
		);
	},
	fileSize: (maxSizeMB) => (file) => {
		if (!file) return true;
		const maxSizeBytes = maxSizeMB * 1024 * 1024;
		return file.size <= maxSizeBytes || `حجم الملف يجب أن لا يتجاوز ${maxSizeMB} ميجابايت`;
	},

	// Custom validations for auction platform
	propertyTitle: (value) => {
		if (!value) return 'عنوان العقار مطلوب';
		if (value.length < 5) return 'عنوان العقار يجب أن يكون 5 أحرف على الأقل';
		if (value.length > 100) return 'عنوان العقار يجب أن لا يتجاوز 100 حرف';
		return true;
	},

	startingPrice: (value) => {
		if (!value) return 'السعر الابتدائي مطلوب';
		if (isNaN(parseFloat(value))) return 'يجب إدخال رقم صحيح';
		if (parseFloat(value) <= 0) return 'يجب أن يكون السعر الابتدائي أكبر من 0';
		return true;
	},

	// Bid validation
	bidAmount: (currentBid, minIncrement) => (value) => {
		if (!value) return 'قيمة المزايدة مطلوبة';
		if (isNaN(parseFloat(value))) return 'يجب إدخال رقم صحيح';

		const minBid = currentBid + minIncrement;
		return parseFloat(value) >= minBid || `يجب أن تكون قيمة المزايدة ${minBid} على الأقل`;
	},

	// Compare two field values (e.g., password confirmation)
	match: (field, fieldName) => (value, formData) => {
		return (
			!value || !formData[field] || value === formData[field] || `يجب أن يتطابق مع ${fieldName}`
		);
	}
};

/**
 * Validate a complete form
 * @param {Object} formData - Form data object
 * @param {Object} validationSchema - Validation schema object with field names and rule arrays
 * @returns {Object} - Object with errors keyed by field name
 */
export const validateForm = (formData, validationSchema) => {
	const errors = {};

	for (const [field, fieldRules] of Object.entries(validationSchema)) {
		const value = formData[field];

		for (const rule of fieldRules) {
			const result = rule(value, formData);

			if (result !== true) {
				errors[field] = result;
				break;
			}
		}
	}

	return errors;
};

/**
 * Check if a form is valid
 * @param {Object} errors - Errors object
 * @returns {boolean} - True if the form is valid
 */
export const isFormValid = (errors) => Object.keys(errors).length === 0;

/**
 * Create a validation handler for Svelte forms
 * @param {Object} initialData - Initial form data
 * @param {Object} schema - Validation schema
 * @returns {Object} - Form handler with data, errors, and validation methods
 */
export const createForm = (initialData, schema) => {
	let data = { ...initialData };
	let errors = {};

	// Validate a single field
	const validateField = (field) => {
		const fieldRules = schema[field];
		if (!fieldRules) return true;

		for (const rule of fieldRules) {
			const result = rule(data[field], data);

			if (result !== true) {
				errors[field] = result;
				return false;
			}
		}

		// Clear error if field is valid
		if (errors[field]) {
			delete errors[field];
		}

		return true;
	};

	// Validate all fields
	const validate = () => {
		errors = {};

		for (const field in schema) {
			validateField(field);
		}

		return Object.keys(errors).length === 0;
	};

	// Update a field value and validate it
	const handleChange = (field, value) => {
		data[field] = value;
		validateField(field);
		return errors[field];
	};

	return {
		data,
		errors,
		validate,
		validateField,
		handleChange,
		isValid: () => Object.keys(errors).length === 0,
		reset: () => {
			data = { ...initialData };
			errors = {};
		}
	};
};

export default {
	rules,
	validateForm,
	isFormValid,
	createForm,
	patterns
};
