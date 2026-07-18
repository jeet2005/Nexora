import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Github, KeyRound, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

type AuthMode = 'login' | 'signup' | 'forgot' | 'passwordless';

export default function LoginModal({ isOpen, onClose }: Props) {
  const { 
    signInWithGoogle, signInWithGithub, 
    signInWithEmail, signUpWithEmail, 
    sendPasswordlessLink, resetPassword,
    resendVerificationEmail, resendMagicLink,
    canResendNow, resendCooldownSeconds,
  } = useAuth();
  
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setMode('login');
      setEmail('');
      setPassword('');
      setName('');
      setError('');
      setSuccessMsg('');
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (mode === 'login') {
        await signInWithEmail(email, password);
        onClose();
      } else if (mode === 'signup') {
        await signUpWithEmail(email, password, name);
        setSuccessMsg('Account created! Please check your email to verify.');
        // Don't close immediately so they can see the message
      } else if (mode === 'forgot') {
        await resetPassword(email);
        setSuccessMsg('Password reset email sent! Check your inbox.');
      } else if (mode === 'passwordless') {
        await sendPasswordlessLink(email);
        setSuccessMsg('Magic link sent! Check your email to sign in.');
      }
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    setError('');
    try {
      if (provider === 'google') await signInWithGoogle();
      if (provider === 'github') await signInWithGithub();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden relative"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors z-10"
            >
              <X size={24} />
            </button>
            
            <div className="p-8">
              {mode !== 'login' && (
                <button 
                  onClick={() => { setMode('login'); setError(''); setSuccessMsg(''); }}
                  className="absolute top-4 left-4 text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1 text-sm font-medium z-10"
                >
                  <ArrowLeft size={16} /> Back
                </button>
              )}

              <div className="text-center mb-8 mt-2">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {mode === 'login' ? 'Welcome Back' : 
                   mode === 'signup' ? 'Create Account' : 
                   mode === 'forgot' ? 'Reset Password' :
                   'Magic Link'}
                </h2>
                <p className="text-gray-500">
                  {mode === 'login' ? 'Sign in to access your Nexora dashboard.' : 
                   mode === 'signup' ? 'Join Nexora to deploy predictive models.' :
                   mode === 'forgot' ? 'Enter your email to receive a reset link.' :
                   'Enter your email to receive a secure sign-in link.'}
                </p>
              </div>
              
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm flex items-start gap-2">
                  <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {successMsg && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm flex items-start gap-2">
                  <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}
              
              {successMsg && mode === 'signup' && (
                <button
                  type="button"
                  disabled={!canResendNow('nexora_resend_verify')}
                  onClick={async () => {
                    try {
                      await resendVerificationEmail();
                      setSuccessMsg('Verification email resent!');
                    } catch (err: unknown) {
                      setError(err instanceof Error ? err.message : 'Could not resend');
                    }
                  }}
                  className="mb-4 text-sm text-nexora-primary hover:underline disabled:opacity-50"
                >
                  Resend verification email
                  {!canResendNow('nexora_resend_verify') ? ` (${resendCooldownSeconds('nexora_resend_verify')}s)` : ''}
                </button>
              )}

              {successMsg && mode === 'passwordless' && (
                <button
                  type="button"
                  disabled={!canResendNow('nexora_resend_magic')}
                  onClick={async () => {
                    try {
                      await resendMagicLink(email);
                      setSuccessMsg('Magic link resent!');
                    } catch (err: unknown) {
                      setError(err instanceof Error ? err.message : 'Could not resend');
                    }
                  }}
                  className="mb-4 text-sm text-nexora-primary hover:underline disabled:opacity-50"
                >
                  Resend magic link
                  {!canResendNow('nexora_resend_magic') ? ` (${resendCooldownSeconds('nexora_resend_magic')}s)` : ''}
                </button>
              )}
              
              <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
                {mode === 'signup' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                    <input 
                      type="text" required
                      name="nexora-display-name"
                      autoComplete="off"
                      value={name} onChange={e => setName(e.target.value)}
                      className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20 focus:border-nexora-accent"
                    />
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                  <input 
                    type="email"
                    required
                    name="nexora-user-email"
                    autoComplete="off"
                    autoCorrect="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    value={email} onChange={e => setEmail(e.target.value)}
                    className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20 focus:border-nexora-accent"
                  />
                </div>

                {(mode === 'login' || mode === 'signup') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input 
                      type="password" required minLength={6}
                      name="nexora-user-passcode"
                      autoComplete="new-password"
                      value={password} onChange={e => setPassword(e.target.value)}
                      className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20 focus:border-nexora-accent"
                    />
                  </div>
                )}

                {mode === 'login' && (
                  <div className="flex justify-end">
                    <button type="button" onClick={() => setMode('forgot')} className="text-sm text-nexora-primary hover:underline">
                      Forgot password?
                    </button>
                  </div>
                )}

                <button
                  type="submit" disabled={loading}
                  className="w-full btn-primary py-3 rounded-xl flex justify-center items-center"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    mode === 'login' ? 'Sign In' : 
                    mode === 'signup' ? 'Sign Up' :
                    'Send Link'
                  )}
                </button>
              </form>

              {mode === 'login' && (
                <>
                  <div className="mt-6">
                    <button 
                      onClick={() => setMode('passwordless')}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                    >
                      <KeyRound size={18} />
                      Sign in with Magic Link
                    </button>
                  </div>

                  <div className="mt-6 flex items-center gap-4">
                    <div className="flex-1 h-px bg-gray-200"></div>
                    <div className="text-sm text-gray-400 font-medium">OR</div>
                    <div className="flex-1 h-px bg-gray-200"></div>
                  </div>

                  <div className="mt-6 space-y-3">
                    <button
                      onClick={() => handleOAuth('google')}
                      className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                    >
                      <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
                      Continue with Google
                    </button>
                    
                    <button
                      onClick={() => handleOAuth('github')}
                      className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-gray-200 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                    >
                      <Github className="w-5 h-5" />
                      Continue with GitHub
                    </button>
                  </div>

                  <div className="mt-8 text-center text-sm text-gray-500">
                    Don&apos;t have an account?{' '}
                    <button onClick={() => setMode('signup')} className="text-nexora-primary hover:underline font-medium">
                      Sign up
                    </button>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
