import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { FileText, Download } from 'lucide-react';

export const Reports = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data: any = await api.get('/reports');
        setReports(data.items || data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const handleDownload = async (id: string) => {
    try {
      const data: any = await api.get(`/reports/download/${id}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Download failed');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading reports...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        Verification Reports
      </h2>
      
      <div className="glass-card overflow-hidden">
        {reports.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No reports generated yet.</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-slate-800/50 border-b border-glass-border">
              <tr>
                <th className="p-4 font-medium text-slate-300">Report ID</th>
                <th className="p-4 font-medium text-slate-300">Verification ID</th>
                <th className="p-4 font-medium text-slate-300">Date Generated</th>
                <th className="p-4 font-medium text-slate-300 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 flex items-center gap-3 font-mono text-sm">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <span className="text-slate-200">{report.id.substring(0, 8)}...</span>
                  </td>
                  <td className="p-4 font-mono text-slate-400 text-sm">
                    {report.verification_id?.substring(0, 8)}...
                  </td>
                  <td className="p-4 text-slate-400 text-sm">
                    {new Date(report.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4 flex justify-end gap-2">
                    <button onClick={() => handleDownload(report.id)} className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors" title="Download JSON">
                      <Download className="w-4 h-4" />
                    </button>
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
