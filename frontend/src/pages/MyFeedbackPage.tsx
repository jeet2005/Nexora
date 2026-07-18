import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { communityApi, FeedbackItem, FeedbackStatus } from '../api/community';
import FeedbackCard from '../components/FeedbackCard';
import { Plus } from 'lucide-react';

const filters: { label: string; value: FeedbackStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Waiting', value: 'waiting' },
  { label: 'Under Review', value: 'under_review' },
  { label: 'Planned', value: 'planned' },
  { label: 'Implemented', value: 'implemented' },
  { label: 'Closed', value: 'closed' },
];

export default function MyFeedbackPage() {
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FeedbackStatus | 'all'>('all');

  useEffect(() => {
    communityApi.getMyFeedback()
      .then(setFeedback)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = activeFilter === 'all'
    ? feedback
    : feedback.filter(item => item.status === activeFilter);

  const handleUpdate = (updated: FeedbackItem) => {
    setFeedback(current => current.map(item => item.id === updated.id ? updated : item));
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
        <div>
          <p className="text-sm font-semibold text-nexora-accent mb-2">Community</p>
          <h1 className="text-3xl font-bold text-gray-900">My Feedback</h1>
          <p className="text-gray-500 mt-2">Track your submitted feedback, admin replies, stars, and badges.</p>
        </div>
        <Link to="/feedback/new" className="btn-primary py-2.5 px-5 flex items-center gap-2 text-sm">
          <Plus size={16} /> Submit Feedback
        </Link>
      </div>

      <div className="flex gap-2 mb-6 flex-wrap">
        {filters.map(f => (
          <button
            key={f.value}
            onClick={() => setActiveFilter(f.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activeFilter === f.value
                ? 'bg-nexora-accent/10 text-nexora-accent'
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            {f.label}
            {f.value !== 'all' && (
              <span className="ml-1.5 text-xs opacity-60">
                {feedback.filter(item => item.status === f.value).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="glass rounded-2xl p-12 text-center text-gray-400">Loading your feedback...</div>
      ) : filtered.length === 0 ? (
        <div className="glass rounded-2xl p-12 text-center">
          <p className="text-gray-400">No feedback found.</p>
          <Link to="/feedback/new" className="text-nexora-accent text-sm hover:underline mt-2 inline-block">Submit your first feedback</Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map(item => (
            <FeedbackCard key={item.id} feedback={item} onUpdate={handleUpdate} />
          ))}
        </div>
      )}
    </div>
  );
}
