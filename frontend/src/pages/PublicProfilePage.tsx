import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { userApi, UserProfile } from '../api/users';
import { communityApi, ReputationSummary, statusLabels } from '../api/community';
import { useAuth } from '../contexts/AuthContext';
import { Github, Linkedin, ExternalLink, BadgeCheck } from 'lucide-react';

export default function PublicProfilePage() {
  const { user } = useAuth();
  const { username } = useParams<{ username: string }>();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [reputation, setReputation] = useState<ReputationSummary | null>(null);

  useEffect(() => {
    if (!username) return;
    userApi.getPublicProfile(username)
      .then((data) => {
        setProfile(data);
        communityApi.getReputation(data.user_id).then(setReputation).catch(() => setReputation(null));
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Profile not found');
      })
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) {
    return <div className="text-center py-20 text-gray-400">Loading profile...</div>;
  }

  if (error || !profile) {
    return <div className="text-center py-20 text-gray-500">{error || 'Profile not found'}</div>;
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <div className="glass rounded-2xl p-8 flex items-start gap-6">
        <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-white shadow-xl flex-shrink-0">
          {profile.avatar_url ? (
            <img src={profile.avatar_url} alt={profile.name || username} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-nexora-primary/10 flex items-center justify-center text-3xl font-bold text-nexora-primary">
              {(profile.name || username || '?')[0].toUpperCase()}
            </div>
          )}
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{profile.name || username}</h1>
          <p className="text-nexora-accent font-medium">@{profile.username || username}</p>
          {profile.bio && <p className="text-gray-600 mt-3">{profile.bio}</p>}
          {profile.links && (
            <div className="flex flex-wrap gap-4 mt-4">
              {profile.links.github?.url && (
                <a href={profile.links.github.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
                  <Github size={16} /> GitHub
                  {profile.links.github.verified && <BadgeCheck size={14} className="text-green-600" />}
                </a>
              )}
              {profile.links.linkedin?.url && (
                <a href={profile.links.linkedin.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
                  <Linkedin size={16} /> LinkedIn
                </a>
              )}
              {profile.links.orcid?.url && (
                <a href={profile.links.orcid.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
                  <ExternalLink size={16} /> ORCID
                </a>
              )}
              {profile.links.portfolio?.url && (
                <a href={profile.links.portfolio.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
                  <ExternalLink size={16} /> Portfolio
                </a>
              )}
            </div>
          )}
        </div>
      </div>

      {reputation && (
        <div className="glass rounded-2xl p-6 mt-6 space-y-5">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <h2 className="font-semibold text-gray-900">Community Contributions</h2>
              <p className="text-sm text-gray-500">Level {reputation.level} · {reputation.contribution_score} points · {reputation.administrator_stars} admin stars</p>
            </div>
            <div className="text-sm text-gray-500">{reputation.implemented_suggestions} implemented suggestions</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {reputation.badges.map((badge) => (
              <span key={badge.name} title={badge.reason} className="px-3 py-1.5 rounded-full border border-nexora-accent/20 bg-nexora-accent/10 text-nexora-accent text-sm font-medium">{badge.name}</span>
            ))}
            {reputation.badges.length === 0 && <span className="text-sm text-gray-400">No badges earned yet.</span>}
          </div>
          {reputation.recent_feedback.length > 0 && (
            <div className="border-t border-gray-100 pt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Recent Feedback</h3>
              <div className="space-y-2">
                {reputation.recent_feedback.map((item) => (
                  <div key={item.id} className="p-3 rounded-xl border border-gray-100 bg-white shadow-sm flex flex-col gap-2 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-gray-700 font-medium truncate">{item.title}</span>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{statusLabels[item.status]}</span>
                    </div>
                    {/* Reactions Row */}
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {[
                        { key: 'helpful', label: 'Helpful' },
                        { key: 'interesting', label: 'Interesting' },
                        { key: 'needs_more_info', label: 'Needs More' },
                        { key: 'agree', label: 'Agree' },
                        { key: 'research_worthy', label: 'Research' }
                      ].map(reaction => {
                        const count = item.reactions?.[reaction.key]?.length || 0;
                        const hasReacted = user && item.reactions?.[reaction.key]?.includes(user.uid);
                        return (
                          <button
                            key={reaction.key}
                            onClick={() => {
                              if (!user) return;
                              communityApi.react(item.id, reaction.key).then(updated => {
                                setReputation(current => {
                                  if (!current) return current;
                                  return {
                                    ...current,
                                    recent_feedback: current.recent_feedback.map(f => f.id === updated.id ? updated : f)
                                  };
                                });
                              });
                            }}
                            className={`px-2 py-0.5 text-[11px] rounded border flex items-center gap-1 transition-colors ${
                              hasReacted 
                                ? 'border-nexora-accent bg-nexora-accent/10 text-nexora-accent'
                                : 'border-gray-200 bg-gray-50 text-gray-600 hover:border-gray-300'
                            }`}
                          >
                            <span>{reaction.label}</span>
                            {count > 0 && <span className="font-medium">{count}</span>}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      <p className="text-center text-sm text-gray-400 mt-6">
        <Link to="/" className="hover:text-nexora-accent">Back to Nexora</Link>
      </p>
    </div>
  );
}
