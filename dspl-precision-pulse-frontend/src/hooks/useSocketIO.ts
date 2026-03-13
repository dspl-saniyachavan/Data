import { useEffect, useState, useCallback } from 'react';
import io, { Socket } from 'socket.io-client';

interface UseSocketIOOptions {
  url?: string;
  autoConnect?: boolean;
}

export function useSocketIO(options: UseSocketIOOptions = {}) {
  const { url = 'http://localhost:5000', autoConnect = true } = options;
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [telemetryData, setTelemetryData] = useState<any>(null);
  const [mqttStatus, setMqttStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    if (!autoConnect) return;

    console.log('[Socket.IO] Initializing connection to', url);
    const newSocket = io(url, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
      timeout: 20000,
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true,
      forceNew: false,
      autoConnect: true
    });

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('[Socket.IO] ✓ Connected, SID:', newSocket.id);
    });

    newSocket.on('disconnect', (reason) => {
      setIsConnected(false);
      console.log('[Socket.IO] ✗ Disconnected, reason:', reason);
      
      // Don't redirect, just log and let auto-reconnect handle it
      if (reason === 'io server disconnect') {
        console.log('[Socket.IO] → Server initiated disconnect, reconnecting...');
        setTimeout(() => {
          if (!newSocket.connected) {
            newSocket.connect();
          }
        }, 1000);
      } else if (reason === 'transport close' || reason === 'transport error') {
        console.log('[Socket.IO] → Transport issue, auto-reconnect will handle it');
      } else {
        console.log('[Socket.IO] → Disconnect reason:', reason, '- auto-reconnect active');
      }
    });

    newSocket.on('connect_error', (error) => {
      console.error('[Socket.IO] ✗ Connection error:', error.message);
      setIsConnected(false);
      // Don't redirect, just log
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log('[Socket.IO] ✓ Reconnected after', attemptNumber, 'attempts');
      setIsConnected(true);
    });

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log('[Socket.IO] → Reconnection attempt', attemptNumber);
    });

    newSocket.on('reconnect_error', (error) => {
      console.error('[Socket.IO] ✗ Reconnection error:', error.message);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('[Socket.IO] ✗ Reconnection failed after all attempts');
      // Still don't redirect - keep trying in background
    });

    newSocket.on('connection_response', (data) => {
      console.log('[Socket.IO] Connection response:', data);
    });

    newSocket.on('telemetry_update', (data) => {
      console.log('[Socket.IO] Telemetry update received');
      setTelemetryData(data);
    });

    newSocket.on('mqtt_status', (data: { status: 'online' | 'offline' }) => {
      console.log('[Socket.IO] MQTT status event received:', data.status);
      setMqttStatus(data.status);
    });

    newSocket.on('error', (error) => {
      console.error('[Socket.IO] Error:', error);
    });

    setSocket(newSocket);

    return () => {
      console.log('[Socket.IO] Cleaning up connection');
      newSocket.disconnect();
    };
  }, [url, autoConnect]);

  const authenticate = useCallback((userId: string) => {
    if (socket && isConnected) {
      socket.emit('authenticate', { user_id: userId });
    }
  }, [socket, isConnected]);

  return {
    socket,
    isConnected,
    telemetryData,
    mqttStatus,
    authenticate
  };
}
