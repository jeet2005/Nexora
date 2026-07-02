import React, { useEffect, useState } from 'react';
import { adminApi } from '../../api/admin';
import { ADMIN_AVATARS } from '../../constants/avatars';
import { FileText, Save, Check, Bell, User } from 'lucide-react';

export const Content: React.FC = () => {
  const [announcement, setAnnouncement] = useState('');
  const [roadmap, setRoadmap] = useState('');
  const [changelog, setChangelog] = useState('');
  const [notifyUsers, setNotifyUsers] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [adminName, setAdminName] = useState('');
  const [adminAvatar, setAdminAvatar] = useState(ADMIN_AVATARS[0]);
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    adminApi.getMe().then((me) => {
      setAdminName(me.name || '');
      setAdminAvatar(me.avatar_url || ADMIN_AVATARS[0]);
    });
    adminApi.getContent('announcement_banner').then(res => setAnnouncement(res.value || ''));
    adminApi.getContent('roadmap').then(res => setRoadmap(typeof res.value === 'string' ? res.value : JSON.stringify(res.value || [], null, 2)));
    adminApi.getContent('changelog').then(res => setChangelog(res.value || ''));
  }, []);

  const handleSave = async (key: string, value: string) => {
    setSaving(key);
    try {
      const result = await adminApi.updateContent(key, value, key === 'announcement_banner' && notifyUsers);
      if (key === 'announcement_banner' && result.emails_sent) {
        alert(`Saved! ${result.emails_sent} users notified by email.`);
      }
      setTimeout(() => setSaving(null), 2000);
    } catch (err) {
      console.error(err);
      setSaving(null);
    }
  };

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    try {
      await adminApi.updateProfile({ name: adminName, avatar_url: adminAvatar });
    } catch (err) {
      console.error(err);
    } finally {
      setProfileSaving(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <FileText className="text-nexora-accent" size={24} />
          Site Content Management
        </h1>
      </div>

      {/* Admin Profile */}
      <div className="glass p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-nexora-dark flex items-center gap-2">
              <User size={18} className="text-nexora-accent" />
              Admin Profile
            </h2>
            <p className="text-sm text-nexora-dark/60">Shown on announcements and public notifications.</p>
          </div>
          <button onClick={handleSaveProfile} disabled={profileSaving} className="btn-primary py-2 px-4 text-sm">
            {profileSaving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
        <div className="flex flex-col sm:flex-row gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Display Name</label>
            <input
              value={adminName}
              onChange={e => setAdminName(e.target.value)}
              className="w-full sm:w-64 px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Avatar</label>
            <div className="flex gap-2">
              {ADMIN_AVATARS.map(url => (
                <button
                  key={url}
                  type="button"
                  onClick={() => setAdminAvatar(url)}
                  className={`w-12 h-12 rounded-xl overflow-hidden border-2 ${
                    adminAvatar === url ? 'border-nexora-accent' : 'border-transparent'
                  }`}
                >
                  <img src={url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Announcement Banner */}
      <div className="glass p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-nexora-dark">Announcement Banner</h2>
            <p className="text-sm text-nexora-dark/60">Displays at the top of the landing page with your name and avatar.</p>
          </div>
          <button
            onClick={() => handleSave('announcement_banner', announcement)}
            className="btn-primary py-2 px-4 flex items-center gap-2"
          >
            {saving === 'announcement_banner' ? <Check size={18} /> : <Save size={18} />}
            {saving === 'announcement_banner' ? 'Saved' : 'Save'}
          </button>
        </div>
        <label className="flex items-center gap-2 mb-3 text-sm text-gray-600 cursor-pointer">
          <input type="checkbox" checked={notifyUsers} onChange={e => setNotifyUsers(e.target.checked)} />
          <Bell size={14} />
          Email all users when saving (requires SMTP in backend .env)
        </label>
        <textarea
          value={announcement}
          onChange={e => setAnnouncement(e.target.value)}
          className="w-full h-24 bg-white border border-nexora-border rounded-xl p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-nexora-accent/50 transition-shadow"
          placeholder="New release v1.0.2 out now!"
        />
      </div>

      {/* Roadmap Editor */}
      <div className="glass p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-nexora-dark">Roadmap</h2>
            <p className="text-sm text-nexora-dark/60">JSON array of roadmap items to render on the site.</p>
          </div>
          <button
            onClick={() => handleSave('roadmap', roadmap)}
            className="btn-primary py-2 px-4 flex items-center gap-2"
          >
            {saving === 'roadmap' ? <Check size={18} /> : <Save size={18} />}
            {saving === 'roadmap' ? 'Saved' : 'Save'}
          </button>
        </div>
        <textarea
          value={roadmap}
          onChange={e => setRoadmap(e.target.value)}
          className="w-full h-48 bg-white border border-nexora-border rounded-xl p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-nexora-accent/50 transition-shadow"
          placeholder='[{"title": "Multi-modal Support", "status": "planned"}]'
        />
      </div>

      {/* Changelog Editor */}
      <div className="glass p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-nexora-dark">Changelog</h2>
            <p className="text-sm text-nexora-dark/60">Markdown content for the public changelog page.</p>
          </div>
          <button
            onClick={() => handleSave('changelog', changelog)}
            className="btn-primary py-2 px-4 flex items-center gap-2"
          >
            {saving === 'changelog' ? <Check size={18} /> : <Save size={18} />}
            {saving === 'changelog' ? 'Saved' : 'Save'}
          </button>
        </div>
        <textarea
          value={changelog}
          onChange={e => setChangelog(e.target.value)}
          className="w-full h-64 bg-white border border-nexora-border rounded-xl p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-nexora-accent/50 transition-shadow"
          placeholder="## v1.0.2&#10;- Added new feature&#10;- Fixed bug"
        />
      </div>
    </div>
  );
};
