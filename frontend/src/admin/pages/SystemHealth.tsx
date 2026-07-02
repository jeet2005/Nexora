import React, { useEffect, useState } from 'react';
import { adminApi, SystemHealthData } from '../../api/admin';
import { Activity, Server, Database, Globe, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';

export const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const data = await adminApi.getSystemHealth();
      setHealth(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / (3600 * 24));
    const hrs = Math.floor((seconds % (3600 * 24)) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hrs}h ${mins}m`;
  };

  const uptimeSeconds = health?.system?.uptime_seconds ?? null;

  const getStatusIcon = (status: string) => {
    if (status === 'healthy' || status === 'online') return <CheckCircle2 className="text-green-500" size={20} />;
    if (status === 'degraded') return <AlertTriangle className="text-yellow-500" size={20} />;
    return <AlertCircle className="text-red-500" size={20} />;
  };

  if (loading && !health) {
    return <div className="animate-pulse text-nexora-dark/50 p-8">Loading system metrics...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <Activity className="text-nexora-accent" size={24} />
          System Health
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* API Service */}
        <div className="glass p-6 rounded-2xl flex items-center gap-4">
          <div className="p-3 bg-nexora-accent/10 rounded-xl text-nexora-accent">
            <Server size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-nexora-dark/70 uppercase tracking-wider">Backend API</h3>
            <div className="flex items-center gap-2 mt-1">
              {getStatusIcon(health?.services?.api || 'offline')}
              <span className="font-medium capitalize">{health?.services?.api || 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Database */}
        <div className="glass p-6 rounded-2xl flex items-center gap-4">
          <div className="p-3 bg-nexora-accent/10 rounded-xl text-nexora-accent">
            <Database size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-nexora-dark/70 uppercase tracking-wider">MongoDB Cluster</h3>
            <div className="flex items-center gap-2 mt-1">
              {getStatusIcon(health?.services?.database || 'offline')}
              <span className="font-medium capitalize">{health?.services?.database || 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Frontend */}
        <div className="glass p-6 rounded-2xl flex items-center gap-4">
          <div className="p-3 bg-nexora-accent/10 rounded-xl text-nexora-accent">
            <Globe size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-nexora-dark/70 uppercase tracking-wider">Frontend App</h3>
            <div className="flex items-center gap-2 mt-1">
              {getStatusIcon(health?.services?.frontend || 'offline')}
              <span className="font-medium capitalize">{health?.services?.frontend || 'Unknown'}</span>
            </div>
          </div>
        </div>
      </div>

      <h2 className="text-lg font-semibold text-nexora-dark mt-8 mb-4">Host Metrics</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass p-6 rounded-2xl">
          <h3 className="text-sm font-semibold text-nexora-dark/70">CPU Usage</h3>
          <div className="text-3xl font-display font-bold mt-2">
            {health?.system?.cpu_percent?.toFixed(1) || 0}%
          </div>
        </div>
        <div className="glass p-6 rounded-2xl">
          <h3 className="text-sm font-semibold text-nexora-dark/70">Memory Usage</h3>
          <div className="text-3xl font-display font-bold mt-2">
            {health?.system?.memory_percent?.toFixed(1) || 0}%
          </div>
        </div>
        <div className="glass p-6 rounded-2xl">
          <h3 className="text-sm font-semibold text-nexora-dark/70">System Uptime</h3>
          <div className="text-xl font-display font-bold mt-2 pt-1">
            {uptimeSeconds !== null ? formatUptime(uptimeSeconds) : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
};
