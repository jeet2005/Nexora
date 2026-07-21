import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  X,
  Bot,
  Loader2,
  Terminal,
} from 'lucide-react';
import { explainError } from '../api/client';

interface GodErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  errorMessage: string;
  datasetId?: string;
  contextInfo?: string;
  onRetry?: () => void;
  category?: 'Data' | 'Training' | 'Preprocessing' | 'System' | 'Network';
}

export default function GodErrorModal({
  isOpen,
  onClose,
  title = 'An Error Occurred',
  errorMessage,
  datasetId,
  contextInfo,
  onRetry,
  category = 'System',
}: GodErrorModalProps) {
  const [aiLoading, setAiLoading] = useState(false);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showTechnical, setShowTechnical] = useState(false);

  const handleExplainWithAi = async () => {
    setAiLoading(true);
    try {
      const res = await explainError(errorMessage, datasetId, contextInfo);
      setAiExplanation(res.explanation);
    } catch {
      setAiExplanation(
        '### 🔍 AI Diagnostic Summary\n\n' +
          `**Error:** \`${errorMessage.slice(0, 200)}\`\n\n` +
          '• **Fix:** Please check target column selection, dataset headers, or retry the operation.',
      );
    } finally {
      setAiLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(`[Nexora Error Trace]\nCategory: ${category}\nTitle: ${title}\nContext: ${contextInfo || 'N/A'}\nError: ${errorMessage}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
        {/* Backdrop Glow */}
        <div className="absolute inset-0 bg-gradient-to-tr from-rose-950/30 via-red-900/10 to-amber-950/20 pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-rose-500/30 bg-slate-900/95 text-slate-100 shadow-2xl shadow-rose-950/50 backdrop-blur-xl"
        >
          {/* Top Decorative Neon Pulse Bar */}
          <div className="h-1.5 w-full bg-gradient-to-r from-rose-500 via-amber-500 to-red-600 animate-pulse" />

          {/* Header */}
          <div className="p-6 border-b border-slate-800/80 flex items-start justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="relative p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 shrink-0">
                <AlertTriangle className="w-6 h-6 text-rose-500 animate-bounce" />
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
                </span>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/30 text-rose-300 text-[11px] font-mono font-semibold uppercase tracking-wider">
                    {category} Exception
                  </span>
                  {contextInfo && (
                    <span className="text-xs text-slate-400 font-mono truncate max-w-[200px]">
                      • {contextInfo}
                    </span>
                  )}
                </div>
                <h3 className="text-xl font-bold font-display text-slate-100 tracking-tight">
                  {title}
                </h3>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto custom-scrollbar">
            {/* Primary Error Alert Box */}
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/20 text-rose-200 text-sm font-sans leading-relaxed">
              <p className="font-medium">{errorMessage}</p>
            </div>

            {/* AI Ollama Explanation Section */}
            {aiExplanation && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-5 rounded-xl bg-gradient-to-br from-emerald-950/40 to-slate-900 border border-emerald-500/30 text-slate-200 space-y-3"
              >
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                  <Bot className="w-5 h-5" />
                  <span>Ollama AI Diagnostic Assistant</span>
                </div>
                <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                  {aiExplanation}
                </div>
              </motion.div>
            )}

            {/* Toggle Technical Stack Trace Drawer */}
            <div>
              <button
                type="button"
                onClick={() => setShowTechnical(!showTechnical)}
                className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                <Terminal className="w-3.5 h-3.5" />
                {showTechnical ? 'Hide Raw Details' : 'View Technical Stack Details'}
              </button>

              {showTechnical && (
                <motion.pre
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-2.5 p-3.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-rose-300/80 overflow-x-auto whitespace-pre-wrap"
                >
                  {`[Exception Log]\nTimestamp: ${new Date().toISOString()}\nCategory: ${category}\nMessage: ${errorMessage}\nDatasetID: ${datasetId || 'N/A'}`}
                </motion.pre>
              )}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-6 border-t border-slate-800/80 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
            {/* Left Action: Explain with AI */}
            <button
              type="button"
              onClick={handleExplainWithAi}
              disabled={aiLoading}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-emerald-950/40 border border-emerald-400/30 transition-all disabled:opacity-50"
            >
              {aiLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-200" />
                  <span>Asking Ollama AI…</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-emerald-200" />
                  <span>Explain Error with AI (Ollama)</span>
                </>
              )}
            </button>

            {/* Right Actions: Copy, Retry, Close */}
            <div className="flex items-center gap-2 ml-auto">
              <button
                type="button"
                onClick={handleCopy}
                className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs flex items-center gap-1.5 border border-slate-700 transition-colors"
                title="Copy error stack"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied' : 'Copy Log'}</span>
              </button>

              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-medium text-sm flex items-center gap-1.5 shadow-md border border-amber-400/30 transition-all"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry</span>
                </button>
              )}

              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm border border-slate-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
