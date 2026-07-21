import { motion } from 'framer-motion';
import {
  Download as DownloadIcon,
  Monitor,
  HardDrive,
  Cpu,
  Shield,
  Zap,
  Battery,
  DownloadCloud,
  CheckCircle2,
  Globe,
  Lock,
  Server,
  ArrowRight,
  Terminal,
  ChevronDown,
  ChevronUp,
  Laptop,
} from 'lucide-react';
import NexoraLogo from '../components/NexoraLogo';
import { useState } from 'react';

const GITHUB_RELEASE = 'https://github.com/jeet2005/Nexora/releases/download/v1.0.1/Nexora.Setup.1.0.1.exe';

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  }),
};

const DESKTOP_FEATURES = [
  {
    icon: Shield,
    title: 'CyberShield — Local Threat Detection',
    desc: 'Real-time network anomaly scoring powered by your own CPU. Streams live traffic events, scores them with an Isolation Forest model, and visualises threats on an interactive geo-map — all without sending a single packet to the cloud.',
  },
  {
    icon: Terminal,
    title: 'Ollama LLM Chat — On-Device AI',
    desc: 'Ask plain-English questions about your datasets and models. Ollama launches automatically with the app and serves open-weight models (Phi-3 Mini, LLaMA 3, Mistral) directly on your hardware. Your prompts and data stay on your machine.',
  },
  {
    icon: Server,
    title: 'Full Backend Bundled',
    desc: 'The desktop app ships with everything you need: the FastAPI backend, ML pipeline, preprocessing engine, training arena, prediction studio, and report generator — all running locally on http://localhost:8000.',
  },
  {
    icon: Lock,
    title: 'Zero Cloud Compute',
    desc: 'Training, inference, explainability, and drift monitoring all run on your own CPU/GPU. No API keys, no metered billing, no data leaving your network. Perfect for sensitive enterprise and research datasets.',
  },
];

const COMPARISON = [
  { feature: 'Dataset Upload & Profiling', web: true, desktop: true },
  { feature: 'Model Training & Registry', web: true, desktop: true },
  { feature: 'Predictions & Batch Scoring', web: true, desktop: true },
  { feature: 'Explainability & Reports', web: true, desktop: true },
  { feature: 'Community & Leaderboard', web: true, desktop: true },
  { feature: 'CyberShield Threat Detection', web: false, desktop: true },
  { feature: 'Ollama Local LLM Chat', web: false, desktop: true },
  { feature: 'Offline Mode (No Internet)', web: false, desktop: true },
  { feature: 'Zero Cloud Compute Costs', web: false, desktop: true },
  { feature: 'Full Data Privacy', web: false, desktop: true },
];

const INSTALL_STEPS = [
  {
    step: '1',
    title: 'Download the Installer',
    desc: 'Click the download button above to grab the latest Nexora Setup (.exe) from GitHub Releases.',
  },
  {
    step: '2',
    title: 'Run the Installer',
    desc: 'Double-click the downloaded file. Windows Defender may show a SmartScreen warning — click "More info" → "Run anyway". The app installs in under 30 seconds.',
  },
  {
    step: '3',
    title: 'Install Ollama (Optional)',
    desc: 'For local AI chat, download Ollama from ollama.com and install it. Nexora will automatically start and manage Ollama every time you open the app.',
  },
  {
    step: '4',
    title: 'Start Your Backend',
    desc: 'Open a terminal in the Nexora project folder and run the Python backend (python main.py). The desktop app connects to it on localhost:8000.',
  },
];

const FAQ = [
  {
    q: 'Do I need an internet connection?',
    a: 'Only for the initial sign-in via Firebase Authentication. After that, all ML training, predictions, CyberShield monitoring, and Ollama chat work completely offline.',
  },
  {
    q: 'Is the desktop app free?',
    a: 'Yes. Nexora Desktop is free and open-source. You can view the full source code on GitHub.',
  },
  {
    q: 'Which Ollama models are supported?',
    a: 'Any model Ollama supports — Phi-3 Mini (recommended, 2.3 GB), LLaMA 3 8B, Mistral 7B, Gemma 2, and more. Run "ollama pull phi3:mini" to get started.',
  },
  {
    q: 'Will it slow down my computer?',
    a: 'The desktop app is ~425 MB as it bundles the complete Python ML backend and pre-packaged runtime environment. LLM models use RAM only when actively chatting. CyberShield uses minimal CPU.',
  },
  {
    q: 'How do I update to a new version?',
    a: 'Simply download the latest installer from the Releases page. It will overwrite the previous version while keeping your data intact.',
  },
];

export default function Download() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">

      {/* ── Hero ── */}
      <motion.section
        className="text-center mb-20"
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
      >
        <motion.div variants={fadeUp} custom={0} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-nexora-primary/10 text-nexora-primary text-sm font-medium mb-6">
          <Laptop size={14} /> v1.0.1 — Windows Available
        </motion.div>

        <motion.h1 variants={fadeUp} custom={1} className="text-4xl md:text-5xl lg:text-6xl font-display font-bold text-gray-900 mb-6 leading-tight">
          Nexora Desktop
        </motion.h1>

        <motion.p variants={fadeUp} custom={2} className="text-lg md:text-xl text-nexora-dark/60 max-w-3xl mx-auto mb-10 leading-relaxed">
          Everything you love about the web platform, plus CyberShield and Ollama running natively on your hardware.
          Complete privacy. Zero cloud costs. One installer.
        </motion.p>

        <motion.div variants={fadeUp} custom={3} className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href={GITHUB_RELEASE}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary py-3.5 px-8 text-base flex items-center justify-center gap-2 shadow-xl shadow-nexora-primary/20 hover:scale-105 transition-transform"
          >
            <DownloadIcon size={20} />
            Download for Windows
          </a>
          <div className="flex gap-3">
            <button disabled className="btn-outline py-3 px-5 text-sm flex flex-col items-center justify-center gap-0.5 opacity-40 cursor-not-allowed border-dashed">
              <span className="flex items-center gap-1.5">
                <DownloadIcon size={14} /> macOS
              </span>
              <span className="text-[10px] text-gray-400">Coming soon</span>
            </button>
            <button disabled className="btn-outline py-3 px-5 text-sm flex flex-col items-center justify-center gap-0.5 opacity-40 cursor-not-allowed border-dashed">
              <span className="flex items-center gap-1.5">
                <DownloadIcon size={14} /> Linux
              </span>
              <span className="text-[10px] text-gray-400">Coming soon</span>
            </button>
          </div>
        </motion.div>

        <motion.p variants={fadeUp} custom={4} className="text-xs text-gray-400 mt-4">
          ~425 MB · Windows 10/11 (64-bit) · Full Python Backend Bundled
        </motion.p>
      </motion.section>

      {/* ── Desktop-Only Features ── */}
      <section className="mb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-gray-900 mb-3">What Makes Desktop Special</h2>
          <p className="text-gray-500 max-w-xl mx-auto">Features that require local hardware access and aren't available on the web version.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {DESKTOP_FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              className="glass p-6 rounded-2xl border border-nexora-border hover:border-nexora-primary/30 transition-colors group"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
            >
              <div className="w-10 h-10 rounded-xl bg-nexora-primary/10 text-nexora-primary flex items-center justify-center mb-4 group-hover:bg-nexora-primary group-hover:text-white transition-colors">
                <f.icon size={20} />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Web vs Desktop Comparison ── */}
      <section className="mb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-gray-900 mb-3">Web vs Desktop</h2>
          <p className="text-gray-500">Both share the same core. Desktop unlocks local-only capabilities.</p>
        </div>
        <div className="glass rounded-2xl border border-nexora-border overflow-hidden max-w-3xl mx-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-nexora-border bg-gray-50/50">
                <th className="py-4 px-6 font-semibold text-gray-700 text-sm">Feature</th>
                <th className="py-4 px-4 font-semibold text-gray-700 text-sm text-center">
                  <div className="flex items-center justify-center gap-1.5"><Globe size={14} /> Web</div>
                </th>
                <th className="py-4 px-4 font-semibold text-gray-700 text-sm text-center">
                  <div className="flex items-center justify-center gap-1.5"><Monitor size={14} /> Desktop</div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-sm">
              {COMPARISON.map((row) => (
                <tr key={row.feature} className="hover:bg-gray-50/50 transition-colors">
                  <td className="py-3 px-6 text-gray-700">{row.feature}</td>
                  <td className="py-3 px-4 text-center">
                    {row.web ? (
                      <CheckCircle2 size={16} className="text-nexora-primary mx-auto" />
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <CheckCircle2 size={16} className="text-nexora-primary mx-auto" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Pros & Cons ── */}
      <section className="mb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="glass p-8 rounded-2xl border border-green-200/60 bg-gradient-to-br from-green-50/40 to-transparent">
            <h2 className="text-xl font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Zap className="text-green-500" size={20} /> Advantages
            </h2>
            <ul className="space-y-4">
              {[
                { icon: Shield, title: 'Complete Privacy', desc: 'Your data, models, and prompts never leave your machine.' },
                { icon: DownloadCloud, title: 'All-in-One Install', desc: 'Ollama auto-starts with the app. No manual setup needed.' },
                { icon: Zap, title: 'No API Costs', desc: 'Run unlimited training, predictions, and chat sessions for free.' },
              ].map((item) => (
                <li key={item.title} className="flex gap-3">
                  <item.icon className="text-green-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <strong className="block text-gray-900 text-sm">{item.title}</strong>
                    <span className="text-gray-500 text-xs">{item.desc}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div className="glass p-8 rounded-2xl border border-amber-200/60 bg-gradient-to-br from-amber-50/40 to-transparent">
            <h2 className="text-xl font-bold text-gray-900 mb-5 flex items-center gap-2">
              <Battery className="text-amber-500" size={20} /> Trade-offs
            </h2>
            <ul className="space-y-4">
              {[
                { icon: Cpu, title: 'Hardware Dependent', desc: 'LLM speed and training time depend on your CPU, GPU, and RAM.' },
                { icon: HardDrive, title: 'Storage Requirement', desc: 'LLM models need 2–8 GB of disk space each.' },
                { icon: Battery, title: 'Resource Usage', desc: 'Active LLM inference uses significant RAM and may drain laptop batteries faster.' },
              ].map((item) => (
                <li key={item.title} className="flex gap-3">
                  <item.icon className="text-amber-500 shrink-0 mt-0.5" size={18} />
                  <div>
                    <strong className="block text-gray-900 text-sm">{item.title}</strong>
                    <span className="text-gray-500 text-xs">{item.desc}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── Installation Steps ── */}
      <section className="mb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-gray-900 mb-3">Installation</h2>
          <p className="text-gray-500">Up and running in under 2 minutes.</p>
        </div>
        <div className="max-w-2xl mx-auto space-y-4">
          {INSTALL_STEPS.map((s, i) => (
            <motion.div
              key={s.step}
              className="flex gap-5 items-start"
              initial={{ opacity: 0, x: -16 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="w-9 h-9 rounded-full bg-nexora-primary text-white font-bold text-sm flex items-center justify-center shrink-0 mt-0.5">
                {s.step}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── System Requirements ── */}
      <section className="mb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-gray-900 mb-3">System Requirements</h2>
          <p className="text-gray-500">Minimum specs for a smooth experience.</p>
        </div>
        <div className="glass rounded-2xl border border-nexora-border overflow-hidden max-w-3xl mx-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-nexora-border bg-gray-50/50">
                <th className="py-4 px-6 font-semibold text-gray-700 text-sm">Component</th>
                <th className="py-4 px-4 font-semibold text-gray-700 text-sm">Windows</th>
                <th className="py-4 px-4 font-semibold text-gray-700 text-sm">macOS</th>
                <th className="py-4 px-4 font-semibold text-gray-700 text-sm">Linux</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-sm">
              <tr>
                <td className="py-3.5 px-6 font-medium text-gray-900 flex items-center gap-2"><Monitor size={14} className="text-gray-400" /> OS</td>
                <td className="py-3.5 px-4 text-gray-600">Windows 10/11 (64-bit)</td>
                <td className="py-3.5 px-4 text-gray-600">macOS 12+ (Intel / Apple Silicon)</td>
                <td className="py-3.5 px-4 text-gray-600">Ubuntu 20.04+, Fedora 34+</td>
              </tr>
              <tr>
                <td className="py-3.5 px-6 font-medium text-gray-900 flex items-center gap-2"><Cpu size={14} className="text-gray-400" /> RAM</td>
                <td className="py-3.5 px-4 text-gray-600">8 GB min · 16 GB rec.</td>
                <td className="py-3.5 px-4 text-gray-600">8 GB min · 16 GB rec.</td>
                <td className="py-3.5 px-4 text-gray-600">8 GB min · 16 GB rec.</td>
              </tr>
              <tr>
                <td className="py-3.5 px-6 font-medium text-gray-900 flex items-center gap-2"><Cpu size={14} className="text-gray-400" /> Processor</td>
                <td className="py-3.5 px-4 text-gray-600">Intel i5 / AMD Ryzen 5</td>
                <td className="py-3.5 px-4 text-gray-600">M1/M2/M3 or Intel i5</td>
                <td className="py-3.5 px-4 text-gray-600">Intel i5 / AMD Ryzen 5</td>
              </tr>
              <tr>
                <td className="py-3.5 px-6 font-medium text-gray-900 flex items-center gap-2"><HardDrive size={14} className="text-gray-400" /> Storage</td>
                <td className="py-3.5 px-4 text-gray-600">20 GB available SSD</td>
                <td className="py-3.5 px-4 text-gray-600">20 GB available SSD</td>
                <td className="py-3.5 px-4 text-gray-600">20 GB available SSD</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="mb-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-gray-900 mb-3">Frequently Asked Questions</h2>
        </div>
        <div className="max-w-2xl mx-auto space-y-3">
          {FAQ.map((item, i) => (
            <div
              key={i}
              className="glass rounded-xl border border-nexora-border overflow-hidden"
            >
              <button
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50/50 transition-colors"
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
              >
                <span className="font-medium text-gray-900 text-sm">{item.q}</span>
                {openFaq === i ? (
                  <ChevronUp size={16} className="text-gray-400 shrink-0" />
                ) : (
                  <ChevronDown size={16} className="text-gray-400 shrink-0" />
                )}
              </button>
              {openFaq === i && (
                <div className="px-6 pb-4 text-sm text-gray-500 leading-relaxed border-t border-gray-100 pt-3">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section className="text-center">
        <div className="glass rounded-2xl border border-nexora-border p-10 bg-gradient-to-br from-nexora-primary/5 to-transparent max-w-2xl mx-auto">
          <NexoraLogo size="md" className="text-nexora-primary mx-auto mb-4" />
          <h3 className="text-2xl font-display font-bold text-gray-900 mb-3">Ready to go local?</h3>
          <p className="text-gray-500 mb-6 text-sm">Download Nexora Desktop and take full control of your data pipeline.</p>
          <a
            href={GITHUB_RELEASE}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary py-3 px-8 text-base inline-flex items-center gap-2 shadow-xl shadow-nexora-primary/20 hover:scale-105 transition-transform"
          >
            <DownloadIcon size={18} />
            Download for Windows
            <ArrowRight size={16} />
          </a>
        </div>
      </section>
    </div>
  );
}
