import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ShieldCheck, Clock, XCircle, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Verifications = () => {
  const [verifications, setVerifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVerifications = async () => {
      try {
        const data: any = await api.get('/verifications');
        setVerifications(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchVerifications();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <ShieldCheck className="w-5 h-5 text-green-400" />;
      case 'PROCESSING': return <Clock className="w-5 h-5 text-blue-400 animate-pulse" />;
      case 'FAILED': return <XCircle className="w-5 h-5 text-red-400" />;
      default: return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading verifications...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        Verification History
      </h2>
      
      <div className="glass-card overflow-hidden">
        {verifications.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No verifications found.</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-slate-800/50 border-b border-glass-border">
              <tr>
                <th className="p-4 font-medium text-slate-300">ID</th>
                <th className="p-4 font-medium text-slate-300">Status</th>
                <th className="p-4 font-medium text-slate-300">Trust Score</th>
                <th className="p-4 font-medium text-slate-300">Date</th>
                <th className="p-4 font-medium text-slate-300 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border">
              {verifications.map((v) => (
                <tr key={v.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-mono text-sm text-slate-400 truncate max-w-[150px]">
                    {v.id}
                  </td>
                  <td className="p-4 flex items-center gap-2">
                    {getStatusIcon(v.status)}
                    <span className="font-medium text-slate-200">{v.status}</span>
                  </td>
                  <td className="p-4">
                    <span className={`font-bold ${v.trust_score >= 0.8 ? 'text-green-400' : v.trust_score >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {v.trust_score !== null ? `${Math.round(v.trust_score * 100)}%` : 'N/A'}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400 text-sm">
                    {new Date(v.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4 flex justify-end gap-2">
                    <Link to={`/verifications/${v.id}`} className="px-3 py-1 bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 rounded-lg transition-colors text-sm font-medium">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
