import { useEffect, useState } from 'react';
import { Award, Star, Trophy } from 'lucide-react';
import { communityApi, LeaderboardEntry } from '../api/community';

const periods = ['weekly', 'monthly', 'all'];

export default function CommunityLeaderboardPage() {
  const [period, setPeriod] = useState('all');
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    communityApi.getLeaderboard(period)
      .then(setRows)
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
        <div>
          <p className="text-sm font-semibold text-nexora-accent mb-2">Community</p>
          <h1 className="text-3xl font-bold text-gray-900">Leaderboard</h1>
          <p className="text-gray-500 mt-2">Top contributors, researchers, testers, feedback authors, and bug hunters.</p>
        </div>
        <div className="flex gap-2 rounded-xl border border-nexora-border p-1 bg-white">
          {periods.map((item) => (
            <button key={item} onClick={() => setPeriod(item)} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${period === item ? 'bg-nexora-accent/10 text-nexora-accent' : 'text-gray-500 hover:text-gray-900'}`}>
              {item === 'all' ? 'All Time' : item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-sm text-gray-500">
            <tr>
              <th className="px-6 py-4">Rank</th>
              <th className="px-6 py-4">Contributor</th>
              <th className="px-6 py-4">Level</th>
              <th className="px-6 py-4">Score</th>
              <th className="px-6 py-4">Stars</th>
              <th className="px-6 py-4">Badges</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-400">Loading leaderboard...</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-10 text-center text-gray-400">No community contributions yet.</td></tr>
            ) : rows.map((row, index) => (
              <tr key={row.user_id} className="hover:bg-gray-50/50">
                <td className="px-6 py-4 font-semibold text-gray-900">#{index + 1}</td>
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900">{row.name}</div>
                  <div className="text-xs text-gray-400">{row.feedback_submitted} feedback items</div>
                </td>
                <td className="px-6 py-4"><span className="inline-flex items-center gap-1 text-sm text-nexora-accent"><Trophy size={15} /> {row.level}</span></td>
                <td className="px-6 py-4 font-semibold text-gray-900">{row.contribution_score}</td>
                <td className="px-6 py-4"><span className="inline-flex items-center gap-1 text-sm"><Star size={15} className="text-nexora-accent" /> {row.administrator_stars}</span></td>
                <td className="px-6 py-4"><span className="inline-flex items-center gap-1 text-sm"><Award size={15} className="text-nexora-accent" /> {row.badges_earned}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
