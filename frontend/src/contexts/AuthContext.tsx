import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  User,
  onAuthStateChanged,
  signInWithPopup,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  sendPasswordResetEmail,
  sendEmailVerification,
  updateProfile,
  updatePassword,
  deleteUser,
  reauthenticateWithCredential,
  EmailAuthProvider,
  verifyBeforeUpdateEmail,
} from 'firebase/auth';
import { auth, googleProvider, githubProvider } from '../config/firebase';
import { api } from '../api/client';
import { userApi } from '../api/users';
import { getRandomUserAvatar } from '../constants/avatars';
import { canResend, markResent } from '../utils/otpCooldown';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signInWithGithub: () => Promise<void>;
  signUpWithEmail: (email: string, pass: string, name: string) => Promise<void>;
  signInWithEmail: (email: string, pass: string) => Promise<void>;
  sendPasswordlessLink: (email: string) => Promise<void>;
  verifyPasswordlessLink: (email: string, url: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  resendVerificationEmail: () => Promise<void>;
  resendMagicLink: (email: string) => Promise<void>;
  resendCooldownSeconds: (key: string) => number;
  canResendNow: (key: string) => boolean;
  updateUserPassword: (currentPassword: string, newPassword: string) => Promise<void>;
  updateUserEmail: (newEmail: string, currentPassword: string) => Promise<void>;
  revokeAllSessions: () => Promise<void>;
  deleteAccount: (password?: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => useContext(AuthContext);

const RESEND_VERIFY_KEY = 'nexora_resend_verify';
const RESEND_MAGIC_KEY = 'nexora_resend_magic';

async function syncUserWithBackend(firebaseUser: User) {
  const token = await firebaseUser.getIdToken();
  await api.post('/users/register', {
    user_id: firebaseUser.uid,
    email: firebaseUser.email,
    name: firebaseUser.displayName,
    avatar_url: getRandomUserAvatar(),
  }, {
    headers: { Authorization: `Bearer ${token}` },
  });
  try {
    await userApi.notifyNewLogin();
  } catch {
    // optional notification
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        try {
          await syncUserWithBackend(firebaseUser);
        } catch (e) {
          console.error('Failed to register user in backend', e);
        }
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    await signInWithPopup(auth, googleProvider);
  };

  const signInWithGithub = async () => {
    await signInWithPopup(auth, githubProvider);
  };

  const signUpWithEmail = async (email: string, pass: string, name: string) => {
    const credential = await createUserWithEmailAndPassword(auth, email, pass);
    await updateProfile(credential.user, { displayName: name });
    await sendEmailVerification(credential.user);
    markResent(RESEND_VERIFY_KEY);
  };

  const signInWithEmail = async (email: string, pass: string) => {
    const credential = await signInWithEmailAndPassword(auth, email, pass);
    try {
      const profile = await userApi.getMe();
      if (profile.requires_2fa) {
        await auth.signOut();
        await sendPasswordlessLink(email);
        throw new Error('2FA enabled: check your email for a magic link to complete sign-in.');
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('2FA enabled')) throw err;
    }
    if (!credential.user.emailVerified) {
      console.warn('Email not verified yet');
    }
  };

  const sendPasswordlessLink = async (email: string) => {
    const actionCodeSettings = {
      url: window.location.origin + '/login',
      handleCodeInApp: true,
    };
    await sendSignInLinkToEmail(auth, email, actionCodeSettings);
    window.localStorage.setItem('emailForSignIn', email);
    markResent(RESEND_MAGIC_KEY);
  };

  const verifyPasswordlessLink = async (email: string, url: string) => {
    if (isSignInWithEmailLink(auth, url)) {
      await signInWithEmailLink(auth, email, url);
      window.localStorage.removeItem('emailForSignIn');
    }
  };

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email);
  };

  const resendVerificationEmail = async () => {
    if (!auth.currentUser) throw new Error('Not signed in');
    if (!canResend(RESEND_VERIFY_KEY)) {
      throw new Error(`Wait ${Math.ceil((60000 - (Date.now() - Number(localStorage.getItem(RESEND_VERIFY_KEY)))) / 1000)}s before resending`);
    }
    await sendEmailVerification(auth.currentUser);
    markResent(RESEND_VERIFY_KEY);
  };

  const resendMagicLink = async (email: string) => {
    if (!canResend(RESEND_MAGIC_KEY)) {
      throw new Error(`Wait before requesting another magic link`);
    }
    await sendPasswordlessLink(email);
  };

  const resendCooldownSeconds = (key: string) => {
    const last = Number(localStorage.getItem(key) || 0);
    return Math.max(0, Math.ceil((60000 - (Date.now() - last)) / 1000));
  };

  const canResendNow = (key: string) => canResend(key);

  const updateUserPassword = async (currentPassword: string, newPassword: string) => {
    const currentUser = auth.currentUser;
    if (!currentUser?.email) throw new Error('Not signed in with email');
    const credential = EmailAuthProvider.credential(currentUser.email, currentPassword);
    await reauthenticateWithCredential(currentUser, credential);
    await updatePassword(currentUser, newPassword);
    try {
      await userApi.notifyPasswordChanged();
    } catch {
      // optional
    }
  };

  const updateUserEmail = async (newEmail: string, currentPassword: string) => {
    const currentUser = auth.currentUser;
    if (!currentUser?.email) throw new Error('Not signed in with email');
    const credential = EmailAuthProvider.credential(currentUser.email, currentPassword);
    await reauthenticateWithCredential(currentUser, credential);
    await verifyBeforeUpdateEmail(currentUser, newEmail);
  };

  const revokeAllSessions = async () => {
    await userApi.revokeAllSessions();
    await auth.signOut();
  };

  const deleteAccount = async (password?: string) => {
    const currentUser = auth.currentUser;
    if (!currentUser) return;
    if (password && currentUser.email) {
      const credential = EmailAuthProvider.credential(currentUser.email, password);
      await reauthenticateWithCredential(currentUser, credential);
    }
    await deleteUser(currentUser);
  };

  const signOut = async () => {
    await auth.signOut();
  };

  return (
    <AuthContext.Provider value={{
      user, loading,
      signInWithGoogle, signInWithGithub,
      signUpWithEmail, signInWithEmail,
      sendPasswordlessLink, verifyPasswordlessLink,
      resetPassword, resendVerificationEmail, resendMagicLink,
      resendCooldownSeconds, canResendNow,
      updateUserPassword, updateUserEmail,
      revokeAllSessions, deleteAccount, signOut,
    }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
