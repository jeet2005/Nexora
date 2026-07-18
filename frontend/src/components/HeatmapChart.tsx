
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

// Simple heatmap placeholder using area chart
export default function HeatmapChart({ data }: { data: { date: string; contributions: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#5efc3b" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#5efc3b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="date" hide />
        <YAxis hide />
        <Tooltip />
        <Area type="monotone" dataKey="contributions" stroke="#5efc3b" fillOpacity={1} fill="url(#colorGrad)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
