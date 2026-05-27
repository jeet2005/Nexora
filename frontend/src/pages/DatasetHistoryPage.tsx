import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Archive,
  ArchiveRestore,
  Database,
  Download,
  Loader2,
  Trash2,
} from "lucide-react";
import {
  archiveDataset,
  deleteDataset,
  getDatasetHistory,
  getReportDownloadUrl,
  type DatasetHistoryItem,
} from "../api/client";

export default function DatasetHistoryPage() {
  const [items, setItems] = useState<DatasetHistoryItem[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await getDatasetHistory(includeArchived));
      setError(null);
    } catch {
      setError("Could not load dataset history.");
    } finally {
      setLoading(false);
    }
  }, [includeArchived]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleArchive = async (item: DatasetHistoryItem) => {
    await archiveDataset(item.dataset_id, !item.archived);
    await load();
  };

  const remove = async (item: DatasetHistoryItem) => {
    const confirmed = window.confirm(`Delete ${item.filename}? This removes local files and model artifacts.`);
    if (!confirmed) return;
    await deleteDataset(item.dataset_id);
    await load();
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <p className="text-emerald-600 font-mono text-xs uppercase tracking-widest mb-2">
          Workspace
        </p>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl text-gray-900">Dataset History</h1>
            <p className="text-gray-500 mt-2">
              Reopen datasets, download reports, and manage saved model work.
            </p>
          </div>
          <label className="inline-flex items-center gap-2 text-sm text-gray-500">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(event) => setIncludeArchived(event.target.checked)}
              className="accent-emerald-600"
            />
            Show archived
          </label>
        </div>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-emerald-600">
          <Loader2 className="w-5 h-5 animate-spin" />
        </div>
      ) : error ? (
        <div className="glass p-8 text-center text-red-500">{error}</div>
      ) : items.length === 0 ? (
        <div className="glass p-10 text-center">
          <Database className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No saved datasets yet.</p>
          <Link to="/" className="btn-primary mt-5">
            Upload a dataset
          </Link>
        </div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-5">
          {items.map((item) => (
            <motion.article
              key={item.dataset_id}
              className={`glass p-5 ${item.archived ? "opacity-70" : ""}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Link
                    to={`/dataset/${item.dataset_id}`}
                    className="text-lg font-display text-gray-900 hover:text-emerald-700 truncate block"
                  >
                    {item.filename}
                  </Link>
                  <p className="text-xs text-gray-400 mt-1">
                    {item.rows.toLocaleString()} rows · {item.columns} columns · health {item.health_score}/100
                  </p>
                </div>
                <span className="text-[10px] uppercase tracking-wide px-2 py-1 rounded border border-gray-200 text-gray-500">
                  {item.status}
                </span>
              </div>

              <div className="grid sm:grid-cols-2 gap-3 mt-5 text-sm">
                <Info label="Target" value={item.target_column ?? "Not selected"} />
                <Info label="Problem" value={item.problem_type ?? "Not configured"} />
                <Info label="Last model" value={item.last_trained_model ?? "None"} />
                <Info label="Trained models" value={String(item.trained_model_count)} />
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                <Link to={`/dataset/${item.dataset_id}`} className="btn-primary px-4 py-2 text-sm">
                  Open
                </Link>
                {item.report_available && (
                  <a href={getReportDownloadUrl(item.dataset_id)} className="btn-ghost border border-gray-200 text-sm">
                    <Download className="w-4 h-4" />
                    Report
                  </a>
                )}
                <button type="button" onClick={() => toggleArchive(item)} className="btn-ghost border border-gray-200 text-sm">
                  {item.archived ? <ArchiveRestore className="w-4 h-4" /> : <Archive className="w-4 h-4" />}
                  {item.archived ? "Restore" : "Archive"}
                </button>
                <button type="button" onClick={() => remove(item)} className="btn-ghost border border-red-100 text-sm text-red-500 hover:text-red-600">
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </motion.article>
          ))}
        </div>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-gray-50 border border-gray-100 p-3 min-w-0">
      <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">{label}</p>
      <p className="text-gray-700 truncate" title={value}>
        {value}
      </p>
    </div>
  );
}
