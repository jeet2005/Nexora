import { useEffect, useState } from 'react';
import { MessageSquare, Pin, Star } from 'lucide-react';
import { adminFeedbackApi, categoryLabels, FeedbackAnalytics, FeedbackItem, FeedbackPriority, FeedbackStatus, statusLabels } from '../../api/community';

const statuses: FeedbackStatus[] = ['waiting', 'under_review', 'planned', 'implemented', 'closed', 'duplicate'];
const priorities: FeedbackPriority[] = ['low', 'normal', 'high', 'urgent'];
const badges = ['Founding Tester', 'Early Adopter', 'Community Supporter', 'Research Contributor', 'Feedback Champion', 'Top Tester', 'Bug Hunter', 'Dataset Explorer', 'Verified Researcher', 'Power User'];

export function FeedbackReview() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [analytics, setAnalytics] = useState<FeedbackAnalytics | null>(null);
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([adminFeedbackApi.list(), adminFeedbackApi.analytics()])
      .then(([feedback, stats]) => {
        setItems(feedback);
        setAnalytics(stats);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const update = async (id: string, payload: Parameters<typeof adminFeedbackApi.update>[1]) => {
    const updated = await adminFeedbackApi.update(id, payload);
    setItems((current) => current.map((item) => item.id === id ? updated : item));
    adminFeedbackApi.analytics().then(setAnalytics).catch(() => undefined);
  };

  const reply = async (id: string) => {
    const message = replyDrafts[id]?.trim();
    if (!message) return;
    const updated = await adminFeedbackApi.reply(id, message);
    setItems((current) => current.map((item) => item.id === id ? updated : item));
    setReplyDrafts((current) => ({ ...current, [id]: '' }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-nexora-dark">Feedback Review</h1>
        <p className="text-sm text-nexora-dark/60 mt-1">Review community ideas, reward helpful reports, and move suggestions through implementation.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Stat label="Submitted" value={analytics?.submitted ?? 0} />
        <Stat label="Open" value={analytics?.open ?? 0} />
        <Stat label="Implemented" value={analytics?.implemented ?? 0} />
        <Stat label="Closed" value={analytics?.closed ?? 0} />
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="glass rounded-2xl p-8 text-center text-gray-400">Loading feedback...</div>
        ) : items.length === 0 ? (
          <div className="glass rounded-2xl p-8 text-center text-gray-400">No feedback submitted yet.</div>
        ) : items.map((item) => (
          <article key={item.id} className="glass rounded-2xl p-5 space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 mb-2">
                  {item.pinned && <span className="inline-flex items-center gap-1 text-nexora-accent"><Pin size={13} /> Pinned</span>}
                  <span>{categoryLabels[item.category]}</span>
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  <span>{item.user_name || item.user_email || 'Nexora User'}</span>
                </div>
                <h2 className="font-semibold text-gray-900">{item.title}</h2>
                <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{item.description}</p>
                {item.suggestion && <p className="text-sm text-gray-500 mt-2"><span className="font-medium text-gray-700">Suggestion:</span> {item.suggestion}</p>}
              </div>
              <div className="flex items-center gap-1 text-nexora-accent"><Star size={16} /> {item.stars}</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              <Select label="Status" value={item.status} options={statuses} labels={statusLabels} onChange={(value) => update(item.id, { status: value as FeedbackStatus })} />
              <Select label="Priority" value={item.priority} options={priorities} onChange={(value) => update(item.id, { priority: value as FeedbackPriority })} />
              <Select label="Stars" value={String(item.stars || 0)} options={['0', '1', '2', '3']} onChange={(value) => update(item.id, { stars: Number(value) })} />
              <Select label="Badge" value={item.badge_awarded || ''} options={['', ...badges]} onChange={(value) => update(item.id, { badge_awarded: value || null })} />
              <label className="text-xs text-gray-500 flex flex-col gap-1">
                Pin
                <button type="button" onClick={() => update(item.id, { pinned: !item.pinned })} className={`px-3 py-2 rounded-xl border text-sm ${item.pinned ? 'border-nexora-accent text-nexora-accent bg-nexora-accent/10' : 'border-gray-200 text-gray-600 bg-white'}`}>
                  {item.pinned ? 'Pinned' : 'Pin feedback'}
                </button>
              </label>
            </div>

            {item.admin_replies && item.admin_replies.length > 0 && (
              <div className="border-t border-gray-100 pt-3 space-y-2">
                {item.admin_replies.map((entry) => (
                  <p key={entry.id} className="text-sm text-gray-600"><span className="font-medium text-gray-900">{entry.admin_email}:</span> {entry.message}</p>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              <input value={replyDrafts[item.id] || ''} onChange={(event) => setReplyDrafts((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Reply to this feedback" className="flex-1 px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
              <button type="button" onClick={() => reply(item.id)} className="btn-primary py-2 px-4 flex items-center gap-2"><MessageSquare size={15} /> Reply</button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

function Select({ label, value, options, labels, onChange }: { label: string; value: string; options: string[]; labels?: Record<string, string>; onChange: (value: string) => void }) {
  return (
    <label className="text-xs text-gray-500 flex flex-col gap-1">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="px-3 py-2 rounded-xl border border-gray-200 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20">
        {options.map((option) => <option key={option || 'none'} value={option}>{option ? (labels?.[option] || option) : 'None'}</option>)}
      </select>
    </label>
  );
}
