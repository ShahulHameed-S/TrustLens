import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { UploadCloud, FileType, CheckCircle } from 'lucide-react';

export const Verify = () => {
  const [file, setFile] = useState<File | null>(null);
  const [assetType, setAssetType] = useState('IMAGE');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return alert('Please select a file');

    setLoading(true);
    setSuccess(false);

    try {
      // 1. Upload Asset
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', assetType);

      const assetRes: any = await api.post('/assets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const assetId = assetRes.id || assetRes.asset_id;

      // 2. Trigger Verification depending on type
      let endpoint = '';
      if (assetType === 'PDF') endpoint = '/verifications/pdf';
      else if (assetType === 'IMAGE') endpoint = '/verifications/image';
      else if (assetType === 'AUDIO') endpoint = '/verifications/audio';

      const verifyRes: any = await api.post(endpoint, { asset_id: assetId });
      
      setSuccess(true);
      setTimeout(() => {
        navigate(`/verifications/${verifyRes.id || verifyRes.verification_id || ''}`);
      }, 1500);

    } catch (err: any) {
      console.error(err);
      alert(err?.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
          Verify an Asset
        </h2>
        <p className="text-slate-400">Upload a file to securely generate a proof and verify its authenticity.</p>
      </div>

      <div className="glass-card p-8">
        {success ? (
          <div className="flex flex-col items-center justify-center py-12 text-center space-y-4 animate-in fade-in zoom-in duration-500">
            <CheckCircle className="w-16 h-16 text-green-400" />
            <h3 className="text-2xl font-bold text-white">Verification Started!</h3>
            <p className="text-slate-400">Redirecting to verification details...</p>
          </div>
        ) : (
          <form onSubmit={handleUpload} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Asset Type</label>
              <div className="flex gap-4">
                {['IMAGE', 'PDF', 'AUDIO'].map(type => (
                  <label key={type} className={`flex-1 flex flex-col items-center justify-center p-4 border rounded-xl cursor-pointer transition-all ${assetType === type ? 'border-blue-500 bg-blue-500/20 text-blue-300' : 'border-glass-border bg-slate-800/30 text-slate-400 hover:bg-slate-800/50'}`}>
                    <input type="radio" name="type" value={type} className="hidden" onChange={() => setAssetType(type)} checked={assetType === type} />
                    <FileType className="w-8 h-8 mb-2" />
                    <span className="font-medium">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Upload File</label>
              <div className="border-2 border-dashed border-glass-border rounded-xl p-10 flex flex-col items-center justify-center bg-slate-800/20 hover:bg-slate-800/40 transition-colors relative">
                <input 
                  type="file" 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={e => setFile(e.target.files ? e.target.files[0] : null)}
                  required 
                />
                <UploadCloud className="w-12 h-12 text-slate-400 mb-4" />
                <p className="font-medium text-slate-300 mb-1">{file ? file.name : 'Click or drag file to upload'}</p>
                <p className="text-sm text-slate-500">{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Supported formats depend on asset type'}</p>
              </div>
            </div>

            <button type="submit" disabled={loading || !file} className="glass-button-primary w-full py-3 text-lg mt-4">
              {loading ? 'Processing...' : 'Verify Asset'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
