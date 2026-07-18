import React from 'react';
import { FeedbackItem, categoryLabels, statusLabels, communityApi } from '../api/community';
import { Star, BadgeCheck, MessageSquare, ThumbsUp, Lightbulb, HelpCircle, CheckCircle, FlaskConical } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const priorityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  normal: 'bg-blue-50 text-blue-600',
  high: 'bg-amber-50 text-amber-600',
  urgent: 'bg-red-50 text-red-600',
};

const reactions = [
  { key: 'helpful', label: 'Helpful', icon: ThumbsUp },
  { key: 'interesting', label: 'Interesting', icon: Lightbulb },
  { key: 'needs_more_info', label: 'Needs More', icon: HelpCircle },
  { key: 'agree', label: 'Agree', icon: CheckCircle },
  { key: 'research_worthy', label: 'Research', icon: FlaskConical },
];

export default function FeedbackCard({ feedback, onUpdate }: { feedback: FeedbackItem; onUpdate?: (updated: FeedbackItem) => void }) {
  const { user } = useAuth();
  const { id, title, category, status, priority, stars, badge_awarded, created_at, admin_replies, description } = feedback;
  const date = new Date(created_at).toLocaleDateString();
  const replyCount = admin_replies?.length || 0;

  const handleReact = async (reactionKey: string) => {
    if (!user) return;
    try {
      const updated = await communityApi.react(id, reactionKey);
      onUpdate?.(updated);
    } catch (e) {
      console.error('Failed to react', e);
    }
  };

  return (
    <div className="glass rounded-2xl p-5 border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-semibold text-gray-900 line-clamp-1">{title}</h2>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{description}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-nexora-accent/10 text-nexora-accent">
          {categoryLabels[category] || category}
        </span>
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          {statusLabels[status] || status}
        </span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityColors[priority] || 'bg-gray-100 text-gray-600'}`}>
          {priority}
        </span>
        <span className="text-xs text-gray-400">{date}</span>
      </div>
      <div className="flex items-center gap-3 mb-3">
        {stars > 0 && (
          <span className="flex items-center gap-1 text-amber-500 text-sm font-medium">
            {Array.from({ length: stars }).map((_, i) => <Star key={i} size={14} fill="currentColor" />)}
          </span>
        )}
        {badge_awarded && (
          <span className="flex items-center gap-1 text-nexora-accent text-sm">
            <BadgeCheck size={14} /> {badge_awarded}
          </span>
        )}
        {replyCount > 0 && (
          <span className="flex items-center gap-1 text-gray-500 text-sm">
            <MessageSquare size={14} /> {replyCount} {replyCount === 1 ? 'reply' : 'replies'}
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5 border-t border-gray-100 pt-3">
        {reactions.map(reaction => {
          const count = feedback.reactions?.[reaction.key]?.length || 0;
          const hasReacted = user && feedback.reactions?.[reaction.key]?.includes(user.uid);
          const Icon = reaction.icon;
          return (
            <button
              key={reaction.key}
              onClick={() => handleReact(reaction.key)}
              className={`px-2 py-1 text-xs rounded-lg border flex items-center gap-1 transition-colors ${
                hasReacted
                  ? 'border-nexora-accent bg-nexora-accent/10 text-nexora-accent'
                  : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-300'
              }`}
            >
              <Icon size={12} />
              <span>{reaction.label}</span>
              {count > 0 && <span className="font-medium">{count}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
