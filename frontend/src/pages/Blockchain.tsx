import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { Database, ShieldCheck } from 'lucide-react';

export const Blockchain = () => {
  const [blocks, setBlocks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  
  const user = useAuthStore(state => state.user);
  const isAdmin = user?.roles?.includes('admin');

  const fetchBlocks = async () => {
    try {
      const data: any = await api.get('/blockchain');
      setBlocks(data.items || data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlocks();
  }, []);

  const handleValidate = async () => {
    setValidating(true);
    setValidationResult(null);
    try {
      await api.get('/blockchain/validate');
      setValidationResult({ success: true, message: 'Blockchain is valid and fully intact.' });
    } catch (err: any) {
      setValidationResult({ success: false, message: err?.message || 'Blockchain validation failed!' });
    } finally {
      setValidating(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading blockchain ledger...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 flex items-center gap-2">
          <Database className="w-6 h-6 text-blue-400" /> Immutable Ledger
        </h2>
        
        {isAdmin && (
          <button 
            onClick={handleValidate} 
            disabled={validating}
            className="glass-button-primary"
          >
            <ShieldCheck className="w-5 h-5" />
            {validating ? 'Validating...' : 'Validate Chain'}
          </button>
        )}
      </div>
      
      {validationResult && (
        <div className={`p-4 rounded-xl border ${validationResult.success ? 'bg-green-500/20 border-green-500/50 text-green-200' : 'bg-red-500/20 border-red-500/50 text-red-200'}`}>
          <p className="font-medium flex items-center gap-2">
            {validationResult.success ? <ShieldCheck className="w-5 h-5" /> : null}
            {validationResult.message}
          </p>
        </div>
      )}

      <div className="space-y-4">
        {blocks.map((block) => (
          <div key={block.id} className="glass-card flex flex-col gap-2 relative overflow-hidden group">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 to-purple-500"></div>
            <div className="flex justify-between items-start">
              <div>
                <span className="px-2 py-1 bg-slate-800/50 rounded-md text-xs font-mono text-slate-400 border border-slate-700">
                  Block #{block.block_index}
                </span>
                <p className="text-sm text-slate-400 mt-2">Timestamp: {new Date(block.timestamp).toLocaleString()}</p>
              </div>
            </div>
            
            <div className="mt-2 space-y-1">
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Hash</span>
                <span className="font-mono text-sm text-blue-300 break-all">{block.hash}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Previous Hash</span>
                <span className="font-mono text-sm text-slate-400 break-all">{block.previous_hash}</span>
              </div>
            </div>
          </div>
        ))}
        {blocks.length === 0 && (
          <div className="glass-card p-8 text-center text-slate-400">Ledger is empty.</div>
        )}
      </div>
    </div>
  );
};
