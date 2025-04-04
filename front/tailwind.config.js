/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				// Primary: Deep blue color scheme
				primary: {
					50: '#EFF6FF', // Lightest blue
					100: '#DBEAFE',
					200: '#BFDBFE',
					300: '#93C5FD',
					400: '#60A5FA',
					500: '#3B82F6', // Default blue
					600: '#2563EB',
					700: '#1D4ED8',
					800: '#1E40AF',
					900: '#1E3A8A',
					950: '#172554' // Darkest blue
				},

				// Secondary: Emerald green color scheme
				secondary: {
					50: '#ECFDF5',
					100: '#D1FAE5',
					200: '#A7F3D0',
					300: '#6EE7B7',
					400: '#34D399',
					500: '#10B981', // Default green
					600: '#059669',
					700: '#047857',
					800: '#065F46',
					900: '#064E3B',
					950: '#022C22'
				},

				// Accent: Purple color scheme
				accent: {
					50: '#F5F3FF',
					100: '#EDE9FE',
					200: '#DDD6FE',
					300: '#C4B5FD',
					400: '#A78BFA',
					500: '#8B5CF6', // Default purple
					600: '#7C3AED',
					700: '#6D28D9',
					800: '#5B21B6',
					900: '#4C1D95',
					950: '#2E1065'
				},

				// Neutral: Gray color scheme
				neutral: {
					50: '#F9FAFB',
					100: '#F3F4F6',
					200: '#E5E7EB',
					300: '#D1D5DB',
					400: '#9CA3AF',
					500: '#6B7280', // Default gray
					600: '#4B5563',
					700: '#374151',
					800: '#1F2937',
					900: '#111827',
					950: '#030712'
				},

				// Error: Red color scheme
				error: {
					50: '#FEF2F2',
					100: '#FEE2E2',
					200: '#FECACA',
					300: '#FCA5A5',
					400: '#F87171',
					500: '#EF4444', // Default red
					600: '#DC2626',
					700: '#B91C1C',
					800: '#991B1B',
					900: '#7F1D1D',
					950: '#450A0A'
				},

				// Warning: Amber color scheme
				warning: {
					50: '#FFFBEB',
					100: '#FEF3C7',
					200: '#FDE68A',
					300: '#FCD34D',
					400: '#FBBF24',
					500: '#F59E0B', // Default amber
					600: '#D97706',
					700: '#B45309',
					800: '#92400E',
					900: '#78350F',
					950: '#451A03'
				},

				// Success: Green color scheme
				success: {
					50: '#F0FDF4',
					100: '#DCFCE7',
					200: '#BBF7D0',
					300: '#86EFAC',
					400: '#4ADE80',
					500: '#22C55E', // Default green
					600: '#16A34A',
					700: '#15803D',
					800: '#166534',
					900: '#14532D',
					950: '#052E16'
				},

				// Info: Sky blue color scheme
				info: {
					50: '#F0F9FF',
					100: '#E0F2FE',
					200: '#BAE6FD',
					300: '#7DD3FC',
					400: '#38BDF8',
					500: '#0EA5E9', // Default sky blue
					600: '#0284C7',
					700: '#0369A1',
					800: '#075985',
					900: '#0C4A6E',
					950: '#082F49'
				},

				// Surface colors for glass effects and overlays
				surface: {
					light: 'rgba(255, 255, 255, 0.85)',
					dark: 'rgba(23, 23, 33, 0.75)',
					glass: 'rgba(255, 255, 255, 0.1)',
					overlay: 'rgba(17, 24, 39, 0.5)'
				}
			},
			fontFamily: {
				sans: ['Inter', 'IBM Plex Sans Arabic', 'Tajawal', 'sans-serif'],
				mono: ['IBM Plex Mono', 'monospace'],
				heading: ['Inter', 'Tajawal', 'IBM Plex Sans Arabic', 'sans-serif']
			},
			boxShadow: {
				sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
				DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
				md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
				lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
				xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
				'2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
				inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
				glass: '0 8px 32px 0 rgba(31, 38, 135, 0.05)',
				'glass-sm': '0 4px 16px 0 rgba(31, 38, 135, 0.05)',
				'glass-lg': '0 12px 48px 0 rgba(31, 38, 135, 0.07)',
				none: 'none'
			},
			backdropBlur: {
				xs: '2px',
				sm: '4px',
				DEFAULT: '8px',
				md: '12px',
				lg: '16px',
				xl: '24px',
				'2xl': '40px',
				'3xl': '64px'
			},
			borderRadius: {
				none: '0',
				sm: '0.125rem',
				DEFAULT: '0.25rem',
				md: '0.375rem',
				lg: '0.5rem',
				xl: '0.75rem',
				'2xl': '1rem',
				'3xl': '1.5rem',
				full: '9999px'
			},
			animation: {
				float: 'float 6s ease-in-out infinite',
				'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				fadeIn: 'fadeIn 0.5s ease-in',
				shimmer: 'shimmer 2s linear infinite'
			},
			keyframes: {
				float: {
					'0%, 100%': { transform: 'translateY(0)' },
					'50%': { transform: 'translateY(-10px)' }
				},
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' }
				},
				shimmer: {
					'0%': { backgroundPosition: '-200% 0' },
					'100%': { backgroundPosition: '200% 0' }
				}
			}
		}
	},
	plugins: [
		// Custom RTL plugin
		function ({ addUtilities }) {
			const rtlUtilities = {
				'.dir-rtl': {
					direction: 'rtl',
					textAlign: 'right'
				},
				'.dir-ltr': {
					direction: 'ltr',
					textAlign: 'left'
				}
			};
			addUtilities(rtlUtilities);
		}
	]
};
