// src/lib/stores/ui.js
import { writable } from 'svelte/store';

export const notifications = writable([]);
export const loading = writable(false);
export const toasts = writable([]);

let toastId = 0;

export function addToast(message, type = 'info', timeout = 5000) {
	const id = toastId++;
	const toast = { id, message, type, timeout };

	toasts.update((all) => [toast, ...all]);

	if (timeout > 0) {
		setTimeout(() => {
			removeToast(id);
		}, timeout);
	}

	return id;
}

export function removeToast(id) {
	toasts.update((all) => all.filter((t) => t.id !== id));
}

export function clearToasts() {
	toasts.set([]);
}
