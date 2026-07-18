import React, { useEffect, useState } from 'react';
import { adminApi } from '../../api/admin';
import { Database, Key, AlertTriangle, ShieldCheck, FileText, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    trainingJobs24h: 0,
    apiKeys: 0,
    driftAlerts: 0,
    health: 'unknown',
    totalUsers: 0,
  });
  const [growthData, setGrowthData] = useState<{ date: string; users: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [keys, drift, health, growth] = await Promise.all([
          adminApi.listApiKeys(),
          adminApi.getDriftAlerts(),
          adminApi.getSystemHealth(),
          adminApi.getUserGrowthStats(),
        ]);

        const openDrift = drift.filter((d: { status?: string }) => d.status !== 'resolved');

        setStats({
          trainingJobs24h: growth.training_jobs_24h ?? 0,
          apiKeys: keys.filter((k: { active?: boolean }) => k.active).length,
          driftAlerts: openDrift.length,
          health: health.status,
          totalUsers: growth.total ?? 0,
        });
        setGrowthData(growth.daily ?? []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return <div className="animate-pulse p-8">Loading dashboard metrics...</div>;
  }

  const chartData = growthData.map((d) => ({
    name: new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' }),
    users: d.users,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <ShieldCheck className="text-nexora-accent" size={24} />
          Admin Overview
        </h1>
        <span className="text-sm text-gray-500">{stats.totalUsers} total users</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Link to="/admin/datasets" className="glass p-6 rounded-2xl hover:bg-white/50 transition-colors block">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-nexora-dark/70">Training Jobs (24h)</h3>
            <Database className="text-nexora-accent" size={20} />
          </div>
          <div className="text-3xl font-display font-bold mt-4 text-nexora-dark">{stats.trainingJobs24h}</div>
        </Link>

        <Link to="/admin/keys" className="glass p-6 rounded-2xl hover:bg-white/50 transition-colors block">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-nexora-dark/70">Active API Keys</h3>
            <Key className="text-nexora-accent" size={20} />
          </div>
          <div className="text-3xl font-display font-bold mt-4 text-nexora-dark">{stats.apiKeys}</div>
        </Link>

        <Link to="/admin/drift" className="glass p-6 rounded-2xl hover:bg-white/50 transition-colors block">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-nexora-dark/70">Open Drift Alerts</h3>
            <AlertTriangle className={stats.driftAlerts > 0 ? 'text-red-500' : 'text-green-500'} size={20} />
          </div>
          <div className="text-3xl font-display font-bold mt-4 text-nexora-dark">{stats.driftAlerts}</div>
        </Link>

        <Link to="/admin/health" className="glass p-6 rounded-2xl hover:bg-white/50 transition-colors block">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-nexora-dark/70">System Health</h3>
            <Activity className={stats.health === 'healthy' ? 'text-green-500' : 'text-yellow-500'} size={20} />
          </div>
          <div className="text-3xl font-display font-bold mt-4 text-nexora-dark capitalize">{stats.health}</div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="glass p-8 rounded-2xl">
          <h2 className="text-xl font-display font-semibold mb-4 text-nexora-dark flex items-center gap-2">
            <FileText className="text-nexora-accent" size={20} />
            Quick Actions
          </h2>
          <div className="space-y-3">
            <Link to="/admin/content" className="block p-4 rounded-xl border border-nexora-border hover:border-nexora-accent/50 hover:bg-white/50 transition-all">
              <div className="font-semibold text-nexora-dark">Manage Site Content</div>
              <div className="text-sm text-nexora-dark/60 mt-1">Update announcement banners, roadmaps, and changelogs.</div>
            </Link>
            <Link to="/admin/users" className="block p-4 rounded-xl border border-nexora-border hover:border-nexora-accent/50 hover:bg-white/50 transition-all">
              <div className="font-semibold text-nexora-dark">View All Users</div>
              <div className="text-sm text-nexora-dark/60 mt-1">Browse registered users and their activity.</div>
            </Link>
            <Link to="/admin/feedback" className="block p-4 rounded-xl border border-nexora-border hover:border-nexora-accent/50 hover:bg-white/50 transition-all">
              <div className="font-semibold text-nexora-dark">Review Feedback</div>
              <div className="text-sm text-nexora-dark/60 mt-1">Review community ideas, report bugs, and assign badges.</div>
            </Link>
          </div>
        </div>

        <div className="glass p-8 rounded-2xl">
          <h2 className="text-xl font-display font-semibold mb-6 text-nexora-dark flex items-center gap-2">
            <Activity className="text-nexora-accent" size={20} />
            New Signups (Last 7 Days)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dx={-10} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                  itemStyle={{ color: '#10b981', fontWeight: 600 }}
                />
                <Area type="monotone" dataKey="users" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorUsers)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
