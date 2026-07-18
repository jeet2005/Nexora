import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { Send, UploadCloud } from 'lucide-react';
import { categoryLabels, communityApi, FeedbackCategory, FeedbackPriority, FeedbackAttachment } from '../api/community';
import { useAuth } from '../contexts/AuthContext';

const categories = Object.keys(categoryLabels) as FeedbackCategory[];
const priorities: FeedbackPriority[] = ['low', 'normal', 'high', 'urgent'];

export default function SubmitFeedbackPage() {
  const { user } = useAuth();
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<FeedbackCategory>('feature');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<FeedbackPriority>('normal');
  const [suggestion, setSuggestion] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');



  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!user) {
      setError('Please sign in to submit feedback.');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      let finalAttachments: FeedbackAttachment[] = [];
      if (files.length > 0) {
        const uploadRes = await communityApi.uploadFiles(files);
        finalAttachments = uploadRes.attachments;
      }
      
      await communityApi.submitFeedback({ 
        title, 
        category, 
        description, 
        priority, 
        suggestion, 
        attachments: finalAttachments 
      });
      setTitle('');
      setDescription('');
      setSuggestion('');
      setFiles([]);
      setMessage('Feedback submitted. Admins can now review, reply, star, and mark progress.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not submit feedback');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-sm font-semibold text-nexora-accent mb-2">Community</p>
          <h1 className="text-3xl font-bold text-gray-900">Submit Feedback</h1>
          <p className="text-gray-500 mt-2 max-w-2xl">Share bugs, research ideas, dataset needs, performance notes, or feature requests with the Nexora team.</p>
        </div>
        <Link to="/feedback" className="btn-outline py-2 px-4 text-sm">My Feedback</Link>
      </div>

      {!user && <div className="mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50 text-sm text-amber-700">Sign in before submitting feedback.</div>}
      {message && <div className="mb-6 p-4 rounded-xl border border-green-200 bg-green-50 text-sm text-green-700">{message}</div>}
      {error && <div className="mb-6 p-4 rounded-xl border border-red-200 bg-red-50 text-sm text-red-600">{error}</div>}

      <form onSubmit={handleSubmit} className="glass rounded-2xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="Support notebook exports for reports" className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value as FeedbackCategory)} className="w-full px-4 py-2 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-nexora-accent/20">
              {categories.map((item) => <option key={item} value={item}>{categoryLabels[item]}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value as FeedbackPriority)} className="w-full px-4 py-2 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-nexora-accent/20">
              {priorities.map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} required rows={6} placeholder="What happened, what should happen, and why it matters..." className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Suggestion</label>
          <textarea value={suggestion} onChange={(e) => setSuggestion(e.target.value)} rows={3} placeholder="Optional implementation or workflow suggestion" className="w-full px-4 py-2 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-nexora-accent/20" />
        </div>
        <label className="block border border-dashed border-nexora-border rounded-2xl p-5 cursor-pointer hover:border-nexora-accent/50 transition-colors">
          <input type="file" multiple className="hidden" onChange={(e) => setFiles(Array.from(e.target.files || []))} />
          <span className="flex items-center gap-3 text-sm text-gray-600"><UploadCloud size={18} className="text-nexora-accent" /> Attach screenshots or files</span>
          {files.length > 0 && <span className="block mt-2 text-xs text-gray-400">{files.map((file) => file.name).join(', ')}</span>}
        </label>
        <button type="submit" disabled={saving || !user} className="btn-primary py-3 px-5 flex items-center gap-2 disabled:opacity-60">
          <Send size={16} /> {saving ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  );
}
