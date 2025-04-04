/**
 * Arabic language utilities for Real Estate Auction Platform
 */

/**
 * Arabic character ranges and special characters
 */
export const ARABIC_CHAR_RANGES = {
	// Basic Arabic characters
	BASIC: '\u0621-\u063A\u0641-\u064A',
	// Arabic-Indic digits
	DIGITS: '\u0660-\u0669',
	// Arabic punctuation
	PUNCTUATION: '\u060C\u060D\u061B\u061E\u061F\u066A-\u066D\u06D4',
	// Tatweel (kashida), diacritics and other shapes
	EXTRAS: '\u0640\u064B-\u065F\u0670\u06C1\u06CC\u06D2',
	// Ligatures like Allah
	LIGATURES: '\u0671-\u06B7\u06BA-\u06C0\u06C2-\u06CB\u06CD-\u06D1\u06D3\u06D5',
	// All Arabic Unicode ranges combined
	ALL: '\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF'
};

/**
 * Test if a string contains only Arabic characters
 * @param {string} text - Text to test
 * @returns {boolean} True if text contains only Arabic characters
 */
export const isArabicOnly = (text) => {
	if (!text) return false;

	// Regex that allows Arabic characters, numbers, space and punctuation
	const arabicRegex = new RegExp(`^[${ARABIC_CHAR_RANGES.ALL}\\s0-9.,!?؟،:;\\-()]+$`);
	return arabicRegex.test(text);
};

/**
 * Test if a string contains Arabic characters
 * @param {string} text - Text to test
 * @returns {boolean} True if text contains Arabic characters
 */
export const containsArabic = (text) => {
	if (!text) return false;

	const arabicRegex = new RegExp(`[${ARABIC_CHAR_RANGES.BASIC}]`);
	return arabicRegex.test(text);
};

/**
 * Get Arabic letter forms (isolated, initial, medial, final)
 * @param {string} letter - Arabic letter
 * @returns {Object} Letter forms
 */
export const getLetterForms = (letter) => {
	const arabicForms = {
		ا: { isolated: 'ا', initial: 'ا', medial: 'ـا', final: 'ـا' },
		ب: { isolated: 'ب', initial: 'بـ', medial: 'ـبـ', final: 'ـب' },
		ت: { isolated: 'ت', initial: 'تـ', medial: 'ـتـ', final: 'ـت' },
		ث: { isolated: 'ث', initial: 'ثـ', medial: 'ـثـ', final: 'ـث' },
		ج: { isolated: 'ج', initial: 'جـ', medial: 'ـجـ', final: 'ـج' },
		ح: { isolated: 'ح', initial: 'حـ', medial: 'ـحـ', final: 'ـح' },
		خ: { isolated: 'خ', initial: 'خـ', medial: 'ـخـ', final: 'ـخ' },
		د: { isolated: 'د', initial: 'د', medial: 'ـد', final: 'ـد' },
		ذ: { isolated: 'ذ', initial: 'ذ', medial: 'ـذ', final: 'ـذ' },
		ر: { isolated: 'ر', initial: 'ر', medial: 'ـر', final: 'ـر' },
		ز: { isolated: 'ز', initial: 'ز', medial: 'ـز', final: 'ـز' },
		س: { isolated: 'س', initial: 'سـ', medial: 'ـسـ', final: 'ـس' },
		ش: { isolated: 'ش', initial: 'شـ', medial: 'ـشـ', final: 'ـش' },
		ص: { isolated: 'ص', initial: 'صـ', medial: 'ـصـ', final: 'ـص' },
		ض: { isolated: 'ض', initial: 'ضـ', medial: 'ـضـ', final: 'ـض' },
		ط: { isolated: 'ط', initial: 'طـ', medial: 'ـطـ', final: 'ـط' },
		ظ: { isolated: 'ظ', initial: 'ظـ', medial: 'ـظـ', final: 'ـظ' },
		ع: { isolated: 'ع', initial: 'عـ', medial: 'ـعـ', final: 'ـع' },
		غ: { isolated: 'غ', initial: 'غـ', medial: 'ـغـ', final: 'ـغ' },
		ف: { isolated: 'ف', initial: 'فـ', medial: 'ـفـ', final: 'ـف' },
		ق: { isolated: 'ق', initial: 'قـ', medial: 'ـقـ', final: 'ـق' },
		ك: { isolated: 'ك', initial: 'كـ', medial: 'ـكـ', final: 'ـك' },
		ل: { isolated: 'ل', initial: 'لـ', medial: 'ـلـ', final: 'ـل' },
		م: { isolated: 'م', initial: 'مـ', medial: 'ـمـ', final: 'ـم' },
		ن: { isolated: 'ن', initial: 'نـ', medial: 'ـنـ', final: 'ـن' },
		ه: { isolated: 'ه', initial: 'هـ', medial: 'ـهـ', final: 'ـه' },
		و: { isolated: 'و', initial: 'و', medial: 'ـو', final: 'ـو' },
		ي: { isolated: 'ي', initial: 'يـ', medial: 'ـيـ', final: 'ـي' },
		ى: { isolated: 'ى', initial: 'ى', medial: 'ـى', final: 'ـى' },
		ء: { isolated: 'ء', initial: 'ء', medial: 'ء', final: 'ء' },
		آ: { isolated: 'آ', initial: 'آ', medial: 'ـآ', final: 'ـآ' },
		ة: { isolated: 'ة', initial: 'ة', medial: 'ـة', final: 'ـة' },
		ؤ: { isolated: 'ؤ', initial: 'ؤ', medial: 'ـؤ', final: 'ـؤ' },
		ئ: { isolated: 'ئ', initial: 'ئـ', medial: 'ـئـ', final: 'ـئ' }
	};

	return arabicForms[letter] || null;
};

/**
 * Arabic diacritics (tashkeel) characters
 */
export const DIACRITICS = [
	'\u064B', // FATHATAN
	'\u064C', // DAMMATAN
	'\u064D', // KASRATAN
	'\u064E', // FATHA
	'\u064F', // DAMMA
	'\u0650', // KASRA
	'\u0651', // SHADDA
	'\u0652', // SUKUN
	'\u0653', // MADDAH
	'\u0654', // HAMZA ABOVE
	'\u0655', // HAMZA BELOW
	'\u0670' // SUPERSCRIPT ALEF
];

/**
 * Remove diacritics (tashkeel) from an Arabic text
 * @param {string} text - Text with diacritics
 * @returns {string} Text without diacritics
 */
export const removeDiacritics = (text) => {
	if (!text) return '';

	const diacriticsRegex = new RegExp(`[${DIACRITICS.join('')}]`, 'g');
	return text.replace(diacriticsRegex, '');
};

/**
 * Convert Farsi/Persian characters to Arabic
 * @param {string} text - Text with Farsi characters
 * @returns {string} Text with Arabic characters
 */
export const persianToArabic = (text) => {
	if (!text) return '';

	const charMap = {
		ی: 'ي', // YEH
		ک: 'ك', // KAF
		گ: 'غ', // GAF to GHAIN
		چ: 'تش', // CHEH to TEH + SHEEN
		پ: 'ب', // PEH to BEH
		ژ: 'ز', // JEH to ZAIN
		ۀ: 'ة' // HEH WITH YEH ABOVE to TEH MARBUTA
	};

	return text.replace(/[یکگچپژۀ]/g, (match) => charMap[match]);
};

/**
 * Get Arabic day name
 * @param {number} dayIndex - Day index (0-6, 0 is Sunday)
 * @returns {string} Arabic day name
 */
export const getArabicDayName = (dayIndex) => {
	const days = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];

	return days[dayIndex] || '';
};

/**
 * Get Arabic month name
 * @param {number} monthIndex - Month index (0-11, 0 is January)
 * @returns {string} Arabic month name
 */
export const getArabicMonthName = (monthIndex) => {
	const months = [
		'يناير',
		'فبراير',
		'مارس',
		'أبريل',
		'مايو',
		'يونيو',
		'يوليو',
		'أغسطس',
		'سبتمبر',
		'أكتوبر',
		'نوفمبر',
		'ديسمبر'
	];

	return months[monthIndex] || '';
};

/**
 * Generate an Arabic slug for SEO-friendly URLs
 * @param {string} text - Text to convert to slug
 * @returns {string} Arabic slug
 */
export const generateArabicSlug = (text) => {
	if (!text) return '';

	// Remove diacritics
	let slug = removeDiacritics(text);

	// Replace spaces and special characters with hyphens
	slug = slug.replace(/[\s\u060C\u060D\u061B\u061E\u061F\u066A-\u066D\u06D4.,!?؟]/g, '-');

	// Replace multiple hyphens with a single hyphen
	slug = slug.replace(/-+/g, '-');

	// Remove leading and trailing hyphens
	slug = slug.replace(/^-+|-+$/g, '');

	return slug;
};

/**
 * Get the appropriate Arabic numeric suffix (ordinal)
 * @param {number} num - Number
 * @returns {string} Arabic ordinal
 */
export const getArabicOrdinal = (num) => {
	if (typeof num !== 'number') return '';

	if (num === 1) return 'الأول';
	if (num === 2) return 'الثاني';
	if (num === 3) return 'الثالث';
	if (num === 4) return 'الرابع';
	if (num === 5) return 'الخامس';
	if (num === 6) return 'السادس';
	if (num === 7) return 'السابع';
	if (num === 8) return 'الثامن';
	if (num === 9) return 'التاسع';
	if (num === 10) return 'العاشر';

	// For numbers beyond 10
	return `رقم ${num}`;
};

/**
 * Parse Arabic numbers to JavaScript numbers
 * @param {string} arabicNumber - Number in Arabic numerals
 * @returns {number} JavaScript number
 */
export const parseArabicNumber = (arabicNumber) => {
	if (!arabicNumber) return NaN;

	const digitMap = {
		'٠': '0',
		'١': '1',
		'٢': '2',
		'٣': '3',
		'٤': '4',
		'٥': '5',
		'٦': '6',
		'٧': '7',
		'٨': '8',
		'٩': '9'
	};

	// Replace Arabic digits with Latin digits
	const numStr = arabicNumber.replace(/[٠-٩]/g, (match) => digitMap[match]);

	return parseFloat(numStr);
};

/**
 * Get grammatical number form for Arabic (singular, dual, plural)
 * @param {number} count - Count
 * @param {string} singular - Singular form
 * @param {string} dual - Dual form
 * @param {string} plural - Plural form
 * @returns {string} Appropriate form
 */
export const getArabicNumberForm = (count, singular, dual, plural) => {
	if (count === 0) return plural;
	if (count === 1) return singular;
	if (count === 2) return dual;
	if (count >= 3 && count <= 10) return plural;
	return plural; // For counts 11+, rules get more complex in Arabic
};

/**
 * Arabic definite article handling - el/al (ال) assimilation
 * Some Arabic letters cause the lam in 'al' to be assimilated
 * @param {string} word - Arabic word
 * @returns {string} Word with proper definite article
 */
export const arabicDefiniteArticle = (word) => {
	if (!word) return '';

	// List of sun letters that cause assimilation
	const sunLetters = 'تثدذرزسشصضطظلن';

	// Check if word starts with a sun letter
	if (word.length > 0 && sunLetters.includes(word[0])) {
		// Use 'a' + doubled first letter (assimilation)
		return `ا${word[0]}${word}`;
	}

	// Otherwise use 'al'
	return `ال${word}`;
};

/**
 * Arabic text reshaper (primitive)
 * For proper Arabic text display, characters should connect properly
 * This is a basic implementation - for production, use a library like arabic-reshaper
 * @param {string} text - Arabic text to reshape
 * @returns {string} Reshaped text
 */
export const reshapeArabic = (text) => {
	// This is a placeholder for a more complex reshaping algorithm
	// For production, use a proper library like arabic-reshaper

	return text;
};

export default {
	ARABIC_CHAR_RANGES,
	DIACRITICS,
	isArabicOnly,
	containsArabic,
	getLetterForms,
	removeDiacritics,
	persianToArabic,
	getArabicDayName,
	getArabicMonthName,
	generateArabicSlug,
	getArabicOrdinal,
	parseArabicNumber,
	getArabicNumberForm,
	arabicDefiniteArticle,
	reshapeArabic
};
