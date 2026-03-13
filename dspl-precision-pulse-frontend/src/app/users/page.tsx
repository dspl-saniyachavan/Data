'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  isActive: boolean;
  createdAt: string;
}

function UsersPageContent() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'user' });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setCurrentUser(JSON.parse(userData));
    }
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/users', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        const data = await res.json();
        setUsers(data.map((u: any) => ({
          id: u.id.toString(),
          email: u.email,
          name: u.name,
          role: u.role,
          isActive: u.is_active,
          createdAt: u.created_at
        })));
      }
    } catch (err) {
      console.error('Failed to fetch users');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);
    
    const validationErrors: string[] = [];

    if (!editingId && users.some(u => u.email === formData.email)) {
      validationErrors.push('Email already exists');
    }

    if (!editingId && formData.password.length < 6) {
      validationErrors.push('Password must be at least 6 characters');
    }

    if (!editingId && !/[A-Z]/.test(formData.password)) {
      validationErrors.push('Password must contain at least one uppercase letter');
    }

    if (!editingId && !/[a-z]/.test(formData.password)) {
      validationErrors.push('Password must contain at least one lowercase letter');
    }

    if (!editingId && !/[0-9]/.test(formData.password)) {
      validationErrors.push('Password must contain at least one number');
    }

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const method = editingId ? 'PUT' : 'POST';
      const url = editingId ? `http://localhost:5000/api/users/${editingId}` : 'http://localhost:5000/api/users';
      const body = editingId ? { role: formData.role } : formData;
      
      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });
      
      if (res.ok) {
        setShowModal(false);
        setFormData({ name: '', email: '', password: '', role: 'user' });
        setEditingId(null);
        setErrors([]);
        
        // Zero-refresh: Update local state instead of fetching
        if (editingId) {
          setUsers(users.map(u => u.id === editingId ? {...u, role: formData.role} : u));
        } else {
          const newUser = await res.json();
          setUsers([...users, {
            id: newUser.id.toString(),
            email: newUser.email,
            name: newUser.name,
            role: newUser.role,
            isActive: newUser.is_active,
            createdAt: newUser.created_at
          }]);
        }
      } else {
        const data = await res.json();
        setErrors([data.error || (editingId ? 'Failed to update user' : 'Failed to create user')]);
      }
    } catch (err) {
      setErrors(['Network error']);
    }
  };

  const handleEdit = (user: User) => {
    setFormData({ name: user.name, email: user.email, password: '', role: user.role });
    setEditingId(user.id);
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (id === currentUser?.id) {
      alert('You cannot delete yourself!');
      return;
    }
    if (confirm('Delete this user?')) {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`http://localhost:5000/api/users/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          setUsers(users.filter(u => u.id !== id));
        } else {
          alert('Failed to delete user');
        }
      } catch (err) {
        alert('Error deleting user');
      }
    }
  };

  if (!currentUser) return null;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-gray-300 border-b border-gray-400 sticky top-0 z-50">
        <div className="px-4 sm:px-8 py-0 flex flex-col sm:flex-row justify-between items-start sm:items-center h-auto sm:h-24 py-4 sm:py-0 gap-4 sm:gap-0">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="PrecisionPulse Logo" className="w-8 h-8 sm:w-12 sm:h-12" />
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-slate-900">PrecisionPulse</h1>
              <p className="text-xs sm:text-sm text-slate-600">User Management</p>
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

      <div className="px-4 sm:px-8 lg:px-20 py-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h2 className="text-2xl sm:text-4xl font-bold text-white mb-2">Manage Users</h2>
            <p className="text-sm sm:text-lg text-gray-400">Add, edit, or remove user accounts</p>
          </div>
          <button
            onClick={() => { setShowModal(true); setEditingId(null); setFormData({ name: '', email: '', password: '', role: 'user' }); }}
            className="w-full sm:w-auto px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg"
          >
            + Add User
          </button>
        </div>

        {/* Info box */}
        <div className="bg-blue-100 border-l-4 border-blue-600 rounded-lg p-4 mb-8">
          <p className="text-blue-900 text-sm font-medium">
            Total users: {users.length}. Manage user accounts and permissions.
          </p>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-3xl shadow-lg overflow-hidden overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-gray-100 border-b border-gray-300">
              <tr>
                <th className="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Name</th>
                <th className="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Email</th>
                <th className="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Role</th>
                <th className="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Status</th>
                <th className="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold text-slate-900">Created</th>
                <th className="px-3 sm:px-6 py-4 text-right text-xs sm:text-sm font-semibold text-slate-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                  <td className="px-3 sm:px-6 py-4 text-slate-900 font-medium text-sm">{user.name}</td>
                  <td className="px-3 sm:px-6 py-4 text-slate-700 text-sm">{user.email}</td>
                  <td className="px-3 sm:px-6 py-4">
                    <span className={`px-2 sm:px-3 py-1 rounded-lg text-xs font-semibold ${
                      user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {user.role.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 sm:px-6 py-4">
                    <span className={`px-2 sm:px-3 py-1 rounded-lg text-xs font-semibold ${
                      user.isActive ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {user.isActive ? '● Active' : '● Inactive'}
                    </span>
                  </td>
                  <td className="px-3 sm:px-6 py-4 text-slate-600 text-xs sm:text-sm">{new Date(user.createdAt).toLocaleDateString()}</td>
                  <td className="px-3 sm:px-6 py-4 text-right space-x-1 sm:space-x-2">
                    <button 
                      onClick={() => handleEdit(user)} 
                      disabled={user.email === 'admin@precisionpulse.com'}
                      className={`px-2 sm:px-3 py-1 rounded-lg text-xs sm:text-sm ${
                        user.email === 'admin@precisionpulse.com'
                          ? 'bg-gray-300 text-gray-600 cursor-not-allowed' 
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      Edit
                    </button>
                    <button 
                      onClick={() => handleDelete(user.id)} 
                      disabled={user.id === currentUser?.id || user.email === 'admin@precisionpulse.com'}
                      className={`px-2 sm:px-3 py-1 rounded-lg text-xs sm:text-sm ${
                        user.id === currentUser?.id || user.email === 'admin@precisionpulse.com'
                          ? 'bg-gray-300 text-gray-600 cursor-not-allowed' 
                          : 'bg-red-600 hover:bg-red-700 text-white'
                      }`}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
            <h3 className="text-2xl font-bold text-slate-900 mb-6">{editingId ? 'Edit User Role' : 'Add New User'}</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                  required
                  disabled={!!editingId}
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                  required
                  disabled={!!editingId}
                />
              </div>
              {!editingId && (
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Password</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                    required
                  />
                  <div className="mt-2 text-xs text-slate-600 space-y-1">
                    <p className="font-semibold">Password must contain:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>At least 6 characters</li>
                      <li>One uppercase letter (A-Z)</li>
                      <li>One lowercase letter (a-z)</li>
                      <li>One number (0-9)</li>
                    </ul>
                  </div>
                </div>
              )}
              {errors.length > 0 && (
                <div className="p-4 bg-red-50 border-l-4 border-red-600 rounded-lg">
                  <p className="text-red-800 font-semibold text-sm mb-2">Please fix the following errors:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {errors.map((error, index) => (
                      <li key={index} className="text-red-700 text-sm">{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none text-slate-900"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg">
                  {editingId ? 'Update' : 'Create'}
                </button>
                <button type="button" onClick={() => { setShowModal(false); setEditingId(null); }} className="flex-1 py-3 bg-gray-300 hover:bg-gray-400 text-slate-900 font-semibold rounded-lg">
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

export default function UsersPage() {
  return (
    <ProtectedRoute allowedRoles={['admin']}>
      <UsersPageContent />
    </ProtectedRoute>
  );
}
