import React, { useEffect, useState } from 'react';
import { adminApi } from '../../api/admin';
import { ClipboardList } from 'lucide-react';

export const AuditLog: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getAuditLog(100).then(data => {
      setLogs(data);
    }).catch(err => {
      console.error(err);
    }).finally(() => {
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-semibold text-nexora-dark flex items-center gap-2">
          <ClipboardList className="text-nexora-accent" size={24} />
          Audit Log
        </h1>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-nexora-dark/5 text-sm font-semibold text-nexora-dark/70">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Admin Email</th>
                <th className="px-6 py-4">Action</th>
                <th className="px-6 py-4">Resource ID</th>
                <th className="px-6 py-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-nexora-border">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-nexora-dark/50">
                    <div className="animate-pulse">Loading audit logs...</div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-nexora-dark/50">
                    No admin actions recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log, i) => (
                  <tr key={i} className="hover:bg-black/5 transition-colors">
                    <td className="px-6 py-4 text-sm text-nexora-dark/80 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 font-medium text-sm">{log.admin_email}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className="inline-flex items-center px-2 py-1 rounded bg-black/5 font-mono text-xs">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-sm text-nexora-dark/60">{log.resource_id || '-'}</td>
                    <td className="px-6 py-4 text-sm text-nexora-dark/80 max-w-xs truncate" title={log.details}>
                      {log.details || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
