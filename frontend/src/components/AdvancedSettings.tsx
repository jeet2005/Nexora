import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings2, ChevronDown, ChevronUp, Info, Clock } from "lucide-react";
import { getTimingEstimates, type TimingEstimates } from "../api/client";
import { formatDuration } from "../utils/formatDuration";

export interface AdvancedConfig {
  testSplit: number;
  cvFolds: number;
  maxModels: number;
  timeout: number;
  seed: number;
  enableEarlyStopping: boolean;
}

const DEFAULTS: AdvancedConfig = {
  testSplit: 0.2,
  cvFolds: 5,
  maxModels: 100,
  timeout: 600,
  seed: 42,
  enableEarlyStopping: true,
};

interface Props {
  config: AdvancedConfig;
  onChange: (config: AdvancedConfig) => void;
  datasetId?: string;
}

export default function AdvancedSettings({ config, onChange, datasetId }: Props) {
  const [open, setOpen] = useState(false);
  const [timing, setTiming] = useState<TimingEstimates | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    getTimingEstimates(datasetId, { maxModels: config.maxModels })
      .then(setTiming)
      .catch(() => setTiming(null));
  }, [datasetId, config.maxModels]);

  const update = <K extends keyof AdvancedConfig>(key: K, value: AdvancedConfig[K]) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <motion.div
      className="glass overflow-hidden"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
            <Settings2 className="w-4 h-4 text-gray-500" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-gray-700">Advanced Settings</p>
            <p className="text-xs text-gray-400">Train/test split, CV folds, model limits & more</p>
          </div>
        </div>
        {open ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 pt-2 border-t border-gray-100 space-y-5">
              {/* Test/Train Split */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-gray-500 uppercase tracking-wider flex items-center gap-1">
                    Test Split Ratio
                    <Tip text="Fraction of data held out for testing" />
                  </label>
                  <span className="font-mono text-sm text-emerald-600">{(config.testSplit * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min={0.1}
                  max={0.4}
                  step={0.05}
                  value={config.testSplit}
                  onChange={(e) => update("testSplit", parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5"
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>10%</span>
                  <span>40%</span>
                </div>
              </div>

              {/* CV Folds */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-gray-500 uppercase tracking-wider flex items-center gap-1">
                    Cross-Validation Folds
                    <Tip text="Number of CV folds for model evaluation" />
                  </label>
                  <span className="font-mono text-sm text-emerald-600">{config.cvFolds}</span>
                </div>
                <div className="flex gap-2">
                  {[3, 5, 7, 10].map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => update("cvFolds", n)}
                      className={`flex-1 py-2 rounded-lg text-sm border transition-all ${
                        config.cvFolds === n
                          ? "border-emerald-400 bg-emerald-50 text-emerald-700 font-medium"
                          : "border-gray-200 text-gray-500 hover:border-gray-300"
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              {/* Max Models */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-gray-500 uppercase tracking-wider flex items-center gap-1">
                    Max Models
                    <Tip text="Maximum number of models to train" />
                  </label>
                  <span className="font-mono text-sm text-emerald-600">{config.maxModels}</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={200}
                  step={10}
                  value={config.maxModels}
                  onChange={(e) => update("maxModels", parseInt(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5"
                />
                <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>10 (fast)</span>
                  <span>200 (thorough)</span>
                </div>
              </div>

              {/* Timeout */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    min={60}
                    max={3600}
                    step={60}
                    value={config.timeout}
                    onChange={(e) => update("timeout", parseInt(e.target.value) || 600)}
                    className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">
                    Random Seed
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={99999}
                    value={config.seed}
                    onChange={(e) => update("seed", parseInt(e.target.value) || 42)}
                    className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
                  />
                </div>
              </div>

              {/* Early Stopping */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                <div>
                  <p className="text-sm text-gray-700">Early Stopping</p>
                  <p className="text-xs text-gray-400">Stop training when no improvement is detected</p>
                </div>
                <button
                  type="button"
                  onClick={() => update("enableEarlyStopping", !config.enableEarlyStopping)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    config.enableEarlyStopping ? "bg-emerald-500" : "bg-gray-300"
                  }`}
                >
                  <motion.div
                    className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm"
                    animate={{ left: config.enableEarlyStopping ? 22 : 2 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                </button>
              </div>

              {/* Expected timing */}
              {timing && (
                <div className="rounded-lg bg-emerald-50 border border-emerald-100 p-3 flex items-start gap-2">
                  <Clock className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                  <div className="text-xs text-emerald-800 space-y-1">
                    <p>
                      Benchmark (~{timing.benchmark_model_count} models):{" "}
                      <span className="font-mono font-medium">{formatDuration(timing.benchmark_sec)}</span>
                    </p>
                    <p className="text-emerald-600">
                      Preprocess ~{formatDuration(timing.preprocess_sec)} · Production train ~
                      {formatDuration(timing.production_train_sec)}
                    </p>
                  </div>
                </div>
              )}

              {/* Reset */}
              <button
                type="button"
                onClick={() => onChange(DEFAULTS)}
                className="text-xs text-gray-400 hover:text-emerald-600 transition-colors"
              >
                Reset to defaults
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export { DEFAULTS as DEFAULT_CONFIG };

function Tip({ text }: { text: string }) {
  return (
    <span className="group relative cursor-help">
      <Info className="w-3 h-3 text-gray-300" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 text-[10px] bg-gray-800 text-white rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
        {text}
      </span>
    </span>
  );
}
