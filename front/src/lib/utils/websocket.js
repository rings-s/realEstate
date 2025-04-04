/**
 * WebSocket utilities for real-time communication
 */
import { browser } from '$app/environment';

/**
 * Create a WebSocket connection with authentication
 * @param {string} path - WebSocket path/endpoint
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection and handlers
 */
export const createWebSocketConnection = (path, options = {}) => {
	if (!browser) {
		return {
			socket: null,
			isConnected: false,
			connect: () => {},
			disconnect: () => {},
			send: () => {},
			onMessage: () => {},
			onError: () => {},
			onOpen: () => {},
			onClose: () => {}
		};
	}

	const {
		secure = window.location.protocol === 'https:',
		host = window.location.host,
		reconnectInterval = 5000,
		maxReconnectAttempts = 5,
		onMessage = () => {},
		onOpen = () => {},
		onClose = () => {},
		onError = () => {},
		autoReconnect = true
	} = options;

	// Get authentication token
	const token = localStorage.getItem('access_token');

	// Construct WebSocket URL
	const protocol = secure ? 'wss://' : 'ws://';
	const baseURL = import.meta.env.VITE_WS_URL || `${protocol}${host}`;
	const wsPath = path.startsWith('/') ? path : `/${path}`;
	const wsURL = `${baseURL}${wsPath}${token ? `?token=${token}` : ''}`;

	let socket = null;
	let isConnected = false;
	let reconnectCount = 0;
	let reconnectTimeout = null;

	// Create WebSocket connection
	const connect = () => {
		try {
			// Clear any pending reconnection
			if (reconnectTimeout) {
				clearTimeout(reconnectTimeout);
				reconnectTimeout = null;
			}

			// Close existing connection if any
			if (
				socket &&
				(socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)
			) {
				socket.close();
			}

			socket = new WebSocket(wsURL);

			socket.onopen = (event) => {
				isConnected = true;
				reconnectCount = 0;
				console.log(`WebSocket connected: ${wsURL}`);
				onOpen(event);
			};

			socket.onclose = (event) => {
				isConnected = false;
				console.log(`WebSocket closed: ${wsURL}`);
				onClose(event);

				// Attempt to reconnect if enabled
				if (autoReconnect && reconnectCount < maxReconnectAttempts) {
					reconnectCount++;
					console.log(`Attempting to reconnect (${reconnectCount}/${maxReconnectAttempts})...`);
					reconnectTimeout = setTimeout(connect, reconnectInterval);
				}
			};

			socket.onerror = (error) => {
				console.error(`WebSocket error:`, error);
				onError(error);
			};

			socket.onmessage = (event) => {
				// Parse message data
				try {
					const data = JSON.parse(event.data);
					onMessage(data, event);
				} catch (error) {
					console.error('Error parsing WebSocket message:', error);
					onMessage(event.data, event);
				}
			};

			return socket;
		} catch (error) {
			console.error('Error creating WebSocket connection:', error);
			onError(error);
			return null;
		}
	};

	// Disconnect WebSocket
	const disconnect = () => {
		if (reconnectTimeout) {
			clearTimeout(reconnectTimeout);
			reconnectTimeout = null;
		}

		if (socket) {
			socket.close();
			socket = null;
			isConnected = false;
		}
	};

	// Send message through WebSocket
	const send = (data) => {
		if (!socket || socket.readyState !== WebSocket.OPEN) {
			console.error('WebSocket is not connected');
			return false;
		}

		try {
			// Convert data to string if it's an object
			const message = typeof data === 'object' ? JSON.stringify(data) : data;
			socket.send(message);
			return true;
		} catch (error) {
			console.error('Error sending WebSocket message:', error);
			onError(error);
			return false;
		}
	};

	// Initial connection
	connect();

	return {
		socket,
		isConnected: () => isConnected,
		connect,
		disconnect,
		send,
		onMessage: (callback) => {
			onMessage = callback;
		},
		onOpen: (callback) => {
			onOpen = callback;
		},
		onClose: (callback) => {
			onClose = callback;
		},
		onError: (callback) => {
			onError = callback;
		}
	};
};

/**
 * Create a connection for a specific auction room
 * @param {string|number} auctionId - Auction ID
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection
 */
export const connectToAuctionRoom = (auctionId, options = {}) => {
	return createWebSocketConnection(`ws/auctions/${auctionId}/`, options);
};

/**
 * Create a connection for a specific message thread
 * @param {string|number} threadId - Message thread ID
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection
 */
export const connectToMessageThread = (threadId, options = {}) => {
	return createWebSocketConnection(`ws/messages/${threadId}/`, options);
};

/**
 * Create a connection for real-time notifications
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection
 */
export const connectToNotifications = (options = {}) => {
	return createWebSocketConnection('ws/notifications/', options);
};

/**
 * Create a connection for live property viewings
 * @param {string|number} propertyId - Property ID
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection
 */
export const connectToPropertyViewing = (propertyId, options = {}) => {
	return createWebSocketConnection(`ws/property-viewings/${propertyId}/`, options);
};

/**
 * Create a connection for a contract signing room
 * @param {string|number} contractId - Contract ID
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket connection
 */
export const connectToContractRoom = (contractId, options = {}) => {
	return createWebSocketConnection(`ws/contracts/${contractId}/`, options);
};

export default {
	createWebSocketConnection,
	connectToAuctionRoom,
	connectToMessageThread,
	connectToNotifications,
	connectToPropertyViewing,
	connectToContractRoom
};
