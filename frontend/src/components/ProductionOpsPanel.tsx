import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Copy,
  Download,
  KeyRound,
  Loader2,
  Rocket,
  Upload,
} from "lucide-react";
import {
  createDeployment,
  deactivateDeployment,
  getBatchPredictions,
  getDeployments,
  runBatchPrediction,
  type BatchPredictionSummary,
  type ModelDeployment,
} from "../api/client";
import type { ProductionStatus } from "../types/production";

interface Props {
  datasetId: string;
  status: ProductionStatus | null;
  selectedModelIds: string[];
}

export default function ProductionOpsPanel({ datasetId, status, selectedModelIds }: Props) {
  const [batches, setBatches] = useState<BatchPredictionSummary[]>([]);
  const [deployments, setDeployments] = useState<ModelDeployment[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ready = Boolean(status?.models.length);
  const baseApi = (import.meta.env.VITE_API_BASE_URL ?? "/api").replace(/\/$/, "");
  const selected = useMemo(
    () => selectedModelIds.filter((id) => status?.models.some((model) => model.model_id === id)),
    [selectedModelIds, status]
  );

  const load = useCallback(async () => {
    if (!ready) return;
    const [batchData, deploymentData] = await Promise.all([
      getBatchPredictions(datasetId),
      getDeployments(datasetId),
    ]);
    setBatches(batchData);
    setDeployments(deploymentData);
  }, [datasetId, ready]);

  useEffect(() => {
    load().catch(() => undefined);
  }, [load]);

  const submitBatch = async () => {
    if (!file) return;
    setBusy("batch");
    setError(null);
    try {
      const batch = await runBatchPrediction(datasetId, file, selected.length ? selected : undefined);
      setBatches((current) => [batch, ...current]);
      setFile(null);
    } catch (err: unknown) {
      setError(apiError(err, "Batch prediction failed."));
    } finally {
      setBusy(null);
    }
  };

  const deploy = async () => {
    setBusy("deploy");
    setError(null);
    try {
      const res = await createDeployment(datasetId, "Production endpoint", selected.length ? selected : undefined);
      setDeployments((current) => [res.deployment, ...current]);
      setApiKey(res.api_key);
    } catch (err: unknown) {
      setError(apiError(err, "Could not create deployment endpoint."));
    } finally {
      setBusy(null);
    }
  };

  const deactivate = async (deploymentId: string) => {
    setBusy(deploymentId);
    await deactivateDeployment(datasetId, deploymentId);
    await load();
    setBusy(null);
  };

  if (!ready) {
    return (
      <section className="glass p-6 text-sm text-gray-400">
        Train selected models to unlock batch prediction, API deployment, and drift monitoring.
      </section>
    );
  }

  return (
    <motion.section className="glass p-6" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-5 mb-5">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-emerald-600 font-mono mb-1">
            Production Operations
          </p>
          <h3 className="font-display text-lg text-gray-900">Batch, Drift & API Deployment</h3>
          <p className="text-sm text-gray-500 mt-1">
            Use saved models against new files or expose a stable prediction endpoint.
          </p>
        </div>
        <button type="button" onClick={deploy} disabled={busy === "deploy"} className="btn-primary shrink-0">
          {busy === "deploy" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
          Create API Endpoint
        </button>
      </div>

      {apiKey && (
        <div className="mb-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <p className="font-medium mb-1">Copy this API key now. It will not be shown again.</p>
          <code className="block break-all text-xs bg-white/70 rounded p-2">{apiKey}</code>
        </div>
      )}

      {error && (
        <div className="mb-5 flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="grid xl:grid-cols-[0.9fr_1.1fr] gap-5">
        <div className="rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Upload className="w-4 h-4 text-emerald-600" />
            <h4 className="text-sm font-medium text-gray-800">Batch Prediction</h4>
          </div>
          <input
            type="file"
            accept=".csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-3 file:rounded-lg file:border-0 file:bg-emerald-50 file:px-3 file:py-2 file:text-emerald-700"
          />
          <button
            type="button"
            onClick={submitBatch}
            disabled={!file || busy === "batch"}
            className="btn-primary w-full mt-4 disabled:opacity-50"
          >
            {busy === "batch" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Run Batch
          </button>

          <div className="mt-4 space-y-2 max-h-[260px] overflow-y-auto">
            {batches.length === 0 ? (
              <p className="text-xs text-gray-400">No batch files processed yet.</p>
            ) : (
              batches.map((batch) => (
                <div key={batch.batch_id} className="rounded-lg bg-gray-50 border border-gray-100 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm text-gray-800 truncate">{batch.filename}</p>
                      <p className="text-xs text-gray-400">
                        {batch.rows.toLocaleString()} rows · drift {batch.drift.severity ?? "low"}
                      </p>
                    </div>
                    <a
                      href={baseApi.endsWith("/api") ? `${baseApi.replace(/\/api$/, "")}${batch.download_url}` : `${baseApi}${batch.download_url}`}
                      className="p-2 rounded-lg text-emerald-700 hover:bg-emerald-50"
                      title="Download predictions"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                  {batch.drift.features?.slice(0, 2).map((feature) => (
                    <p key={String(feature.feature)} className="text-[11px] text-gray-500 mt-1">
                      {String(feature.feature)} drift score: {String(feature.score)}
                    </p>
                  ))}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-3">
            <KeyRound className="w-4 h-4 text-emerald-600" />
            <h4 className="text-sm font-medium text-gray-800">Prediction API</h4>
          </div>
          <div className="space-y-2 max-h-[360px] overflow-y-auto">
            {deployments.length === 0 ? (
              <p className="text-xs text-gray-400">No API endpoints created yet.</p>
            ) : (
              deployments.map((deployment) => (
                <div key={deployment.deployment_id} className="rounded-lg bg-gray-50 border border-gray-100 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm text-gray-800">{deployment.name}</p>
                      <p className="text-xs text-gray-400">
                        {deployment.model_ids.length} models · {deployment.active ? "active" : "inactive"}
                      </p>
                    </div>
                    {deployment.active && (
                      <button
                        type="button"
                        onClick={() => deactivate(deployment.deployment_id)}
                        disabled={busy === deployment.deployment_id}
                        className="text-xs text-red-500 hover:text-red-600"
                      >
                        Disable
                      </button>
                    )}
                  </div>
                  <div className="mt-2 flex gap-2">
                    <code className="flex-1 text-[11px] bg-white rounded p-2 overflow-hidden text-ellipsis">
                      {deployment.predict_url.replace("http://127.0.0.1:8000/api", baseApi)}
                    </code>
                    <button
                      type="button"
                      onClick={() => navigator.clipboard.writeText(deployment.predict_url.replace("http://127.0.0.1:8000/api", baseApi))}
                      className="p-2 rounded-lg text-gray-500 hover:bg-white"
                      title="Copy URL"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                  {deployment.api_key_preview && (
                    <p className="text-[11px] text-gray-400 mt-2">Key: {deployment.api_key_preview}</p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </motion.section>
  );
}

function apiError(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

