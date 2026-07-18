import { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Mail, Megaphone } from 'lucide-react';
import { getPublicContent } from '../api/users';
import { communityApi, CommunityNotification } from '../api/community';
import { useAuth } from '../contexts/AuthContext';

interface Announcement {
  value?: string;
  updated_by_name?: string;
  updated_by_avatar?: string;
  updated_at?: string;
}

export default function NotificationsPage() {
  const { user } = useAuth();
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [communityNotifications, setCommunityNotifications] = useState<CommunityNotification[]>([]);

  useEffect(() => {
    getPublicContent('announcement_banner')
      .then((res) => setAnnouncement(res ?? null))
      .catch(() => setAnnouncement(null));
    if (user) {
      communityApi.getNotifications()
        .then(setCommunityNotifications)
        .catch(() => setCommunityNotifications([]));
    }
  }, [user]);

  return (
    <div className="min-h-[calc(100vh-8rem)] bg-white">
      <section className="border-b border-nexora-border bg-nexora-bg">
        <div className="max-w-5xl mx-auto px-6 py-12">
          <div className="flex items-center gap-3 text-nexora-accent mb-4">
            <Bell className="w-5 h-5" />
            <span className="text-sm font-semibold">Notifications</span>
          </div>
          <h1 className="font-display text-3xl md:text-4xl text-nexora-dark mb-3">
            Platform updates and account alerts
          </h1>
          <p className="text-nexora-dark/60 max-w-2xl">
            Review current announcements, feedback updates, and the account events Nexora can send by email.
          </p>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-10 space-y-5">
        <div className="border border-nexora-border rounded-lg p-5">
          <div className="flex items-start gap-4">
            {announcement?.updated_by_avatar ? (
              <img
                src={announcement.updated_by_avatar}
                alt=""
                className="w-10 h-10 rounded-full object-cover border border-nexora-border"
              />
            ) : (
              <div className="w-10 h-10 rounded-lg bg-nexora-accent/10 text-nexora-accent flex items-center justify-center">
                <Megaphone className="w-5 h-5" />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h2 className="font-semibold text-nexora-dark">Announcement banner</h2>
              <p className="text-sm text-nexora-dark/60 mt-1 leading-relaxed">
                {announcement?.value || 'No active announcement right now.'}
              </p>
              {announcement?.updated_by_name && (
                <p className="text-xs text-nexora-dark/40 mt-3">
                  Posted by {announcement.updated_by_name}
                  {announcement.updated_at &&
                    ` on ${new Date(announcement.updated_at).toLocaleDateString()}`}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="border border-nexora-border rounded-lg p-5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-nexora-accent/10 text-nexora-accent flex items-center justify-center">
              <Bell className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-nexora-dark flex items-center gap-2">
                  Community notifications
                  {communityNotifications.filter(n => !n.read).length > 0 && (
                    <span className="bg-nexora-accent text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {communityNotifications.filter(n => !n.read).length} new
                    </span>
                  )}
                </h2>
                {communityNotifications.filter(n => !n.read).length > 0 && (
                  <button
                    onClick={() => {
                      communityApi.markNotificationsRead().then(() => {
                        setCommunityNotifications(prev => prev.map(n => ({ ...n, read: true })));
                      });
                    }}
                    className="text-xs text-nexora-accent hover:underline font-medium"
                  >
                    Mark all as read
                  </button>
                )}
              </div>
              <div className="mt-3 space-y-3">
                {communityNotifications.length === 0 ? (
                  <p className="text-sm text-nexora-dark/60">No feedback replies, stars, badges, or implementation updates yet.</p>
                ) : communityNotifications.map((item) => (
                  <div key={item.id} className={`border-t border-nexora-border pt-3 first:border-t-0 first:pt-0 ${!item.read ? 'border-l-2 border-l-nexora-accent bg-nexora-accent/5 pl-3 py-2 rounded-r-lg -ml-3' : ''}`}>
                    <div className="text-sm font-medium text-nexora-dark">{item.title}</div>
                    <div className="text-sm text-nexora-dark/60 mt-1">{item.message}</div>
                    <div className="text-xs text-nexora-dark/40 mt-1">{new Date(item.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="border border-nexora-border rounded-lg p-5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-nexora-accent/10 text-nexora-accent flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-semibold text-nexora-dark">Email alerts</h2>
              <p className="text-sm text-nexora-dark/60 mt-1">
                Nexora can notify you for new sign-ins and password changes when SMTP is configured
                on the backend.
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-nexora-dark/70">
                <span className="inline-flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-nexora-accent" />
                  New sign-in
                </span>
                <span className="inline-flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-nexora-accent" />
                  Password changed
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
