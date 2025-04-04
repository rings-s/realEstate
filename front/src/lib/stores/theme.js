import { derived, get } from 'svelte/store';
import { uiStore, theme as uiTheme } from './ui';

// Re-export the theme store from ui.js
export const theme = uiTheme;

// Implement toggleTheme function
export const toggleTheme = () => {
	const currentTheme = get(theme);
	const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
	uiStore.setTheme(newTheme);
};

// Initialize theme from localStorage
if (typeof window !== 'undefined') {
	const savedTheme = localStorage.getItem('theme');
	if (savedTheme === 'dark' || savedTheme === 'light') {
		uiStore.setTheme(savedTheme);
	} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
		// Use dark theme if user prefers dark mode and no theme is saved
		uiStore.setTheme('dark');
	} else {
		// Default to light theme
		uiStore.setTheme('light');
	}

	// Ensure dark class is applied on page load if needed
	if (
		savedTheme === 'dark' ||
		(savedTheme !== 'light' &&
			window.matchMedia &&
			window.matchMedia('(prefers-color-scheme: dark)').matches)
	) {
		document.documentElement.classList.add('dark');
	} else {
		document.documentElement.classList.remove('dark');
	}
}
