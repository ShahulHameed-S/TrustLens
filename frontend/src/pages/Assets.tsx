import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { File, Trash2 } from 'lucide-react';

export const Assets = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAssets = async () => {
    try {
      const data: any = await api.get('/assets');
      setAssets(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this asset?')) return;
    try {
      await api.delete(`/assets/${id}`);
      setAssets(assets.filter(a => a.id !== id));
    } catch (err) {
      console.error(err);
      alert('Failed to delete asset');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading assets...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
        My Assets
      </h2>
      
      <div className="glass-card overflow-hidden">
        {assets.length === 0 ? (
          <div className="p-8 text-center text-slate-400">No assets found.</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-slate-800/50 border-b border-glass-border">
              <tr>
                <th className="p-4 font-medium text-slate-300">Filename</th>
                <th className="p-4 font-medium text-slate-300">Type</th>
                <th className="p-4 font-medium text-slate-300">Hash</th>
                <th className="p-4 font-medium text-slate-300">Date</th>
                <th className="p-4 font-medium text-slate-300 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-glass-border">
              {assets.map((asset) => (
                <tr key={asset.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 flex items-center gap-3">
                    <File className="w-5 h-5 text-blue-400" />
                    <span className="font-medium text-slate-200">{asset.original_filename}</span>
                  </td>
                  <td className="p-4 text-slate-400 text-sm">{asset.asset_type}</td>
                  <td className="p-4 text-slate-400 text-sm font-mono truncate max-w-[150px]" title={asset.hash_value}>
                    {asset.hash_value?.substring(0, 16)}...
                  </td>
                  <td className="p-4 text-slate-400 text-sm">
                    {new Date(asset.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4 flex justify-end gap-2">
                    <button onClick={() => handleDelete(asset.id)} className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
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
