/**
 * Svelte action to detect clicks outside of an element
 * Used for dropdowns, modals, etc.
 *
 * @param {HTMLElement} node - The element to detect clicks outside of
 * @param {Function} callback - Function to call when a click outside is detected
 * @returns {Object} - Svelte action object with destroy method
 *
 * Usage:
 * <div use:clickOutside={handleClickOutside}>...</div>
 */
/**
 * Svelte action that dispatches an event when a click occurs outside of an element
 */
export function clickOutside(node, { enabled = true, callback = () => {} } = {}) {
	const handleOutsideClick = (event) => {
		if (!node.contains(event.target)) {
			if (callback) callback(event);
			node.dispatchEvent(new CustomEvent('outclick'));
		}
	};

	function update({ enabled: newEnabled }) {
		if (newEnabled) {
			window.addEventListener('click', handleOutsideClick);
		} else {
			window.removeEventListener('click', handleOutsideClick);
		}
	}

	update({ enabled });

	return {
		update,
		destroy() {
			window.removeEventListener('click', handleOutsideClick);
		}
	};
}

export default clickOutside;
