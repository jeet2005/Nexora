from typing import Any, Literal

from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    missing_count: int
    missing_pct: float
    unique_count: int
    is_numeric: bool
    is_categorical: bool
    is_datetime: bool
    is_id_like: bool
    sample_values: list[Any] = Field(default_factory=list)


class DatasetStats(BaseModel):
    mean: dict[str, float | None] = Field(default_factory=dict)
    median: dict[str, float | None] = Field(default_factory=dict)
    std: dict[str, float | None] = Field(default_factory=dict)
    skewness: dict[str, float | None] = Field(default_factory=dict)
    correlation: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    outlier_counts: dict[str, int] = Field(default_factory=dict)


class HealthScore(BaseModel):
    missing_values: int
    data_quality: int
    prediction_readiness: int
    feature_quality: int
    overall: int


class PredictionSuggestion(BaseModel):
    target_column: str
    problem_type: str
    confidence: float
    description: str


class ModelEligibilityFinding(BaseModel):
    task: str
    eligible: bool
    reason: str
    target_candidates: list[str] = Field(default_factory=list)
    model_examples: list[str] = Field(default_factory=list)


class DatasetAnalysis(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    duplicate_rows: int
    memory_mb: float
    column_profiles: list[ColumnProfile]
    stats: DatasetStats
    health: HealthScore
    prediction_suggestions: list[PredictionSuggestion]
    model_eligibility: list[ModelEligibilityFinding] = Field(default_factory=list)
    semantic_summary: str
    preview: list[dict[str, Any]]


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    message: str
    analysis: DatasetAnalysis


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


# --- Phase 2: Session & Preprocessing ---

ProblemType = Literal["classification", "regression", "time_series", "clustering"]


class ConfigureTargetRequest(BaseModel):
    target_column: str
    problem_type: ProblemType | None = None
    exclude_columns: list[str] = Field(default_factory=list)


class ProblemDetection(BaseModel):
    problem_type: str
    confidence: float
    target_column: str
    unique_values: int
    hints: list[str] = Field(default_factory=list)


class FeatureSelection(BaseModel):
    feature_columns: list[str]
    excluded_id_columns: list[str]
    excluded_datetime_columns: list[str]


class PreprocessStep(BaseModel):
    step: str
    detail: str
    affected_rows_or_cols: int = 0


class PreprocessMeta(BaseModel):
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    feature_count: int
    encoders: dict[str, str] = Field(default_factory=dict)
    scalers: dict[str, str] = Field(default_factory=dict)


class CorrelationInsight(BaseModel):
    feature: str
    correlation: float


class DatasetInsights(BaseModel):
    top_correlations: list[CorrelationInsight]
    class_balance: list[dict[str, Any]]
    target_stats: dict[str, Any]
    quality_warnings: list[str]
    estimated_difficulty: int
    narrative: str
    preprocessing_summary: str


class PreprocessResult(BaseModel):
    steps: list[PreprocessStep]
    meta: PreprocessMeta
    insights: DatasetInsights
    preview: list[dict[str, Any]]
    feature_columns: list[str]


class ModelResult(BaseModel):
    model_id: str
    model_name: str
    family: str
    status: str = "completed"
    metrics: dict[str, float] = Field(default_factory=dict)
    primary_score: float = 0.0
    train_time_sec: float = 0.0
    speed: str = "medium"
    error: str | None = None


class TrainingResult(BaseModel):
    dataset_id: str
    problem_type: str
    primary_metric: str
    total_attempted: int
    total_completed: int
    total_failed: int
    registry_available: int
    best_model: ModelResult | None = None
    leaderboard: list[ModelResult] = Field(default_factory=list)


class DatasetSession(BaseModel):
    dataset_id: str
    target_column: str | None = None
    problem_type: str | None = None
    problem_detection: ProblemDetection | None = None
    feature_selection: FeatureSelection | None = None
    status: Literal["analyzed", "configured", "preprocessed", "trained"] = "analyzed"
    preprocess_result: PreprocessResult | None = None
    training_result: TrainingResult | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    model: str
    ok: bool


class TrainingStartRequest(BaseModel):
    max_models: int | None = None
    test_split: float | None = Field(default=None, ge=0.05, le=0.5)
    cv_folds: int | None = Field(default=None, ge=2, le=10)
    timeout_sec: int | None = Field(default=None, ge=10, le=3600)
    seed: int | None = Field(default=None, ge=0)


class RegistryStatsResponse(BaseModel):
    total: int
    classification: int
    regression: int
    families: list[str]
    family_count: int


class TimingEstimatesResponse(BaseModel):
    preprocess_sec: int
    benchmark_sec: int
    benchmark_model_count: int
    benchmark_per_model_avg_sec: float
    production_train_sec: int
    time_series_sec: int
    clustering_sec: int


class DeployableModelOption(BaseModel):
    model_id: str
    model_name: str
    family: str
    speed: str
    recommended: bool = False


class PredictionInputField(BaseModel):
    name: str
    kind: Literal["number", "category", "date", "text"]
    required: bool = False
    default: Any = None
    min_value: float | None = None
    max_value: float | None = None
    options: list[str] = Field(default_factory=list)


class DeployedModel(BaseModel):
    model_id: str
    model_name: str
    family: str
    problem_type: str
    metrics: dict[str, float] = Field(default_factory=dict)
    primary_score: float = 0.0
    train_time_sec: float = 0.0


class ProductionStatus(BaseModel):
    dataset_id: str
    target_column: str
    problem_type: str
    input_fields: list[PredictionInputField] = Field(default_factory=list)
    models: list[DeployedModel] = Field(default_factory=list)
    trained_at: str | None = None


class ProductionModelsResponse(BaseModel):
    dataset_id: str
    target_column: str
    problem_type: str
    available_models: list[DeployableModelOption]
    eligibility_reason: str = ""
    limitations: list[str] = Field(default_factory=list)
    deployed: ProductionStatus | None = None


class ProductionTrainRequest(BaseModel):
    model_ids: list[str] = Field(default_factory=list, min_length=1, max_length=5)


class PredictionRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    model_ids: list[str] = Field(default_factory=list)


class PredictionOutput(BaseModel):
    model_id: str
    model_name: str
    family: str
    prediction: Any
    metrics: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    probabilities: dict[str, float] = Field(default_factory=dict)


class PredictionReceipt(BaseModel):
    dataset_id: str
    target_column: str
    problem_type: str
    submitted_inputs: dict[str, Any] = Field(default_factory=dict)
    assumed_inputs: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    predictions: list[PredictionOutput]
    consensus: Any = None
    consensus_label: str = ""
    created_at: str


class DatasetHistoryItem(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    health_score: int
    status: str = "analyzed"
    target_column: str | None = None
    problem_type: str | None = None
    last_trained_model: str | None = None
    trained_model_count: int = 0
    report_available: bool = False
    archived: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class DatasetHistoryResponse(BaseModel):
    datasets: list[DatasetHistoryItem]


class ArchiveDatasetRequest(BaseModel):
    archived: bool = True


class ArchiveDatasetResponse(BaseModel):
    dataset_id: str
    archived: bool


class ExperimentRecord(BaseModel):
    run_id: str
    dataset_id: str
    kind: Literal["benchmark", "production", "clustering", "time_series"]
    created_at: str
    problem_type: str
    target_column: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    models: list[dict[str, Any]] = Field(default_factory=list)
    best_model: dict[str, Any] | None = None
    artifact_refs: dict[str, str] = Field(default_factory=dict)


class ExperimentsResponse(BaseModel):
    experiments: list[ExperimentRecord]


class ExperimentCompareResponse(BaseModel):
    dataset_id: str
    metric_names: list[str]
    rows: list[dict[str, Any]]


class BatchPredictionSummary(BaseModel):
    batch_id: str
    dataset_id: str
    filename: str
    rows: int
    model_ids: list[str]
    created_at: str
    download_url: str
    drift: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class BatchPredictionListResponse(BaseModel):
    batches: list[BatchPredictionSummary]


class PredictionContribution(BaseModel):
    feature: str
    submitted_value: Any = None
    baseline_value: Any = None
    contribution: float
    direction: Literal["increases", "decreases", "neutral"]


class PredictionExplainRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    model_id: str | None = None


class PredictionExplainResponse(BaseModel):
    dataset_id: str
    model_id: str
    model_name: str
    prediction: Any
    baseline_prediction: Any
    score_delta: float
    method: str
    contributions: list[PredictionContribution]
    warnings: list[str] = Field(default_factory=list)


class ModelDeployment(BaseModel):
    deployment_id: str
    dataset_id: str
    name: str
    model_ids: list[str]
    active: bool = True
    created_at: str
    last_used_at: str | None = None
    predict_url: str
    api_key_preview: str | None = None


class CreateDeploymentRequest(BaseModel):
    name: str = "Production endpoint"
    model_ids: list[str] = Field(default_factory=list)


class CreateDeploymentResponse(BaseModel):
    deployment: ModelDeployment
    api_key: str


class DeploymentListResponse(BaseModel):
    deployments: list[ModelDeployment]


class PublicPredictionRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    model_ids: list[str] = Field(default_factory=list)


class ClusteringRequest(BaseModel):
    n_clusters: int = Field(default=3, ge=2, le=12)
    feature_columns: list[str] = Field(default_factory=list)


class ClusteringResult(BaseModel):
    dataset_id: str
    run_id: str
    n_clusters: int
    feature_columns: list[str]
    metrics: dict[str, float] = Field(default_factory=dict)
    clusters: list[dict[str, Any]]
    preview: list[dict[str, Any]]
    created_at: str


class TimeSeriesRequest(BaseModel):
    date_column: str
    target_column: str
    periods: int = Field(default=12, ge=1, le=365)
    frequency: Literal["D", "W", "M"] = "M"


class TimeSeriesResult(BaseModel):
    dataset_id: str
    run_id: str
    date_column: str
    target_column: str
    frequency: str
    periods: int
    metrics: dict[str, float] = Field(default_factory=dict)
    history: list[dict[str, Any]]
    forecast: list[dict[str, Any]]
    created_at: str


class ConfigureTargetResponse(BaseModel):
    session: DatasetSession
    problem_detection: ProblemDetection
    feature_selection: FeatureSelection


class PreprocessRequest(BaseModel):
    missing_strategy: str = "auto"
    outlier_method: str = "iqr_cap"
    scaling: Literal["standard", "minmax", "none"] = "standard"
    encode_categorical: bool = True
    remove_duplicates: bool = True
    remove_constant: bool = True
    drop_id_columns: bool = True


class PreprocessResponse(BaseModel):
    session: DatasetSession
    result: PreprocessResult
