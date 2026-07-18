import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fallbackProfileFromFirebaseUser, userApi, UserProfile } from '../api/users';
import { communityApi, ReputationSummary } from '../api/community';

import { Database, Cpu, Clock, Settings, Github, Linkedin, ExternalLink, BadgeCheck } from 'lucide-react';
import HeatmapChart from '../components/HeatmapChart';



export const Profile: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [activity, setActivity] = useState<Awaited<ReturnType<typeof userApi.getActivity>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [reputation, setReputation] = useState<ReputationSummary | null>(null);
  const [heatmap, setHeatmap] = useState<{ date: string; contributions: number }[]>([]);

  useEffect(() => {
    if (!user) return;

    let cancelled = false;
    setLoading(true);
    Promise.allSettled([userApi.getMe(), userApi.getMyDatasets(), userApi.getActivity()])
      .then(([profileResult, datasetsResult, activityResult]) => {
        if (cancelled) return;
        if (profileResult.status === 'fulfilled') {
          setProfile(profileResult.value);
          communityApi.getReputation(profileResult.value.user_id).then(setReputation).catch(() => setReputation(null));
          communityApi.getHeatmap(profileResult.value.user_id).then(data => {
            setHeatmap(data.map(d => ({ date: d.date, contributions: d.count })));
          }).catch(() => setHeatmap([]));
        } else {
          console.error(profileResult.reason);
          const fallback = fallbackProfileFromFirebaseUser();
          setProfile(fallback);
          if (fallback) {
            communityApi.getReputation(fallback.user_id).then(setReputation).catch(() => setReputation(null));
            communityApi.getHeatmap(fallback.user_id).then(data => {
              setHeatmap(data.map(d => ({ date: d.date, contributions: d.count })));
            }).catch(() => setHeatmap([]));
          }
        }
        if (datasetsResult.status === 'fulfilled') {
          setHistory(datasetsResult.value);
        } else {
          console.error(datasetsResult.reason);
          setHistory([]);
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

  if (!user) {
    return <div className="text-center py-20">Please log in to view your profile.</div>;
  }

  const avatar = profile?.avatar_url || user.photoURL;
  const displayName = profile?.name || user.displayName || 'Nexora User';

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="flex items-start justify-between mb-12">
        <div className="flex items-center gap-6">
          <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-white shadow-xl">
            {avatar ? (
              <img src={avatar} alt={displayName} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-nexora-primary/10 flex items-center justify-center text-3xl font-bold text-nexora-primary">
                {user.email?.[0].toUpperCase()}
              </div>
            )}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{displayName}</h1>
            {profile?.username && (
              <p className="text-nexora-accent font-medium">@{profile.username}</p>
            )}
            <p className="text-gray-500">{user.email}</p>
            {profile?.bio && <p className="text-gray-600 mt-2 max-w-lg">{profile.bio}</p>}
            {profile?.links && (
              <div className="flex gap-3 mt-3">
                {profile.links.github?.is_visible !== false && profile.links.github?.url && (
                  <a href={profile.links.github.url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-700 flex items-center gap-0.5">
                    <Github size={18} />
                    {profile.links.github.verified && <BadgeCheck size={12} className="text-green-600" />}
                  </a>
                )}
                {profile.links.linkedin?.is_visible !== false && profile.links.linkedin?.url && (
                  <a href={profile.links.linkedin.url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-700">
                    <Linkedin size={18} />
                  </a>
                )}
                {profile.links.portfolio?.is_visible !== false && profile.links.portfolio?.url && (
                  <a href={profile.links.portfolio.url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-700">
                    <ExternalLink size={18} />
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
        <Link to="/profile/settings" className="btn-outline py-2 px-4 flex items-center gap-2 text-sm">
          <Settings size={16} /> Edit Profile
        </Link>
        {profile?.username && (
          <Link to={`/u/${profile.username}`} className="btn-ghost py-2 px-4 text-sm">
            Public preview
          </Link>
        )}
      </div>

      {reputation && (
        <div className="glass rounded-2xl p-6 mb-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-5">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Community Reputation</h2>
              <p className="text-sm text-gray-500">Level {reputation.level} · {reputation.contribution_score} contribution points</p>
            </div>
            <Link to="/feedback/new" className="btn-outline py-2 px-4 text-sm">Submit Feedback</Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-5">
            <MiniStat label="Accepted" value={reputation.feedback_accepted} />
            <MiniStat label="Features" value={reputation.features_suggested} />
            <MiniStat label="Bugs" value={reputation.bugs_reported} />
            <MiniStat label="Replies" value={reputation.replies_received} />
            <MiniStat label="Badges" value={reputation.badges_earned} />
            <MiniStat label="Stars" value={reputation.administrator_stars} />
          </div>
          <div className="flex flex-wrap gap-2">
            {reputation.badges.length === 0 ? (
              <span className="text-sm text-gray-400">Badges appear here as admins recognize your contributions.</span>
            ) : reputation.badges.map((badge) => (
              <span key={badge.name} title={badge.reason} className="px-3 py-1.5 rounded-full border border-nexora-accent/20 bg-nexora-accent/10 text-nexora-accent text-sm font-medium">
                {badge.name}
              </span>
            ))}
          </div>
        </div>
      )}
{/* Heatmap */}
<div className="glass rounded-2xl p-6 mb-12">
  <h2 className="text-lg font-bold text-gray-900 mb-4">Contribution Heatmap</h2>
  <HeatmapChart data={heatmap} />
</div>

{(profile?.best_dataset || profile?.favorite_model || (profile?.pinned_achievements && profile.pinned_achievements.length > 0)) && (
  <div className="glass rounded-2xl p-6 mb-12">
    <h2 className="text-lg font-bold text-gray-900 mb-4">Showcase</h2>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {profile.best_dataset && (
        <div className="rounded-xl border border-gray-100 bg-white/70 p-4">
          <p className="text-sm text-gray-500 font-medium">Best Dataset</p>
          <p className="text-gray-900 mt-1 font-semibold">{profile.best_dataset}</p>
        </div>
      )}
      {profile.favorite_model && (
        <div className="rounded-xl border border-gray-100 bg-white/70 p-4">
          <p className="text-sm text-gray-500 font-medium">Favorite Model</p>
          <p className="text-gray-900 mt-1 font-semibold">{profile.favorite_model}</p>
        </div>
      )}
      {profile.pinned_achievements && profile.pinned_achievements.length > 0 && (
        <div className="rounded-xl border border-gray-100 bg-white/70 p-4">
          <p className="text-sm text-gray-500 font-medium">Pinned Achievement</p>
          <p className="text-gray-900 mt-1 font-semibold">{profile.pinned_achievements[0]}</p>
        </div>
      )}
    </div>
  </div>
)}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="glass rounded-2xl p-6 flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Database size={24} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Datasets Uploaded</p>
            <p className="text-2xl font-bold text-gray-900">{history.length}</p>
          </div>
        </div>
        <div className="glass rounded-2xl p-6 flex items-center gap-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <Cpu size={24} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Models Trained</p>
            <p className="text-2xl font-bold text-gray-900">
              {history.reduce((acc, curr) => acc + ((curr.trained_model_count as number) || 0), 0)}
            </p>
          </div>
        </div>
        <div className="glass rounded-2xl p-6 flex items-center gap-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <Clock size={24} />
          </div>
          <div>
            <p className="text-gray-500 text-sm font-medium">Last Login</p>
            <p className="text-lg font-bold text-gray-900">
              {activity?.last_login
                ? new Date(activity.last_login).toLocaleString()
                : '—'}
            </p>
          </div>
        </div>
      </div>

      {activity?.login_history && activity.login_history.length > 0 && (
        <div className="glass rounded-2xl p-6 mb-12">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Recent Sign-ins</h2>
          <div className="space-y-2">
            {activity.login_history.slice(0, 5).map((entry: { at: string; method: string; user_agent?: string; ip?: string }, i: number) => (
              <div key={i} className="text-sm text-gray-600 flex justify-between">
                <span>{entry.method} · {entry.user_agent?.slice(0, 40) || 'Unknown device'}</span>
                <span className="text-gray-400">{new Date(entry.at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Recent Activity</h2>
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-sm font-medium text-gray-500">
              <tr>
                <th className="px-6 py-4">Dataset Name</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Models</th>
                <th className="px-6 py-4">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">Loading history...</td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-400">No activity yet.</td>
                </tr>
              ) : (
                history.map((dataset) => (
                  <tr key={String(dataset.session_id || dataset.dataset_id)} className="hover:bg-gray-50/50">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {String(dataset.dataset_name || dataset.filename || 'Dataset')}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {String(dataset.status || 'Completed')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{String(dataset.trained_model_count || 0)}</td>
                    <td className="px-6 py-4 text-gray-500 text-sm flex items-center gap-2">
                      <Clock size={14} />
                      {dataset.last_updated || dataset.updated_at
                        ? new Date(String(dataset.last_updated || dataset.updated_at)).toLocaleDateString()
                        : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white/70 p-3">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="text-lg font-semibold text-gray-900">{value}</div>
    </div>
  );
}
