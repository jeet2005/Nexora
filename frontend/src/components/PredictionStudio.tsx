import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  FlaskConical,
  Gauge,
  Loader2,
  Play,
  SlidersHorizontal,
  TriangleAlert,
  Download,
} from "lucide-react";
import {
  explainPrediction,
  getProductionModels,
  getTimingEstimates,
  runProductionPrediction,
  trainProductionModels,
  downloadModel,
  type PredictionExplainResponse,
} from "../api/client";
import { formatDuration } from "../utils/formatDuration";
import type {
  DeployableModelOption,
  PredictionInputField,
  PredictionReceipt,
  ProductionStatus,
} from "../types/production";
import ProductionOpsPanel from "./ProductionOpsPanel";

interface Props {
  datasetId: string;
  onModelsTrained?: () => void;
}

export default function PredictionStudio({ datasetId, onModelsTrained }: Props) {
  const [available, setAvailable] = useState<DeployableModelOption[]>([]);
  const [status, setStatus] = useState<ProductionStatus | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [receipt, setReceipt] = useState<PredictionReceipt | null>(null);
  const [lastInputs, setLastInputs] = useState<Record<string, unknown>>({});
  const [explanation, setExplanation] = useState<PredictionExplainResponse | null>(null);
  const [eligibilityReason, setEligibilityReason] = useState("");
  const [limitations, setLimitations] = useState<string[]>([]);
  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trainEstimateSec, setTrainEstimateSec] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    getProductionModels(datasetId)
      .then((response) => {
        if (!alive) return;
        setAvailable(response.available_models);
        setStatus(response.deployed);
        setEligibilityReason(response.eligibility_reason);
        setLimitations(response.limitations);
        const existing = response.deployed?.models.map((model) => model.model_id) ?? [];
        const preferred = response.available_models
          .filter((model) => model.recommended)
          .slice(0, 2)
          .map((model) => model.model_id);
        setSelected(existing.length ? existing : preferred);
      })
      .catch((err: unknown) => setError(apiError(err, "Could not load model choices.")))
      .finally(() => setLoading(false));
    getTimingEstimates(datasetId, { productionModelCount: 2 })
      .then((t) => {
        if (alive) setTrainEstimateSec(t.production_train_sec);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [datasetId]);

  useEffect(() => {
    if (!selected.length) return;
    getTimingEstimates(datasetId, { productionModelCount: selected.length })
      .then((t) => setTrainEstimateSec(t.production_train_sec))
      .catch(() => undefined);
  }, [datasetId, selected.length]);

  const displayedModels = useMemo(
    () => (showAll ? available : available.filter((model) => model.recommended).slice(0, 8)),
    [available, showAll]
  );
  const modelsReady = useMemo(() => {
    if (!status) return false;
    const trained = status.models.map((model) => model.model_id).sort().join("|");
    return trained === [...selected].sort().join("|");
  }, [selected, status]);

  const selectModel = (modelId: string) => {
    setSelected((current) => {
      if (current.includes(modelId)) return current.filter((id) => id !== modelId);
      if (current.length >= 5) {
        setError("Select up to five models for a prediction run.");
        return current;
      }
      setError(null);
      return [...current, modelId];
    });
  };

  const handleTrain = async () => {
    if (!selected.length) {
      setError("Select at least one model.");
      return;
    }
    setTraining(true);
    setError(null);
    setReceipt(null);
    try {
      const requestedCount = selected.length;
      const trained = await trainProductionModels(datasetId, selected);
      setStatus(trained);
      setSelected(trained.models.map((model) => model.model_id));
      setValues({});
      if (trained.models.length < requestedCount) {
        setError("Some selected models were incompatible with this data. The trained models shown are ready.");
      }
      onModelsTrained?.();
    } catch (err: unknown) {
      setError(apiError(err, "Training selected models failed."));
    } finally {
      setTraining(false);
    }
  };

  const handlePredict = async () => {
    setPredicting(true);
    setError(null);
    try {
      const inputs = Object.fromEntries(
        Object.entries(values).filter(([, value]) => value !== "")
      );
      const result = await runProductionPrediction(datasetId, inputs);
      setLastInputs(inputs);
      setReceipt(result);
      setExplanation(null);
    } catch (err: unknown) {
      setError(apiError(err, "Prediction failed."));
    } finally {
      setPredicting(false);
    }
  };

  const handleExplainPrediction = async (modelId?: string) => {
    setExplaining(true);
    setError(null);
    try {
      const result = await explainPrediction(datasetId, lastInputs, modelId);
      setExplanation(result);
    } catch (err: unknown) {
      setError(apiError(err, "Prediction explanation failed."));
    } finally {
      setExplaining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-emerald-600">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.section
        className="glass px-6 py-5"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="flex items-start gap-4">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0">
              <FlaskConical className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h2 className="font-display text-lg text-gray-900">Prediction Studio</h2>
              <p className="text-sm text-gray-500 mt-1">
                Select saved models, enter known values, and run a reproducible backend prediction.
              </p>
            </div>
          </div>
          <div className="text-xs text-gray-500 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
            Chat explains. Trained models calculate.
          </div>
        </div>
      </motion.section>

      <section className="grid xl:grid-cols-[1.04fr_0.96fr] gap-6">
        <div className="glass p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-medium text-gray-800">Select Models</h3>
              <p className="text-xs text-gray-400 mt-1">Choose one to five models.</p>
            </div>
            <button
              type="button"
              className="btn-ghost text-xs"
              onClick={() => setShowAll((open) => !open)}
            >
              {showAll ? "Recommended" : "Browse all"}
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAll ? "rotate-180" : ""}`} />
            </button>
          </div>

          <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
            {eligibilityReason && (
              <p className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2 mb-3">
                {eligibilityReason}
              </p>
            )}
            {displayedModels.map((model) => {
              const checked = selected.includes(model.model_id);
              return (
                <label
                  key={model.model_id}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                    checked ? "border-emerald-200 bg-emerald-50/70" : "border-gray-100 hover:border-emerald-100"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => selectModel(model.model_id)}
                    className="w-4 h-4 accent-emerald-600"
                  />
                  <span className="flex-1 min-w-0">
                    <span className="block text-sm text-gray-800 truncate">{model.model_name}</span>
                    <span className="text-xs text-gray-400">
                      {model.family} - {model.speed}
                    </span>
                  </span>
                  {model.recommended && (
                    <span className="text-[10px] text-emerald-700 bg-emerald-100 rounded px-2 py-1">
                      Suggested
                    </span>
                  )}
                </label>
              );
            })}
          </div>

          {limitations.length > 0 && (
            <div className="mt-4 border-t border-gray-100 pt-3 space-y-1.5">
              {limitations.map((limitation) => (
                <p key={limitation} className="flex gap-2 text-[11px] leading-relaxed text-gray-500">
                  <TriangleAlert className="w-3.5 h-3.5 shrink-0 text-amber-500 mt-0.5" />
                  {limitation}
                </p>
              ))}
            </div>
          )}

          <button
            type="button"
            onClick={handleTrain}
            disabled={training || selected.length === 0}
            className="btn-primary w-full mt-5 disabled:opacity-50"
          >
            {training ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Training selected models...
              </>
            ) : (
              <>
                <BrainCircuit className="w-4 h-4" />
                Train {selected.length || ""} Selected Model{selected.length === 1 ? "" : "s"}
              </>
            )}
          </button>
          {trainEstimateSec != null && selected.length > 0 && !training && (
            <p className="text-xs text-gray-400 text-center mt-2">
              Expected training time: ~{formatDuration(trainEstimateSec)}
            </p>
          )}
        </div>

        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-4">
            <SlidersHorizontal className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-medium text-gray-800">Prediction Inputs</h3>
          </div>

          {!status ? (
            <div className="h-[310px] flex items-center justify-center text-center text-sm text-gray-400 px-8">
              Train your selected models to generate the input form.
            </div>
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-4">
                Target: <span className="text-emerald-600 font-medium">{status.target_column}</span>.
                Blank fields use typical training values.
              </p>
              {!modelsReady && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 mb-4">
                  Model selection changed. Train the selected models before predicting.
                </p>
              )}
              <div className="grid sm:grid-cols-2 gap-3 max-h-[290px] overflow-y-auto pr-1">
                {status.input_fields.map((field) => (
                  <InputField
                    key={field.name}
                    field={field}
                    value={values[field.name] ?? ""}
                    onChange={(value) => setValues((current) => ({ ...current, [field.name]: value }))}
                  />
                ))}
              </div>
              <button
                type="button"
                onClick={handlePredict}
                disabled={predicting || !modelsReady}
                className="btn-primary w-full mt-5 disabled:opacity-50"
              >
                {predicting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Prediction
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </section>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl border border-red-100 bg-red-50 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {receipt && (
        <PredictionResultView
          datasetId={datasetId}
          receipt={receipt}
          explanation={explanation}
          explaining={explaining}
          onExplain={handleExplainPrediction}
        />
      )}

      <ProductionOpsPanel datasetId={datasetId} status={status} selectedModelIds={selected} />
    </div>
  );
}

function InputField({
  field,
  value,
  onChange,
}: {
  field: PredictionInputField;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs text-gray-500">
      <span className="block mb-1.5 truncate" title={field.name}>{field.name}</span>
      {field.kind === "category" ? (
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full h-10 bg-white border border-gray-200 rounded-lg px-3 text-sm text-gray-700 focus:border-emerald-400 focus:outline-none"
        >
          <option value="">Typical: {String(field.default ?? "-")}</option>
          {field.options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      ) : (
        <input
          type={field.kind === "number" ? "number" : field.kind === "date" ? "date" : "text"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={field.default == null ? "Enter value" : `Typical: ${field.default}`}
          className="w-full h-10 bg-white border border-gray-200 rounded-lg px-3 text-sm text-gray-700 placeholder:text-gray-400 focus:border-emerald-400 focus:outline-none"
        />
      )}
    </label>
  );
}

function PredictionResultView({
  datasetId,
  receipt,
  explanation,
  explaining,
  onExplain,
}: {
  datasetId: string;
  receipt: PredictionReceipt;
  explanation: PredictionExplainResponse | null;
  explaining: boolean;
  onExplain: (modelId?: string) => void;
}) {
  const metric = receipt.problem_type === "classification" ? "accuracy" : "r2";
  const renderValue = (value: string | number) =>
    typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : value;

  return (
    <motion.section
      className="glass p-6"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-5 mb-5">
        <div>
          <p className="text-[11px] uppercase text-emerald-600 font-mono mb-1">Prediction Receipt</p>
          <h3 className="text-lg text-gray-900">
            {receipt.target_column}: <span className="font-semibold text-emerald-700">{renderValue(receipt.consensus)}</span>
          </h3>
          <p className="text-xs text-gray-400 mt-1">{receipt.consensus_label}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 px-3 py-2 rounded-lg border border-green-100">
          <CheckCircle2 className="w-4 h-4" />
          Calculated by trained backend models
        </div>
      </div>

      {receipt.warnings.length > 0 && (
        <div className="mb-5 space-y-2">
          {receipt.warnings.map((warning) => (
            <div key={warning} className="flex gap-2 text-xs text-amber-700">
              <TriangleAlert className="w-4 h-4 shrink-0" />
              {warning}
            </div>
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
        {receipt.predictions.map((output) => (
          <div key={output.model_id} className="border border-gray-100 rounded-xl p-4">
            <div className="flex justify-between items-start">
              <div className="min-w-0">
                <p className="text-sm text-gray-800 truncate pr-2">{output.model_name}</p>
                <p className="text-xs text-gray-400 mt-1">{output.family}</p>
              </div>
              <button
                type="button"
                onClick={() => downloadModel(datasetId, output.model_id)}
                className="text-gray-400 hover:text-emerald-600 transition-colors flex-shrink-0"
                title="Download Model (.joblib)"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
            <p className="text-2xl text-emerald-700 font-mono mt-3">{renderValue(output.prediction)}</p>
            <div className="flex gap-3 mt-3 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1">
                <Gauge className="w-3.5 h-3.5" />
                {metric}: {formatScore(output.metrics[metric], receipt.problem_type)}
              </span>
              {output.confidence != null && <span>{(output.confidence * 100).toFixed(1)}% confidence</span>}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 border-t border-gray-100 pt-5">
        <button
          type="button"
          onClick={() => onExplain(receipt.predictions[0]?.model_id)}
          disabled={explaining}
          className="btn-ghost border border-emerald-100 text-sm disabled:opacity-50 hover:bg-emerald-50/40"
        >
          {explaining ? <Loader2 className="w-4 h-4 animate-spin text-emerald-600" /> : <BrainCircuit className="w-4 h-4 text-emerald-600" />}
          Why this prediction?
        </button>

        {explanation && (
          <div className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4">
            <p className="text-xs text-emerald-600 uppercase tracking-wider mb-2">{explanation.method}</p>
            <p className="text-sm text-gray-700 mb-3">
              {explanation.model_name} moved from typical baseline{" "}
              <span className="font-mono">{renderValue(explanation.baseline_prediction)}</span> to{" "}
              <span className="font-mono text-emerald-700">{renderValue(explanation.prediction)}</span>.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {explanation.contributions.slice(0, 6).map((item) => (
                <div key={item.feature} className="rounded-lg bg-white border border-emerald-100 p-3">
                  <p className="text-xs text-gray-500 truncate" title={item.feature}>{item.feature}</p>
                  <p className={`font-mono text-sm mt-1 ${item.contribution >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                    {item.contribution >= 0 ? "+" : ""}{item.contribution.toFixed(4)}
                  </p>
                  <p className="text-[11px] text-gray-400 mt-1">
                    vs typical {String(item.baseline_value ?? "-")}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {Object.keys(receipt.assumed_inputs).length > 0 && (
        <p className="text-xs text-gray-400 mt-5">
          Typical values used for blank inputs:{" "}
          {Object.entries(receipt.assumed_inputs)
            .slice(0, 8)
            .map(([key, value]) => `${key}=${String(value)}`)
            .join(", ")}
        </p>
      )}
    </motion.section>
  );
}

function formatScore(score: number | undefined, type: string) {
  if (score == null) return "-";
  return type === "classification" ? `${(score * 100).toFixed(1)}%` : score.toFixed(3);
}

function apiError(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
