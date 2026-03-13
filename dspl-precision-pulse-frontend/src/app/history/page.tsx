'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler,
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
);

interface Parameter {
  id: number;
  name: string;
  unit: string;
  min: number;
  max: number;
}

interface HistoryRecord {
  id: number;
  parameter_id: number;
  value: number;
  timestamp: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [selectedParamId, setSelectedParamId] = useState<number | null>(null);
  const [timeRange, setTimeRange] = useState<number>(60);
  const [historyData, setHistoryData] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchParameters();
  }, []);

  useEffect(() => {
    if (selectedParamId) {
      fetchHistory();
      fetchStatistics();
    }
  }, [selectedParamId, timeRange]);

  const fetchParameters = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/parameters', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setParameters(data.parameters || []);
      if (data.parameters?.length > 0) {
        setSelectedParamId(data.parameters[0].id);
      }
    } catch (error) {
      console.error('Error fetching parameters:', error);
    }
  };

  const fetchHistory = async () => {
    if (!selectedParamId) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:5000/api/parameter-stream/parameter/${selectedParamId}/history?minutes=${timeRange}&limit=1000`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const data = await response.json();
      setHistoryData(data.data || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    if (!selectedParamId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:5000/api/parameter-stream/statistics?parameter_id=${selectedParamId}&minutes=${timeRange}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const selectedParam = parameters.find(p => p.id === selectedParamId);

  const chartData = {
    labels: historyData.map(record => new Date(record.timestamp)),
    datasets: [
      {
        label: selectedParam?.name || 'Parameter',
        data: historyData.map(record => record.value),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        fill: true,
      },
    ],
  };

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#e2e8f0',
        bodyColor: '#cbd5e1',
        borderColor: '#3b82f6',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: function(context: any) {
            return `${context.parsed.y.toFixed(2)} ${selectedParam?.unit || ''}`;
          }
        }
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: (timeRange <= 60 ? 'minute' : 'hour') as any,
          displayFormats: {
            minute: 'HH:mm',
            hour: 'HH:mm'
          }
        },
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
        },
        ticks: {
          color: '#94a3b8',
        },
      },
      y: {
        grid: {
          color: 'rgba(148, 163, 184, 0.1)',
        },
        ticks: {
          color: '#94a3b8',
          callback: function(value: any) {
            return value.toFixed(1);
          }
        },
        min: selectedParam?.min,
        max: selectedParam?.max,
      },
    },
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b border-indigo-500/20 sticky top-0 z-50">
        <div className="px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button onClick={() => router.push('/dashboard')} className="text-slate-400 hover:text-white transition-colors">
              ← Back
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white">Parameter History</h1>
              <p className="text-sm text-slate-400">View historical telemetry data</p>
            </div>
          </div>
          <button onClick={handleLogout} className="px-6 py-3 bg-slate-700/50 hover:bg-slate-600/50 text-slate-200 rounded-lg font-semibold text-sm border border-slate-600 transition-all">
            Logout
          </button>
        </div>
      </div>

      <div className="px-8 py-8 space-y-6">
        {/* Filters */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-xl p-6 border border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">
                📊 Parameter
              </label>
              <select
                value={selectedParamId || ''}
                onChange={(e) => setSelectedParamId(Number(e.target.value))}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              >
                {parameters.map((param) => (
                  <option key={param.id} value={param.id}>
                    {param.name} ({param.unit})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">
                ⏱️ Time Range
              </label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              >
                <option value={5}>Last 5 minutes</option>
                <option value={15}>Last 15 minutes</option>
                <option value={30}>Last 30 minutes</option>
                <option value={60}>Last 1 hour</option>
                <option value={180}>Last 3 hours</option>
                <option value={360}>Last 6 hours</option>
                <option value={720}>Last 12 hours</option>
                <option value={1440}>Last 24 hours</option>
              </select>
            </div>
          </div>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl shadow-xl p-6 border border-blue-500">
              <div className="text-blue-100 text-sm font-semibold mb-2">📈 Records</div>
              <div className="text-4xl font-bold text-white">{statistics.count}</div>
            </div>
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-2xl shadow-xl p-6 border border-green-500">
              <div className="text-green-100 text-sm font-semibold mb-2">⬇️ Minimum</div>
              <div className="text-4xl font-bold text-white">
                {statistics.min?.toFixed(2)}
              </div>
              <div className="text-green-100 text-xs mt-1">{selectedParam?.unit}</div>
            </div>
            <div className="bg-gradient-to-br from-red-600 to-red-700 rounded-2xl shadow-xl p-6 border border-red-500">
              <div className="text-red-100 text-sm font-semibold mb-2">⬆️ Maximum</div>
              <div className="text-4xl font-bold text-white">
                {statistics.max?.toFixed(2)}
              </div>
              <div className="text-red-100 text-xs mt-1">{selectedParam?.unit}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-2xl shadow-xl p-6 border border-purple-500">
              <div className="text-purple-100 text-sm font-semibold mb-2">📊 Average</div>
              <div className="text-4xl font-bold text-white">
                {statistics.avg?.toFixed(2)}
              </div>
              <div className="text-purple-100 text-xs mt-1">{selectedParam?.unit}</div>
            </div>
          </div>
        )}

        {/* Chart */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-xl p-8 border border-slate-700">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              {selectedParam?.name || 'Parameter'} Trend
            </h2>
            <p className="text-slate-400 text-sm">
              Showing {historyData.length} data points over the last {timeRange < 60 ? `${timeRange} minutes` : `${timeRange / 60} hours`}
            </p>
          </div>
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-slate-400 text-lg">Loading data...</div>
            </div>
          ) : historyData.length > 0 ? (
            <div className="h-96">
              <Line data={chartData} options={chartOptions} />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-96 text-slate-400">
              <svg className="w-24 h-24 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-lg">No data available for this time range</p>
            </div>
          )}
        </div>

        {/* Data Table */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-xl overflow-hidden border border-slate-700">
          <div className="px-8 py-6 border-b border-slate-700">
            <h2 className="text-xl font-bold text-white">📋 Recent Records</h2>
            <p className="text-slate-400 text-sm mt-1">Showing up to 50 most recent data points</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {historyData.slice(0, 50).map((record, index) => (
                  <tr key={record.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-8 py-4 whitespace-nowrap text-sm text-slate-300">
                      {new Date(record.timestamp).toLocaleString()}
                    </td>
                    <td className="px-8 py-4 whitespace-nowrap text-sm font-semibold text-white">
                      {record.value.toFixed(2)} {selectedParam?.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
