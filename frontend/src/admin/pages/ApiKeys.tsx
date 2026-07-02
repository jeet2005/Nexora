import React, { useEffect, useState } from 'react';
import { adminApi, ApiKey } from '../../api/admin';
import { Key, Ban, CheckCircle2, XCircle } from 'lucide-react';

export const ApiKeys: React.FC = () => {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchKeys = async () => {
    try {
      const data = await adminApi.listApiKeys();
      setKeys(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleRevoke = async (datasetId: string, deploymentId: string) => {
    if (!window.confirm("Are you sure you want to deactivate this API key? This cannot be undone from the UI.")) return;
    try {
      await adminApi.revokeApiKey(datasetId, deploymentId);
      fetchKeys(); // refresh
    } catch (err) {
      console.error("Failed to revoke", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <Key className="text-nexora-accent" size={24} />
          API Keys
        </h1>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-nexora-dark/5 text-sm font-semibold text-nexora-dark/70">
              <tr>
                <th className="px-6 py-4">API Key Preview</th>
                <th className="px-6 py-4">Dataset ID</th>
                <th className="px-6 py-4">Created At</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nexora-border">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-nexora-dark/50">
                    <div className="animate-pulse">Loading deployments...</div>
                  </td>
                </tr>
              ) : keys.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-nexora-dark/50">
                    No active API keys found. Deploy a model to create one.
                  </td>
                </tr>
              ) : (
                keys.map((k, i) => (
                  <tr key={`${k.dataset_id}-${k.id}-${i}`} className="hover:bg-black/5 transition-colors">
                    <td className="px-6 py-4 font-mono text-sm font-bold text-nexora-dark">{k.api_key_preview || 'nx_****'}</td>
                    <td className="px-6 py-4 text-sm font-mono text-nexora-dark/60" title={k.dataset_id}>{k.dataset_id.substring(0,8)}...</td>
                    <td className="px-6 py-4 text-sm text-nexora-dark/80">{new Date(k.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      {k.active ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                          <CheckCircle2 size={14} /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                          <XCircle size={14} /> Revoked
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {k.active && (
                        <button
                          onClick={() => handleRevoke(k.dataset_id, k.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                        >
                          <Ban size={16} /> Deactivate
                        </button>
                      )}
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
