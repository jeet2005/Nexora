import React, { useState, useEffect } from 'react';
import { Users as UsersIcon, Shield, Search } from 'lucide-react';
import { adminApi } from '../../api/admin';

interface AdminUserRow {
  user_id: string;
  name?: string;
  email: string;
  role: string;
  avatar_url?: string;
  created_at: string;
  datasets_count?: number;
}

export const Users: React.FC = () => {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    adminApi.listUsers()
      .then(setUsers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredUsers = users.filter(u =>
    (u.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <UsersIcon className="text-nexora-accent" size={24} />
          User Management
        </h1>
        <span className="text-sm text-gray-500">{users.length} registered users</span>
      </div>

      <div className="glass rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search users..."
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20 focus:border-nexora-accent transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-gray-100 text-sm text-gray-500 font-medium">
              <tr>
                <th className="pb-4 font-semibold px-4">User</th>
                <th className="pb-4 font-semibold px-4">Role</th>
                <th className="pb-4 font-semibold px-4">Joined</th>
                <th className="pb-4 font-semibold px-4 text-right">Datasets</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-gray-400">Loading users...</td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-gray-400">No users found.</td>
                </tr>
              ) : (
                filteredUsers.map(user => (
                  <tr key={user.user_id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        {user.avatar_url ? (
                          <img src={user.avatar_url} alt="" className="w-10 h-10 rounded-full object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-nexora-primary/10 flex items-center justify-center text-nexora-primary font-bold">
                            {(user.name || user.email).charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-gray-900">{user.name || 'Unnamed'}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                        user.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                        user.role === 'contributor' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {user.role === 'admin' && <Shield size={12} />}
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-sm text-gray-500">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-4 px-4 text-right text-sm font-medium text-gray-900">
                      {user.datasets_count ?? 0}
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
};
