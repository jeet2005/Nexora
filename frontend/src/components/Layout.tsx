import { Outlet, Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import NexoraLogo from "./NexoraLogo";

export default function Layout() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="min-h-screen flex flex-col bg-nexora-bg relative overflow-x-hidden">
      {/* Animated background gradient */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-nexora-accent/10 to-transparent rounded-full blur-3xl animate-float"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-tl from-nexora-accent/5 to-transparent rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }}></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 inset-x-0 z-50 border-b border-nexora-border bg-white/95 backdrop-blur-md">
        <motion.div
          className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between relative z-10"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <Link to="/" className="flex items-center gap-2 group text-nexora-dark hover:text-nexora-accent transition-colors duration-300">
            <NexoraLogo size="sm" />
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm text-nexora-dark/60">

            {isHome && (
              <>
                <a href="#how-it-works" className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium">
                  How It Works
                </a>
                <a href="#features" className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium">
                  Features
                </a>
                <a href="#upload" className="hover:text-nexora-accent transition-colors duration-300 underline-animate font-medium">
                  Upload
                </a>
              </>
            )}
          </nav>

          <Link to="/" className="btn-ghost text-sm group font-medium">
            <span className="group-hover:translate-x-0.5 transition-transform duration-200">New dataset</span>
          </Link>
        </motion.div>
      </header>

      <main className="flex-1 pt-16 relative z-10">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-nexora-border py-8 text-center text-sm text-nexora-dark/40 relative z-10">
        <div className="flex items-center justify-center gap-2 mb-1">
          <NexoraLogo size="sm" className="text-nexora-accent/50" />
        </div>
        <p className="font-medium">Autonomous AI Predictive Analytics Platform</p>
      </footer>
    </div>
  );
}
