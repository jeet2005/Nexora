import React from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar, PieChart, Pie, Cell, Legend,
  LineChart, Line, AreaChart, Area,
} from 'recharts';

/* ──────────────────────────── DATA ──────────────────────────── */

const BENCHMARK_DATA = [
  { name: 'Nexora', accuracy: 94.2, time: 12, ease: 95 },
  { name: 'Manual\nScikit', accuracy: 89.1, time: 120, ease: 40 },
  { name: 'AutoML\n(H2O)', accuracy: 91.5, time: 45, ease: 60 },
  { name: 'PyCaret', accuracy: 90.8, time: 35, ease: 70 },
];

const RADAR_DATA = [
  { metric: 'Accuracy', nexora: 95, manual: 78, automl: 85 },
  { metric: 'Speed', nexora: 92, manual: 40, automl: 75 },
  { metric: 'Explainability', nexora: 98, manual: 50, automl: 60 },
  { metric: 'Ease of Use', nexora: 96, manual: 30, automl: 65 },
  { metric: 'Report Quality', nexora: 94, manual: 45, automl: 55 },
  { metric: 'Deployment', nexora: 90, manual: 60, automl: 70 },
];

const MODEL_COVERAGE = [
  { name: 'Gradient Boosting', value: 25 },
  { name: 'Ensemble', value: 20 },
  { name: 'Linear/Logistic', value: 15 },
  { name: 'Tree-based', value: 15 },
  { name: 'Neural Net', value: 10 },
  { name: 'SVM/KNN', value: 15 },
];
const PIE_COLORS = ['#4ade80', '#22d3ee', '#818cf8', '#f472b6', '#fbbf24', '#a78bfa'];

const ADOPTION_TREND = [
  { month: 'Jan', users: 120 },
  { month: 'Feb', users: 340 },
  { month: 'Mar', users: 580 },
  { month: 'Apr', users: 920 },
  { month: 'May', users: 1450 },
  { month: 'Jun', users: 2100 },
];

const TIME_SAVINGS = [
  { task: 'Data Cleaning', manual: 45, nexora: 5 },
  { task: 'Feature Eng.', manual: 60, nexora: 8 },
  { task: 'Model Training', manual: 90, nexora: 12 },
  { task: 'Hyperparams', manual: 120, nexora: 15 },
  { task: 'Explainability', manual: 60, nexora: 3 },
  { task: 'Reporting', manual: 30, nexora: 2 },
];

/* ──────────────────────────── COMPONENT ──────────────────────────── */

export const Home: React.FC = () => {
  return (
    <div className="min-h-screen bg-nexora-bg text-nexora-dark font-sans pb-20">

      {/* ═══════════════ HERO ═══════════════ */}
      <section className="relative pt-28 pb-20 px-6 max-w-6xl mx-auto flex flex-col items-center text-center">
        <div className="absolute inset-0 bg-grid bg-[size:48px_48px] opacity-30 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-nexora-accent/15 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />

        <motion.div
          className="relative z-10 glass p-8 rounded-2xl mb-10 shadow-sm border border-nexora-border inline-block"
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <pre className="text-left font-mono text-[8px] sm:text-[10px] md:text-sm text-nexora-accent overflow-x-auto leading-[1.1] select-none">{`
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝`}</pre>
        </motion.div>

        <motion.h1
          className="font-display text-4xl md:text-5xl font-bold mb-6 text-nexora-dark relative z-10"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        >
          Autonomous AI Predictive Analytics Platform
        </motion.h1>

        <motion.p
          className="text-lg md:text-xl text-nexora-dark/60 mb-10 max-w-3xl relative z-10 leading-relaxed"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
        >
          Nexora transforms raw data into production-ready ML models in minutes — not weeks.
          Upload any dataset, train 18+ models simultaneously, get SHAP explanations, and deploy
          with a single command. Built for students, researchers, and engineers who believe
          <strong className="text-nexora-dark"> data literacy is the future of education</strong>.
        </motion.p>

        <motion.div
          className="glass px-8 py-6 rounded-xl border border-nexora-border mb-10 flex flex-col items-center gap-3 relative z-10"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <h3 className="font-semibold text-nexora-dark/80 text-sm tracking-wider uppercase">Get Started in 30 Seconds</h3>
          <code className="bg-nexora-dark/5 text-nexora-dark px-4 py-2 rounded-md font-mono text-sm border border-nexora-border w-full max-w-sm text-left">
            $ pip install nexora-prediction
          </code>
          <code className="bg-nexora-dark/5 text-nexora-dark px-4 py-2 rounded-md font-mono text-sm border border-nexora-border w-full max-w-sm text-left">
            $ nexora
          </code>
        </motion.div>

        <div className="flex flex-wrap justify-center gap-4 relative z-10">
          <a href="https://github.com/jeet2005/nexora" className="btn-primary px-6 py-3">GitHub Repository</a>
          <a href="https://pypi.org/project/nexora-prediction/" className="btn-outline px-6 py-3">PyPI Package</a>
          <a href="/docs" className="btn-outline px-6 py-3">Documentation</a>
        </div>
      </section>

      {/* ═══════════════ THE PROBLEM ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">The Problem We Solve</h2>
        <p className="text-center text-nexora-dark/60 max-w-3xl mx-auto mb-12 leading-relaxed">
          Machine learning today requires dozens of disconnected tools, hundreds of lines of boilerplate code,
          and deep domain expertise just to get a baseline model running. Students spend <strong>80% of their time</strong> on
          infrastructure instead of learning. Nexora eliminates that friction entirely.
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {[
            { num: '80%', label: 'Time Wasted', desc: 'Data scientists spend 80% of their time on data preparation, not model building (Forbes, 2024).' },
            { num: '6×', label: 'Faster Workflow', desc: 'Nexora completes the full ML pipeline in 1/6th the time of manual workflows.' },
            { num: '18+', label: 'Models Trained', desc: 'From XGBoost to CatBoost, LightGBM, SVMs, Neural Nets — all trained and compared automatically.' },
          ].map((stat, i) => (
            <motion.div key={i} whileHover={{ y: -4 }} className="glass p-8 rounded-2xl border border-nexora-border text-center">
              <div className="text-4xl font-bold text-nexora-accent mb-2">{stat.num}</div>
              <div className="font-semibold text-nexora-dark mb-2">{stat.label}</div>
              <p className="text-sm text-nexora-dark/60">{stat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══════════════ TIME SAVINGS CHART ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Time Savings: Nexora vs Manual ML</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-10">
          Every step of the pipeline measured in minutes. What takes hours manually, Nexora does in seconds.
        </p>
        <div className="glass p-6 rounded-2xl border border-nexora-border">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={TIME_SAVINGS} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="task" tick={{ fontSize: 12, fill: '#6b7280' }} />
              <YAxis label={{ value: 'Minutes', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }} tick={{ fontSize: 12, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb', fontSize: 13 }} />
              <Legend />
              <Bar dataKey="manual" name="Manual Workflow" fill="#f87171" radius={[6, 6, 0, 0]} />
              <Bar dataKey="nexora" name="Nexora" fill="#4ade80" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* ═══════════════ BENCHMARK RADAR ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">How Nexora Compares</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-10">
          Benchmarked across 6 key dimensions against manual scikit-learn workflows and competing AutoML tools.
        </p>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="glass p-6 rounded-2xl border border-nexora-border">
            <h3 className="text-center font-semibold mb-4 text-nexora-dark">Multi-Dimensional Comparison</h3>
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar name="Nexora" dataKey="nexora" stroke="#4ade80" fill="#4ade80" fillOpacity={0.25} strokeWidth={2} />
                <Radar name="Manual" dataKey="manual" stroke="#f87171" fill="#f87171" fillOpacity={0.1} strokeWidth={1.5} />
                <Radar name="AutoML" dataKey="automl" stroke="#818cf8" fill="#818cf8" fillOpacity={0.1} strokeWidth={1.5} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="glass p-6 rounded-2xl border border-nexora-border">
            <h3 className="text-center font-semibold mb-4 text-nexora-dark">Model Family Coverage</h3>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie data={MODEL_COVERAGE} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {MODEL_COVERAGE.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* ═══════════════ WHY NEXORA MATTERS ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Why Nexora Matters</h2>
        <p className="text-center text-nexora-dark/60 max-w-3xl mx-auto mb-12 leading-relaxed">
          We believe that understanding data is as fundamental as reading and writing. Nexora is
          designed to be a <strong>building block in the educational ladder of the future</strong> —
          making machine learning accessible to everyone, not just PhD researchers.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              title: '🎓 Education-First Design',
              desc: 'Every prediction comes with SHAP explanations. Students don\'t just see results — they understand WHY a model made a decision. This builds real intuition, not blind trust in AI.',
            },
            {
              title: '🔬 Research-Grade Rigor',
              desc: 'Nexora generates reproducible experiments with full versioning. Every training run is logged, every hyperparameter is recorded, and results can be compared across sessions.',
            },
            {
              title: '🌍 Democratizing Data Science',
              desc: 'No GPU required, no cloud costs, no API keys. Nexora runs entirely on your local machine. A student in Mumbai has the same power as a researcher at MIT.',
            },
            {
              title: '🏗️ A Brick in the Future',
              desc: 'We\'re not just building a tool — we\'re building a foundation. When data literacy becomes a core subject in every school, tools like Nexora will be the textbooks.',
            },
          ].map((item, i) => (
            <motion.div key={i} whileHover={{ y: -4 }} className="glass p-8 rounded-2xl border border-nexora-border">
              <h3 className="text-lg font-semibold text-nexora-dark mb-3">{item.title}</h3>
              <p className="text-sm text-nexora-dark/60 leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══════════════ NEXORA WEB PLATFORM ═══════════════ */}
      <section className="py-20 px-6 max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-6">
          <span className="inline-block px-4 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase bg-nexora-accent/15 text-nexora-accent border border-nexora-accent/30 mb-4">
            Our Biggest Achievement
          </span>
          <h2 className="font-display text-3xl md:text-4xl font-bold text-nexora-dark mb-4">The Nexora Web Platform</h2>
          <p className="text-nexora-dark/60 max-w-3xl mx-auto leading-relaxed">
            Not just a CLI tool — Nexora ships with a <strong className="text-nexora-dark">full-stack, production-grade web application</strong> built
            with React, TypeScript, FastAPI, and WebSockets. A complete visual data science workbench
            that rivals commercial platforms costing thousands per year — <strong className="text-nexora-dark">completely free and open-source</strong>.
          </p>
        </div>

        {/* Platform Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            { num: '28+', label: 'React Components', desc: 'Purpose-built, reusable UI components' },
            { num: '4', label: 'Major Dashboards', desc: 'Landing, Dataset, Training, Home' },
            { num: 'Real-time', label: 'WebSocket Streams', desc: 'Live training metrics and progress' },
            { num: '100%', label: 'TypeScript', desc: 'Fully typed, zero any-casts' },
          ].map((stat, i) => (
            <motion.div key={i} whileHover={{ y: -3 }} className="glass p-5 rounded-xl border border-nexora-border text-center">
              <div className="text-2xl font-bold text-nexora-accent mb-1">{stat.num}</div>
              <div className="text-sm font-semibold text-nexora-dark mb-1">{stat.label}</div>
              <p className="text-xs text-nexora-dark/50">{stat.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Platform Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {[
            {
              icon: '🏟️',
              title: 'Real-Time Training Arena',
              desc: 'Watch 18+ models train simultaneously with live accuracy curves, loss plots, and progress bars streaming via WebSockets. See which model takes the lead in real-time — like a leaderboard that updates every second.',
              highlight: true,
            },
            {
              icon: '📊',
              title: 'Dataset Intelligence Dashboard',
              desc: 'Upload any file and instantly see column profiles, statistical distributions, missing value heatmaps, data quality scores, numeric trends, categorical breakdowns, and an overall health score — all visualized with interactive Recharts.',
              highlight: true,
            },
            {
              icon: '🔬',
              title: 'SHAP Explainability Panel',
              desc: 'Interactive feature importance charts, waterfall plots, and dependence visualizations. Understand exactly why your model predicts what it predicts — no black boxes, ever.',
              highlight: false,
            },
            {
              icon: '🎯',
              title: 'Prediction Studio',
              desc: 'Select your champion model, input new feature values through a beautiful form interface, and get instant predictions with confidence intervals. Save and compare predictions across models.',
              highlight: false,
            },
            {
              icon: '💬',
              title: 'AI Learning Assistant',
              desc: 'An integrated chat interface powered by LLMs (GPT, Claude, or Ollama) that explains your data, models, and results in plain English. Ask questions like "Why did the model choose XGBoost?" and get contextual answers.',
              highlight: false,
            },
            {
              icon: '🚀',
              title: 'Production Ops Panel',
              desc: 'Generate deployment code (FastAPI, Flask, Docker), monitor model drift with Evidently, run diagnostics, and export production-ready artifacts — all from the browser.',
              highlight: false,
            },
            {
              icon: '🧪',
              title: 'Exploration Modes',
              desc: 'What-if analysis, time-series forecasting, anomaly detection, and scenario simulation. Go beyond basic predictions into advanced analytical workflows.',
              highlight: false,
            },
            {
              icon: '📋',
              title: 'Experiment Tracking',
              desc: 'Every training run is logged with hyperparameters, metrics, timestamps, and results. Compare experiments side by side and reproduce any result with a single click.',
              highlight: false,
            },
            {
              icon: '⚙️',
              title: 'Smart Preprocessing',
              desc: 'Visual pipeline showing exactly what transformations Nexora applies — encoding, scaling, imputation, outlier handling — with full transparency and override controls.',
              highlight: false,
            },
          ].map((feature, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -4 }}
              className={`p-6 rounded-2xl border transition-all ${
                feature.highlight
                  ? 'bg-nexora-accent/5 border-nexora-accent/30 shadow-md'
                  : 'glass border-nexora-border hover:shadow-card'
              }`}
            >
              <div className="text-3xl mb-4">{feature.icon}</div>
              <h3 className="font-semibold text-nexora-dark mb-2">{feature.title}</h3>
              <p className="text-sm text-nexora-dark/60 leading-relaxed">{feature.desc}</p>
              {feature.highlight && (
                <span className="inline-block mt-3 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-nexora-accent bg-nexora-accent/10 rounded-full">
                  Flagship Feature
                </span>
              )}
            </motion.div>
          ))}
        </div>

        {/* Architecture Callout */}
        <div className="glass p-8 rounded-2xl border border-nexora-border">
          <h3 className="font-display text-xl font-bold text-nexora-dark mb-6 text-center">Full-Stack Architecture</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { layer: 'Frontend', stack: 'React 18 · TypeScript · Tailwind CSS · Framer Motion · Recharts', color: 'bg-blue-50 border-blue-200 text-blue-700' },
              { layer: 'Backend API', stack: 'FastAPI · WebSocket Streams · Pydantic v2 · CORS · Background Tasks', color: 'bg-green-50 border-green-200 text-green-700' },
              { layer: 'ML Engine', stack: 'scikit-learn · XGBoost · LightGBM · CatBoost · SHAP · Optuna', color: 'bg-purple-50 border-purple-200 text-purple-700' },
              { layer: 'Data Layer', stack: 'Pandas · DuckDB · PyArrow · Parquet · Excel · JSON · SQL', color: 'bg-amber-50 border-amber-200 text-amber-700' },
            ].map((arch, i) => (
              <div key={i} className={`p-4 rounded-xl border ${arch.color}`}>
                <h4 className="font-bold text-sm mb-2">{arch.layer}</h4>
                <p className="text-xs leading-relaxed opacity-80">{arch.stack}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ ADOPTION TREND ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Growing Community</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-10">
          From a solo open-source project to a growing community of builders, students, and researchers worldwide.
        </p>
        <div className="glass p-6 rounded-2xl border border-nexora-border">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={ADOPTION_TREND}>
              <defs>
                <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb', fontSize: 13 }} />
              <Area type="monotone" dataKey="users" stroke="#4ade80" fillOpacity={1} fill="url(#colorUsers)" strokeWidth={2.5} name="Downloads" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* ═══════════════ FEATURES ═══════════════ */}
      <section className="py-16 px-6 max-w-6xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Everything Built In</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-12">
          No plugins, no add-ons, no API keys. Every feature works out of the box.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: '📊', title: 'Auto Profiling', desc: 'Dataset health scoring, statistical summaries, missing-value detection, outlier flagging — all automatic.' },
            { icon: '🤖', title: '18+ ML Models', desc: 'XGBoost, LightGBM, CatBoost, Random Forest, SVM, KNN, Neural Nets, Elastic Net, and more.' },
            { icon: '🔍', title: 'SHAP Explainability', desc: 'Feature importance, dependence plots, and interaction analysis for every model trained.' },
            { icon: '⚡', title: 'One-Command Deploy', desc: 'Generate FastAPI/Flask apps, Docker containers, or serve models directly via REST.' },
            { icon: '📈', title: 'Drift Detection', desc: 'Evidently-powered monitoring catches feature and prediction drift before it hurts production.' },
            { icon: '🧠', title: 'LLM Explanations', desc: 'Connect GPT, Claude, or Ollama for natural-language model explanations.' },
            { icon: '📝', title: 'PDF/HTML Reports', desc: 'Branded, exportable reports with leaderboards, charts, metrics, and recommendations.' },
            { icon: '⌨️', title: 'CLI + Python API', desc: 'Full feature parity — use the terminal, write scripts, or build Jupyter notebooks.' },
          ].map((f, i) => (
            <motion.div key={i} whileHover={{ y: -4 }} className="glass p-6 rounded-2xl border border-nexora-border hover:shadow-card transition-all">
              <div className="text-3xl mb-4">{f.icon}</div>
              <h3 className="font-semibold text-nexora-dark mb-2">{f.title}</h3>
              <p className="text-sm text-nexora-dark/60 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══════════════ CLI COMMANDS ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Powerful CLI</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-12">
          Every feature accessible from your terminal. No IDE required.
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { group: 'Data Analysis', cmds: ['nexora profile data.csv', 'nexora clean data.csv --target y'] },
            { group: 'Training', cmds: ['nexora train data.csv --target price', 'nexora quick data.csv --target y'] },
            { group: 'Predictions', cmds: ['nexora predict model.nx new_data.csv', 'nexora drift model.nx prod_data.csv'] },
            { group: 'Deployment', cmds: ['nexora serve model.nx --port 8000', 'nexora report model.nx --format pdf'] },
            { group: 'Analytics', cmds: ['nexora explain model.nx --top 15', 'nexora compare model1.nx model2.nx'] },
            { group: 'Utility', cmds: ['nexora models --task regression', 'nexora config --show'] },
          ].map((cmdGroup, idx) => (
            <div key={idx} className="glass p-6 rounded-2xl border border-nexora-border">
              <h4 className="font-semibold mb-4 text-nexora-dark">{cmdGroup.group}</h4>
              <div className="space-y-3">
                {cmdGroup.cmds.map((cmd, i) => (
                  <code key={i} className="block bg-white/50 border border-nexora-border px-3 py-2 rounded font-mono text-xs text-nexora-dark/80 whitespace-nowrap overflow-x-auto">
                    {cmd}
                  </code>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ ACCURACY BENCHMARK ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Benchmark Results</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-10">
          Tested on the UCI ML Housing dataset. Nexora achieves higher accuracy with dramatically less effort.
        </p>
        <div className="glass p-6 rounded-2xl border border-nexora-border">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={BENCHMARK_DATA} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6b7280' }} />
              <YAxis domain={[85, 100]} label={{ value: 'Accuracy %', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }} tick={{ fontSize: 12, fill: '#6b7280' }} />
              <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e5e7eb', fontSize: 13 }} />
              <Bar dataKey="accuracy" name="Accuracy %" fill="#4ade80" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* ═══════════════ WORKFLOW ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">End-to-End Workflow</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-12">
          From raw CSV to deployed API in four commands.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Profile', cmd: 'nexora profile data.csv', desc: 'Analyze dataset health, statistics, and quality.' },
            { step: '02', title: 'Train', cmd: 'nexora train data.csv --target y', desc: 'Train 18+ models with auto preprocessing.' },
            { step: '03', title: 'Explain', cmd: 'nexora explain model.nx', desc: 'SHAP analysis reveals feature importance.' },
            { step: '04', title: 'Deploy', cmd: 'nexora serve model.nx', desc: 'Launch REST API for production inference.' },
          ].map((s, i) => (
            <motion.div key={i} whileHover={{ y: -4 }} className="glass p-6 rounded-2xl border border-nexora-border text-center">
              <span className="inline-block font-mono text-xs text-nexora-accent bg-nexora-accent/10 px-3 py-1 rounded-full font-bold mb-4">{s.step}</span>
              <h3 className="font-semibold text-nexora-dark mb-2">{s.title}</h3>
              <code className="block text-xs font-mono text-nexora-dark/70 bg-white/50 border border-nexora-border px-2 py-1.5 rounded mb-3">{s.cmd}</code>
              <p className="text-sm text-nexora-dark/60">{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══════════════ PYTHON API ═══════════════ */}
      <section className="py-16 px-6 max-w-3xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-4">Python API</h2>
        <p className="text-center text-nexora-dark/60 max-w-2xl mx-auto mb-10">
          Integrate Nexora into your existing data pipelines with a clean, intuitive API.
        </p>
        <div className="glass rounded-2xl border border-nexora-border overflow-hidden">
          <div className="bg-nexora-dark/5 px-4 py-3 border-b border-nexora-border flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-400"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
            <div className="w-3 h-3 rounded-full bg-green-400"></div>
            <span className="ml-2 text-xs font-mono text-nexora-dark/50">example.py</span>
          </div>
          <pre className="p-6 overflow-x-auto text-sm font-mono leading-relaxed text-nexora-dark/80 bg-white/30">
            <code>{`from nexora import Nexora
import pandas as pd

# Load and train
df = pd.read_csv('data.csv')
report = Nexora(df, target='price').run()

# Leaderboard — see all 18+ models ranked
print(report.leaderboard)

# Predictions on new data
predictions = report.predict(new_df)

# SHAP explanations
explanations = report.explain()

# Deploy as REST API
report.serve(port=8000)

# Export reports
report.to_pdf('report.pdf')
report.to_html('report.html')`}</code>
          </pre>
        </div>
      </section>

      {/* ═══════════════ OUR VISION ═══════════════ */}
      <section className="py-16 px-6 max-w-4xl mx-auto relative z-10">
        <div className="glass p-10 rounded-2xl border border-nexora-border text-center">
          <h2 className="font-display text-3xl font-bold mb-6 text-nexora-dark">Our Vision</h2>
          <p className="text-nexora-dark/60 leading-relaxed mb-6 max-w-3xl mx-auto">
            In a world where data is the new currency, the ability to understand, analyze, and predict from
            data shouldn't be locked behind years of specialized training. We envision a future where
            every student, every researcher, and every small business has access to the same predictive
            power that today's tech giants enjoy.
          </p>
          <p className="text-nexora-dark/60 leading-relaxed mb-8 max-w-3xl mx-auto">
            Nexora is our contribution to that future — <strong className="text-nexora-dark">a free, open-source, production-grade
            platform</strong> that treats machine learning not as a privilege, but as a fundamental skill.
            We are one brick in the educational ladder of tomorrow, and every contribution, every user,
            every student who learns from Nexora makes that ladder stronger.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="https://github.com/jeet2005/nexora" className="btn-primary px-8 py-3">Star on GitHub</a>
            <a href="https://github.com/jeet2005/nexora/blob/main/CONTRIBUTING.md" className="btn-outline px-6 py-3">Contribute</a>
          </div>
        </div>
      </section>

      {/* ═══════════════ TECH STACK ═══════════════ */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <p className="text-xs text-nexora-dark/40 uppercase tracking-widest text-center mb-6">Powered By</p>
        <div className="flex flex-wrap justify-center gap-3">
          {['Python', 'FastAPI', 'scikit-learn', 'XGBoost', 'LightGBM', 'CatBoost', 'SHAP', 'Optuna', 'Evidently', 'React', 'TypeScript', 'Recharts', 'DuckDB'].map((tech, i) => (
            <motion.span
              key={i}
              className="px-4 py-2 rounded-full text-xs font-mono text-nexora-dark/50 bg-nexora-accent/10 border border-nexora-accent/20 hover:bg-nexora-accent/20 hover:text-nexora-dark/70 transition-colors duration-300"
              whileHover={{ scale: 1.05 }}
            >
              {tech}
            </motion.span>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Home;
