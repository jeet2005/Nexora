import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Boxes, CalendarClock, Clock, Loader2, Play } from "lucide-react";
import {
  getClustering,
  getTimeSeries,
  getTimingEstimates,
  runClustering,
  runTimeSeries,
  type ClusteringResult,
  type TimeSeriesResult,
} from "../api/client";
import type { DatasetAnalysis } from "../types/dataset";
import { formatDuration } from "../utils/formatDuration";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function pickDefaultDateColumn(analysis: DatasetAnalysis): string {
  const datetime = analysis.column_profiles.filter((p) => p.is_datetime).map((p) => p.name);
  if (datetime.length) return datetime[0];
  const fallback = analysis.column_profiles
    .filter((p) => p.name.toLowerCase().includes("date") || p.name.toLowerCase().includes("time"))
    .map((p) => p.name);
  return fallback[0] ?? "";
}

function pickDefaultTargetColumn(analysis: DatasetAnalysis, dateColumn: string): string {
  const numeric = analysis.column_profiles
    .filter((p) => p.is_numeric && p.name !== dateColumn)
    .map((p) => p.name);
  if (numeric.length) return numeric[0];
  const suggestion = analysis.prediction_suggestions.find((s) => s.problem_type === "regression");
  return suggestion?.target_column ?? numeric[0] ?? "";
}

export default function ExplorationModesPanel({
  datasetId,
  analysis,
}: {
  datasetId: string;
  analysis: DatasetAnalysis;
}) {
  const [clusters, setClusters] = useState<ClusteringResult | null>(null);
  const [forecast, setForecast] = useState<TimeSeriesResult | null>(null);
  const [clusterCount, setClusterCount] = useState(3);
  const [dateColumn, setDateColumn] = useState(() => pickDefaultDateColumn(analysis));
  const [targetColumn, setTargetColumn] = useState(() =>
    pickDefaultTargetColumn(analysis, pickDefaultDateColumn(analysis))
  );
  const [periods, setPeriods] = useState(12);
  const [frequency, setFrequency] = useState<"D" | "W" | "M">("M");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timing, setTiming] = useState<{ clustering_sec: number; time_series_sec: number } | null>(
    null
  );

  const numericColumns = analysis.column_profiles
    .filter((p) => p.is_numeric && p.name !== dateColumn)
    .map((p) => p.name);
  const dateColumns = analysis.column_profiles.filter((p) => p.is_datetime).map((p) => p.name);
  const fallbackDateOptions = analysis.column_profiles
    .filter((p) => p.name.toLowerCase().includes("date") || p.name.toLowerCase().includes("time"))
    .map((p) => p.name);
  const timeDateOptions = [...new Set([...dateColumns, ...fallbackDateOptions])];
  const tsReady = Boolean(dateColumn && targetColumn);

  useEffect(() => {
    Promise.all([getClustering(datasetId), getTimeSeries(datasetId), getTimingEstimates(datasetId)])
      .then(([clusterData, forecastData, timingData]) => {
        if (clusterData) setClusters(clusterData);
        if (forecastData) {
          setForecast(forecastData);
          setDateColumn(forecastData.date_column);
          setTargetColumn(forecastData.target_column);
          setPeriods(forecastData.periods);
          setFrequency(forecastData.frequency as "D" | "W" | "M");
        }
        setTiming({
          clustering_sec: timingData.clustering_sec,
          time_series_sec: timingData.time_series_sec,
        });
      })
      .catch(() => undefined);
  }, [datasetId]);

  const forecastChart = useMemo(() => {
    if (!forecast) return [];
    return [
      ...forecast.history.slice(-24).map((point) => ({ date: point.date, actual: point.value })),
      ...forecast.forecast.map((point) => ({ date: point.date, forecast: point.prediction })),
    ];
  }, [forecast]);

  const startClustering = async () => {
    setBusy("cluster");
    setError(null);
    try {
      setClusters(await runClustering(datasetId, { nClusters: clusterCount }));
    } catch (err: unknown) {
      setError(apiError(err, "Clustering failed."));
    } finally {
      setBusy(null);
    }
  };

  const startForecast = async () => {
    if (!dateColumn || !targetColumn) {
      setError("Choose date and numeric target columns for forecasting.");
      return;
    }
    setBusy("time");
    setError(null);
    try {
      setForecast(
        await runTimeSeries(datasetId, {
          dateColumn,
          targetColumn,
          periods,
          frequency,
        })
      );
    } catch (err: unknown) {
      setError(apiError(err, "Forecasting failed."));
    } finally {
      setBusy(null);
    }
  };

  return (
    <motion.section className="glass p-6 mb-6" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <div className="mb-5">
        <p className="text-[11px] uppercase tracking-widest text-emerald-600 font-mono mb-1">
          Additional Modeling Modes
        </p>
        <h3 className="font-display text-lg text-gray-900">Clustering & Time-Series Forecasting</h3>
        <p className="text-sm text-gray-500 mt-1">
          Run unsupervised segmentation or a dated numeric trend forecast directly from this dataset.
        </p>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <div className="grid xl:grid-cols-2 gap-5">
        <div className="rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-4">
            <Boxes className="w-4 h-4 text-emerald-600" />
            <h4 className="text-sm font-medium text-gray-800">Clustering</h4>
          </div>
          <div className="flex gap-3">
            <select
              value={clusterCount}
              onChange={(event) => setClusterCount(Number(event.target.value))}
              className="h-10 rounded-lg border border-gray-200 px-3 text-sm"
            >
              {[2, 3, 4, 5, 6, 8].map((count) => (
                <option key={count} value={count}>{count} clusters</option>
              ))}
            </select>
            <button type="button" onClick={startClustering} disabled={busy === "cluster"} className="btn-primary py-2">
              {busy === "cluster" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run
            </button>
          </div>
          {timing && (
            <p className="mt-2 text-xs text-gray-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Expected ~{formatDuration(timing.clustering_sec)}
            </p>
          )}

          {clusters && (
            <div className="mt-4">
              <p className="text-xs text-gray-400 mb-3">
                Silhouette {clusters.metrics.silhouette?.toFixed(3) ?? "-"} · inertia {clusters.metrics.inertia?.toLocaleString() ?? "-"}
              </p>
              <div className="grid sm:grid-cols-2 gap-2">
                {clusters.clusters.map((cluster) => (
                  <div key={String(cluster.cluster)} className="rounded-lg bg-gray-50 border border-gray-100 p-3">
                    <p className="text-sm text-gray-800">Cluster {String(cluster.cluster)}</p>
                    <p className="text-xs text-gray-400">
                      {String(cluster.size)} rows · {String(cluster.percentage)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-gray-100 p-4">
          <div className="flex items-center gap-2 mb-4">
            <CalendarClock className="w-4 h-4 text-emerald-600" />
            <h4 className="text-sm font-medium text-gray-800">Time-Series Forecast</h4>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 mb-3">
            <select
              value={dateColumn}
              onChange={(event) => setDateColumn(event.target.value)}
              className="h-10 rounded-lg border border-gray-200 px-3 text-sm"
            >
              <option value="">Date column</option>
              {timeDateOptions.map((column) => (
                <option key={column} value={column}>{column}</option>
              ))}
            </select>
            <select
              value={targetColumn}
              onChange={(event) => setTargetColumn(event.target.value)}
              className="h-10 rounded-lg border border-gray-200 px-3 text-sm"
            >
              <option value="">Numeric target</option>
              {numericColumns.map((column) => (
                <option key={column} value={column}>{column}</option>
              ))}
            </select>
            <select
              value={frequency}
              onChange={(event) => setFrequency(event.target.value as "D" | "W" | "M")}
              className="h-10 rounded-lg border border-gray-200 px-3 text-sm"
            >
              <option value="D">Daily</option>
              <option value="W">Weekly</option>
              <option value="M">Monthly</option>
            </select>
            <input
              type="number"
              min={1}
              max={365}
              value={periods}
              onChange={(event) => setPeriods(Number(event.target.value) || 12)}
              className="h-10 rounded-lg border border-gray-200 px-3 text-sm"
              placeholder="Forecast periods"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={startForecast}
              disabled={busy === "time" || !tsReady}
              className="btn-primary py-2 disabled:opacity-50"
            >
              {busy === "time" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Run Forecast
            </button>
            {timing && (
              <span className="text-xs text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Expected ~{formatDuration(timing.time_series_sec)}
              </span>
            )}
          </div>
          {!tsReady && (
            <p className="mt-2 text-xs text-amber-600">
              Select a date column and numeric metric to enable forecasting.
            </p>
          )}

          {forecast && (
            <div className="mt-4">
              <p className="text-xs text-gray-400 mb-3">
                {forecast.date_column} → {forecast.target_column} · {forecast.frequency} ·{" "}
                MAE {forecast.metrics.mae?.toLocaleString() ?? "-"} · R² {forecast.metrics.r2?.toFixed(3) ?? "-"}
              </p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={forecastChart} margin={{ top: 8, right: 12, left: 0, bottom: 20 }}>
                  <CartesianGrid stroke="#eef2f7" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6b7280" }} />
                  <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="actual" stroke="#4285f4" dot={false} strokeWidth={2} name="History" />
                  <Line type="monotone" dataKey="forecast" stroke="#34a853" dot={false} strokeWidth={2} name="Forecast" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </motion.section>
  );
}

function apiError(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
