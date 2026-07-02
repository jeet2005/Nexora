import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, ArrowRight, Home } from 'lucide-react';

type ErrorPageProps = {
  code: string;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
};

export default function ErrorPage({
  code,
  title,
  description,
  actionLabel = 'Back home',
  actionHref = '/',
}: ErrorPageProps) {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="glass w-full max-w-3xl rounded-3xl border border-nexora-border p-8 sm:p-12"
      >
        <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-nexora-accent/20 bg-nexora-accent/10 px-3 py-1 text-sm font-semibold text-nexora-accent">
              <AlertTriangle size={16} />
              <span>Runtime signal issue</span>
            </div>
            <div className="mb-4 text-6xl font-black tracking-tight text-nexora-dark/80">{code}</div>
            <h1 className="text-3xl font-semibold text-nexora-dark sm:text-4xl">{title}</h1>
            <p className="mt-4 text-lg leading-8 text-nexora-dark/70">{description}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to={actionHref} className="btn-primary">
                <Home size={16} />
                {actionLabel}
              </Link>
              <Link to="/datasets" className="btn-outline">
                Browse datasets
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>

          <div className="rounded-2xl border border-nexora-border bg-gradient-to-br from-nexora-accent/10 via-white to-nexora-accent/5 p-6 shadow-sm">
            <div className="text-sm font-semibold uppercase tracking-[0.25em] text-nexora-dark/50">Diagnostic</div>
            <div className="mt-4 space-y-3 text-sm text-nexora-dark/70">
              <div className="rounded-xl border border-nexora-border/70 bg-white/70 px-4 py-3">The route may be outdated, mistyped, or temporarily unavailable.</div>
              <div className="rounded-xl border border-nexora-border/70 bg-white/70 px-4 py-3">If this is unexpected, please return to the workspace and try again.</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
