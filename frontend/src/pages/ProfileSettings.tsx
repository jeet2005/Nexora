import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fallbackProfileFromFirebaseUser, userApi, UserProfile } from '../api/users';
import { USER_AVATARS } from '../constants/avatars';
import {
  Save, Check, Globe, Lock, Github, Linkedin, ExternalLink, Download, Trash2, Eye,
} from 'lucide-react';

const LINK_FIELDS = [
  { key: 'github', label: 'GitHub', icon: Github, placeholder: 'https://github.com/username' },
  { key: 'linkedin', label: 'LinkedIn', icon: Linkedin, placeholder: 'https://linkedin.com/in/username' },
  { key: 'orcid', label: 'ORCID', icon: ExternalLink, placeholder: 'https://orcid.org/0000-0000-0000-0000' },
  { key: 'portfolio', label: 'Portfolio', icon: ExternalLink, placeholder: 'https://yoursite.com' },
] as const;

export const ProfileSettings: React.FC = () => {
  const {
    user, signOut, updateUserPassword, updateUserEmail,
    revokeAllSessions, resendVerificationEmail, canResendNow, resendCooldownSeconds, deleteAccount,
  } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [activity, setActivity] = useState<Awaited<ReturnType<typeof userApi.getActivity>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [emailPassword, setEmailPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (!user) return;

    let cancelled = false;
    setLoading(true);
    Promise.allSettled([userApi.getMe(), userApi.getActivity()])
      .then(([profileResult, activityResult]) => {
        if (cancelled) return;
        if (profileResult.status === 'fulfilled') {
          setProfile(profileResult.value);
        } else {
          console.error(profileResult.reason);
          setProfile(fallbackProfileFromFirebaseUser());
        }
        if (activityResult.status === 'fulfilled') {
          setActivity(activityResult.value);
        } else {
          console.error(activityResult.reason);
          setActivity(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  const updateField = (field: keyof UserProfile, value: unknown) => {
    if (!profile) return;
    setProfile({ ...profile, [field]: value });
  };

  const updateLink = (key: string, field: 'url' | 'is_visible', value: string | boolean) => {
    if (!profile) return;
    const links = { ...(profile.links || {}) };
    links[key] = { ...(links[key] || {}), url: links[key]?.url || '', is_visible: links[key]?.is_visible ?? true, [field]: value };
    setProfile({ ...profile, links });
  };

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setError('');
    try {
      const updated = await userApi.updateMe({
        name: profile.name,
        username: profile.username,
        bio: profile.bio,
        avatar_url: profile.avatar_url,
        is_public: profile.is_public,
        requires_2fa: profile.requires_2fa,
        links: profile.links,
      });
      setProfile(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save profile';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    const data = await userApi.exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexora-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete your account? Export your data first if needed.')) return;
    setError('');
    try {
      const password = window.prompt(
        'Enter your password to confirm account deletion (leave blank if you signed in with Google/GitHub):',
      );
      await userApi.deleteAccount();
      await deleteAccount(password || undefined);
      await signOut();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete account';
      setError(msg);
    }
  };

  const handlePasswordChange = async () => {
    if (!currentPassword || !newPassword || newPassword.length < 6) {
      setError('Enter current password and a new password (min 6 chars)');
      return;
    }
    setError('');
    try {
      await updateUserPassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setInfo('Password updated successfully.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update password');
    }
  };

  const handleEmailChange = async () => {
    if (!newEmail || !emailPassword) {
      setError('Enter new email and current password');
      return;
    }
    setError('');
    try {
      await updateUserEmail(newEmail, emailPassword);
      setInfo('Verification email sent to your new address. Click the link to confirm.');
      setNewEmail('');
      setEmailPassword('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update email');
    }
  };

  const handleRevokeSessions = async () => {
    if (!window.confirm('Sign out of all devices? You will need to sign in again here.')) return;
    await revokeAllSessions();
  };

  const handleResendVerification = async () => {
    setError('');
    try {
      await resendVerificationEmail();
      setInfo('Verification email sent.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not resend verification');
    }
  };

  if (!user) {
    return <div className="text-center py-20">Please log in to manage your profile.</div>;
  }

  if (loading || !profile) {
    return <div className="text-center py-20 text-gray-400">Loading profile...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
        <Link
          to={profile.username ? `/u/${profile.username}` : '/profile'}
          className="text-sm text-nexora-accent hover:underline flex items-center gap-1"
        >
          <Eye size={14} /> View public profile
        </Link>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm">{error}</div>
      )}

      {info && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{info}</div>
      )}

      {/* Avatar picker */}
      <div className="glass rounded-2xl p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Avatar</h2>
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
          {USER_AVATARS.map((url) => (
            <button
              key={url}
              type="button"
              onClick={() => updateField('avatar_url', url)}
              className={`rounded-xl overflow-hidden border-2 transition-all ${
                profile.avatar_url === url ? 'border-nexora-accent scale-105' : 'border-transparent hover:border-gray-200'
              }`}
            >
              <img src={url} alt="" className="w-full aspect-square object-cover" />
            </button>
          ))}
        </div>
      </div>

      {/* Basic info */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Basic Info</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
          <input
            value={profile.name || ''}
            onChange={(e) => updateField('name', e.target.value)}
            className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            value={profile.username || ''}
            onChange={(e) => updateField('username', e.target.value)}
            placeholder="your-handle"
            className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
          <textarea
            value={profile.bio || ''}
            onChange={(e) => updateField('bio', e.target.value)}
            rows={3}
            className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
          />
        </div>
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={profile.is_public}
              onChange={(e) => updateField('is_public', e.target.checked)}
              className="rounded"
            />
            <Globe size={16} className="text-gray-500" />
            <span className="text-sm text-gray-700">Public profile</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={profile.requires_2fa}
              onChange={(e) => updateField('requires_2fa', e.target.checked)}
              className="rounded"
            />
            <Lock size={16} className="text-gray-500" />
            <span className="text-sm text-gray-700">Require OTP on login</span>
          </label>
        </div>
      </div>

      {/* External links */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">External Links</h2>
        {LINK_FIELDS.map(({ key, icon: Icon, placeholder }) => (
          <div key={key} className="flex gap-3 items-center">
            <Icon size={18} className="text-gray-400 flex-shrink-0" />
            <input
              value={profile.links?.[key]?.url || ''}
              onChange={(e) => updateLink(key, 'url', e.target.value)}
              placeholder={placeholder}
              className="flex-1 px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20 text-sm"
            />
            <label className="flex items-center gap-1 text-xs text-gray-500 whitespace-nowrap">
              <input
                type="checkbox"
                checked={profile.links?.[key]?.is_visible ?? true}
                onChange={(e) => updateLink(key, 'is_visible', e.target.checked)}
              />
              Show
            </label>
          </div>
        ))}
      </div>

      {/* Email */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Email</h2>
        <p className="text-sm text-gray-500">Current: {user.email}</p>
        {!user.emailVerified && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-amber-600">Email not verified</span>
            <button
              type="button"
              onClick={handleResendVerification}
              disabled={!canResendNow('nexora_resend_verify')}
              className="text-sm text-nexora-accent hover:underline disabled:opacity-50"
            >
              Resend verification{!canResendNow('nexora_resend_verify') ? ` (${resendCooldownSeconds('nexora_resend_verify')}s)` : ''}
            </button>
          </div>
        )}
        <input
          type="email"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          placeholder="New email address"
          className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
        />
        <input
          type="password"
          value={emailPassword}
          onChange={(e) => setEmailPassword(e.target.value)}
          placeholder="Current password to confirm"
          className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
        />
        <button onClick={handleEmailChange} className="btn-outline py-2 px-4 text-sm">
          Update Email (sends verification link)
        </button>
      </div>

      {/* Password */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Change Password</h2>
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          placeholder="Current password"
          className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
        />
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="New password (min 6 chars)"
          className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
        />
        <button onClick={handlePasswordChange} className="btn-outline py-2 px-4 text-sm">
          Update Password
        </button>
      </div>

      {/* Security & sessions */}
      <div className="glass rounded-2xl p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Security & Sessions</h2>
        {activity?.last_login && (
          <p className="text-sm text-gray-600">
            Last login: {new Date(activity.last_login).toLocaleString()}
          </p>
        )}
        {activity?.login_history && activity.login_history.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Recent sign-ins</p>
            {activity.login_history.slice(0, 5).map((entry: { at: string; method: string; user_agent?: string; ip?: string }, i: number) => (
              <div key={i} className="text-xs text-gray-500 border-b border-gray-100 pb-2">
                {new Date(entry.at).toLocaleString()} · {entry.method}
                {entry.ip ? ` · ${entry.ip}` : ''}
              </div>
            ))}
          </div>
        )}
        <button onClick={handleRevokeSessions} className="btn-outline py-2 px-4 text-sm">
          Log out of all devices
        </button>
        <p className="text-xs text-gray-400">
          Email notifications on password change require SMTP configured on the backend.
        </p>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <button onClick={handleSave} disabled={saving} className="btn-primary py-2 px-6 flex items-center gap-2">
          {saved ? <Check size={18} /> : <Save size={18} />}
          {saved ? 'Saved' : saving ? 'Saving...' : 'Save Profile'}
        </button>
        <button onClick={handleExport} className="btn-outline py-2 px-4 flex items-center gap-2 text-sm">
          <Download size={16} /> Export Data
        </button>
        <button onClick={handleDelete} className="py-2 px-4 flex items-center gap-2 text-sm text-red-600 border border-red-200 rounded-xl hover:bg-red-50">
          <Trash2 size={16} /> Delete Account
        </button>
      </div>
    </div>
  );
};

export default ProfileSettings;
