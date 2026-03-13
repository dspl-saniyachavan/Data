'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import RBACGuard from '@/components/RBACGuard';
import ModernDateTimeWidget from '@/components/ModernDateTimeWidget';
import { useSocketIO } from '@/hooks/useSocketIO';

interface Parameter {
  id: number;
  name: string;
  enabled: boolean;
  unit: string;
  description: string;
  color?: string;
}

interface TelemetryData {
  [key: string]: number;
  timestamp: number;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  label: string;
  value: string;
  time: string;
  color: string;
}

const PARAM_COLORS = [
  '#6439ff', '#54d7ff', '#f472b6', '#a78bfa',
  '#fb923c', '#34d399', '#ef4444', '#8b5cf6',
  '#06b6d4', '#10b981', '#f59e0b', '#ec4899'
];

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryData[]>([]);
  const [latestData, setLatestData] = useState<TelemetryData>({ timestamp: Date.now() });
  const [prevValues, setPrevValues] = useState<{ [key: string]: number }>({});
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, x: 0, y: 0, label: '', value: '', time: '', color: '#000' });
  const { socket, isConnected, mqttStatus } = useSocketIO();
  const [isMqttConnected, setIsMqttConnected] = useState(false);
  const [isDataStale, setIsDataStale] = useState(false);

  useEffect(() => {
    if (!socket) return;

    const handleMqttStatus = (data: { status: 'online' | 'offline' }) => {
      console.log('[MQTT] Status update received:', data.status);
      setIsMqttConnected(data.status === 'online');
    };

    socket.on('mqtt_status', handleMqttStatus);

    const checkMqttStatus = async () => {
      try {
        console.log('[MQTT] Polling status from API...');
        const res = await fetch('http://localhost:5000/api/mqtt/status');
        if (res.ok) {
          const data = await res.json();
          console.log('[MQTT] Initial status from API:', data.status);
          setIsMqttConnected(data.status === 'online');
        }
      } catch (err) {
        console.error('[MQTT] Error checking status:', err);
      }
    };
    checkMqttStatus();

    const pollInterval = setInterval(checkMqttStatus, 5000);

    // Listen for data stale/fresh events
    socket.on('data_stale', (data: any) => {
      console.log('[TELEMETRY] Data stale event received');
      setIsDataStale(true);
    });

    socket.on('data_fresh', (data: any) => {
      console.log('[TELEMETRY] Data fresh event received');
      setIsDataStale(false);
    });

    return () => {
      socket.off('mqtt_status', handleMqttStatus);
      socket.off('data_stale');
      socket.off('data_fresh');
      clearInterval(pollInterval);
    };
  }, [socket]);

  useEffect(() => {
    if (!isMqttConnected) {
      console.log('[TELEMETRY] MQTT disconnected - clearing all data');
      setTelemetryHistory([]);
      setLatestData({ timestamp: Date.now() });
      setPrevValues({});
    }
  }, [isMqttConnected]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');

    if (!token) {
      router.push('/login');
      return;
    }

    if (userData) {
      setUser(JSON.parse(userData));
    }

    const loadParameters = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/parameters', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          const data = await res.json();
          const enabledParams = (data.parameters || []).filter((p: Parameter) => p.enabled);
          setParameters(enabledParams);
          console.log('[PARAMS] Loaded parameters:', enabledParams);
        }
      } catch (err) {
        console.error('Error loading parameters:', err);
      }
    };

    loadParameters();

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'parameters') loadParameters();
    };

    const handleParametersChanged = () => loadParameters();

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('focus', loadParameters);
    window.addEventListener('parametersChanged', handleParametersChanged);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('focus', loadParameters);
      window.removeEventListener('parametersChanged', handleParametersChanged);
    };
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const loadParameters = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/parameters', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          const data = await res.json();
          const enabledParams = (data.parameters || []).filter((p: Parameter) => p.enabled);
          setParameters(enabledParams);
          console.log('[PARAMS] Loaded parameters:', enabledParams);
        }
      } catch (err) {
        console.error('Error loading parameters:', err);
      }
    };

    loadParameters();
    const paramInterval = setInterval(loadParameters, 5000);

    return () => clearInterval(paramInterval);
  }, []);

  useEffect(() => {
    if (parameters.length === 0 || !isMqttConnected || isDataStale) {
      console.log('[TELEMETRY] Skipping fetch - MQTT connected:', isMqttConnected, 'Data stale:', isDataStale);
      return;
    }

    console.log('[TELEMETRY] Starting telemetry fetch - MQTT connected');

    const fetchTelemetry = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/telemetry/latest', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          const response = await res.json();
          const data = response.data;
          
          if (data && data.parameters && Array.isArray(data.parameters)) {
            const newData: TelemetryData = { timestamp: Date.now() };
            
            data.parameters.forEach((param: any) => {
              const paramId = String(param.id);
              const value = parseFloat(param.value);
              
              if (!isNaN(value)) {
                newData[paramId] = value;
              }
            });
            
            setLatestData(prevLatest => {
              setPrevValues(prevLatest);
              return newData;
            });
            setTelemetryHistory(prev => {
              const updated = [...prev, newData];
              return updated.slice(-20);
            });
          }
        }
      } catch (err) {
        console.error('[TELEMETRY] Error fetching telemetry:', err);
      }
    };

    const telemetryInterval = setInterval(fetchTelemetry, 1000);
    fetchTelemetry();

    return () => {
      console.log('[TELEMETRY] Stopping telemetry fetch');
      clearInterval(telemetryInterval);
    };
  }, [parameters, isMqttConnected, isDataStale]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    document.cookie = 'token=; path=/; max-age=0';
    window.location.href = '/login';
  };

  const getChartColor = (paramId: number, index: number) => {
    return PARAM_COLORS[index % PARAM_COLORS.length];
  };

  const getTrendIndicator = (paramId: number) => {
    const paramIdStr = String(paramId);
    const current = latestData[paramIdStr] || 0;
    const prev = prevValues[paramIdStr] || current;
    if (current > prev + 0.1) return { symbol: '▲', color: '#059669' };
    if (current < prev - 0.1) return { symbol: '▼', color: '#dc2626' };
    return { symbol: '', color: '#64748b' };
  };

  const handlePointHover = (e: React.MouseEvent<SVGCircleElement>, label: string, value: number, timestamp: number, color: string) => {
    const svg = (e.currentTarget as SVGCircleElement).closest('svg');
    if (!svg) return;
    
    const rect = svg.getBoundingClientRect();
    const cx = parseFloat((e.currentTarget as SVGCircleElement).getAttribute('cx') || '0');
    const cy = parseFloat((e.currentTarget as SVGCircleElement).getAttribute('cy') || '0');
    
    const x = rect.left + (cx / svg.clientWidth) * rect.width;
    const y = rect.top + (cy / svg.clientHeight) * rect.height;
    
    const time = new Date(timestamp).toLocaleTimeString();
    
    setTooltip({
      visible: true,
      x,
      y,
      label,
      value: value.toFixed(2),
      time,
      color
    });
  };

  const renderLineChart = (data: number[], color: string, label: string, timestamps: number[], unit: string) => {
    if (data.length === 0 || data.length === 1) return (
      <div className="h-64 flex items-center justify-center text-gray-400 bg-slate-800 rounded-lg">
        <p>Collecting data...</p>
      </div>
    );
    
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const padding = { top: 80, right: 40, bottom: 50, left: 70 };
    const chartWidth = 1400;
    const chartHeight = 350;
    const innerWidth = chartWidth - padding.left - padding.right;
    const innerHeight = chartHeight - padding.top - padding.bottom;
    
    const points = data.map((value, index) => {
      const x = padding.left + (index / Math.max(data.length - 1, 1)) * innerWidth;
      const y = padding.top + innerHeight - ((value - min) / range) * innerHeight;
      return { x: isNaN(x) ? padding.left : x, y: isNaN(y) ? padding.top : y, value, timestamp: timestamps[index] };
    }).filter(p => !isNaN(p.x) && !isNaN(p.y));
    
    if (points.length === 0) return (
      <div className="h-64 flex items-center justify-center text-gray-400 bg-slate-800 rounded-lg">
        <p>Invalid data...</p>
      </div>
    );
    
    const pathData = points.map((point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      return `L ${point.x} ${point.y}`;
    }).join(' ');
    
    const yTicks = 5;
    const yTickValues = Array.from({ length: yTicks }, (_, i) => {
      return max - (range * i / (yTicks - 1));
    });
    
    const currentValue = data[data.length - 1];
    
    return (
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <svg width="100%" height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="overflow-visible">
          <text x={padding.left} y="35" fontSize="24" fontWeight="bold" fill="#e2e8f0">
            {label}
          </text>
          
          <text x={chartWidth - padding.right - 200} y="40" fontSize="32" fontWeight="bold" fill={color}>
            {currentValue.toFixed(1)} {unit}
          </text>
          
          <text x={chartWidth - padding.right - 200} y="60" fontSize="12" fill="#94a3b8">
            Current Value
          </text>
          
          {yTickValues.map((value, i) => {
            const y = padding.top + innerHeight - ((value - min) / range) * innerHeight;
            return (
              <g key={i}>
                <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#334155" strokeWidth="1" />
                <text x={padding.left - 10} y={y + 4} textAnchor="end" fontSize="11" fill="#64748b">
                  {value.toFixed(1)}
                </text>
              </g>
            );
          })}
          
          {[0, 10, 20, 30, 40, 50, 60].map((seconds) => {
            const x = padding.left + (seconds / 60) * innerWidth;
            return (
              <text key={seconds} x={x} y={chartHeight - 10} textAnchor="middle" fontSize="11" fill="#64748b">
                {seconds}s
              </text>
            );
          })}
          
          <path
            d={`${pathData} L ${points[points.length - 1].x} ${padding.top + innerHeight} L ${padding.left} ${padding.top + innerHeight} Z`}
            fill={color}
            fillOpacity="0.1"
          />
          
          <path d={pathData} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          
          {points.map((point, index) => (
            <g key={index}>
              <circle cx={point.x} cy={point.y} r="5" fill="#1e293b" stroke={color} strokeWidth="3" />
              <circle 
                cx={point.x} 
                cy={point.y} 
                r="8" 
                fill="transparent" 
                className="cursor-pointer"
                onMouseEnter={(e) => handlePointHover(e, label, point.value, point.timestamp, color)}
                onMouseLeave={() => setTooltip({ ...tooltip, visible: false })}
              />
            </g>
          ))}
        </svg>
      </div>
    );
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-indigo-500/20 sticky top-0 z-50">
        <div className="px-4 sm:px-8 py-4 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 lg:gap-3">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="PrecisionPulse Logo" className="w-8 h-8 sm:w-12 sm:h-12" />
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-white">PrecisionPulse</h1>
              <p className="text-xs sm:text-sm text-slate-400">Real-time Telemetry</p>
            </div>
          </div>
          
          <div className="hidden lg:block">
            <ModernDateTimeWidget />
          </div>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3 w-full lg:w-auto">
            <RBACGuard permission="manage_users">
              <button onClick={() => router.push('/users')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white rounded-lg font-semibold text-sm transition-all">
                Manage Users
              </button>
            </RBACGuard>
            <RBACGuard permission="manage_parameters">
              <button onClick={() => router.push('/parameters')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white rounded-lg font-semibold text-sm transition-all">
                Parameters
              </button>
            </RBACGuard>
            <button onClick={() => router.push('/config')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg font-semibold text-sm transition-all">
              Config
            </button>
            <button onClick={() => router.push('/history')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white rounded-lg font-semibold text-sm transition-all">
              History
            </button>
            <button onClick={() => router.push('/profile')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white rounded-lg font-semibold text-sm transition-all">
              Profile
            </button>
            <div className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg w-full sm:w-auto justify-center sm:justify-start border ${
              mqttStatus === 'online' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                mqttStatus === 'online' ? 'bg-emerald-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm font-semibold">
                {mqttStatus === 'online' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button onClick={handleLogout} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-slate-700/50 hover:bg-slate-600/50 text-slate-200 rounded-lg font-semibold text-sm border border-slate-600 transition-all">
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-8 lg:px-20 py-12">
        <div className="mb-8">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-2">Welcome back, {user.name}!</h2>
          <p className="text-slate-400 text-base sm:text-lg lg:text-xl">Monitor your telemetry streams in real-time</p>
        </div>

        {/* Live Data Stream */}
        <div className="mb-12">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Live Data Stream</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {parameters.map((param, index) => {
              const trend = getTrendIndicator(param.id);
              const color = getChartColor(param.id, index);
              const paramIdStr = String(param.id);
              const currentValue = latestData[paramIdStr];
              
              return (
                <div key={param.id} className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 shadow-lg border border-slate-700 hover:border-slate-600 transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-6xl font-bold text-white">
                      {currentValue !== undefined ? currentValue.toFixed(1) : '0.0'}
                    </div>
                    {trend.symbol && (
                    <div style={{ color: trend.color }} className="text-3xl">
                      {trend.symbol}
                    </div>
                  )}
                  </div>
                  <div className="text-slate-400 text-sm mb-4 font-medium">{param.name} ({param.unit})</div>
                  <div className="h-16 flex items-end gap-1">
                    {telemetryHistory.slice(-14).map((data, i) => {
                      const value = data[paramIdStr] || 0;
                      const values = telemetryHistory.map(d => d[paramIdStr] || 0);
                      const min = Math.min(...values);
                      const max = Math.max(...values);
                      const range = max - min || 1;
                      const height = ((value - min) / range) * 100;
                      return (
                        <div key={i} className="flex-1 rounded-t" style={{ height: `${Math.max(height, 10)}%`, backgroundColor: color }} />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Historical Trends */}
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Historical Trends</h3>
          <div className="space-y-6">
            {parameters.map((param, index) => {
              const color = getChartColor(param.id, index);
              const paramIdStr = String(param.id);
              
              return (
                <div key={param.id} className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-6 shadow-lg border border-slate-700">
                  {renderLineChart(
                    telemetryHistory.map(d => d[paramIdStr] || 0), 
                    color, 
                    param.name,
                    telemetryHistory.map(d => d.timestamp),
                    param.unit
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {tooltip.visible && (
        <div 
          className="fixed bg-slate-900 border-2 rounded px-3 py-2 text-sm font-medium pointer-events-none z-50 shadow-lg"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y - 80}px`,
            borderColor: tooltip.color,
            transform: 'translateX(-50%)'
          }}
        >
          <div style={{ color: tooltip.color }}>{tooltip.label}: {tooltip.value}</div>
          <div style={{ color: tooltip.color }} className="text-xs opacity-75">Time: {tooltip.time}</div>
        </div>
      )}
    </div>
  );
}
