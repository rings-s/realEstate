/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			// Color System
			colors: {
				primary: {
					50: '#f0f7ff',
					100: '#e0efff',
					200: '#b9ddff',
					300: '#7cc2ff',
					400: '#3aa1ff',
					500: '#0078ff', // Primary Brand Color
					600: '#0062d6',
					700: '#004eb3',
					800: '#003d8f',
					900: '#002a66',
					950: '#001947'
				},
				secondary: {
					50: '#f6f8ff',
					100: '#eef1ff',
					200: '#dde3ff',
					300: '#c1cbff',
					400: '#9da7ff',
					500: '#7b7fff', // Secondary Brand Color
					600: '#5a51ff',
					700: '#4537e5',
					800: '#382dba',
					900: '#2f2893',
					950: '#1c185d'
				},
				neutral: {
					50: '#f8fafc',
					100: '#f0f3f8',
					200: '#e2e8f0',
					300: '#cbd5e1',
					400: '#94a3b8',
					500: '#64748b',
					600: '#475569',
					700: '#334155',
					800: '#1e293b',
					900: '#0f172a',
					950: '#020617'
				},
				success: {
					50: '#ecfff4',
					100: '#d5ffe6',
					200: '#9effcd',
					300: '#47ffa4',
					400: '#1af288',
					500: '#00dd71',
					600: '#00b55c',
					700: '#008c4a',
					800: '#066a3b',
					900: '#085732',
					950: '#003119'
				},
				warning: {
					50: '#fff8ec',
					100: '#ffefd3',
					200: '#ffd9a5',
					300: '#ffbf6d',
					400: '#ff9832',
					500: '#ff7a0a',
					600: '#f45d00',
					700: '#c44102',
					800: '#9c330b',
					900: '#7d2b0c',
					950: '#431204'
				},
				error: {
					50: '#fff1f1',
					100: '#ffdfdf',
					200: '#ffc5c5',
					300: '#ff9d9d',
					400: '#ff6464',
					500: '#ff2727',
					600: '#f51616',
					700: '#cc0d0d',
					800: '#a70f0f',
					900: '#891414',
					950: '#4b0404'
				}
			},

			// Typography System
			fontFamily: {
				sans: ['IBM Plex Sans Arabic', 'sans-serif'],
				heading: ['Noto Kufi Arabic', 'serif']
			},
			fontSize: {
				'2xs': ['0.625rem', { lineHeight: '0.75rem' }], // 10px
				xs: ['0.75rem', { lineHeight: '1rem' }], // 12px
				sm: ['0.875rem', { lineHeight: '1.25rem' }], // 14px
				base: ['1rem', { lineHeight: '1.5rem' }], // 16px
				lg: ['1.125rem', { lineHeight: '1.75rem' }], // 18px
				xl: ['1.25rem', { lineHeight: '1.75rem' }], // 20px
				'2xl': ['1.5rem', { lineHeight: '2rem' }], // 24px
				'3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
				'4xl': ['2.25rem', { lineHeight: '2.5rem' }], // 36px
				'5xl': ['3rem', { lineHeight: '1' }] // 48px
			},

			// Spacing System
			spacing: {
				px: '1px',
				0.25: '0.0625rem', // 1px
				0.5: '0.125rem', // 2px
				1: '0.25rem', // 4px
				1.5: '0.375rem', // 6px
				2: '0.5rem', // 8px
				2.5: '0.625rem', // 10px
				3: '0.75rem', // 12px
				3.5: '0.875rem', // 14px
				4: '1rem', // 16px
				5: '1.25rem', // 20px
				6: '1.5rem', // 24px
				7: '1.75rem', // 28px
				8: '2rem', // 32px
				9: '2.25rem', // 36px
				10: '2.5rem', // 40px
				11: '2.75rem', // 44px
				12: '3rem', // 48px
				14: '3.5rem', // 56px
				16: '4rem', // 64px
				20: '5rem', // 80px
				24: '6rem', // 96px
				28: '7rem', // 112px
				32: '8rem', // 128px
				36: '9rem', // 144px
				40: '10rem', // 160px
				44: '11rem', // 176px
				48: '12rem', // 192px
				52: '13rem', // 208px
				56: '14rem', // 224px
				60: '15rem', // 240px
				64: '16rem', // 256px
				72: '18rem', // 288px
				80: '20rem', // 320px
				96: '24rem' // 384px
			},

			// Border Radius
			borderRadius: {
				none: '0',
				xs: '0.125rem', // 2px
				sm: '0.25rem', // 4px
				md: '0.375rem', // 6px
				lg: '0.5rem', // 8px
				xl: '0.75rem', // 12px
				'2xl': '1rem', // 16px
				'3xl': '1.5rem', // 24px
				full: '9999px'
			},

			// Shadows
			boxShadow: {
				xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
				sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
				md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
				lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
				xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
				'2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
				inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)'
			},

			// Z-index
			zIndex: {
				0: '0',
				10: '10',
				20: '20',
				30: '30',
				40: '40',
				50: '50',
				60: '60',
				70: '70',
				80: '80',
				90: '90',
				100: '100',
				nav: '1000',
				modal: '1100',
				popup: '1200',
				tooltip: '1300'
			},

			// Animation
			animation: {
				'spin-slow': 'spin 3s linear infinite',
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'bounce-slow': 'bounce 3s infinite'
			},
			transitionProperty: {
				height: 'height',
				spacing: 'margin, padding'
			},
			transitionTimingFunction: {
				'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
			},
			transitionDuration: {
				250: '250ms',
				350: '350ms',
				400: '400ms'
			}
		}
	},
	plugins: [
		require('@tailwindcss/forms'),
		require('@tailwindcss/typography'),
		require('@tailwindcss/aspect-ratio')
	]
};
