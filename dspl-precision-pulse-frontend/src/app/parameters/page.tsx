'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';

interface Parameter {
  id: number;
  name: string;
  enabled: boolean;
  unit: string;
  description: string;
  is_default?: boolean;
}

function ParametersPageContent() {
  const router = useRouter();
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', unit: '', description: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<number>(0);

  const sortParameters = (params: Parameter[]): Parameter[] => {
    return [...params].sort((a, b) => {
      if (a.enabled === b.enabled) {
        return a.name.localeCompare(b.name);
      }
      return a.enabled ? -1 : 1;
    });
  };

  const fetchParameters = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/parameters', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        const data = await res.json();
        const newParams = sortParameters(data.parameters || []);
        
        // Only update if parameters have changed
        if (JSON.stringify(newParams) !== JSON.stringify(parameters)) {
          console.log('[PARAMS] Parameters updated from backend');
          setParameters(newParams);
          setLastUpdate(Date.now());
        }
      } else {
        console.error('Failed to fetch parameters:', res.status, res.statusText);
      }
    } catch (err) {
      console.error('Failed to fetch parameters:', err);
    }
  };

  useEffect(() => {
    console.log('[PARAMS] Mounting parameters page');
    fetchParameters();
    
    // Poll for parameter changes every 5 seconds
    const pollInterval = setInterval(() => {
      console.log('[PARAMS] Polling for parameter changes');
      fetchParameters();
    }, 5000);
    
    // Listen for parameter changes from other tabs/windows
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'parametersUpdated') {
        console.log('[PARAMS] Storage event detected - refreshing parameters');
        fetchParameters();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      console.log('[PARAMS] Unmounting parameters page');
      clearInterval(pollInterval);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const toggleParameter = async (id: number, enabled: boolean) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/api/parameters/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ enabled: !enabled })
      });
      
      if (res.ok) {
        console.log(`[PARAMS] Parameter ${id} toggled to ${!enabled}`);
        
        // Zero-refresh: Update parameter in local state and sort
        const updated = parameters.map(p => 
          p.id === id ? {...p, enabled: !enabled} : p
        );
        const sorted = sortParameters(updated);
        setParameters(sorted);
        
        // Notify other tabs
        localStorage.setItem('parametersUpdated', Date.now().toString());
        
        // Trigger dashboard refresh
        window.dispatchEvent(new Event('parametersChanged'));
      }
    } catch (err) {
      console.error('Failed to toggle parameter');
    }
  };

  const addParameter = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/parameters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        console.log('[PARAMS] Parameter created successfully');
        setShowModal(false);
        setFormData({ name: '', unit: '', description: '' });
        
        // Zero-refresh: Add new parameter to local state and sort
        const newParam = await res.json();
        const updated = [...parameters, {
          id: newParam.parameter.id,
          name: newParam.parameter.name,
          unit: newParam.parameter.unit,
          description: newParam.parameter.description,
          enabled: newParam.parameter.enabled
        }];
        const sorted = sortParameters(updated);
        setParameters(sorted);
        
        // Notify other tabs
        localStorage.setItem('parametersUpdated', Date.now().toString());
        
        // Trigger dashboard refresh
        window.dispatchEvent(new Event('parametersChanged'));
      } else {
        const data = await res.json();
        setError(data.error || 'Failed to add parameter');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const removeParameter = async (id: number) => {
    if (confirm('Remove this parameter?')) {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5000/api/parameters/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          console.log(`[PARAMS] Parameter ${id} deleted successfully`);
          
          // Zero-refresh: Remove parameter from local state
          setParameters(parameters.filter(p => p.id !== id));
          
          // Notify other tabs
          localStorage.setItem('parametersUpdated', Date.now().toString());
        } else {
          alert('Failed to delete parameter');
        }
      } catch (err) {
        alert('Error deleting parameter');
      }
    }
  };

  const enabledCount = parameters.filter(p => p.enabled).length;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-gray-300 border-b border-gray-400 sticky top-0 z-50">
        <div className="px-4 sm:px-8 lg:px-20 py-0 flex flex-col sm:flex-row justify-between items-start sm:items-center h-auto sm:h-24 py-4 sm:py-0 gap-4 sm:gap-0">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="PrecisionPulse Logo" className="w-8 h-8 sm:w-12 sm:h-12" />
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-slate-900">PrecisionPulse</h1>
              <p className="text-xs sm:text-sm text-slate-600">Parameter Configuration</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-white hover:bg-gray-100 text-slate-900 rounded-lg font-semibold text-sm border border-gray-300"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="px-4 sm:px-8 lg:px-20 py-8 sm:py-12">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-white mb-2">Telemetry Parameters</h2>
            <p className="text-gray-400 text-sm sm:text-base lg:text-lg">Configure which parameters the desktop application should collect</p>
            {lastUpdate > 0 && (
              <p className="text-gray-500 text-xs mt-2">Last updated: {new Date(lastUpdate).toLocaleTimeString()}</p>
            )}
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-sm"
          >
            + Add Parameter
          </button>
        </div>

        <div className="bg-blue-100 border-l-4 border-blue-600 rounded-lg p-3 sm:p-4 mb-8">
          <p className="text-blue-900 text-xs sm:text-sm font-medium">
            <strong>{enabledCount}</strong> of <strong>{parameters.length}</strong> parameters enabled. 
            Desktop will collect and send only enabled parameters every 3 seconds.
          </p>
        </div>

        <div className="bg-white rounded-3xl shadow-lg overflow-x-auto">
          <table className="w-full text-sm sm:text-base">
            <thead className="bg-gray-100 border-b border-gray-300">
              <tr>
                <th className="px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Status</th>
                <th className="px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Parameter</th>
                <th className="hidden sm:table-cell px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Unit</th>
                <th className="hidden lg:table-cell px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Description</th>
                <th className="px-3 sm:px-6 py-3 sm:py-4 text-right text-xs sm:text-sm font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {parameters.map((param) => (
                <tr key={param.id} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                  <td className="px-3 sm:px-6 py-3 sm:py-4">
                    <button
                      onClick={() => toggleParameter(param.id, param.enabled)}
                      className={`px-2 sm:px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                        param.enabled 
                          ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' 
                          : 'bg-red-100 text-red-700 hover:bg-red-200'
                      }`}
                    >
                      {param.enabled ? '✓ Enabled' : '✗ Disabled'}
                    </button>
                  </td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-slate-900 font-medium text-xs sm:text-sm">{param.name}</td>
                  <td className="hidden sm:table-cell px-3 sm:px-6 py-3 sm:py-4 text-slate-700 text-xs sm:text-sm">{param.unit}</td>
                  <td className="hidden lg:table-cell px-3 sm:px-6 py-3 sm:py-4 text-slate-600 text-xs sm:text-sm">{param.description}</td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-right">
                    <button
                      onClick={() => removeParameter(param.id)}
                      className="px-2 sm:px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs sm:text-sm transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
            <h3 className="text-2xl font-bold text-slate-900 mb-6">Add New Parameter</h3>
            <form onSubmit={addParameter} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Parameter Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                  placeholder="e.g., Temperature"
                  required
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Unit</label>
                <input
                  type="text"
                  value={formData.unit}
                  onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                  placeholder="e.g., °C, kPa, L/s"
                  required
                  disabled={loading}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                  placeholder="Brief description of this parameter"
                  rows={3}
                  required
                  disabled={loading}
                />
              </div>
              {error && (
                <div className="p-4 bg-red-50 border-l-4 border-red-600 rounded-lg">
                  <p className="text-red-800 font-semibold text-sm">{error}</p>
                </div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors"
                >
                  {loading ? 'Adding...' : 'Add Parameter'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setFormData({ name: '', unit: '', description: '' }); setError(''); }}
                  className="flex-1 py-3 bg-gray-300 hover:bg-gray-400 text-slate-900 font-semibold rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ParametersPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <ParametersPageContent />
    </ProtectedRoute>
  );
}
