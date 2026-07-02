import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import TabLoader from '../components/TabLoader';

export default function LoginPage() {
  const { user, verifyPasswordlessLink } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const finishSignIn = async () => {
      const email = window.localStorage.getItem('emailForSignIn');
      if (!email) {
        setError('No sign-in email found. Request a new magic link from the sign-in modal.');
        return;
      }

      try {
        await verifyPasswordlessLink(email, window.location.href);
        navigate('/home', { replace: true });
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Magic link sign-in failed.';
        setError(msg);
      }
    };

    if (user) {
      navigate('/home', { replace: true });
      return;
    }

    finishSignIn();
  }, [user, verifyPasswordlessLink, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="max-w-md text-center space-y-4">
          <h1 className="text-xl font-semibold text-gray-900">Sign-in link expired</h1>
          <p className="text-gray-600 text-sm">{error}</p>
          <button onClick={() => navigate('/')} className="btn-primary px-6 py-2">
            Back to home
          </button>
        </div>
      </div>
    );
  }

  return <TabLoader label="Completing sign-in…" />;
}
