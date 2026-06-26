import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cog, Loader2, Play, AlertCircle, Clock } from "lucide-react";
import { getTimingEstimates, runPreprocess } from "../api/client";
import type { PreprocessResponse } from "../types/pipeline";
import { formatDuration } from "../utils/formatDuration";
import PreprocessSteps from "./PreprocessSteps";

interface Props {
  datasetId: string;
  onComplete: (response: PreprocessResponse) => void;
}

export default function PreprocessPanel({ datasetId, onComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scaling, setScaling] = useState<"standard" | "minmax" | "none">("standard");
  const [expectedSec, setExpectedSec] = useState<number | null>(null);

  useEffect(() => {
    getTimingEstimates(datasetId)
      .then((t) => setExpectedSec(t.preprocess_sec))
      .catch(() => undefined);
  }, [datasetId]);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runPreprocess(datasetId, {
        scaling,
        remove_duplicates: true,
        remove_constant: true,
        drop_id_columns: true,
        encode_categorical: true,
        outlier_method: "iqr_cap",
      });
      onComplete(res);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Preprocessing failed.";
      setError(typeof msg === "string" ? msg : "Preprocessing failed.");
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
          <Cog className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase">
            Automated Preprocessing Engine
          </h3>
          <p className="text-sm text-gray-500">
            Missing values · encoding · scaling · outliers · duplicates
            {expectedSec != null && (
              <span className="block text-xs text-emerald-600 mt-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Expected runtime: ~{formatDuration(expectedSec)}
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-3 mb-6 text-sm">
        {[
          { label: "Missing values", value: "Auto (median / mode)" },
          { label: "Encoding", value: "Label + One-Hot" },
          { label: "Outliers", value: "IQR capping" },
        ].map((item) => (
          <div key={item.label} className="px-3 py-2 rounded-lg bg-gray-50 border border-gray-100">
            <p className="text-gray-400 text-xs">{item.label}</p>
            <p className="text-gray-700">{item.value}</p>
          </div>
        ))}
      </div>

      <motion.div className="mb-6">
        <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">
          Feature Scaling
        </label>
        <div className="flex gap-2">
          {(["standard", "minmax", "none"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setScaling(s)}
              className={`px-4 py-2 rounded-lg text-sm border capitalize transition-all ${
                scaling === s
                  ? "border-emerald-400 bg-emerald-50 text-emerald-700"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"
              }`}
            >
              {s === "standard" ? "StandardScaler" : s === "minmax" ? "MinMaxScaler" : "None"}
            </button>
          ))}
        </div>
      </motion.div>

      <PreprocessSteps
        steps={[
          { step: "drop_id_columns", detail: "Remove ID-like columns", affected_rows_or_cols: 0 },
          { step: "remove_duplicates", detail: "Deduplicate rows", affected_rows_or_cols: 0 },
          { step: "fill_missing", detail: "Impute missing values", affected_rows_or_cols: 0 },
          { step: "outlier_cap", detail: "IQR outlier capping", affected_rows_or_cols: 0 },
          { step: "encode", detail: "Encode categoricals", affected_rows_or_cols: 0 },
          { step: "scale", detail: "Scale numeric features", affected_rows_or_cols: 0 },
        ]}
        pending
      />

      {error && (
        <motion.div className="flex items-center gap-2 text-red-500 text-sm mt-4">
          <AlertCircle className="w-4 h-4" />
          {error}
        </motion.div>
      )}

      <button
        type="button"
        onClick={handleRun}
        disabled={loading}
        className="btn-primary mt-6 disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Running preprocessing pipeline…
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Run Preprocessing Pipeline
          </>
        )}
      </button>
    </motion.div>
  );
}
