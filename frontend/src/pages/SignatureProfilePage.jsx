import { useEffect, useRef, useState } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { getErrorMessage } from '../utils/error';

export default function SignatureProfilePage() {
  const { user } = useAuth();
  const canvasRef = useRef(null);
  const drawingRef = useRef(false);
  const [hasSaved, setHasSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [signatureHash, setSignatureHash] = useState('');
  const [validUntil, setValidUntil] = useState('');

  const loadSignatureProfile = async () => {
    try {
      const res = await api.get('/api/signatures/me');
      const exists = Boolean(res.data?.has_saved_signature);
      setHasSaved(exists);
      if (!exists) {
        setPreviewUrl('');
        return;
      }
      
      const hashText = res.data?.signature_hash || '';
      setSignatureHash(hashText ? `${hashText.substring(0, 4)}...${hashText.substring(hashText.length - 4)}` : '');
      
      const dateUpdated = res.data?.updated_at ? new Date(res.data.updated_at) : new Date();
      dateUpdated.setFullYear(dateUpdated.getFullYear() + 1);
      setValidUntil(dateUpdated.toLocaleString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }));

      const imgRes = await api.get('/api/signatures/me/image', {
        responseType: 'blob',
        params: { t: Date.now() },
        headers: {
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
      });
      const blobUrl = URL.createObjectURL(new Blob([imgRes.data]));
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return blobUrl;
      });
    } catch {
      setHasSaved(false);
      setPreviewUrl('');
    }
  };

  useEffect(() => {
    loadSignatureProfile();
  }, [user?.id]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const getPoint = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    let clientX, clientY;
    if ('touches' in e && e.touches.length > 0) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY,
    };
  };

  const startDraw = (e) => {
    drawingRef.current = true;
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getPoint(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!drawingRef.current) return;
    if (e.cancelable) e.preventDefault();
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getPoint(e);
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#1a2e26'; // primary color
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  };

  const endDraw = () => {
    drawingRef.current = false;
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setMessage('');
  };

  const saveSignature = async () => {
    setMessage('');
    setError(false);
    setSaving(true);
    try {
      const canvas = canvasRef.current;
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
      if (!blob) throw new Error('Gagal membuat gambar tanda tangan');

      const form = new FormData();
      form.append('file', blob, 'signature.png');
      await api.post('/api/signatures/me', form);
      await loadSignatureProfile();
      setMessage('Tanda tangan berhasil disimpan dalam profil Anda.');
    } catch (err) {
      setError(true);
      setMessage(getErrorMessage(err, 'Gagal menyimpan tanda tangan'));
    } finally {
      setSaving(false);
    }
  };

  // Remove placeholder logic, we use real state variables now
  const certHash = signatureHash || "-";
  const certExpiry = validUntil || "-";

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Profil &middot; Tanda Tangan</p>
        <div className="max-w-2xl">
          <h1 className="text-4xl font-serif text-primary mb-3">
            Tanda tangan <span className="italic">resmi</span> Anda.
          </h1>
          <p className="text-sm text-primary/70 leading-relaxed">
            Goresan ini akan tertaut pada setiap surat yang Anda setujui. Terenkripsi dengan sertifikat institusi dan tercatat dalam arsip audit.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        
        {/* Left Column - Canvas */}
        <div className="lg:col-span-3">
          <div className="bg-ivory border border-sepia-200 rounded-sm">
            <div className="p-6 border-b border-sepia-200 flex justify-between items-start sm:items-center bg-ivory/30">
              <div>
                <h3 className="text-base font-serif text-primary">Kanvas Goresan</h3>
                <p className="text-xs text-primary/60 mt-1">Tulis tanda tangan Anda secara alami.</p>
              </div>
            </div>

            <div className="p-6 sm:p-8">
              <div className="bg-white border border-sepia-200 rounded-sm relative touch-none group">
                <canvas
                  ref={canvasRef}
                  width={800}
                  height={300}
                  className="w-full h-auto cursor-crosshair"
                  onMouseDown={startDraw}
                  onMouseMove={draw}
                  onMouseUp={endDraw}
                  onMouseLeave={endDraw}
                  onTouchStart={startDraw}
                  onTouchMove={draw}
                  onTouchEnd={endDraw}
                />
                
                {/* Decorative Elements */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <span className="text-2xl font-serif italic text-sepia-200/60 transition-opacity group-hover:opacity-0">Tanda tangan di sini</span>
                </div>
                <div className="absolute bottom-4 left-4 text-[10px] font-mono text-primary/30 pointer-events-none">
                  A4 &middot; 210 &times; 74 mm
                </div>
                <div className="absolute bottom-4 right-4 text-[10px] tracking-widest uppercase text-primary/30 pointer-events-none border-b border-primary/20 pb-0.5">
                  Garis Dasar
                </div>
              </div>

              {message && (
                <div className={`mt-6 p-4 rounded-sm text-sm ${error ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                  {message}
                </div>
              )}

              <div className="mt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
                <p className="text-xs text-primary/50 text-center sm:text-left">
                  Anda dapat memperbarui tanda tangan kapan saja.<br />
                  Pastikan goresan terlihat jelas.
                </p>
                <div className="flex items-center gap-4">
                  <button 
                    type="button" 
                    onClick={clearCanvas}
                    className="text-sm font-medium text-primary hover:text-primary-dark transition-colors"
                  >
                    Ulang
                  </button>
                  <button 
                    type="button" 
                    onClick={saveSignature}
                    disabled={saving}
                    className="px-6 py-2.5 bg-primary text-white text-sm font-medium hover:bg-primary-dark rounded-sm transition-colors disabled:opacity-70"
                  >
                    {saving ? 'Menyimpan...' : 'Simpan Goresan'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Preview & Security */}
        <div className="lg:col-span-2 space-y-8">
          
          <div className="bg-white border border-sepia-200 rounded-sm">
            <div className="p-6 border-b border-sepia-200 flex justify-between items-center bg-ivory/30">
              <h3 className="text-base font-serif text-primary">Pratinjau Tersimpan</h3>
              <div className="flex items-center gap-2 text-[10px] tracking-widest text-primary/60 uppercase">
                {hasSaved ? (
                  <><span className="w-1.5 h-1.5 rounded-full bg-green-600"></span> Aktif</>
                ) : (
                  <><span className="w-1.5 h-1.5 rounded-full bg-red-600"></span> Kosong</>
                )}
              </div>
            </div>
            <div className="p-6">
              <div className="bg-ivory border border-sepia-200 rounded-sm p-4 h-40 flex items-center justify-center mb-6">
                {previewUrl ? (
                  <img src={previewUrl} alt="Preview tanda tangan" className="max-h-32 object-contain filter contrast-125" />
                ) : (
                  <span className="text-sm text-primary/40 italic font-serif">Belum ada tanda tangan</span>
                )}
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-between text-xs">
                  <span className="text-primary/60">Disertifikasi oleh</span>
                  <span className="text-primary font-medium font-mono">Agridesk Secure Inc.</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-primary/60">Sidik pasti (hash)</span>
                  <span className="text-primary font-mono">{certHash}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-primary/60">Berlaku hingga</span>
                  <span className="text-primary font-medium">{certExpiry}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-ivory border border-sepia-200 rounded-sm p-6">
            <h3 className="text-sm font-bold tracking-widest text-primary/70 uppercase mb-3">Catatan Keamanan</h3>
            <p className="text-xs text-primary/70 leading-relaxed">
              Tanda tangan Anda hanya digunakan pada surat yang Anda setujui secara eksplisit. Setiap penempelan tercatat dalam jejak audit dan tidak dapat disalin oleh pihak lain secara independen.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}
