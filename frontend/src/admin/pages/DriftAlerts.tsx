import React, { useEffect, useState } from 'react';
import { adminApi } from '../../api/admin';
import { AlertTriangle, TrendingDown, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DriftAlert {
  dataset_id: string;
  batch_id: string;
  feature: string;
  score?: number;
  severity: string;
  status: string;
  created_at: string;
}

export const DriftAlerts: React.FC = () => {
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');

  const fetchAlerts = async () => {
    try {
      const data = await adminApi.getDriftAlerts();
      setAlerts(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleResolve = async (alert: DriftAlert) => {
    await adminApi.resolveDriftAlert(alert.dataset_id, alert.batch_id, alert.feature);
    fetchAlerts();
  };

  const filtered = alerts.filter(a => {
    if (severityFilter && a.severity !== severityFilter) return false;
    if (statusFilter && a.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <AlertTriangle className="text-nexora-accent" size={24} />
          Drift Alerts
        </h1>
        <div className="flex gap-3">
          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-gray-200 text-sm"
          >
            <option value="">All severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
          </select>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl border border-gray-200 text-sm"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-nexora-dark/5 text-sm font-semibold text-nexora-dark/70">
              <tr>
                <th className="px-6 py-4">Dataset ID</th>
                <th className="px-6 py-4">Feature</th>
                <th className="px-6 py-4">Drift Score</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Detected At</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nexora-border">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-nexora-dark/50">
                    <div className="animate-pulse">Scanning for drift...</div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-nexora-dark/50">
                    No drift alerts match your filters.
                  </td>
                </tr>
              ) : (
                filtered.map((a, i) => (
                  <tr key={`${a.dataset_id}-${a.feature}-${i}`} className="hover:bg-black/5 transition-colors">
                    <td className="px-6 py-4 font-mono text-sm" title={a.dataset_id}>{a.dataset_id.substring(0, 8)}...</td>
                    <td className="px-6 py-4 font-medium">{a.feature}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <TrendingDown size={16} className={a.severity === 'high' ? 'text-red-500' : 'text-yellow-500'} />
                        <span className={a.severity === 'high' ? 'text-red-700 font-bold' : 'text-yellow-700 font-medium'}>
                          {a.score?.toFixed(3) || 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                        a.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-nexora-dark/80">
                      {new Date(a.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {a.status === 'open' && (
                        <button
                          onClick={() => handleResolve(a)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-green-700 hover:bg-green-50 rounded-lg"
                        >
                          <CheckCircle size={14} /> Resolve
                        </button>
                      )}
                      <Link
                        to={`/dataset/${a.dataset_id}`}
                        target="_blank"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-nexora-accent hover:bg-nexora-accent/10 rounded-lg transition-colors"
                      >
                        Investigate
                      </Link>
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
