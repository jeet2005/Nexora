import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bell,
  MessageSquare,
  Shield,
  Trophy,
  User,
  Download,
  FolderKanban,
  PlusCircle,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import NexoraLogo from './NexoraLogo';
import { useAuth } from '../contexts/AuthContext';
import LoginModal from './LoginModal';
import { useEffect, useState, useRef } from 'react';
import { userApi } from '../api/users';
import { communityApi } from '../api/community';

export default function Layout() {
  const location = useLocation();
  const isDesktop = typeof window !== 'undefined' && navigator.userAgent.includes('Electron');
  const { user, signOut } = useAuth();
  const [isLoginModalOpen, setLoginModalOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user) {
      setAvatarUrl(null);
      setUnreadCount(0);
      return;
    }
    userApi
      .getMe()
      .then((profile) => setAvatarUrl(profile.avatar_url ?? null))
      .catch(() => setAvatarUrl(null));

    communityApi
      .getNotifications()
      .then((notes) => setUnreadCount(notes.filter((n) => !n.read).length))
      .catch(() => setUnreadCount(0));
  }, [user]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navLinks = [
    { to: '/datasets', label: 'My Datasets', icon: FolderKanban },
    { to: '/cybershield', label: 'CyberShield', icon: Shield },
    { to: '/community', label: 'Community', icon: Trophy },
    { to: '/feedback', label: 'Feedback', icon: MessageSquare },
  ];

  if (!isDesktop) {
    navLinks.push({ to: '/download', label: 'Desktop App', icon: Download });
  }

  return (
    <div className="min-h-screen flex flex-col bg-nexora-bg relative overflow-x-hidden">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-500/5 rounded-full blur-3xl" />
      </div>

      {/* Common Header Navbar */}
      <header className="fixed top-0 inset-x-0 z-50 border-b border-gray-200/80 bg-white/90 backdrop-blur-md shadow-xs">
        <motion.div
          className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between relative z-10"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Brand Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5 group hover:opacity-90 transition-all shrink-0"
          >
            <NexoraLogo size="sm" />
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;

              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3.5 py-2 rounded-xl text-sm font-medium flex items-center gap-2 transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-700 font-semibold shadow-xs'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/80'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600' : 'text-gray-400'}`} />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Section Actions */}
          <div className="flex items-center gap-3">
            {/* New Dataset Action Button */}
            <Link
              to="/"
              className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-sm transition-all"
            >
              <PlusCircle className="w-4 h-4 text-emerald-100" />
              <span>New Dataset</span>
            </Link>

            {/* Notification Bell Icon */}
            <Link
              to="/notifications"
              className="relative p-2 rounded-xl border border-gray-200 text-gray-600 hover:text-emerald-600 hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors"
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell className="w-4.5 h-4.5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4.5 h-4.5 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center shadow-xs animate-pulse">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>

            {/* User Profile / Auth State */}
            {user ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-gray-100/80 transition-colors border border-transparent hover:border-gray-200"
                >
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt="Avatar"
                      className="w-8 h-8 rounded-full border border-emerald-300 object-cover"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm border border-emerald-200">
                      {user.email ? user.email[0].toUpperCase() : <User size={16} />}
                    </div>
                  )}
                  <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                </button>

                {/* Dropdown Menu */}
                {userDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 8, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 8, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-gray-200/90 shadow-xl py-2 z-50 text-sm text-gray-700"
                  >
                    <div className="px-4 py-2 border-b border-gray-100">
                      <p className="text-xs text-gray-400 font-medium">Signed in as</p>
                      <p className="font-semibold text-gray-900 truncate">{user.email}</p>
                    </div>

                    <Link
                      to="/profile"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 hover:bg-emerald-50 text-gray-700 hover:text-emerald-700 transition-colors"
                    >
                      <User className="w-4 h-4 text-emerald-600" />
                      <span>My Profile & Models</span>
                    </Link>

                    <Link
                      to="/datasets"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2 hover:bg-emerald-50 text-gray-700 hover:text-emerald-700 transition-colors"
                    >
                      <FolderKanban className="w-4 h-4 text-emerald-600" />
                      <span>My Datasets</span>
                    </Link>

                    <button
                      type="button"
                      onClick={() => {
                        setUserDropdownOpen(false);
                        signOut();
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-2 text-rose-600 hover:bg-rose-50 transition-colors border-t border-gray-100 mt-1"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </motion.div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setLoginModalOpen(true)}
                className="px-4 py-2 rounded-xl bg-gray-900 hover:bg-gray-800 text-white font-medium text-xs sm:text-sm shadow-xs transition-all"
              >
                Sign In
              </button>
            )}
          </div>
        </motion.div>
      </header>

      {/* Main Content View */}
      <main className="flex-1 pt-16 relative z-10">
        <Outlet />
      </main>

      {/* Common Footer */}
      <footer className="border-t border-gray-200/80 py-8 text-center text-sm text-gray-400 relative z-10 bg-white/50">
        <div className="flex items-center justify-center gap-2 mb-1">
          <NexoraLogo size="sm" className="opacity-60" />
        </div>
        <p className="font-medium text-xs text-gray-500">
          Autonomous AI Predictive Analytics Platform • Powered by Scikit-Learn, LightGBM, XGBoost & Ollama AI
        </p>
      </footer>

      <LoginModal isOpen={isLoginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </div>
  );
}
