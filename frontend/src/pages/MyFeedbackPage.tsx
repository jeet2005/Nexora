import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { BadgeCheck, MessageSquare, Star } from 'lucide-react';
import { categoryLabels, communityApi, FeedbackItem, statusLabels } from '../api/community';
import { useAuth } from '../contexts/AuthContext';

const statusClass: Record<string, string> = {
  waiting: 'bg-gray-100 text-gray-700',
  under_review: 'bg-blue-50 text-blue-700',
  planned: 'bg-nexora-accent/10 text-nexora-accent',
  implemented: 'bg-green-50 text-green-700',
  closed: 'bg-gray-100 text-gray-500',
  duplicate: 'bg-amber-50 text-amber-700',
};

export default function MyFeedbackPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    communityApi.getMyFeedback()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) return <div className="text-center py-20">Please log in to view your feedback.</div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-sm font-semibold text-nexora-accent mb-2">Community</p>
          <h1 className="text-3xl font-bold text-gray-900">My Feedback</h1>
          <p className="text-gray-500 mt-2">Track admin replies, stars, badges, and implementation progress.</p>
        </div>
        <Link to="/feedback/new" className="btn-primary py-2 px-4 text-sm">Submit Feedback</Link>
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="glass rounded-2xl p-8 text-center text-gray-400">Loading feedback...</div>
        ) : items.length === 0 ? (
          <div className="glass rounded-2xl p-8 text-center text-gray-500">
            No feedback yet. <Link to="/feedback/new" className="text-nexora-accent hover:underline">Submit your first idea</Link>.
          </div>
        ) : items.map((item) => (
          <article key={item.id} className="glass rounded-2xl p-5 hover:bg-white/80 transition-colors">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusClass[item.status]}`}>{statusLabels[item.status]}</span>
                  <span className="text-xs text-gray-400">{categoryLabels[item.category]}</span>
                  <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
                <h2 className="font-semibold text-gray-900">{item.title}</h2>
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">{item.description}</p>
              </div>
              <div className="flex flex-wrap gap-3 text-sm text-gray-500 md:justify-end">
                <span className="inline-flex items-center gap-1"><MessageSquare size={15} /> {item.admin_replies?.length || 0} replies</span>
                <span className="inline-flex items-center gap-1"><Star size={15} className="text-nexora-accent" /> {item.stars || 0}</span>
                {item.badge_awarded && <span className="inline-flex items-center gap-1 text-nexora-accent"><BadgeCheck size={15} /> {item.badge_awarded}</span>}
              </div>
            </div>
            {item.admin_replies && item.admin_replies.length > 0 && (
              <div className="mt-4 border-t border-gray-100 pt-4 space-y-2">
                {item.admin_replies.slice(-2).map((reply) => (
                  <p key={reply.id} className="text-sm text-gray-600"><span className="font-medium text-gray-900">Admin:</span> {reply.message}</p>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
