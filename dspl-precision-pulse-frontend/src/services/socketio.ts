import io, { Socket } from 'socket.io-client';

interface SocketIOServiceInterface {
  socket: Socket | null;
  isConnected: boolean;
  listeners: { [key: string]: Function[] };
  connect(url?: string): Promise<void>;
  disconnect(): void;
  authenticate(userId: string): void;
  on(event: string, callback: Function): void;
  off(event: string, callback: Function): void;
  emit(event: string, data: any): void;
  getConnectionStatus(): boolean;
}

class SocketIOService implements SocketIOServiceInterface {
  socket: Socket | null = null;
  isConnected: boolean = false;
  listeners: { [key: string]: Function[] } = {};

  connect(url: string = 'http://localhost:5000'): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(url, {
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionDelayMax: 5000,
          reconnectionAttempts: 5,
          transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
          this.isConnected = true;
          console.log('[Socket.IO] Connected to server');
          this.emit('connection_status', { connected: true });
          resolve();
        });

        this.socket.on('disconnect', () => {
          this.isConnected = false;
          console.log('[Socket.IO] Disconnected from server');
          this.emit('connection_status', { connected: false });
        });

        this.socket.on('telemetry_update', (data: any) => {
          this.emit('telemetry_update', data);
        });

        this.socket.on('connection_response', (data: any) => {
          console.log('[Socket.IO] Server response:', data);
        });

        this.socket.on('error', (error: any) => {
          console.error('[Socket.IO] Error:', error);
          this.emit('connection_error', error);
        });

        this.socket.on('connect_error', (error: any) => {
          console.error('[Socket.IO] Connection error:', error);
          this.emit('connection_error', error);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.isConnected = false;
    }
  }

  authenticate(userId: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('authenticate', { user_id: userId });
    }
  }

  on(event: string, callback: Function): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event: string, callback: Function): void {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event: string, data: any): void {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }
}

export default new SocketIOService();
