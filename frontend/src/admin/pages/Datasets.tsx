import React, { useEffect, useState } from 'react';
import { adminApi, DatasetRecord } from '../../api/admin';
import { Database, Trash2, Activity, FileSpreadsheet } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Datasets: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDatasets = async () => {
    try {
      const data = await adminApi.listDatasets();
      setDatasets(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleDelete = async (datasetId: string) => {
    if (!window.confirm("Delete this dataset entirely? This removes all local files and database records permanently.")) return;
    try {
      await adminApi.deleteDataset(datasetId);
      fetchDatasets();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <Database className="text-nexora-accent" size={24} />
          Datasets & Training Jobs
        </h1>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-nexora-dark/5 text-sm font-semibold text-nexora-dark/70">
              <tr>
                <th className="px-6 py-4">Dataset Name</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Models Trained</th>
                <th className="px-6 py-4">Health Score</th>
                <th className="px-6 py-4">Updated At</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nexora-border">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-nexora-dark/50">
                    <div className="animate-pulse">Loading datasets...</div>
                  </td>
                </tr>
              ) : datasets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-nexora-dark/50">
                    No datasets found.
                  </td>
                </tr>
              ) : (
                datasets.map((ds) => (
                  <tr key={ds.dataset_id} className="hover:bg-black/5 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <FileSpreadsheet size={16} className="text-nexora-accent" />
                        <span className="font-medium text-nexora-dark">{ds.filename}</span>
                        {ds.archived && (
                          <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded text-gray-700">Archived</span>
                        )}
                      </div>
                      <div className="text-xs text-nexora-dark/50 mt-1 font-mono">{ds.dataset_id}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 capitalize">
                        {ds.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {ds.trained_model_count > 0 ? (
                        <div className="flex flex-col">
                          <span className="text-sm font-medium">{ds.trained_model_count} models</span>
                          <span className="text-xs text-nexora-dark/60" title={ds.last_trained_model}>Best: {ds.last_trained_model?.length > 20 ? ds.last_trained_model.substring(0,20)+'...' : ds.last_trained_model}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-nexora-dark/40">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${ds.health_score > 80 ? 'bg-green-500' : ds.health_score > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${ds.health_score}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium">{Math.round(ds.health_score)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-nexora-dark/80">
                      {new Date(ds.updated_at || ds.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to={`/dataset/${ds.dataset_id}`}
                          target="_blank"
                          className="p-2 text-nexora-accent hover:bg-nexora-accent/10 rounded-lg transition-colors tooltip-trigger"
                          title="View Dataset Dashboard"
                        >
                          <Activity size={18} />
                        </Link>
                        <button
                          onClick={() => handleDelete(ds.dataset_id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors tooltip-trigger"
                          title="Permanently Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
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
