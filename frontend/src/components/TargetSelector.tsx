import { useState } from "react";
import { motion } from "framer-motion";
import { Target, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { configureTarget } from "../api/client";
import type { DatasetAnalysis } from "../types/dataset";
import type { ConfigureTargetResponse, ProblemType } from "../types/pipeline";

const PROBLEM_TYPES: { value: ProblemType; label: string; disabled?: boolean }[] = [
  { value: "classification", label: "Classification" },
  { value: "regression", label: "Regression" },
  { value: "time_series", label: "Time Series → Exploration Modes (Overview)", disabled: true },
  { value: "clustering", label: "Clustering → Exploration Modes (Overview)", disabled: true },
];

interface Props {
  datasetId: string;
  analysis: DatasetAnalysis;
  onConfigured: (response: ConfigureTargetResponse) => void;
}

export default function TargetSelector({ datasetId, analysis, onConfigured }: Props) {
  const [target, setTarget] = useState(
    analysis.prediction_suggestions[0]?.target_column ?? ""
  );
  const [problemType, setProblemType] = useState<ProblemType | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const columns = analysis.column_profiles.map((p) => p.name);

  const handleConfigure = async () => {
    if (!target) {
      setError("Select a target column.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await configureTarget(datasetId, target, problemType || undefined);
      onConfigured(res);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Configuration failed.";
      setError(typeof msg === "string" ? msg : "Configuration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="glass p-6"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center">
          <Target className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase">
            Prediction Target
          </h3>
          <p className="text-sm text-gray-500">Choose what Nexora should predict</p>
        </div>
      </div>

      {analysis.prediction_suggestions.length > 0 && (
        <div className="mb-6">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">Detected Targets</p>
          <div className="flex flex-wrap gap-2">
            {analysis.prediction_suggestions.map((s) => (
              <button
                key={s.target_column}
                type="button"
                onClick={() => {
                  setTarget(s.target_column);
                  setProblemType(s.problem_type as ProblemType);
                }}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                  target === s.target_column
                    ? "border-emerald-400 bg-emerald-50 text-emerald-700 font-medium"
                    : "border-gray-200 text-gray-500 hover:border-gray-300"
                }`}
              >
                {s.target_column}
                <span className="ml-2 text-xs opacity-60">{s.problem_type}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
            Target Column
          </label>
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100 transition-all"
          >
            <option value="">Select column…</option>
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
            Problem Type (optional override)
          </label>
          <select
            value={problemType}
            onChange={(e) => setProblemType(e.target.value as ProblemType | "")}
            className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3 text-gray-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100 transition-all"
          >
            <option value="">Auto-detect</option>
            {PROBLEM_TYPES.map((p) => (
              <option key={p.value} value={p.value} disabled={p.disabled}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-500 text-sm mb-4">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={handleConfigure}
        disabled={loading || !target}
        className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Detecting problem type…
          </>
        ) : (
          <>
            <CheckCircle2 className="w-4 h-4" />
            Confirm Target & Continue
          </>
        )}
      </button>
    </motion.div>
  );
}
