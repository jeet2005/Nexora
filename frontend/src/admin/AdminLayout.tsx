import React, { useEffect, useState } from 'react';
import { Outlet, Navigate, useNavigate, NavLink } from 'react-router-dom';
import { adminApi } from '../api/admin';
import NexoraLogo from '../components/NexoraLogo';
import { LayoutDashboard, Key, Database, Activity, FileText, LogOut, ShieldAlert, Users, ScrollText } from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    adminApi.getMe()
      .then(() => setIsAuthenticated(true))
      .catch(() => setIsAuthenticated(false));
  }, []);

  const handleLogout = async () => {
    try {
      await adminApi.logout();
      navigate('/admin/login');
    } catch (e) {
      console.error(e);
    }
  };

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-nexora-bg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-nexora-accent"></div>
      </div>
    );
  }

  if (isAuthenticated === false) {
    return <Navigate to="/admin/login" replace />;
  }

  const navItems = [
    { to: '/admin', icon: <LayoutDashboard size={20} />, label: 'Dashboard', end: true },
    { to: '/admin/keys', icon: <Key size={20} />, label: 'API Keys' },
    { to: '/admin/datasets', icon: <Database size={20} />, label: 'Datasets & Training' },
    { to: '/admin/users', icon: <Users size={20} />, label: 'Users' },
    { to: '/admin/drift', icon: <ShieldAlert size={20} />, label: 'Drift Alerts' },
    { to: '/admin/health', icon: <Activity size={20} />, label: 'System Health' },
    { to: '/admin/content', icon: <FileText size={20} />, label: 'Content' },
    { to: '/admin/audit', icon: <ScrollText size={20} />, label: 'Audit Log' },
  ];

  return (
    <div className="min-h-screen flex bg-nexora-bg font-sans text-nexora-dark">
      {/* Sidebar */}
      <aside className="w-64 border-r border-nexora-border bg-white/50 backdrop-blur flex flex-col sticky top-0 h-screen">
        <div className="h-16 flex items-center px-6 border-b border-nexora-border">
          <NexoraLogo size="sm" />
        </div>
        <div className="px-6 py-2 text-xs font-bold tracking-wider text-nexora-dark/50 uppercase mt-4">
          Admin Panel
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive 
                    ? 'bg-nexora-accent/10 text-nexora-accent' 
                    : 'text-nexora-dark/70 hover:bg-black/5 hover:text-nexora-dark'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-nexora-border">
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-8 relative">
        <div className="absolute inset-0 bg-grid-fine opacity-20 pointer-events-none" />
        <div className="relative z-10 max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
