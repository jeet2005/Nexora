import React from 'react';
import './Home.css';

export const Home: React.FC = () => {
  return (
    <div className="home-container">
      {/* Hero Section with CLI Logo */}
      <section className="hero">
        <div className="logo-section">
          <pre className="cli-logo">{`
███╗   ██╗    ███████╗    ██╗  ██╗     ██████╗     ██████╗      █████╗
████╗  ██║    ██╔════╝    ╚██╗██╔╝    ██╔═══██╗    ██╔══██╗    ██╔══██╗
██╔██╗ ██║    █████╗       ╚███╔╝     ██║   ██║    ██████╔╝    ███████║
██║╚██╗██║    ██╔══╝       ██╔██╗     ██║   ██║    ██╔══██╗    ██╔══██║
██║ ╚████║    ███████╗    ██╔╝ ██╗    ╚██████╔╝    ██║  ██║    ██║  ██║
╚═╝  ╚═══╝    ╚══════╝    ╚═╝  ╚═╝     ╚═════╝     ╚═╝  ╚═╝    ╚═╝  ╚═╝`}</pre>
        </div>

        <div className="hero-content">
          <h1>Autonomous AI Predictive Analytics Platform</h1>
          <p className="tagline">
            Drop a CSV → Auto-analyze → Train 18+ models → Generate insights → Deploy to production
          </p>
          
          <div className="quick-install">
            <h3>Quick Start</h3>
            <code className="install-cmd">pip install nexora-prediction</code>
            <code className="install-cmd">nexora</code>
          </div>

          <div className="cta-buttons">
            <a href="https://github.com/jeet2005/nexora" className="btn btn-primary">
              GitHub Repository
            </a>
            <a href="/docs" className="btn btn-secondary">
              View Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose Nexora?</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Auto-Analysis</h3>
            <p>Dataset profiling, missing value detection, outlier analysis, and health scoring in seconds</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>18+ Models</h3>
            <p>Classification & regression across boosting, ensemble, and neural network families</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Explainability</h3>
            <p>SHAP feature importance, partial dependence plots, interaction analysis</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Production-Ready</h3>
            <p>REST API, Docker deployment, FastAPI/Flask code generation in one command</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>Drift Detection</h3>
            <p>Monitor feature distribution shift and data quality degradation in production</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🧠</div>
            <h3>LLM Integration</h3>
            <p>AI-powered explanations with GPT/Claude/Ollama for natural language insights</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📝</div>
            <h3>Full Reports</h3>
            <p>HTML/PDF reports with leaderboards, metrics, and recommendations</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">⌨️</div>
            <h3>CLI First</h3>
            <p>No browser needed. Full feature parity between CLI and Python API</p>
          </div>
        </div>
      </section>

      {/* CLI Commands Section */}
      <section className="commands">
        <h2>Available Commands</h2>
        <div className="commands-grid">
          <div className="command-group">
            <h4>Data Analysis</h4>
            <code>nexora profile data.csv</code>
            <code>nexora clean data.csv --target y</code>
          </div>

          <div className="command-group">
            <h4>Training</h4>
            <code>nexora train data.csv --target price</code>
            <code>nexora quick data.csv --target y</code>
          </div>

          <div className="command-group">
            <h4>Predictions</h4>
            <code>nexora predict model.nx new_data.csv</code>
            <code>nexora drift model.nx prod_data.csv</code>
          </div>

          <div className="command-group">
            <h4>Deployment</h4>
            <code>nexora serve model.nx --port 8000</code>
            <code>nexora report model.nx --format pdf</code>
          </div>

          <div className="command-group">
            <h4>Analytics</h4>
            <code>nexora explain model.nx --top 15</code>
            <code>nexora compare model1.nx model2.nx</code>
          </div>

          <div className="command-group">
            <h4>Utility</h4>
            <code>nexora models --task regression</code>
            <code>nexora config --show</code>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section className="workflow">
        <h2>Typical Workflow</h2>
        <div className="workflow-steps">
          <div className="step">
            <div className="step-number">1</div>
            <h4>Profile</h4>
            <p><code>nexora profile data.csv</code></p>
            <p className="description">Analyze dataset health and quality</p>
          </div>

          <div className="arrow">→</div>

          <div className="step">
            <div className="step-number">2</div>
            <h4>Train</h4>
            <p><code>nexora train data.csv --target y</code></p>
            <p className="description">Train multiple models automatically</p>
          </div>

          <div className="arrow">→</div>

          <div className="step">
            <div className="step-number">3</div>
            <h4>Explain</h4>
            <p><code>nexora explain model.nx</code></p>
            <p className="description">Understand feature importance</p>
          </div>

          <div className="arrow">→</div>

          <div className="step">
            <div className="step-number">4</div>
            <h4>Deploy</h4>
            <p><code>nexora serve model.nx --port 8000</code></p>
            <p className="description">Start REST API in production</p>
          </div>
        </div>
      </section>

      {/* Getting Started Section */}
      <section className="getting-started">
        <h2>Getting Started</h2>
        <div className="guide-steps">
          <div className="guide-step">
            <h4>Step 1: Install</h4>
            <pre><code>pip install nexora-prediction</code></pre>
          </div>

          <div className="guide-step">
            <h4>Step 2: Run Interactive Wizard</h4>
            <pre><code>nexora wizard</code></pre>
          </div>

          <div className="guide-step">
            <h4>Step 3: Or Use Direct Commands</h4>
            <pre><code>{`nexora train data.csv --target price
nexora predict model.nx new_data.csv
nexora serve model.nx --port 8000`}</code></pre>
          </div>

          <div className="guide-step">
            <h4>Step 4: Check Out Examples</h4>
            <pre><code>{`# View saved sessions
nexora history --limit 10

# Get model leaderboard
nexora compare model.nx

# Generate report
nexora report model.nx --format pdf`}</code></pre>
          </div>
        </div>
      </section>

      {/* Python API Section */}
      <section className="python-api">
        <h2>Python API</h2>
        <div className="api-example">
          <pre><code>{`from nexora import Nexora
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
report.to_html('report.html')`}</code></pre>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>Documentation</h4>
            <a href="/docs/quick-start">Quick Start</a>
            <a href="/docs/cli-features">CLI Features</a>
            <a href="/docs/completion-status">Status</a>
          </div>

          <div className="footer-section">
            <h4>Resources</h4>
            <a href="https://github.com/jeet2005/nexora">GitHub</a>
            <a href="https://github.com/jeet2005/nexora/issues">Issues</a>
            <a href="https://github.com/jeet2005/nexora/discussions">Discussions</a>
          </div>

          <div className="footer-section">
            <h4>Project</h4>
            <a href="/docs/completion-report">Completion Report</a>
            <a href="/docs/roadmap">Roadmap</a>
            <a href="https://github.com/jeet2005/nexora/blob/main/LICENSE">License</a>
          </div>

          <div className="footer-section">
            <h4>Support</h4>
            <a href="https://github.com/jeet2005/nexora/blob/main/CONTRIBUTING.md">Contributing</a>
            <a href="https://github.com/jeet2005/nexora/blob/main/CODE_OF_CONDUCT.md">Code of Conduct</a>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 Nexora. Autonomous AI Predictive Analytics Platform.</p>
          <p>Built with Python, FastAPI, React, and machine learning excellence.</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
