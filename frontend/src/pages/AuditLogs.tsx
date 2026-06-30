import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { User, Database, Eye } from 'lucide-react';

export const AuditLogs = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data: any = await api.get('/audit-logs');
        setLogs(data.items || data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getActionColor = (action: string) => {
    if (action.includes('FAILED') || action.includes('DELETE')) return 'text-red-400 bg-red-400/10 border-red-400/20';
    if (action.includes('STARTED') || action.includes('UPLOAD')) return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    if (action.includes('COMPLETED') || action.includes('GENERATED')) return 'text-green-400 bg-green-400/10 border-green-400/20';
    return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading audit logs...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        System Audit Logs
      </h2>
      
      <div className="glass-card overflow-hidden">
        {logs.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No audit logs found.</div>
        ) : (
          <div className="space-y-4">
            {logs.map((log) => (
              <div key={log.id} className="flex flex-col md:flex-row gap-4 p-4 border border-glass-border rounded-xl bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 text-xs font-bold rounded border ${getActionColor(log.action)}`}>
                      {log.action}
                    </span>
                    <span className="text-sm text-slate-400 font-mono">{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-sm text-slate-300">
                    <span className="flex items-center gap-1"><User className="w-4 h-4 text-slate-500" /> {log.user_id.substring(0,8)}...</span>
                    <span className="flex items-center gap-1"><Database className="w-4 h-4 text-slate-500" /> {log.resource_type}: {log.resource_id?.substring(0,8) || 'N/A'}</span>
                    <span className="flex items-center gap-1"><Eye className="w-4 h-4 text-slate-500" /> IP: {log.ip_address}</span>
                  </div>
                </div>
                
                {log.details && Object.keys(log.details).length > 0 && (
                  <div className="md:w-1/3 bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                    <pre className="text-xs text-slate-400 font-mono overflow-auto max-h-24">
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
