'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSocketIO } from '@/hooks/useSocketIO';

interface Config {
  id: number;
  key: string;
  value: string;
  description: string;
  category: string;
  data_type: string;
  is_sensitive: boolean;
  updated_at: string;
  updated_by: string;
}

export default function ConfigPage() {
  const router = useRouter();
  const [configs, setConfigs] = useState<Config[]>([]);
  const [filteredConfigs, setFilteredConfigs] = useState<Config[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState<Config | null>(null);
  const [newValue, setNewValue] = useState('');
  const { socket } = useSocketIO();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    loadConfigs();
    loadCategories();
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handleConfigUpdate = (data: any) => {
      console.log('[CONFIG] Update received:', data);
      loadConfigs();
    };

    socket.on('config_update', handleConfigUpdate);
    socket.on('config_bulk_update', handleConfigUpdate);

    return () => {
      socket.off('config_update', handleConfigUpdate);
      socket.off('config_bulk_update', handleConfigUpdate);
    };
  }, [socket]);

  useEffect(() => {
    if (selectedCategory === 'all') {
      setFilteredConfigs(configs);
    } else {
      setFilteredConfigs(configs.filter(c => c.category === selectedCategory));
    }
  }, [selectedCategory, configs]);

  const loadConfigs = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/config/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setConfigs(data.configs || []);
      }
    } catch (err) {
      console.error('Error loading configs:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/config/categories', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const handleEdit = (config: Config) => {
    setEditingConfig(config);
    setNewValue(config.value);
  };

  const handleSave = async () => {
    if (!editingConfig) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/api/config/${editingConfig.key}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ value: newValue })
      });

      if (res.ok) {
        loadConfigs();
        setEditingConfig(null);
        setNewValue('');
      }
    } catch (err) {
      console.error('Error updating config:', err);
    }
  };

  const handleCancel = () => {
    setEditingConfig(null);
    setNewValue('');
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="bg-gray-300 border-b border-gray-400 sticky top-0 z-50">
        <div className="px-8 py-6 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="Logo" className="w-12 h-12" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900">System Configuration</h1>
              <p className="text-sm text-slate-600">Manage system settings</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
            >
              Back to Dashboard
            </button>
            <button
              onClick={loadConfigs}
              className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="px-20 py-12">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h2 className="text-4xl font-bold text-white mb-2">Configuration Settings</h2>
            <p className="text-gray-400 text-lg">
              {loading ? 'Loading...' : `${filteredConfigs.length} settings`}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <label className="text-white font-semibold">Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="bg-slate-950 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-800">
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Updated
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredConfigs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                    No configurations found
                  </td>
                </tr>
              ) : (
                filteredConfigs.map((config) => (
                  <tr key={config.id} className="hover:bg-slate-900 transition-colors">
                    <td className="px-6 py-4 text-white font-medium font-mono text-sm">
                      {config.key}
                    </td>
                    <td className="px-6 py-4">
                      {editingConfig?.id === config.id ? (
                        <input
                          type="text"
                          value={newValue}
                          onChange={(e) => setNewValue(e.target.value)}
                          className="px-3 py-1 bg-slate-800 text-white rounded border border-slate-700 w-full"
                        />
                      ) : (
                        <span className="text-emerald-400 font-mono text-sm">
                          {config.value}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-blue-900/30 text-blue-400 rounded text-xs font-semibold">
                        {config.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm">
                      {config.description || '-'}
                    </td>
                    <td className="px-6 py-4 text-gray-500 text-xs">
                      {new Date(config.updated_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      {editingConfig?.id === config.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSave}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm font-semibold"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancel}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm font-semibold"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleEdit(config)}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-semibold"
                        >
                          Edit
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
