import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../../api/admin';
import NexoraLogo from '../../components/NexoraLogo';
import { Lock } from 'lucide-react';

const DEFAULT_ADMIN_EMAIL = 'jeet@nexora.admin';
const DEFAULT_ADMIN_PASSWORD = 'Jeet@Nexora2026!';

export const AdminLogin: React.FC = () => {
  const [email, setEmail] = useState(DEFAULT_ADMIN_EMAIL);
  const [password, setPassword] = useState(DEFAULT_ADMIN_PASSWORD);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await adminApi.login(email, password);
      navigate('/admin');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-nexora-bg font-sans relative">
      <div className="absolute inset-0 bg-grid-fine opacity-20 pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-nexora-accent/10 rounded-full blur-3xl pointer-events-none" />
      
      <div className="z-10 mb-8">
        <NexoraLogo size="md" />
      </div>

      <div className="glass w-full max-w-md p-8 relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-nexora-accent/10 flex items-center justify-center text-nexora-accent">
            <Lock size={20} />
          </div>
          <div>
            <h1 className="text-xl font-display font-semibold text-nexora-dark">Admin Login</h1>
            <p className="text-sm text-nexora-dark/60">Secure area for platform operators</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg mb-6 border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-nexora-dark/80 mb-1.5">Email</label>
            <input 
              type="email" 
              required
              className="w-full bg-white border border-nexora-border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-nexora-accent/50 transition-shadow"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-nexora-dark/80 mb-1.5">Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-white border border-nexora-border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-nexora-accent/50 transition-shadow"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full mt-4 flex items-center justify-center rounded-2xl border border-nexora-accent/20 bg-white p-3 shadow-sm transition hover:shadow-md disabled:opacity-70"
            aria-label="Sign in to admin panel"
          >
            {loading ? (
              <span className="text-sm font-semibold text-nexora-dark">Authenticating...</span>
            ) : (
              <NexoraLogo size="sm" className="h-6" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
