import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bell, Shield, User } from 'lucide-react';
import NexoraLogo from './NexoraLogo';
import { useAuth } from '../contexts/AuthContext';
import LoginModal from './LoginModal';
import { useEffect, useState } from 'react';
import { userApi } from '../api/users';

export default function Layout() {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const { user, signOut } = useAuth();
  const [isLoginModalOpen, setLoginModalOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setAvatarUrl(null);
      return;
    }
    userApi.getMe()
      .then((profile) => setAvatarUrl(profile.avatar_url ?? null))
      .catch(() => setAvatarUrl(null));
  }, [user]);

  return (
    <div className="min-h-screen flex flex-col bg-nexora-bg relative overflow-x-hidden">
      {/* Animated background gradient */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-nexora-accent/10 to-transparent rounded-full blur-3xl animate-float"></div>
        <div
          className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-tl from-nexora-accent/5 to-transparent rounded-full blur-3xl animate-float"
          style={{ animationDelay: '2s' }}
        ></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 inset-x-0 z-50 border-b border-nexora-border bg-white/95 backdrop-blur-md">
        <motion.div
          className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between relative z-10"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <Link
            to="/"
            className="flex items-center gap-2 group text-nexora-dark hover:text-nexora-accent transition-colors duration-300"
          >
            <NexoraLogo size="sm" />
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm text-nexora-dark/60">
            {isHome && (
              <>
                <a
                  href="#how-it-works"
                  className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium"
                >
                  How It Works
                </a>
                <a
                  href="#features"
                  className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium"
                >
                  Features
                </a>
                <a
                  href="#upload"
                  className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium"
                >
                  Upload
                </a>
              </>
            )}
            <Link
              to="/cybershield"
              className="flex items-center gap-1.5 hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium"
            >
              <Shield size={15} />
              CyberShield
            </Link>
            <Link
              to="/notifications"
              className="flex items-center gap-1.5 hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium"
            >
              <Bell size={15} />
              Notifications
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link to="/" className="btn-ghost text-sm group font-medium">
              <span className="group-hover:translate-x-0.5 transition-transform duration-200">
                New dataset
              </span>
            </Link>
            <Link
              to="/notifications"
              className="w-9 h-9 rounded-lg border border-nexora-border text-nexora-dark/60 hover:text-nexora-accent hover:border-nexora-accent/40 flex items-center justify-center transition-colors"
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell size={16} />
            </Link>
            
            {user ? (
              <div className="flex items-center gap-3 ml-2">
                <Link to="/profile" className="flex items-center gap-2 group">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="Avatar" className="w-8 h-8 rounded-full border border-gray-200 object-cover" />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-nexora-primary/10 flex items-center justify-center text-nexora-primary">
                      <User size={16} />
                    </div>
                  )}
                </Link>
                <button onClick={signOut} className="text-xs text-gray-500 hover:text-gray-900 font-medium">
                  Log out
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setLoginModalOpen(true)}
                className="btn-primary text-sm px-4 py-2"
              >
                Sign In
              </button>
            )}
          </div>
        </motion.div>
      </header>

      <main className="flex-1 pt-16 relative z-10">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-nexora-border py-8 text-center text-sm text-nexora-dark/40 relative z-10">
        <div className="flex items-center justify-center gap-2 mb-1">
          <NexoraLogo size="sm" className="text-nexora-accent/50" />
        </div>
        <p className="font-medium">Autonomous AI Predictive Analytics Platform</p>
      </footer>
      
      <LoginModal isOpen={isLoginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </div>
  );
}
