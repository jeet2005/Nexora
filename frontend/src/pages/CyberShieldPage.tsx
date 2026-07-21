import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import {
  Shield,
  Activity,
  AlertTriangle,
  Zap,
  TrendingUp,
  Wifi,
  WifiOff,
  Download,
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useCyberStream } from '../hooks/useCyberStream';
import type { ScoredEvent } from '../hooks/useCyberStream';
import './CyberShield.css';

export default function CyberShieldPage() {
  const [rowsPerSec, setRowsPerSec] = useState(10);
  const [showToast, setShowToast] = useState(false);

  const handleCritical = useCallback(() => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 8000);
  }, []);

  const { rows, rollingData, stats, connected, isCritical } = useCyberStream({
    rowsPerSec,
    onCritical: handleCritical,
  });

  const exportPDF = useCallback(() => {
    const element = document.getElementById('cybershield-export-area');
    if (!element) return;

    import('html2pdf.js').then((html2pdf) => {
      const opt = {
        margin: 10,
        filename: 'cybershield-incident-report.pdf',
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false, windowWidth: 1200 },
        jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'landscape' as const },
      };

      html2pdf.default().set(opt).from(element).save();
    });
  }, []);

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)}MB`;
    if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)}KB`;
    return `${bytes}B`;
  };

  return (
    <div className="cybershield-page">
      <div className="cyber-content" id="cybershield-export-area">
        {/* ═══ Header ═══ */}
        <header className="cyber-header">
          <div className="cyber-header-left">
            <motion.div
              className="cyber-shield-icon"
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
            >
              <Shield size={26} color="#fff" strokeWidth={2.5} />
            </motion.div>
            <div>
              <h1 className="cyber-title">CYBERSHIELD</h1>
              <p className="cyber-subtitle">Real-Time Network Threat Detection</p>
            </div>
          </div>

          <div className="cyber-header-right">
            <div className="cyber-status">
              <div className={`cyber-status-dot ${connected ? 'connected' : 'disconnected'}`} />
              {connected ? (
                <span style={{ color: 'var(--cyber-green)' }}>
                  <Wifi
                    size={13}
                    style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}
                  />
                  CONNECTED
                </span>
              ) : (
                <span style={{ color: 'var(--cyber-red)' }}>
                  <WifiOff
                    size={13}
                    style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }}
                  />
                  DISCONNECTED
                </span>
              )}
            </div>

            <div className="cyber-speed-control">
              <span>SPEED</span>
              <input
                type="range"
                min={1}
                max={50}
                value={rowsPerSec}
                onChange={(e) => setRowsPerSec(Number(e.target.value))}
              />
              <span className="cyber-speed-value">{rowsPerSec}</span>
              <span>r/s</span>
            </div>

            <button className="cyber-export-btn" onClick={exportPDF}>
              <Download size={14} /> EXPORT PDF
            </button>
          </div>
        </header>

        {/* ═══ Maintenance / Update Banner ═══ */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            margin: '0 0 24px 0',
            padding: '14px 20px',
            borderRadius: '12px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            color: '#fbbf24',
            fontSize: '13.5px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            fontFamily: 'Inter, system-ui, sans-serif',
            backdropFilter: 'blur(8px)',
          }}
        >
          <span style={{ fontSize: '20px' }}>☕</span>
          <div>
            <strong style={{ color: '#fef08a', display: 'block', marginBottom: '2px', fontSize: '14px' }}>
              CyberShield Status
            </strong>
            We'll be back soon... Our people are working on it so take a chill pill! ☕
          </div>
        </motion.div>

        {/* ═══ Stats Cards ═══ */}
        <div className="cyber-stats-grid">
          <StatCard
            label="Total Events"
            value={stats.totalEvents.toLocaleString()}
            color="cyan"
            icon={<Activity size={18} />}
            delay={0}
          />
          <StatCard
            label="Anomaly Rate"
            value={`${stats.anomalyRate}`}
            unit="%"
            color={stats.anomalyRate >= 80 ? 'red' : stats.anomalyRate >= 40 ? 'amber' : 'green'}
            icon={<TrendingUp size={18} />}
            delay={0.05}
          />
          <StatCard
            label="Threats Detected"
            value={stats.threatsDetected.toLocaleString()}
            color="red"
            icon={<AlertTriangle size={18} />}
            delay={0.1}
          />
          <StatCard
            label="Avg Score"
            value={stats.avgScore.toFixed(2)}
            color="amber"
            icon={<Zap size={18} />}
            delay={0.15}
          />
        </div>

        {/* ═══ Live Chart ═══ */}
        <motion.div
          className="cyber-chart-panel"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="cyber-chart-title">
            <span className="live-dot" />
            ANOMALY RATE — 60s ROLLING WINDOW
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={rollingData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={isCritical ? '#ff1744' : '#00e5ff'}
                    stopOpacity={0.5}
                  />
                  <stop
                    offset="50%"
                    stopColor={isCritical ? '#ff1744' : '#00e5ff'}
                    stopOpacity={0.15}
                  />
                  <stop
                    offset="100%"
                    stopColor={isCritical ? '#ff1744' : '#00e5ff'}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 6"
                stroke="rgba(255,255,255,0.04)"
                vertical={false}
              />
              <XAxis
                dataKey="time"
                tick={{ fill: '#546e7a', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#546e7a', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(12, 18, 32, 0.95)',
                  border: '1px solid rgba(0, 229, 255, 0.2)',
                  borderRadius: 10,
                  fontFamily: 'JetBrains Mono',
                  fontSize: 12,
                  color: '#e8eaf6',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                }}
                formatter={(value: number) => [`${value}%`, 'Anomaly Rate']}
                labelStyle={{ color: '#546e7a' }}
              />
              <ReferenceLine
                y={80}
                stroke="#ff1744"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
                label={{
                  value: 'CRITICAL',
                  fill: '#ff1744',
                  fontSize: 10,
                  fontFamily: 'JetBrains Mono',
                  position: 'insideTopRight',
                }}
              />
              <Area
                type="monotone"
                dataKey="rate"
                stroke={isCritical ? '#ff1744' : '#00e5ff'}
                strokeWidth={2}
                fill="url(#anomalyGradient)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* ═══ Live Map ═══ */}
        <motion.div
          className="cyber-map-panel"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          style={{
            marginTop: 20,
            marginBottom: 20,
            borderRadius: 12,
            overflow: 'hidden',
            border: '1px solid rgba(0, 229, 255, 0.15)',
            height: 350,
          }}
        >
          <div
            className="cyber-chart-title"
            style={{
              padding: '12px 16px',
              background: 'rgba(12, 18, 32, 0.9)',
              borderBottom: '1px solid rgba(0, 229, 255, 0.15)',
            }}
          >
            <span className="live-dot" />
            LIVE SOURCE MAP
          </div>
          <MapContainer
            center={[20, 0]}
            zoom={2}
            style={{ height: '100%', width: '100%', background: '#0a0f1c' }}
            zoomControl={false}
            attributionControl={false}
          >
            <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
            {rows
              .filter((r) => r.raw.src_lat != null && r.raw.src_lon != null)
              .map((row) => {
                const lat = row.raw.src_lat!;
                const lon = row.raw.src_lon!;
                const isDanger = row.threat_level === 'HIGH' || row.threat_level === 'CRITICAL';

                return (
                  <CircleMarker
                    key={row.row_id}
                    center={[lat, lon]}
                    radius={isDanger ? 8 : 4}
                    fillColor={isDanger ? '#ff1744' : '#00e5ff'}
                    color={isDanger ? '#ff1744' : '#00e5ff'}
                    weight={1}
                    opacity={0.8}
                    fillOpacity={0.6}
                  >
                    <Popup>
                      <div
                        style={{
                          fontFamily: 'JetBrains Mono',
                          fontSize: 11,
                          background: 'rgba(12,18,32,0.9)',
                          color: '#fff',
                          padding: 8,
                          borderRadius: 4,
                        }}
                      >
                        <strong>IP:</strong> {row.raw.src_ip}
                        <br />
                        <strong>Threat:</strong>{' '}
                        <span style={{ color: isDanger ? '#ff1744' : '#00e5ff' }}>
                          {row.threat_level}
                        </span>
                        <br />
                        <strong>Score:</strong> {row.anomaly_score.toFixed(2)}
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
          </MapContainer>
        </motion.div>

        {/* ═══ Data Table ═══ */}
        <motion.div
          className="cyber-table-panel"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="cyber-table-header">
            <span className="cyber-table-title">
              <Activity
                size={14}
                style={{
                  display: 'inline',
                  marginRight: 8,
                  verticalAlign: 'middle',
                  color: 'var(--cyber-cyan)',
                }}
              />
              LIVE NETWORK EVENTS
            </span>
            <span className="cyber-table-count">{rows.length} / 50 rows</span>
          </div>
          <div className="cyber-table-scroll">
            <table className="cyber-table" id="cyber-events-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Source IP</th>
                  <th>Dest IP</th>
                  <th>Protocol</th>
                  <th>Bytes</th>
                  <th>Score</th>
                  <th>Threat</th>
                  <th>Top Features</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {rows.map((row) => (
                    <TableRow
                      key={row.row_id}
                      row={row}
                      formatTimestamp={formatTimestamp}
                      formatBytes={formatBytes}
                    />
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>

      {/* ═══ Critical Toast ═══ */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            className="cyber-toast"
            initial={{ opacity: 0, x: 60, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 60, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            <AlertTriangle className="toast-icon" size={22} />
            <div>
              <div style={{ fontWeight: 700, marginBottom: 2 }}>CRITICAL ALERT</div>
              <div style={{ fontSize: 11, opacity: 0.8 }}>
                Anomaly rate exceeded 80% threshold in 60s window
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

function StatCard({
  label,
  value,
  unit,
  color,
  icon,
  delay = 0,
}: {
  label: string;
  value: string;
  unit?: string;
  color: string;
  icon: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      className={`cyber-stat-card ${color}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="cyber-stat-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ color: `var(--cyber-${color})`, opacity: 0.8 }}>{icon}</span>
        {label}
      </div>
      <div className={`cyber-stat-value ${color}`}>
        {value}
        {unit && <span className="cyber-stat-unit">{unit}</span>}
      </div>
    </motion.div>
  );
}

function TableRow({
  row,
  formatTimestamp,
  formatBytes,
}: {
  row: ScoredEvent;
  formatTimestamp: (ts: string) => string;
  formatBytes: (b: number) => string;
}) {
  return (
    <motion.tr
      className={`threat-${row.threat_level}`}
      initial={{ opacity: 0, x: -20, height: 0 }}
      animate={{ opacity: 1, x: 0, height: 'auto' }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      layout
    >
      <td>{formatTimestamp(row.timestamp)}</td>
      <td>{row.raw.src_ip}</td>
      <td>{row.raw.dst_ip}</td>
      <td style={{ color: 'var(--cyber-cyan-dim)' }}>{row.raw.protocol}</td>
      <td>
        <span
          style={{
            color: row.raw.bytes_sent > 100000 ? 'var(--cyber-amber)' : 'var(--cyber-text-muted)',
          }}
        >
          ↑{formatBytes(row.raw.bytes_sent)}
        </span>{' '}
        <span style={{ color: 'var(--cyber-text-dim)' }}>
          ↓{formatBytes(row.raw.bytes_received)}
        </span>
      </td>
      <td>
        <span className={`score-badge ${row.threat_level}`}>{row.anomaly_score.toFixed(2)}</span>
      </td>
      <td>
        <span className={`score-badge ${row.threat_level}`}>{row.threat_level}</span>
      </td>
      <td>
        {row.top_features.map((f) => (
          <span key={f} className="feature-tag">
            {f}
          </span>
        ))}
      </td>
    </motion.tr>
  );
}
