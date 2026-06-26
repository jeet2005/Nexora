import React from 'react';
import { motion } from 'framer-motion';

export const Home: React.FC = () => {
  return (
    <div className="min-h-screen bg-nexora-bg text-nexora-dark font-sans pb-20">
      {/* Hero Section */}
      <section className="relative pt-28 pb-16 px-6 max-w-6xl mx-auto flex flex-col items-center text-center">
        <div className="absolute inset-0 bg-grid bg-[size:48px_48px] opacity-30 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-nexora-accent/15 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />
        
        <div className="relative z-10 glass p-8 rounded-2xl mb-12 shadow-sm border border-nexora-border inline-block">
          <pre className="text-left font-mono text-[8px] sm:text-[10px] md:text-sm text-nexora-accent overflow-x-auto leading-[1.1]">{`
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝`}</pre>
        </div>

        <h1 className="font-display text-4xl md:text-5xl font-bold mb-6 text-nexora-dark relative z-10">
          Autonomous AI Predictive Analytics Platform
        </h1>
        <p className="text-lg text-nexora-dark/60 mb-10 max-w-3xl relative z-10">
          Drop a CSV → Auto-analyze → Train 18+ models → Generate insights → Deploy to production
        </p>

        <div className="glass px-8 py-6 rounded-xl border border-nexora-border mb-10 flex flex-col items-center gap-3 relative z-10">
          <h3 className="font-semibold text-nexora-dark/80 text-sm tracking-wider uppercase">Quick Start</h3>
          <code className="bg-nexora-dark/5 text-nexora-dark px-4 py-2 rounded-md font-mono text-sm border border-nexora-border w-full max-w-sm text-left">
            $ pip install nexora-prediction
          </code>
          <code className="bg-nexora-dark/5 text-nexora-dark px-4 py-2 rounded-md font-mono text-sm border border-nexora-border w-full max-w-sm text-left">
            $ nexora
          </code>
        </div>

        <div className="flex flex-wrap justify-center gap-4 relative z-10">
          <a href="https://github.com/jeet2005/nexora" className="btn-primary px-6 py-3">
            GitHub Repository
          </a>
          <a href="/docs" className="btn-outline px-6 py-3">
            View Documentation
          </a>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-6 max-w-6xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-12">Why Choose Nexora?</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: "📊", title: "Auto-Analysis", desc: "Dataset profiling, missing value detection, outlier analysis, and health scoring in seconds" },
            { icon: "🤖", title: "18+ Models", desc: "Classification & regression across boosting, ensemble, and neural network families" },
            { icon: "🔍", title: "Explainability", desc: "SHAP feature importance, partial dependence plots, interaction analysis" },
            { icon: "⚡", title: "Production-Ready", desc: "REST API, Docker deployment, FastAPI/Flask code generation in one command" },
            { icon: "📈", title: "Drift Detection", desc: "Monitor feature distribution shift and data quality degradation in production" },
            { icon: "🧠", title: "LLM Integration", desc: "AI-powered explanations with GPT/Claude/Ollama for natural language insights" },
            { icon: "📝", title: "Full Reports", desc: "HTML/PDF reports with leaderboards, metrics, and recommendations" },
            { icon: "⌨️", title: "CLI First", desc: "No browser needed. Full feature parity between CLI and Python API" },
          ].map((feature, idx) => (
            <motion.div key={idx} whileHover={{ y: -4 }} className="glass p-6 rounded-2xl border border-nexora-border hover:shadow-card transition-all">
              <div className="text-3xl mb-4">{feature.icon}</div>
              <h3 className="font-semibold text-nexora-dark mb-2">{feature.title}</h3>
              <p className="text-sm text-nexora-dark/60 leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CLI Commands Section */}
      <section className="py-16 px-6 max-w-5xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-12">Available Commands</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { group: "Data Analysis", cmds: ["nexora profile data.csv", "nexora clean data.csv --target y"] },
            { group: "Training", cmds: ["nexora train data.csv --target price", "nexora quick data.csv --target y"] },
            { group: "Predictions", cmds: ["nexora predict model.nx new_data.csv", "nexora drift model.nx prod_data.csv"] },
            { group: "Deployment", cmds: ["nexora serve model.nx --port 8000", "nexora report model.nx --format pdf"] },
            { group: "Analytics", cmds: ["nexora explain model.nx --top 15", "nexora compare model1.nx model2.nx"] },
            { group: "Utility", cmds: ["nexora models --task regression", "nexora config --show"] },
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

      {/* Getting Started Section */}
      <section className="py-16 px-6 max-w-3xl mx-auto relative z-10">
        <h2 className="font-display text-3xl font-bold text-center mb-12">Python API Example</h2>
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

# Leaderboard
print(report.leaderboard)

# Predictions
predictions = report.predict(new_df)

# Explanations
explanations = report.explain()

# Deploy API
report.serve(port=8000)

# Export
report.to_pdf('report.pdf')
report.to_html('report.html')`}</code>
          </pre>
        </div>
      </section>
    </div>
  );
};

export default Home;
