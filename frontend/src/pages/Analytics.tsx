import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BarChart3, PieChart, Activity } from 'lucide-react';

export const Analytics = () => {
  const [assetTypes, setAssetTypes] = useState<any>({});
  const [riskDist, setRiskDist] = useState<any>({});
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [assetData, riskData, trendData]: any = await Promise.all([
          api.get('/analytics/asset-types'),
          api.get('/analytics/risk-distribution'),
          api.get('/analytics/verification-trends')
        ]);
        setAssetTypes(assetData);
        setRiskDist(riskData);
        setTrends(trendData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading analytics...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        Advanced Analytics
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-blue-400" /> Asset Types
          </h3>
          <div className="space-y-4">
            {Object.entries(assetTypes).map(([type, count]: any) => (
              <div key={type} className="flex justify-between items-center border-b border-glass-border pb-2 last:border-0">
                <span className="text-slate-400">{type}</span>
                <span className="font-bold text-white bg-slate-800/50 px-3 py-1 rounded-full">{count}</span>
              </div>
            ))}
            {Object.keys(assetTypes).length === 0 && <p className="text-slate-500 text-sm">No data available.</p>}
          </div>
        </div>

        <div className="glass-card">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" /> Risk Distribution
          </h3>
          <div className="space-y-4">
            {Object.entries(riskDist).map(([risk, count]: any) => (
              <div key={risk} className="flex justify-between items-center border-b border-glass-border pb-2 last:border-0">
                <span className={`capitalize ${risk === 'high' ? 'text-red-400' : risk === 'medium' ? 'text-yellow-400' : 'text-green-400'}`}>
                  {risk} Risk
                </span>
                <span className="font-bold text-white bg-slate-800/50 px-3 py-1 rounded-full">{count}</span>
              </div>
            ))}
            {Object.keys(riskDist).length === 0 && <p className="text-slate-500 text-sm">No data available.</p>}
          </div>
        </div>
      </div>
      
      <div className="glass-card mt-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-green-400" /> Verification Trends (Last 7 Days)
        </h3>
        <div className="h-64 flex items-end gap-2 pt-4">
          {trends.length === 0 ? (
            <div className="w-full h-full flex items-center justify-center text-slate-500">No trend data available.</div>
          ) : (
            trends.map((t, i) => {
              const max = Math.max(...trends.map(x => x.count), 1);
              const height = `${(t.count / max) * 100}%`;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                  <div className="w-full bg-blue-500/20 rounded-t-sm relative transition-all group-hover:bg-blue-500/40" style={{ height }}>
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      {t.count}
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 transform -rotate-45 origin-top-left mt-2">{t.date}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
