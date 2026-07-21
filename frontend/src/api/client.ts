import axios from 'axios';
import type { DatasetAnalysis, UploadResponse } from '../types/dataset';
import type { ChatMessage, ChatResponse, OllamaStatus } from '../types/chat';
import type {
  ConfigureTargetResponse,
  DatasetSession,
  PreprocessOptions,
  PreprocessResponse,
} from '../types/pipeline';
import type { RegistryStats, TrainingJob, TrainingResult } from '../types/training';
import type {
  PredictionReceipt,
  ProductionModelsResponse,
  ProductionStatus,
} from '../types/production';

function sanitizeBaseUrl(raw: string | undefined): string {
  if (!raw) return '/api';
  let url = raw.trim();
  // Fix common protocol typos (e.g. "ttps://..." → "https://...")
  if (/^ttps:/i.test(url)) url = `h${url}`;
  if (/^ttp:/i.test(url)) url = `h${url}`;
  return url;
}

const api = axios.create({
  baseURL: sanitizeBaseUrl(import.meta.env.VITE_API_BASE_URL as string | undefined),
  timeout: 120_000,
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (
      config &&
      !config._retry &&
      error.response &&
      (error.response.status === 502 || error.response.status === 503)
    ) {
      config._retry = true;
      await new Promise((res) => setTimeout(res, 1200));
      return api(config);
    }
    return Promise.reject(error);
  },
);

export { api };

export async function uploadDataset(file: File, onProgress?: (pct: number) => void) {
  const form = new FormData();
  form.append('file', file);

  try {
    const { data } = await api.post<UploadResponse>('/datasets/upload', form, {
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
    return data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.status === 400) {
      throw error.response.data;
    }
    throw error;
  }
}

export async function getDataset(datasetId: string) {
  const { data } = await api.get<DatasetAnalysis>(`/datasets/${datasetId}`);
  return data;
}

export async function getSession(datasetId: string) {
  const { data } = await api.get<DatasetSession>(`/datasets/${datasetId}/session`);
  return data;
}

export async function configureTarget(
  datasetId: string,
  targetColumn: string,
  problemType?: string,
) {
  const { data } = await api.post<ConfigureTargetResponse>(`/datasets/${datasetId}/configure`, {
    target_column: targetColumn,
    problem_type: problemType ?? null,
  });
  return data;
}

export async function runPreprocess(datasetId: string, options?: PreprocessOptions) {
  const { data } = await api.post<PreprocessResponse>(
    `/datasets/${datasetId}/preprocess`,
    options ?? {},
  );
  return data;
}

export interface TimingEstimates {
  preprocess_sec: number;
  benchmark_sec: number;
  benchmark_model_count: number;
  benchmark_per_model_avg_sec: number;
  production_train_sec: number;
  time_series_sec: number;
  clustering_sec: number;
}

export async function getTimingEstimates(
  datasetId: string,
  options?: { maxModels?: number; productionModelCount?: number },
) {
  const { data } = await api.get<TimingEstimates>(`/datasets/${datasetId}/timing-estimates`, {
    params: {
      max_models: options?.maxModels ?? null,
      production_model_count: options?.productionModelCount ?? 2,
    },
  });
  return data;
}

export async function checkHealth() {
  const { data } = await api.get<{ status: string }>('/health');
  return data;
}

export async function getRegistryStats() {
  const { data } = await api.get<RegistryStats>('/models/registry');
  return data;
}

export async function getTraining(datasetId: string) {
  const { data } = await api.get<{ result: TrainingResult | null; job: TrainingJob | null }>(
    `/datasets/${datasetId}/training`,
  );
  return data;
}

export async function startTraining(datasetId: string, maxModels?: number) {
  const { data } = await api.post<{ status: string; dataset_id: string }>(
    `/datasets/${datasetId}/training/start`,
    { max_models: maxModels ?? null },
  );
  return data;
}

export async function startTrainingWithConfig(
  datasetId: string,
  config: {
    maxModels?: number;
    testSplit?: number;
    cvFolds?: number;
    timeout?: number;
    seed?: number;
  },
) {
  const { data } = await api.post<{ status: string; dataset_id: string }>(
    `/datasets/${datasetId}/training/start`,
    {
      max_models: config.maxModels ?? null,
      test_split: config.testSplit ?? null,
      cv_folds: config.cvFolds ?? null,
      timeout_sec: config.timeout ?? null,
      seed: config.seed ?? null,
    },
  );
  return data;
}

export async function getProductionModels(datasetId: string) {
  const { data } = await api.get<ProductionModelsResponse>(
    `/datasets/${datasetId}/production/models`,
  );
  return data;
}

export async function trainProductionModels(datasetId: string, modelIds: string[]) {
  const { data } = await api.post<ProductionStatus>(
    `/datasets/${datasetId}/production/train`,
    { model_ids: modelIds },
    { timeout: 300_000 },
  );
  return data;
}

export async function runProductionPrediction(
  datasetId: string,
  inputs: Record<string, unknown>,
  modelIds?: string[],
) {
  const { data } = await api.post<PredictionReceipt>(`/datasets/${datasetId}/production/predict`, {
    inputs,
    model_ids: modelIds ?? [],
  });
  return data;
}

export function trainingWebSocketUrl(datasetId: string) {
  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  let targetUrl: URL;

  if (configured && configured.trim() !== '' && configured !== '/api') {
    if (configured.startsWith('http')) {
      targetUrl = new URL(configured);
    } else {
      targetUrl = new URL(configured, window.location.href);
    }
  } else {
    targetUrl = new URL('/api', window.location.href);
  }

  const proto = targetUrl.protocol === 'https:' ? 'wss:' : 'ws:';
  const basePath = targetUrl.pathname.replace(/\/+$/, '');
  const apiPath = basePath.endsWith('/api') ? basePath : `${basePath}/api`;

  return `${proto}//${targetUrl.host}${apiPath}/ws/training/${datasetId}`;
}

export async function getChatStatus(datasetId: string) {
  const { data } = await api.get<OllamaStatus>(`/datasets/${datasetId}/chat/status`);
  return data;
}

export async function sendChatMessage(datasetId: string, message: string, history: ChatMessage[]) {
  const { data } = await api.post<ChatResponse>(
    `/datasets/${datasetId}/chat`,
    {
      message,
      history,
    },
    { timeout: 300_000 },
  );
  return data;
}

export async function explainError(
  errorMessage: string,
  datasetId?: string,
  contextInfo?: string,
) {
  const url = datasetId ? `/datasets/${datasetId}/explain-error` : '/explain-error';
  const { data } = await api.post<{ explanation: string; available: boolean }>(url, {
    error_message: errorMessage,
    dataset_id: datasetId,
    context_info: contextInfo,
  });
  return data;
}

// --- Phase 4: Explainability & Reports ---

export interface ExplainabilityResult {
  model_id: string;
  model_name: string;
  family: string;
  problem_type: string;
  feature_importance: { feature: string; importance: number; percentage: number }[];
  plots: Record<string, string>;
  metrics: Record<string, number>;
  sample_count: number;
  test_count: number;
  feature_count: number;
}

export interface ReportResponse {
  status: string;
  pdf_base64: string;
  filename: string;
}

export async function runExplainability(datasetId: string, modelId?: string) {
  const params = modelId ? `?model_id=${encodeURIComponent(modelId)}` : '';
  const { data } = await api.post<ExplainabilityResult>(`/datasets/${datasetId}/explain${params}`);
  return data;
}

export async function generateReport(datasetId: string, includeShap = true) {
  const { data } = await api.post<ReportResponse>(
    `/datasets/${datasetId}/report/generate?include_shap=${includeShap}`,
    {},
    { timeout: 300_000 },
  );
  return data;
}

export function getReportDownloadUrl(datasetId: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? '/api';
  return `${String(base).replace(/\/$/, '')}/datasets/${datasetId}/report/download`;
}

// --- Dataset history ---

export interface DatasetHistoryItem {
  dataset_id: string;
  filename: string;
  rows: number;
  columns: number;
  health_score: number;
  status: string;
  target_column: string | null;
  problem_type: string | null;
  last_trained_model: string | null;
  trained_model_count: number;
  report_available: boolean;
  archived: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export async function getDatasetHistory(includeArchived = false) {
  const { data } = await api.get<{ datasets: DatasetHistoryItem[] }>('/datasets', {
    params: { include_archived: includeArchived },
  });
  return data.datasets;
}

export async function archiveDataset(datasetId: string, archived: boolean) {
  const { data } = await api.post(`/datasets/${datasetId}/archive`, { archived });
  return data;
}

export async function deleteDataset(datasetId: string) {
  const { data } = await api.delete(`/datasets/${datasetId}`);
  return data;
}

// --- Experiments ---

export interface ExperimentRecord {
  run_id: string;
  dataset_id: string;
  kind: 'benchmark' | 'production' | 'clustering' | 'time_series';
  created_at: string;
  problem_type: string;
  target_column: string | null;
  config: Record<string, unknown>;
  metrics: Record<string, unknown>;
  models: Record<string, unknown>[];
  best_model: Record<string, unknown> | null;
  artifact_refs: Record<string, string>;
}

export async function getExperiments(datasetId: string) {
  const { data } = await api.get<{ experiments: ExperimentRecord[] }>(
    `/datasets/${datasetId}/experiments`,
  );
  return data.experiments;
}

export async function compareExperiments(datasetId: string) {
  const { data } = await api.get<{
    dataset_id: string;
    metric_names: string[];
    rows: Record<string, unknown>[];
  }>(`/datasets/${datasetId}/experiments/compare`);
  return data;
}

// --- Batch prediction, drift, deployments, row explanations ---

export interface BatchPredictionSummary {
  batch_id: string;
  dataset_id: string;
  filename: string;
  rows: number;
  model_ids: string[];
  created_at: string;
  download_url: string;
  drift: {
    overall_score?: number;
    severity?: string;
    summary?: string;
    features?: Record<string, unknown>[];
  };
  warnings: string[];
}

export async function runBatchPrediction(datasetId: string, file: File, modelIds?: string[]) {
  const form = new FormData();
  form.append('file', file);
  form.append('model_ids', (modelIds ?? []).join(','));
  const { data } = await api.post<BatchPredictionSummary>(
    `/datasets/${datasetId}/production/batch-predict`,
    form,
    { timeout: 300_000 },
  );
  return data;
}

export async function getBatchPredictions(datasetId: string) {
  const { data } = await api.get<{ batches: BatchPredictionSummary[] }>(
    `/datasets/${datasetId}/production/batches`,
  );
  return data.batches;
}

export interface PredictionContribution {
  feature: string;
  submitted_value: unknown;
  baseline_value: unknown;
  contribution: number;
  direction: 'increases' | 'decreases' | 'neutral';
}

export interface PredictionExplainResponse {
  dataset_id: string;
  model_id: string;
  model_name: string;
  prediction: string | number;
  baseline_prediction: string | number;
  score_delta: number;
  method: string;
  contributions: PredictionContribution[];
  warnings: string[];
}

export async function explainPrediction(
  datasetId: string,
  inputs: Record<string, unknown>,
  modelId?: string,
) {
  const { data } = await api.post<PredictionExplainResponse>(
    `/datasets/${datasetId}/production/explain-prediction`,
    { inputs, model_id: modelId ?? null },
    { timeout: 300_000 },
  );
  return data;
}

export async function downloadModel(datasetId: string, modelId: string) {
  const response = await api.get(`/datasets/${datasetId}/production/models/${modelId}/download`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${modelId}.joblib`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export interface ModelDeployment {
  deployment_id: string;
  dataset_id: string;
  name: string;
  model_ids: string[];
  active: boolean;
  created_at: string;
  last_used_at: string | null;
  predict_url: string;
  api_key_preview: string | null;
}

export async function getDeployments(datasetId: string) {
  const { data } = await api.get<{ deployments: ModelDeployment[] }>(
    `/datasets/${datasetId}/deployments`,
  );
  return data.deployments;
}

export async function createDeployment(datasetId: string, name: string, modelIds?: string[]) {
  const { data } = await api.post<{ deployment: ModelDeployment; api_key: string }>(
    `/datasets/${datasetId}/deployments`,
    { name, model_ids: modelIds ?? [] },
  );
  return data;
}

export async function deactivateDeployment(datasetId: string, deploymentId: string) {
  const { data } = await api.post<ModelDeployment>(
    `/datasets/${datasetId}/deployments/${deploymentId}/deactivate`,
  );
  return data;
}

// --- Clustering & time series ---

export interface ClusteringResult {
  dataset_id: string;
  run_id: string;
  n_clusters: number;
  feature_columns: string[];
  metrics: Record<string, number>;
  clusters: Record<string, unknown>[];
  preview: Record<string, unknown>[];
  created_at: string;
}

export async function runClustering(
  datasetId: string,
  options: { nClusters: number; featureColumns?: string[] },
) {
  const { data } = await api.post<ClusteringResult>(`/datasets/${datasetId}/clustering/run`, {
    n_clusters: options.nClusters,
    feature_columns: options.featureColumns ?? [],
  });
  return data;
}

export interface TimeSeriesResult {
  dataset_id: string;
  run_id: string;
  date_column: string;
  target_column: string;
  frequency: string;
  periods: number;
  metrics: Record<string, number>;
  history: { date: string; value: number }[];
  forecast: { date: string; prediction: number }[];
  created_at: string;
}

export async function runTimeSeries(
  datasetId: string,
  body: { dateColumn: string; targetColumn: string; periods: number; frequency: 'D' | 'W' | 'M' },
) {
  const { data } = await api.post<TimeSeriesResult>(`/datasets/${datasetId}/time-series/run`, {
    date_column: body.dateColumn,
    target_column: body.targetColumn,
    periods: body.periods,
    frequency: body.frequency,
  });
  return data;
}

export async function getTimeSeries(datasetId: string) {
  const { data } = await api.get<TimeSeriesResult | null>(`/datasets/${datasetId}/time-series`);
  return data;
}

export async function getClustering(datasetId: string) {
  const { data } = await api.get<ClusteringResult | null>(`/datasets/${datasetId}/clustering`);
  return data;
}
