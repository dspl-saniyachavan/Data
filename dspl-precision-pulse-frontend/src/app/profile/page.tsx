'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [formData, setFormData] = useState({ currentPassword: '', newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

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
  }, [router]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (!formData.currentPassword) {
      setError('Current password is required');
      setLoading(false);
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError('New passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    if (!/[a-z]/.test(formData.newPassword)) {
      setError('Password must contain at least one lowercase letter');
      setLoading(false);
      return;
    }

    if (!/[0-9]/.test(formData.newPassword)) {
      setError('Password must contain at least one number');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/api/users/${user.id}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          currentPassword: formData.currentPassword,
          newPassword: formData.newPassword
        })
      });

      if (res.ok) {
        setSuccess('Password changed successfully');
        setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        const data = await res.json();
        setError(data.error || 'Failed to change password');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-gray-300 border-b border-gray-400 sticky top-0 z-50">
        <div className="px-8 py-0 flex justify-between items-center h-24">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="PrecisionPulse Logo" className="w-12 h-12" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900">PrecisionPulse</h1>
              <p className="text-sm text-slate-600">Profile</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-white hover:bg-gray-100 text-slate-900 rounded-lg font-semibold text-sm border border-gray-300"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-8 py-12">
        {/* Profile Info */}
        <div className="bg-white rounded-3xl shadow-lg p-8 mb-8">
          <h2 className="text-3xl font-bold text-slate-900 mb-8">Profile Information</h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-2">Name</label>
              <p className="text-xl text-slate-900 font-medium">{user.name}</p>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-2">Email</label>
              <p className="text-xl text-slate-900 font-medium">{user.email}</p>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-2">Role</label>
              <span className={`inline-block px-4 py-2 rounded-lg text-sm font-semibold ${
                user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 
                user.role === 'client' ? 'bg-blue-100 text-blue-700' :
                'bg-emerald-100 text-emerald-700'
              }`}>
                {user.role.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Change Password */}
        <div className="bg-white rounded-3xl shadow-lg p-8">
          <h2 className="text-3xl font-bold text-slate-900 mb-8">Change Password</h2>
          <form onSubmit={handlePasswordChange} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Current Password</label>
              <input
                type="password"
                value={formData.currentPassword}
                onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                required
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">New Password</label>
              <input
                type="password"
                value={formData.newPassword}
                onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                required
                disabled={loading}
              />
              <div className="mt-2 text-xs text-slate-600 space-y-1">
                <p className="font-semibold">Password must contain:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>At least 6 characters</li>
                  <li>One lowercase letter (a-z)</li>
                  <li>One number (0-9)</li>
                </ul>
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Confirm New Password</label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                required
                disabled={loading}
              />
            </div>

            {error && (
              <div className="p-4 bg-red-50 border-l-4 border-red-600 rounded-lg">
                <p className="font-semibold text-red-800">✖ Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            )}

            {success && (
              <div className="p-4 bg-emerald-50 border-l-4 border-emerald-600 rounded-lg">
                <p className="font-semibold text-emerald-800">✓ Success</p>
                <p className="text-sm text-emerald-700 mt-1">{success}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-all"
            >
              {loading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
