import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Activity, ShieldAlert, CheckCircle, Database } from 'lucide-react';

interface DashboardMetrics {
  total_assets: number;
  total_verifications: number;
  completed_verifications: number;
  failed_verifications: number;
  average_trust_score: number;
  total_reports: number;
}

export const Dashboard = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const data: any = await api.get('/analytics/dashboard');
        setMetrics(data);
      } catch (err) {
        console.error('Failed to fetch dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-pulse flex gap-2"><div className="w-4 h-4 bg-blue-500 rounded-full"></div><div className="w-4 h-4 bg-purple-500 rounded-full"></div><div className="w-4 h-4 bg-pink-500 rounded-full"></div></div></div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        Overview
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card flex items-center gap-4">
          <div className="p-3 bg-blue-500/20 rounded-xl text-blue-400"><Database className="w-6 h-6" /></div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Total Assets</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_assets || 0}</p>
          </div>
        </div>
        
        <div className="glass-card flex items-center gap-4">
          <div className="p-3 bg-purple-500/20 rounded-xl text-purple-400"><Activity className="w-6 h-6" /></div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Verifications</p>
            <p className="text-2xl font-bold text-white">{metrics?.total_verifications || 0}</p>
          </div>
        </div>

        <div className="glass-card flex items-center gap-4">
          <div className="p-3 bg-green-500/20 rounded-xl text-green-400"><CheckCircle className="w-6 h-6" /></div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Completed</p>
            <p className="text-2xl font-bold text-white">{metrics?.completed_verifications || 0}</p>
          </div>
        </div>

        <div className="glass-card flex items-center gap-4">
          <div className="p-3 bg-red-500/20 rounded-xl text-red-400"><ShieldAlert className="w-6 h-6" /></div>
          <div>
            <p className="text-sm text-slate-400 font-medium">Failed</p>
            <p className="text-2xl font-bold text-white">{metrics?.failed_verifications || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="glass-card h-64 flex flex-col justify-center items-center">
          <h3 className="text-lg font-semibold text-slate-300 mb-4">Average Trust Score</h3>
          <div className="relative w-32 h-32 flex items-center justify-center rounded-full border-4 border-slate-700">
            <span className="text-4xl font-bold text-blue-400">{Math.round((metrics?.average_trust_score || 0) * 100)}%</span>
          </div>
        </div>
        
        <div className="glass-card h-64 flex flex-col justify-center items-center">
          <h3 className="text-lg font-semibold text-slate-300 mb-4">Reports Generated</h3>
          <span className="text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-green-400 to-emerald-600">
            {metrics?.total_reports || 0}
          </span>
        </div>
      </div>
    </div>
  );
};
