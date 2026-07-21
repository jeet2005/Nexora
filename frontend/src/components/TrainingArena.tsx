import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Zap, Play, Loader2, Cpu, AlertCircle } from 'lucide-react';
import {
  getRegistryStats,
  getTimingEstimates,
  getTraining,
  startTraining,
  startTrainingWithConfig,
  trainingWebSocketUrl,
} from '../api/client';
import type { ModelResult, RegistryStats, TrainingResult } from '../types/training';
import type { WsTrainingEvent } from '../types/training';
import { formatDuration } from '../utils/formatDuration';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const LAB_COLORS = ['#93C998', '#7ab37f', '#d4a843', '#c97a5a', '#8bb896', '#a8d9a8'];

interface Props {
  datasetId: string;
  problemType: string;
  onComplete?: (result: TrainingResult) => void;
  trainingConfig?: {
    testSplit: number;
    cvFolds: number;
    maxModels: number;
    timeout: number;
    seed: number;
  };
}

export default function TrainingArena({
  datasetId,
  problemType,
  onComplete,
  trainingConfig,
}: Props) {
  const [registry, setRegistry] = useState<RegistryStats | null>(null);
  const [leaderboard, setLeaderboard] = useState<ModelResult[]>([]);
  const [current, setCurrent] = useState<{ name: string; index: number; total: number } | null>(
    null,
  );
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [completed, setCompleted] = useState(0);
  const [failed, setFailed] = useState(0);
  const [, setTotal] = useState(0);
  const [result, setResult] = useState<TrainingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expectedTotalSec, setExpectedTotalSec] = useState<number | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [remainingSec, setRemainingSec] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const metricLabel = problemType === 'regression' ? 'R²' : 'Accuracy';

  useEffect(() => {
    getRegistryStats().then(setRegistry);
    getTraining(datasetId).then((data) => {
      if (data.result) {
        setResult(data.result);
        setLeaderboard(data.result.leaderboard);
        onComplete?.(data.result);
      }
      if (data.job?.status === 'running') setRunning(true);
    });
    getTimingEstimates(datasetId, { maxModels: trainingConfig?.maxModels ?? 100 })
      .then((t) => setExpectedTotalSec(t.benchmark_sec))
      .catch(() => undefined);
  }, [datasetId, onComplete, trainingConfig?.maxModels]);

  const connectWs = useCallback(() => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(trainingWebSocketUrl(datasetId));
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data) as WsTrainingEvent;

      if (data.event === 'snapshot' && data.leaderboard) {
        setLeaderboard(data.leaderboard as ModelResult[]);
      }
      if (data.event === 'training_started') {
        setTotal(data.total_models ?? 0);
        setRunning(true);
        setProgress(0);
        setElapsedSec(0);
        setRemainingSec(data.expected_total_sec ?? expectedTotalSec);
        if (data.expected_total_sec) setExpectedTotalSec(data.expected_total_sec);
      }
      if (data.event === 'model_started') {
        setCurrent({
          name: data.model_name ?? '',
          index: data.index ?? 0,
          total: data.total ?? 0,
        });
      }
      if (data.event === 'model_completed') {
        setCompleted(data.completed_count ?? 0);
        setFailed(data.failed_count ?? 0);
        setProgress(((data.index ?? 0) / (data.total ?? 1)) * 100);
        if (data.elapsed_sec != null) setElapsedSec(data.elapsed_sec);
        if (data.estimated_remaining_sec != null) setRemainingSec(data.estimated_remaining_sec);
        if (data.leaderboard) setLeaderboard(data.leaderboard as ModelResult[]);
      }
      if (data.event === 'training_complete' && data.summary) {
        setRunning(false);
        setCurrent(null);
        getTraining(datasetId).then((d) => {
          if (d.result) {
            setResult(d.result);
            onComplete?.(d.result);
          }
        });
      }
      if (data.event === 'training_failed') {
        setRunning(false);
        setError((data as { error?: string }).error ?? 'Training failed');
      }
    };

    ws.onerror = () => setError('WebSocket connection failed');
    return ws;
  }, [datasetId, onComplete, expectedTotalSec]);

  const handleStart = async () => {
    setError(null);
    setLeaderboard([]);
    setResult(null);
    connectWs();
    try {
      if (trainingConfig) {
        await startTrainingWithConfig(datasetId, trainingConfig);
      } else {
        await startTraining(datasetId);
      }
      setRunning(true);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to start training';
      setError(typeof msg === 'string' ? msg : 'Failed to start training');
      setRunning(false);
    }
  };

  useEffect(() => {
    if (!running) return;

    const interval = setInterval(() => {
      getTraining(datasetId)
        .then((d) => {
          if (d.result) {
            setResult(d.result);
            if (d.result.leaderboard && d.result.leaderboard.length > 0) {
              setLeaderboard(d.result.leaderboard);
              setCompleted(d.result.total_completed ?? d.result.leaderboard.length);
              setProgress(
                d.result.total_attempted > 0
                  ? (d.result.total_completed / d.result.total_attempted) * 100
                  : 100,
              );
            }
            if (d.result.best_model && d.result.total_completed >= (d.result.total_attempted || 1)) {
              setRunning(false);
              onComplete?.(d.result);
            }
          }
        })
        .catch(() => {});
    }, 1500);

    return () => clearInterval(interval);
  }, [running, datasetId, onComplete]);

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  const primaryMetric = (m: ModelResult) =>
    problemType === 'regression'
      ? (m.metrics.r2 ?? m.primary_score)
      : (m.metrics.accuracy ?? m.primary_score);

  const formatMetric = (value: number) =>
    metricLabel === 'Accuracy' ? `${(value * 100).toFixed(1)}%` : value.toFixed(4);

  const topModelChartData = leaderboard.slice(0, 10).map((model, index) => ({
    name: model.model_name.length > 18 ? `${model.model_name.slice(0, 18)}...` : model.model_name,
    fullName: model.model_name,
    score: primaryMetric(model),
    time: model.train_time_sec,
    family: model.family,
    rank: index + 1,
  }));

  const familyChartData = Object.values(
    leaderboard.reduce<
      Record<string, { family: string; scoreSum: number; count: number; best: number }>
    >((acc, model) => {
      const score = primaryMetric(model);
      acc[model.family] ??= { family: model.family, scoreSum: 0, count: 0, best: score };
      acc[model.family].scoreSum += score;
      acc[model.family].count += 1;
      acc[model.family].best = Math.max(acc[model.family].best, score);
      return acc;
    }, {}),
  )
    .map((item) => ({
      family: item.family,
      average: item.scoreSum / item.count,
      best: item.best,
      count: item.count,
    }))
    .sort((a, b) => b.average - a.average)
    .slice(0, 8);

  const speedScoreData = leaderboard.slice(0, 24).map((model, index) => ({
    name: model.model_name,
    time: model.train_time_sec,
    score: primaryMetric(model),
    family: model.family,
    rank: index + 1,
  }));

  return (
    <div className="space-y-6">
      <motion.div
        className="glass p-6"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center">
              <Trophy className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-display text-lg text-gray-800 tracking-wide">
                Model Battle Arena
              </h3>
              <p className="text-sm text-gray-500">
                {registry
                  ? `${registry.total}+ models in registry · ${problemType === 'classification' ? registry.classification : registry.regression} for this task`
                  : 'Loading model registry…'}
                {expectedTotalSec != null && !running && (
                  <span className="block text-xs text-emerald-600 mt-1">
                    Expected benchmark time: ~{formatDuration(expectedTotalSec)}
                  </span>
                )}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleStart}
            disabled={running}
            className="btn-primary disabled:opacity-50 shrink-0"
          >
            {running ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Training…
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Launch Full Benchmark
              </>
            )}
          </button>
        </div>

        {running && (
          <motion.div className="mt-6 space-y-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex justify-between text-sm">
              <span className="text-emerald-600 font-mono">
                {current
                  ? `Training: ${current.name} (${current.index}/${current.total})`
                  : 'Initializing arena…'}
              </span>
              <span className="text-gray-400">
                {completed} ok · {failed} failed
                {running && remainingSec != null && <> · ~{formatDuration(remainingSec)} left</>}
                {running && elapsedSec > 0 && <> · {formatDuration(elapsedSec)} elapsed</>}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-amber-400"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </motion.div>
        )}

        {error && (
          <div className="mt-4 flex items-center gap-2 text-red-500 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </motion.div>

      {result?.best_model && (
        <motion.div
          className="glass p-6 border-amber-200 shadow-glow-green"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <p className="text-xs uppercase tracking-widest text-amber-600 mb-2">Champion Model</p>
          <div className="flex flex-wrap items-center gap-4">
            <Trophy className="w-8 h-8 text-amber-500" />
            <div>
              <p className="text-xl font-display text-gray-800">{result.best_model.model_name}</p>
              <p className="text-sm text-gray-500">
                {metricLabel}:{' '}
                {(
                  primaryMetric(result.best_model) * (metricLabel === 'Accuracy' ? 100 : 1)
                ).toFixed(metricLabel === 'Accuracy' ? 1 : 3)}
                {metricLabel === 'Accuracy' ? '%' : ''}
                {' · '}
                {result.best_model.train_time_sec}s{' · '}
                {result.best_model.family}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            {result.total_completed}/{result.total_attempted} models completed ·{' '}
            {result.registry_available} available in registry
          </p>
        </motion.div>
      )}

      {leaderboard.length > 0 && (
        <motion.div
          className="grid xl:grid-cols-3 gap-6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="glass p-5 xl:col-span-2">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase">
                  Top Model Scores
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Compares the strongest models by {metricLabel}.
                </p>
              </div>
              <span className="text-xs font-mono text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                top {topModelChartData.length}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={topModelChartData}
                margin={{ top: 8, right: 12, left: 0, bottom: 46 }}
              >
                <CartesianGrid stroke="#eef2f7" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#5f6368', fontSize: 10 }}
                  angle={-24}
                  textAnchor="end"
                  height={58}
                  interval={0}
                />
                <YAxis tick={{ fill: '#5f6368', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: '#ffffff',
                    border: '1px solid #dbeafe',
                    borderRadius: 12,
                    boxShadow: '0 12px 28px rgba(66,133,244,0.12)',
                  }}
                  formatter={(value: number, name: string) =>
                    name === 'score' ? [formatMetric(value), metricLabel] : [value, name]
                  }
                />
                <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                  {topModelChartData.map((_, i) => (
                    <Cell key={i} fill={LAB_COLORS[i % LAB_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="glass p-5">
            <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase mb-1">
              Speed vs Score
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Models near the top-left are fast and strong.
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <ScatterChart margin={{ top: 8, right: 12, left: -12, bottom: 8 }}>
                <CartesianGrid stroke="#eef2f7" />
                <XAxis
                  dataKey="time"
                  name="Time"
                  unit="s"
                  tick={{ fill: '#5f6368', fontSize: 10 }}
                  type="number"
                />
                <YAxis
                  dataKey="score"
                  name={metricLabel}
                  tick={{ fill: '#5f6368', fontSize: 10 }}
                  type="number"
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    background: '#ffffff',
                    border: '1px solid #dbeafe',
                    borderRadius: 12,
                    boxShadow: '0 12px 28px rgba(66,133,244,0.12)',
                  }}
                  formatter={(value: number, name: string) =>
                    name === 'score' ? [formatMetric(value), metricLabel] : [value, name]
                  }
                />
                <Scatter data={speedScoreData} fill="#93C998">
                  {speedScoreData.map((_, i) => (
                    <Cell key={i} fill={LAB_COLORS[i % LAB_COLORS.length]} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="glass p-5 xl:col-span-3">
            <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase mb-1">
              Model Family Comparison
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Average score by algorithm family, so people can see which approach works best.
            </p>
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={familyChartData} margin={{ top: 8, right: 12, left: 0, bottom: 20 }}>
                <CartesianGrid stroke="#eef2f7" vertical={false} />
                <XAxis dataKey="family" tick={{ fill: '#5f6368', fontSize: 11 }} />
                <YAxis tick={{ fill: '#5f6368', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: '#ffffff',
                    border: '1px solid #dbeafe',
                    borderRadius: 12,
                    boxShadow: '0 12px 28px rgba(66,133,244,0.12)',
                  }}
                  formatter={(value: number, name: string) => [
                    typeof value === 'number' ? formatMetric(value) : value,
                    name === 'average' ? `Avg ${metricLabel}` : name,
                  ]}
                />
                <Bar dataKey="average" name={`Avg ${metricLabel}`} radius={[8, 8, 0, 0]}>
                  {familyChartData.map((_, i) => (
                    <Cell key={i} fill={LAB_COLORS[i % LAB_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}

      <motion.div
        className="glass overflow-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <motion.div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-display text-sm tracking-widest text-gray-400 uppercase">
            Live Leaderboard
          </h3>
          <span className="text-xs font-mono text-gray-400">{leaderboard.length} ranked</span>
        </motion.div>

        <div className="overflow-x-auto max-h-[480px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white/95 backdrop-blur z-10">
              <tr className="text-left text-gray-400 border-b border-gray-100">
                <th className="px-6 py-3 w-12">#</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Family</th>
                <th className="px-4 py-3">{metricLabel}</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Speed</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence mode="popLayout">
                {leaderboard.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                      {running
                        ? 'Waiting for first results…'
                        : 'Start benchmark to populate leaderboard'}
                    </td>
                  </tr>
                ) : (
                  leaderboard.map((m, i) => (
                    <motion.tr
                      key={m.model_id}
                      layout
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`border-b border-gray-50 ${
                        i === 0 ? 'bg-emerald-50/70' : 'hover:bg-gray-50/50'
                      }`}
                    >
                      <td className="px-6 py-3 font-mono text-gray-400">{i + 1}</td>
                      <td className="px-4 py-3 text-gray-800 font-medium max-w-[240px] truncate">
                        {m.model_name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs px-2 py-0.5 rounded border border-gray-200 text-gray-500">
                          {m.family}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-emerald-600">
                        {metricLabel === 'Accuracy'
                          ? `${(primaryMetric(m) * 100).toFixed(1)}%`
                          : primaryMetric(m).toFixed(4)}
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-400">{m.train_time_sec}s</td>
                      <td className="px-4 py-3">
                        <SpeedBadge speed={m.speed} />
                      </td>
                    </motion.tr>
                  ))
                )}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

function SpeedBadge({ speed }: { speed: string }) {
  const colors: Record<string, string> = {
    fast: 'text-green-700 border-green-200 bg-green-50',
    medium: 'text-amber-700 border-amber-200 bg-amber-50',
    slow: 'text-red-700 border-red-200 bg-red-50',
  };
  const Icon = speed === 'fast' ? Zap : Cpu;
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border capitalize ${colors[speed] ?? colors.medium}`}
    >
      <Icon className="w-3 h-3" />
      {speed}
    </span>
  );
}
