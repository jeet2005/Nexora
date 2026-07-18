import { useEffect, useState } from 'react';
import { MessageSquare, Pin, Star, Paperclip, StickyNote } from 'lucide-react';
import { adminFeedbackApi, categoryLabels, FeedbackAnalytics, FeedbackItem, FeedbackPriority, FeedbackStatus, statusLabels } from '../../api/community';

const statuses: FeedbackStatus[] = ['waiting', 'under_review', 'planned', 'implemented', 'closed', 'duplicate'];
const priorities: FeedbackPriority[] = ['low', 'normal', 'high', 'urgent'];
const badges = ['Founding Tester', 'Early Adopter', 'Community Supporter', 'Research Contributor', 'Feedback Champion', 'Top Tester', 'Bug Hunter', 'Dataset Explorer', 'Verified Researcher', 'Power User'];

export function FeedbackReview() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [analytics, setAnalytics] = useState<FeedbackAnalytics | null>(null);
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
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

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Stat label="Submitted" value={analytics?.submitted ?? 0} />
        <Stat label="Open" value={analytics?.open ?? 0} />
        <Stat label="Implemented" value={analytics?.implemented ?? 0} />
        <Stat label="Closed" value={analytics?.closed ?? 0} />
        <Stat label="Avg Response (hrs)" value={analytics?.average_response_time_hours ?? 0} />
      </div>

      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass p-5 rounded-2xl">
            <h3 className="font-semibold text-sm text-nexora-dark mb-3">Most Requested Features</h3>
            <div className="space-y-2">
              {analytics.most_requested_features?.map(f => (
                <div key={f.category} className="flex justify-between text-sm">
                  <span className="text-gray-600 capitalize">{f.category}</span>
                  <span className="font-medium">{f.count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="glass p-5 rounded-2xl">
            <h3 className="font-semibold text-sm text-nexora-dark mb-3">Trending Research Topics</h3>
            <div className="space-y-2">
              {analytics.trending_research_topics?.map(t => (
                <div key={t.topic} className="flex justify-between text-sm">
                  <span className="text-gray-600">{t.topic}</span>
                  <span className="font-medium">{t.count}</span>
                </div>
              ))}
              {!analytics.trending_research_topics?.length && <div className="text-sm text-gray-400">Not enough data</div>}
            </div>
          </div>
          <div className="glass p-5 rounded-2xl">
            <h3 className="font-semibold text-sm text-nexora-dark mb-3">Top Contributors</h3>
            <div className="space-y-2">
              {analytics.top_contributors?.map(c => (
                <div key={c.user_id} className="flex justify-between text-sm">
                  <span className="text-gray-600">{c.name}</span>
                  <span className="font-medium text-nexora-accent">{c.contribution_score} pts</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

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
                {item.attachments && item.attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {item.attachments.map((att, idx) => (
                      <a key={idx} href={att.url || '#'} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 rounded-lg border border-gray-200 bg-gray-50 text-xs text-gray-600 hover:border-nexora-accent/40">
                        <Paperclip size={12} /> {att.name}
                      </a>
                    ))}
                  </div>
                )}
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
              <label className="text-xs text-gray-500 flex flex-col gap-1">
                Assigned To
                <input value={(item as any).assigned_to || ''} onChange={(e) => update(item.id, { assigned_to: e.target.value } as any)} placeholder="Admin username or email" className="px-3 py-2 rounded-xl border border-gray-200 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
              </label>
              <label className="text-xs text-gray-500 flex flex-col gap-1">
                Duplicate Of
                <input value={item.duplicate_of || ''} onChange={(e) => update(item.id, { duplicate_of: e.target.value || null })} placeholder="Original feedback ID" className="px-3 py-2 rounded-xl border border-gray-200 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
              </label>
            </div>


            {item.admin_replies && item.admin_replies.length > 0 && (
              <div className="border-t border-gray-100 pt-3 space-y-2">
                {item.admin_replies.map((entry) => (
                  <p key={entry.id} className="text-sm text-gray-600"><span className="font-medium text-gray-900">{entry.admin_email}:</span> {entry.message}</p>
                ))}
              </div>
            )}

            <div className="border-t border-gray-100 pt-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-2"><StickyNote size={12} /> Internal Note</div>
              <div className="flex gap-2">
                <input value={noteDrafts[item.id] ?? (item as any).internal_note ?? ''} onChange={(event) => setNoteDrafts((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Private admin note (not visible to user)" className="flex-1 px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
                <button type="button" onClick={() => { const note = noteDrafts[item.id]?.trim(); if (note !== undefined) update(item.id, { internal_note: note } as any); }} className="btn-outline py-2 px-3 text-sm">Save</button>
              </div>
            </div>

            <div className="flex gap-3">
              <input value={replyDrafts[item.id] || ''} onChange={(event) => setReplyDrafts((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Reply to this feedback (sends notification)" className="flex-1 px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
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
