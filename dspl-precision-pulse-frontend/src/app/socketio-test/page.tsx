'use client';

import { useEffect, useState } from 'react';
import { useSocketIO } from '@/hooks/useSocketIO';

export default function SocketIOTestPage() {
  const { socket, isConnected, mqttStatus } = useSocketIO();
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [`[${timestamp}] ${message}`, ...prev].slice(0, 50));
  };

  useEffect(() => {
    if (!socket) return;

    addLog('Socket.IO initialized');

    socket.on('connection_response', (data) => {
      addLog(`Connection: ${JSON.stringify(data)}`);
    });

    socket.on('pong', (data) => {
      addLog(`Pong: ${JSON.stringify(data)}`);
    });

    socket.on('telemetry', (data) => {
      addLog(`Telemetry received`);
    });

    socket.on('mqtt_status', (data) => {
      addLog(`MQTT: ${data.status}`);
    });

    return () => {
      socket.off('connection_response');
      socket.off('pong');
      socket.off('telemetry');
      socket.off('mqtt_status');
    };
  }, [socket]);

  useEffect(() => {
    addLog(`Status: ${isConnected ? 'CONNECTED' : 'DISCONNECTED'}`);
  }, [isConnected]);

  const sendPing = () => {
    if (socket && isConnected) {
      socket.emit('ping');
      addLog('Ping sent');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Socket.IO Test</h1>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className={`p-6 rounded-lg border-2 ${isConnected ? 'bg-green-900/20 border-green-500' : 'bg-red-900/20 border-red-500'}`}>
            <div className="text-sm text-slate-400 mb-2">Socket.IO</div>
            <div className="text-2xl font-bold text-white">{isConnected ? 'Connected' : 'Disconnected'}</div>
          </div>

          <div className={`p-6 rounded-lg border-2 ${mqttStatus === 'online' ? 'bg-blue-900/20 border-blue-500' : 'bg-orange-900/20 border-orange-500'}`}>
            <div className="text-sm text-slate-400 mb-2">MQTT</div>
            <div className="text-2xl font-bold text-white">{mqttStatus}</div>
          </div>

          <div className="p-6 rounded-lg border-2 bg-purple-900/20 border-purple-500">
            <div className="text-sm text-slate-400 mb-2">Logs</div>
            <div className="text-2xl font-bold text-white">{logs.length}</div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 mb-8 border border-slate-700">
          <button
            onClick={sendPing}
            disabled={!isConnected}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-semibold"
          >
            Send Ping
          </button>
          <button
            onClick={() => setLogs([])}
            className="ml-4 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold"
          >
            Clear Logs
          </button>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">Logs</h2>
          <div className="bg-slate-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {logs.map((log, i) => (
              <div key={i} className="text-slate-300 py-1">{log}</div>
            ))}
          </div>
        </div>

        <div className="mt-8">
          <a href="/dashboard" className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold inline-block">
            ← Back
          </a>
        </div>
      </div>
    </div>
  );
}
