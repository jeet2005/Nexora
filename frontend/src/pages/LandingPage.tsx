import { motion, Variants } from 'framer-motion';
import {
  Brain,
  Zap,
  BarChart3,
  MessageSquare,
  Shield,
  Cpu,
  Upload,
  Target,
  Settings2,
  Trophy,
  Sparkles,
  FileDown,
  ArrowRight,
  ChevronDown,
} from 'lucide-react';
import NexoraLogo from '../components/NexoraLogo';
import UploadZone from '../components/UploadZone';
import { useEffect, useState } from 'react';
import { getPublicContent } from '../api/users';
import { Megaphone, X } from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    title: 'Dataset Intelligence',
    desc: 'Automatic structural, statistical, and semantic understanding of your data.',
    accent: 'bg-nexora-accent/10 text-nexora-accent border-nexora-accent/30',
  },
  {
    icon: Zap,
    title: 'Prediction Studio',
    desc: 'Select trusted models, save them locally, and run reproducible predictions.',
    accent: 'bg-nexora-accent/10 text-nexora-accent border-nexora-accent/30',
  },
  {
    icon: BarChart3,
    title: 'SHAP Explainability',
    desc: 'Understand why your model makes predictions with feature importance.',
    accent: 'bg-nexora-accent/10 text-nexora-accent border-nexora-accent/30',
  },
  {
    icon: MessageSquare,
    title: 'Learning Assistant',
    desc: 'Use local AI to understand data and models while the backend computes results.',
    accent: 'bg-nexora-dark/10 text-nexora-dark border-nexora-dark/30',
  },
  {
    icon: Shield,
    title: 'Auto Preprocessing',
    desc: 'Missing values, encoding, scaling, and outlier handling — automatic.',
    accent: 'bg-nexora-accent/10 text-nexora-accent border-nexora-accent/30',
  },
  {
    icon: Cpu,
    title: 'PDF Reports',
    desc: 'Generate branded, exportable intelligence reports with one click.',
    accent: 'bg-nexora-dark/10 text-nexora-dark border-nexora-dark/30',
  },
];

const STEPS = [
  {
    icon: Upload,
    label: 'Upload',
    desc: 'Drop your dataset (CSV, Excel, JSON, Parquet, SQL). Nexora profiles it instantly.',
    num: '01',
  },
  {
    icon: Target,
    label: 'Target',
    desc: 'Pick what to predict. AI auto-detects the problem type.',
    num: '02',
  },
  {
    icon: Settings2,
    label: 'Select Models',
    desc: 'Choose one or several trained-model candidates.',
    num: '03',
  },
  {
    icon: Trophy,
    label: 'Predict',
    desc: 'Run saved backend models with real input values.',
    num: '04',
  },
  {
    icon: Sparkles,
    label: 'Explain',
    desc: 'SHAP analysis shows why the champion model wins.',
    num: '05',
  },
  {
    icon: FileDown,
    label: 'Report',
    desc: 'Download a PDF with everything — data, models, charts.',
    num: '06',
  },
];

const TECH = [
  'Python',
  'FastAPI',
  'scikit-learn',
  'XGBoost',
  'LightGBM',
  'CatBoost',
  'SHAP',
  'React',
  'TypeScript',
  'Recharts',
];

const fadeUp: Variants = { hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0 } };

const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
};

export default function LandingPage() {
  const [announcement, setAnnouncement] = useState<{
    value: string;
    updated_by_name?: string;
    updated_by_avatar?: string;
    updated_at?: string;
  } | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    getPublicContent('announcement_banner')
      .then((res) => {
        if (res?.value) {
          setAnnouncement(res);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-nexora-bg">
      {announcement?.value && !dismissed && (
        <div className="bg-nexora-accent/10 border-b border-nexora-accent/30">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-start gap-3">
            {announcement.updated_by_avatar ? (
              <img
                src={announcement.updated_by_avatar}
                alt=""
                className="w-8 h-8 rounded-full object-cover border border-nexora-accent/30 flex-shrink-0 mt-0.5"
              />
            ) : (
              <Megaphone className="w-5 h-5 text-nexora-accent flex-shrink-0 mt-1" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-nexora-dark leading-relaxed">{announcement.value}</p>
              {announcement.updated_by_name && (
                <p className="text-xs text-nexora-dark/50 mt-1">
                  — {announcement.updated_by_name}
                  {announcement.updated_at &&
                    ` · ${new Date(announcement.updated_at).toLocaleDateString()}`}
                </p>
              )}
            </div>
            <button
              onClick={() => setDismissed(true)}
              className="text-nexora-dark/40 hover:text-nexora-dark p-1"
              aria-label="Dismiss announcement"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid bg-[size:48px_48px] opacity-30" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-nexora-accent/15 rounded-full blur-[120px] -translate-y-1/2 animate-pulse-slow" />

        {/* Floating accent orbs */}
        <motion.div
          className="absolute top-32 left-[12%] w-3 h-3 rounded-full bg-nexora-accent/30"
          animate={{ y: [0, -18, 0], opacity: [0.3, 0.6, 0.3] }}
          transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute top-48 right-[18%] w-2 h-2 rounded-full bg-nexora-accent/20"
          animate={{ y: [0, -12, 0], opacity: [0.2, 0.5, 0.2] }}
          transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut', delay: 1 }}
        />
        <motion.div
          className="absolute top-64 left-[25%] w-1.5 h-1.5 rounded-full bg-nexora-dark/10"
          animate={{ y: [0, -14, 0], opacity: [0.15, 0.4, 0.15] }}
          transition={{ repeat: Infinity, duration: 3.5, ease: 'easeInOut', delay: 0.5 }}
        />

        <div className="relative max-w-5xl mx-auto px-6 pt-28 pb-20 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <NexoraLogo size="hero" className="mx-auto mb-8 text-nexora-dark" />
          </motion.div>

          <motion.p
            className="text-lg md:text-xl text-nexora-dark/60 max-w-2xl mx-auto mb-10 leading-relaxed font-light"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            Upload your dataset (CSV, Excel, Parquet, JSON, SQL, and 100+ more). Select models, run
            backend-owned predictions, understand the results, and export a complete report.
          </motion.p>

          <motion.div
            className="flex justify-center gap-4"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            <a href="#upload" className="btn-primary text-base px-8 py-3.5 group">
              <Upload className="w-5 h-5 transition-transform group-hover:-translate-y-0.5" />
              Start Analyzing
            </a>
            <a href="#how-it-works" className="btn-outline text-base px-6 py-3.5 group">
              How It Works
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </a>
            <a href="/home" className="btn-outline text-base px-6 py-3.5 group">
              Deep-Dive (Home of Nexora)
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </a>
          </motion.div>

          <motion.a
            href="#how-it-works"
            className="inline-block mt-16 text-nexora-accent/50 hover:text-nexora-accent transition-colors"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <ChevronDown className="w-6 h-6 animate-bounce" />
          </motion.a>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-white border-t border-b border-nexora-border">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            className="text-center mb-14"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="font-display text-2xl md:text-3xl text-nexora-dark mb-3">
              How Nexora Works
            </h2>
            <p className="text-nexora-dark/50">
              Six steps from raw data to actionable intelligence
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {STEPS.map((step) => (
              <motion.div
                key={step.num}
                className="relative p-6 rounded-2xl bg-nexora-accent/5 border border-nexora-border hover:border-nexora-accent hover:shadow-card transition-all duration-300 group"
                variants={scaleIn}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="font-mono text-xs text-nexora-accent bg-nexora-accent/10 px-2 py-1 rounded-md font-bold">
                    {step.num}
                  </span>
                  <div className="w-9 h-9 rounded-lg bg-nexora-accent/10 border border-nexora-accent/30 flex items-center justify-center group-hover:bg-nexora-accent/20 group-hover:scale-110 transition-all duration-300">
                    <step.icon className="w-4 h-4 text-nexora-accent" />
                  </div>
                </div>
                <h3 className="font-semibold text-nexora-dark mb-1">{step.label}</h3>
                <p className="text-sm text-nexora-dark/50 leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Why Nexora */}
      <section
        id="why-nexora"
        className="py-20 bg-nexora-dark/5 border-t border-b border-nexora-border"
      >
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            className="text-center mb-14"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="font-display text-2xl md:text-3xl text-nexora-dark mb-3">
              Why Choose Nexora?
            </h2>
            <p className="text-nexora-dark/50">
              Complex data science simplified into a single autonomous workflow
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div
              variants={scaleIn}
              whileHover={{ y: -4 }}
              className="bg-white p-6 rounded-2xl border border-nexora-border shadow-sm"
            >
              <h3 className="font-semibold text-nexora-dark mb-2">100+ Formats Supported</h3>
              <p className="text-sm text-nexora-dark/60">
                Upload CSVs, Excel, JSON, Parquet, or connect directly to SQL. We handle the parsing
                automatically.
              </p>
            </motion.div>
            <motion.div
              variants={scaleIn}
              whileHover={{ y: -4 }}
              className="bg-white p-6 rounded-2xl border border-nexora-border shadow-sm"
            >
              <h3 className="font-semibold text-nexora-dark mb-2">Zero Boilerplate</h3>
              <p className="text-sm text-nexora-dark/60">
                Say goodbye to repetitive data cleaning and model training scripts. Nexora does it
                all in seconds.
              </p>
            </motion.div>
            <motion.div
              variants={scaleIn}
              whileHover={{ y: -4 }}
              className="bg-white p-6 rounded-2xl border border-nexora-border shadow-sm"
            >
              <h3 className="font-semibold text-nexora-dark mb-2">No Black Boxes</h3>
              <p className="text-sm text-nexora-dark/60">
                Every decision is explained via SHAP values, giving you complete transparency into
                model predictions.
              </p>
            </motion.div>
            <motion.div
              variants={scaleIn}
              whileHover={{ y: -4 }}
              className="bg-white p-6 rounded-2xl border border-nexora-border shadow-sm"
            >
              <h3 className="font-semibold text-nexora-dark mb-2">Deploy Anywhere</h3>
              <p className="text-sm text-nexora-dark/60">
                Export your final model as a compiled artifact or deploy it instantly via our
                built-in REST API.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            className="text-center mb-14"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="font-display text-2xl md:text-3xl text-nexora-dark mb-3">
              Built-in Intelligence
            </h2>
            <p className="text-nexora-dark/50">
              Every feature you need — free, local, no API keys required
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {FEATURES.map((f) => (
              <motion.div
                key={f.title}
                className="glass p-6 hover:shadow-lg transition-all duration-300 group"
                variants={scaleIn}
                whileHover={{ y: -3, transition: { duration: 0.2 } }}
              >
                <div
                  className={`w-10 h-10 rounded-lg border flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 ${f.accent}`}
                >
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-nexora-dark mb-1">{f.title}</h3>
                <p className="text-sm text-nexora-dark/60">{f.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Upload */}
      <section id="upload" className="py-20 bg-white border-t border-nexora-border">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div
            className="text-center mb-10"
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h2 className="font-display text-2xl md:text-3xl text-nexora-dark mb-3">Start Now</h2>
            <p className="text-nexora-dark/50">
              Upload your tabular dataset and watch Nexora work its magic
            </p>
          </motion.div>
          <UploadZone />
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-16">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <p className="text-xs text-nexora-dark/40 uppercase tracking-widest mb-4">Powered By</p>
          <motion.div
            className="flex flex-wrap justify-center gap-3"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {TECH.map((t) => (
              <motion.span
                key={t}
                className="px-3 py-1.5 rounded-full text-xs font-mono text-nexora-dark/50 bg-nexora-accent/10 border border-nexora-accent/20 hover:bg-nexora-accent/20 hover:text-nexora-dark/70 transition-colors duration-300"
                variants={{ hidden: { opacity: 0, scale: 0.9 }, visible: { opacity: 1, scale: 1 } }}
              >
                {t}
              </motion.span>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  );
}
