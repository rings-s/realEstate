import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { isAuthenticated } from './auth';

// Create RTC store
const createRtcStore = () => {
  // Define initial state
  const initialState = {
    connected: false,
    connections: {}, // Key-value pairs of connection ID to connection object
    activeRooms: {}, // Rooms the user has joined
    messages: {}, // Messages by room
    participantsByRoom: {}, // Participants by room
    error: null
  };

  const { subscribe, set, update } = writable(initialState);

  // Setup WebSocket connection
  const setupWebSocket = (roomId, type = 'auction') => {
    try {
      if (!browser) return null;

      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Authentication required');
      }

      // WebSocket URL based on room type
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsBase = import.meta.env.VITE_WS_URL || `${wsProtocol}//${window.location.host}`;
      let wsUrl;

      switch (type) {
        case 'auction':
          wsUrl = `${wsBase}/ws/auctions/${roomId}/?token=${token}`;
          break;
        case 'chat':
          wsUrl = `${wsBase}/ws/messages/${roomId}/?token=${token}`;
          break;
        default:
          wsUrl = `${wsBase}/ws/${type}/${roomId}/?token=${token}`;
      }

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        update(state => ({
          ...state,
          connected: true,
          connections: {
            ...state.connections,
            [roomId]: ws
          },
          activeRooms: {
            ...state.activeRooms,
            [roomId]: { type, lastJoined: new Date() }
          }
        }));
      };

      ws.onclose = () => {
        update(state => {
          // Remove connection from connections
          const { [roomId]: _, ...remainingConnections } = state.connections;

          // Remove room from active rooms
          const { [roomId]: __, ...remainingRooms } = state.activeRooms;

          return {
            ...state,
            connections: remainingConnections,
            activeRooms: remainingRooms,
            connected: Object.keys(remainingConnections).length > 0
          };
        });
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error for ${type} room ${roomId}:`, error);
        update(state => ({ ...state, error }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'message':
              // Handle chat messages
              update(state => {
                const roomMessages = state.messages[roomId] || [];
                return {
                  ...state,
                  messages: {
                    ...state.messages,
                    [roomId]: [...roomMessages, data.message]
                  }
                };
              });
              break;

            case 'bid':
              // Handle auction bids
              // You might want to handle this differently or emit an event
              update(state => {
                const roomMessages = state.messages[roomId] || [];
                return {
                  ...state,
                  messages: {
                    ...state.messages,
                    [roomId]: [...roomMessages, {
                      type: 'bid',
                      content: data.bid,
                      sender: data.bidder,
                      timestamp: new Date().toISOString()
                    }]
                  }
                };
              });
              break;

            case 'participant_joined':
            case 'participant_left':
              // Update participants list for room
              update(state => {
                return {
                  ...state,
                  participantsByRoom: {
                    ...state.participantsByRoom,
                    [roomId]: data.participants
                  }
                };
              });
              break;

            default:
              // For other message types, just store in messages
              update(state => {
                const roomMessages = state.messages[roomId] || [];
                return {
                  ...state,
                  messages: {
                    ...state.messages,
                    [roomId]: [...roomMessages, data]
                  }
                };
              });
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };

      return ws;
    } catch (error) {
      console.error('Error setting up WebSocket:', error);
      update(state => ({ ...state, error }));
      return null;
    }
  };

  return {
    subscribe,

    // Join a room by ID
    joinRoom: (roomId, type = 'auction') => {
      if (!browser) return;

      // Check if already connected to this room
      const store = get({ subscribe });
      if (store.connections[roomId]) {
        console.log(`Already connected to ${type} room ${roomId}`);
        return;
      }

      // Setup WebSocket connection
      setupWebSocket(roomId, type);
    },

    // Leave a room by ID
    leaveRoom: (roomId) => {
      if (!browser) return;

      update(state => {
        const connection = state.connections[roomId];
        if (connection) {
          connection.close();
        }

        // Connection will be removed in onclose handler
        return state;
      });
    },

    // Send message to a room
    sendMessage: (roomId, message) => {
      if (!browser) return;

      const store = get({ subscribe });
      const connection = store.connections[roomId];

      if (!connection) {
        console.error(`Not connected to room ${roomId}`);
        return false;
      }

      if (connection.readyState === WebSocket.OPEN) {
        connection.send(JSON.stringify(message));
        return true;
      } else {
        console.error(`Connection to room ${roomId} is not open`);
        return false;
      }
    },

    // Clear messages for a room
    clearMessages: (roomId) => {
      update(state => {
        const { [roomId]: _, ...remainingMessages } = state.messages;
        return {
          ...state,
          messages: remainingMessages
        };
      });
    },

    // Leave all rooms
