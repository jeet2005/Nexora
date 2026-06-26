import { lazy, Suspense, useEffect, useState } from "react";
import { useLocation, useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Database, Rows3, Columns3, Copy } from "lucide-react";
import { getDataset, getSession } from "../api/client";
import type { DatasetAnalysis } from "../types/dataset";
import type { ConfigureTargetResponse, DatasetSession, PreprocessResponse } from "../types/pipeline";
import HealthScoreCard from "../components/HealthScoreCard";
import PredictionSuggestions from "../components/PredictionSuggestions";
import ColumnProfiles from "../components/ColumnProfiles";
import DataPreviewTable from "../components/DataPreviewTable";
import MissingValuesChart from "../components/MissingValuesChart";
import ModelReadinessPanel from "../components/ModelReadinessPanel";
import WorkflowTabs, { type WorkflowTab } from "../components/WorkflowTabs";
import TargetSelector from "../components/TargetSelector";
import ProblemTypeCard from "../components/ProblemTypeCard";
import DatasetChat from "../components/DatasetChat";
import AdvancedSettings, { DEFAULT_CONFIG, type AdvancedConfig } from "../components/AdvancedSettings";
import TabLoader from "../components/TabLoader";

const DatasetCharts = lazy(() => import("../components/DatasetCharts"));
const NumericTrendsChart = lazy(() => import("../components/NumericTrendsChart"));
const CategoricalDistributionChart = lazy(() => import("../components/CategoricalDistributionChart"));
const DataQualityChart = lazy(() => import("../components/DataQualityChart"));
const ExplorationModesPanel = lazy(() => import("../components/ExplorationModesPanel"));
const PredictionStudio = lazy(() => import("../components/PredictionStudio"));
const PreprocessPanel = lazy(() => import("../components/PreprocessPanel"));
const InsightsPanel = lazy(() => import("../components/InsightsPanel"));
const TrainingArena = lazy(() => import("../components/TrainingArena"));
const ExperimentPanel = lazy(() => import("../components/ExperimentPanel"));
const ExplainabilityPanel = lazy(() => import("../components/ExplainabilityPanel"));

export default function DatasetDashboard() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const location = useLocation();
  const [analysis, setAnalysis] = useState<DatasetAnalysis | null>(
    (location.state as { analysis?: DatasetAnalysis })?.analysis ?? null
  );
  const [session, setSession] = useState<DatasetSession | null>(null);
  const [tab, setTab] = useState<WorkflowTab>("overview");
  const [loading, setLoading] = useState(!analysis);
  const [error, setError] = useState<string | null>(null);
  const [advancedConfig, setAdvancedConfig] = useState<AdvancedConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    if (!datasetId) return;

    const load = async () => {
      try {
        const [sess] = await Promise.all([
          getSession(datasetId),
          analysis ? Promise.resolve(null) : getDataset(datasetId).then(setAnalysis),
        ]);
        setSession(sess);
        if (sess.target_column) setTab("studio");
      } catch {
        if (!analysis) setError("Could not load dataset.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [datasetId, analysis]);

  const maxUnlocked: WorkflowTab =
    session?.status === "trained"
      ? "insights"
      : session?.status === "preprocessed"
        ? "arena"
        : session?.status === "configured"
          ? "preprocess"
          : "overview";

  const handleConfigured = (res: ConfigureTargetResponse) => {
    setSession(res.session);
    setTab("studio");
  };

  const handlePreprocessed = (res: PreprocessResponse) => {
    setSession(res.session);
    setTab("arena");
  };

  const handleTrainingComplete = () => {
    getSession(datasetId!).then(setSession);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <motion.div
          className="w-10 h-10 border-2 border-emerald-200 border-t-emerald-500 rounded-full"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        />
      </div>
    );
  }

  if (error || !analysis || !datasetId) {
    return (
      <motion.div className="max-w-lg mx-auto mt-24 text-center px-6">
        <p className="text-red-500 mb-4">{error ?? "Dataset not found."}</p>
        <Link to="/" className="btn-primary">
          Back to upload
        </Link>
      </motion.div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <Link to="/" className="btn-ghost text-sm mb-6 inline-flex">
          <ArrowLeft className="w-4 h-4" />
          Upload another dataset
        </Link>

        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div>
            <p className="text-emerald-600 font-mono text-xs tracking-widest uppercase mb-2">
              Dataset Intelligence Report
            </p>
            <h1 className="font-display text-3xl text-gray-900 mb-3">{analysis.filename}</h1>
            <p className="text-gray-500 max-w-2xl leading-relaxed">{analysis.semantic_summary}</p>
          </div>

          <div className="flex flex-wrap gap-4">
            <Stat icon={Rows3} label="Rows" value={analysis.rows.toLocaleString()} />
            <Stat icon={Columns3} label="Columns" value={String(analysis.columns)} />
            <Stat icon={Copy} label="Duplicates" value={String(analysis.duplicate_rows)} />
            <Stat icon={Database} label="Memory" value={`${analysis.memory_mb} MB`} />
          </div>
        </div>
      </motion.div>

      <WorkflowTabs active={tab} onChange={setTab} maxUnlocked={maxUnlocked} />

      {tab === "overview" && (
        <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <motion.div className="grid lg:grid-cols-2 gap-6 mb-6">
            <HealthScoreCard health={analysis.health} />
            <MissingValuesChart profiles={analysis.column_profiles} />
          </motion.div>

          <Suspense fallback={<TabLoader label="Loading charts…" />}>
            <DatasetCharts analysis={analysis} />
          </Suspense>

          <motion.div className="grid lg:grid-cols-2 gap-6 mb-6">
            <Suspense fallback={<TabLoader label="Loading trends…" />}>
              <NumericTrendsChart analysis={analysis} />
              <CategoricalDistributionChart analysis={analysis} />
            </Suspense>
          </motion.div>

          <motion.div className="mb-6">
            <Suspense fallback={<TabLoader label="Loading quality chart…" />}>
              <DataQualityChart analysis={analysis} />
            </Suspense>
          </motion.div>

          <Suspense fallback={<TabLoader label="Loading exploration modes…" />}>
            <ExplorationModesPanel datasetId={datasetId} analysis={analysis} />
          </Suspense>

          <motion.div className="grid lg:grid-cols-[0.9fr_1.1fr] gap-6 mb-6">
            <ModelReadinessPanel findings={analysis.model_eligibility ?? []} />
            <PredictionSuggestions suggestions={analysis.prediction_suggestions} />
          </motion.div>

          <motion.div className="mb-6">
            <ColumnProfiles profiles={analysis.column_profiles} />
          </motion.div>

          <DataPreviewTable preview={analysis.preview} totalRows={analysis.rows} />

          <motion.div className="mt-6">
            <AdvancedSettings
              config={advancedConfig}
              onChange={setAdvancedConfig}
              datasetId={datasetId}
            />
          </motion.div>

          <motion.div className="mt-8 flex justify-center">
            <button type="button" onClick={() => setTab("configure")} className="btn-primary">
              Configure Prediction Target →
            </button>
          </motion.div>
        </motion.div>
      )}

      {tab === "configure" && (
        <motion.div key="configure" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {!session?.problem_detection ? (
            <TargetSelector
              datasetId={datasetId}
              analysis={analysis}
              onConfigured={handleConfigured}
            />
          ) : (
            <>
              <ProblemTypeCard
                detection={session.problem_detection}
                featureCount={session.feature_selection?.feature_columns.length ?? 0}
              />
              <motion.div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setSession({ ...session, status: "analyzed", problem_detection: null, target_column: null });
                  }}
                  className="btn-ghost"
                >
                  Change target
                </button>
                <button type="button" onClick={() => setTab("studio")} className="btn-primary">
                  Open Prediction Studio
                </button>
                <button
                  type="button"
                  onClick={() => setTab("preprocess")}
                  className="btn-ghost border border-gray-200"
                >
                  Compare Many Models
                </button>
              </motion.div>
            </>
          )}
        </motion.div>
      )}

      {tab === "studio" && (
        <motion.div key="studio" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {session?.target_column ? (
            <Suspense fallback={<TabLoader label="Loading Prediction Studio…" />}>
              <PredictionStudio datasetId={datasetId} />
            </Suspense>
          ) : (
            <motion.div className="glass p-6 text-center text-gray-400">
              <p className="mb-4">Select a prediction target first.</p>
              <button type="button" onClick={() => setTab("configure")} className="btn-primary">
                Go to Target Selection
              </button>
            </motion.div>
          )}
        </motion.div>
      )}

      {tab === "preprocess" && (
        <motion.div key="preprocess" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {session?.status !== "preprocessed" ? (
            <>
              {session?.problem_detection && (
                <ProblemTypeCard
                  detection={session.problem_detection}
                  featureCount={session.feature_selection?.feature_columns.length ?? 0}
                />
              )}
              {session?.target_column ? (
                <Suspense fallback={<TabLoader label="Loading pipeline…" />}>
                  <PreprocessPanel datasetId={datasetId} onComplete={handlePreprocessed} />
                </Suspense>
              ) : (
                <motion.div className="glass p-6 text-center text-gray-400">
                  <p className="mb-4">Configure a prediction target first.</p>
                  <button type="button" onClick={() => setTab("configure")} className="btn-primary">
                    Go to Target Selection
                  </button>
                </motion.div>
              )}
            </>
          ) : (
            <>
              {session.preprocess_result && (
                <Suspense fallback={<TabLoader label="Loading insights…" />}>
                  <InsightsPanel result={session.preprocess_result} />
                </Suspense>
              )}
              <motion.div className="mt-8 flex justify-center">
                <button type="button" onClick={() => setTab("arena")} className="btn-primary">
                  Open Optional Comparison Arena
                </button>
              </motion.div>
            </>
          )}
        </motion.div>
      )}

      {tab === "arena" && (
        <motion.div key="arena" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {session?.status === "preprocessed" || session?.status === "trained" ? (
            <Suspense fallback={<TabLoader label="Loading training arena…" />}>
              <TrainingArena
                datasetId={datasetId}
                problemType={session.problem_type ?? "classification"}
                onComplete={handleTrainingComplete}
                trainingConfig={advancedConfig}
              />
              <motion.div className="mt-6">
                <ExperimentPanel datasetId={datasetId} />
              </motion.div>
            </Suspense>
          ) : (
            <motion.div className="glass p-6 text-center text-gray-400">
              <p className="mb-4">Complete preprocessing before training models.</p>
              <button type="button" onClick={() => setTab("preprocess")} className="btn-primary">
                Go to Pipeline
              </button>
            </motion.div>
          )}
        </motion.div>
      )}

      {tab === "insights" && (
        <motion.div key="insights" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {session?.status === "trained" && session.training_result?.best_model ? (
            <Suspense fallback={<TabLoader label="Loading explainability…" />}>
              <ExplainabilityPanel
                datasetId={datasetId}
                problemType={session.problem_type ?? "classification"}
                bestModelId={session.training_result.best_model.model_id}
                bestModelName={session.training_result.best_model.model_name}
              />
            </Suspense>
          ) : (
            <motion.div className="glass p-6 text-center text-gray-400">
              <p className="mb-4">Complete model training to unlock explainability insights.</p>
              <button type="button" onClick={() => setTab("arena")} className="btn-primary">
                Go to Arena
              </button>
            </motion.div>
          )}
        </motion.div>
      )}

      <DatasetChat datasetId={datasetId} filename={analysis.filename} />
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Rows3;
  label: string;
  value: string;
}) {
  return (
    <div className="glass px-4 py-3 flex items-center gap-3 min-w-[120px]">
      <Icon className="w-4 h-4 text-emerald-500" />
      <div>
        <p className="text-[10px] uppercase tracking-wider text-gray-400">{label}</p>
        <p className="font-mono text-gray-800 font-medium">{value}</p>
      </div>
    </div>
  );
}
