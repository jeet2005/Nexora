export interface ModelResult {
  model_id: string;
  model_name: string;
  family: string;
  status: string;
  metrics: Record<string, number>;
  primary_score: number;
  train_time_sec: number;
  speed: string;
  error?: string | null;
}

export interface TrainingResult {
  dataset_id: string;
  problem_type: string;
  primary_metric: string;
  total_attempted: number;
  total_completed: number;
  total_failed: number;
  registry_available: number;
  best_model: ModelResult | null;
  leaderboard: ModelResult[];
}

export interface RegistryStats {
  total: number;
  classification: number;
  regression: number;
  families: string[];
  family_count: number;
}

export interface TrainingJob {
  dataset_id: string;
  status: string;
  completed?: number;
  total?: number;
  error?: string;
}

export interface WsTrainingEvent {
  event: string;
  index?: number;
  total?: number;
  model_id?: string;
  model_name?: string;
  family?: string;
  result?: ModelResult;
  leaderboard?: ModelResult[];
  completed_count?: number;
  failed_count?: number;
  total_models?: number;
  registry_total?: number;
  summary?: Record<string, unknown>;
  job?: TrainingJob;
  expected_total_sec?: number;
  expected_per_model_sec?: number;
  elapsed_sec?: number;
  estimated_remaining_sec?: number;
}
