import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, ShieldX, Search, User, Clock, FileText, Hash, CheckCircle, XCircle, ChevronRight, AlertTriangle, Download } from 'lucide-react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import api from '../api';
import { getApiBaseUrl } from '../utils/apiBaseUrl';

export default function VerifyPage() {
  const { hash: urlHash } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [hash, setHash] = useState(urlHash || '');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const isSigRoute = location.pathname.startsWith('/verify-sig');

  // Auto-verify on mount if hash is present
  useEffect(() => {
    if (urlHash) {
      performVerification(urlHash);
    }
  }, [urlHash, location.pathname]);

  const performVerification = async (targetHash) => {
    let trimmed = targetHash.trim().replace(/^SHA256:\s*/i, '').replace(/\s/g, '');
    if (!trimmed) return;
    setLoading(true);
    setResult(null);
    setSearched(false);
    
    const endpoint = isSigRoute 
      ? `/api/verify/sig/${encodeURIComponent(trimmed)}`
      : `/api/verify/${encodeURIComponent(trimmed)}`;

    try {
      const res = await api.get(endpoint);
      setResult(res.data);
    } catch {
      setResult({ status: 'INVALID' });
    } finally {
      setLoading(false);
      setSearched(true);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    performVerification(hash);
  };

  const handleTabChange = (type) => {
    setResult(null);
    setSearched(false);
    setHash('');
    if (type === 'sig') {
      navigate('/verify-sig', { replace: true });
    } else {
      navigate('/verify', { replace: true });
    }
  };

  const isValid = result?.status === 'VALID';
  const docStatus = result?.document?.status;

  let statusType = 'invalid'; // 'valid' | 'draft' | 'rejected' | 'invalid'
  if (isValid) {
    if (docStatus === 'SELESAI') {
      statusType = 'valid';
    } else if (docStatus === 'DITOLAK') {
      statusType = 'rejected';
    } else {
      statusType = 'draft';
    }
  }

  const uniqueSigners = (() => {
    if (!result?.signers) return [];
    const map = new Map();
    result.signers.forEach(s => {
      const key = `${s.role}_${s.name}`;
      if (!map.has(key)) {
        map.set(key, s);
      }
    });
    return Array.from(map.values());
  })();

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    const months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')} WIB`;
  };

  return (
    <div className="min-h-[calc(100vh-140px)] flex items-center justify-center px-4 py-16">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-xl">

        {/* Branding */}
        <div className="text-center mb-8">
          <p className="text-[10px] tracking-[0.3em] text-primary/40 uppercase mb-4">Agridesk &middot; Verifikasi Dokumen</p>
          <h1 className="text-3xl sm:text-4xl font-serif text-primary mb-3">
            Verifikasi <span className="italic">keaslian.</span>
          </h1>
          <p className="text-sm text-primary/60 max-w-md mx-auto">
            {isSigRoute 
              ? 'Masukkan kode hash tanda tangan atau pindai QR code pada stempel tanda tangan untuk memverifikasi keaslian penandatangan.' 
              : 'Masukkan kode hash dokumen atau pindai QR code pada dokumen cetak untuk memverifikasi keaslian and integritas dokumen.'}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex bg-sepia-100 p-1 rounded-sm border border-sepia-200">
            <button
              type="button"
              onClick={() => handleTabChange('doc')}
              className={`px-4 py-1.5 text-sm font-medium rounded-sm transition-colors ${!isSigRoute ? 'bg-white shadow-sm text-primary' : 'text-primary/60 hover:text-primary'}`}
            >
              Dokumen
            </button>
            <button
              type="button"
              onClick={() => handleTabChange('sig')}
              className={`px-4 py-1.5 text-sm font-medium rounded-sm transition-colors ${isSigRoute ? 'bg-white shadow-sm text-primary' : 'text-primary/60 hover:text-primary'}`}
            >
              Tanda Tangan
            </button>
          </div>
        </div>

        {/* Search form */}
        <form onSubmit={handleVerify} className="relative flex items-center bg-white border border-sepia-200 rounded-sm shadow-sm p-1.5 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary transition-colors mb-8">
          <Search size={18} className="text-primary/30 ml-2.5 shrink-0" />
          <input
            type="text"
            value={hash}
            onChange={(e) => setHash(e.target.value)}
            placeholder={isSigRoute ? "Masukkan kode hash tanda tangan..." : "Masukkan kode hash dokumen..."}
            className="flex-1 bg-transparent border-none px-3 py-2.5 text-sm focus:outline-none focus:ring-0 min-w-0"
          />
          <button type="submit" disabled={loading || !hash.trim()} className="shrink-0 px-5 py-2 bg-primary text-white text-sm font-medium rounded-sm hover:bg-primary-dark disabled:opacity-40 transition-colors">
            {loading ? 'Memverifikasi...' : 'Verifikasi'}
          </button>
        </form>

        {/* Result */}
        <AnimatePresence mode="wait">
          {searched && result && (
            <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="bg-white border border-sepia-200 rounded-sm shadow-sm overflow-hidden">

              {/* Status banner */}
              {statusType === 'valid' && (
                <div className="px-6 py-5 flex items-center gap-4 bg-emerald-50 border-b border-emerald-200">
                  <ShieldCheck size={36} className="text-emerald-600 shrink-0" />
                  <div>
                    <h2 className="text-xl font-serif font-semibold text-emerald-800">
                      Dokumen Terverifikasi Resmi
                    </h2>
                    <p className="text-sm mt-0.5 text-emerald-600">
                      Keaslian dan integritas dokumen resmi ini terkonfirmasi penuh oleh sistem Agridesk.
                    </p>
                  </div>
                </div>
              )}

              {statusType === 'draft' && (
                <div className="px-6 py-5 flex items-center gap-4 bg-amber-50 border-b border-amber-200">
                  <AlertTriangle size={36} className="text-amber-600 shrink-0" />
                  <div>
                    <h2 className="text-xl font-serif font-semibold text-amber-800">
                      Tanda Tangan Valid (Dokumen Draf)
                    </h2>
                    <p className="text-sm mt-0.5 text-amber-600">
                      Tanda tangan digital valid, namun dokumen ini masih berstatus DRAF / dalam proses pengajuan dan belum diterbitkan resmi.
                    </p>
                  </div>
                </div>
              )}

              {statusType === 'rejected' && (
                <div className="px-6 py-5 flex items-center gap-4 bg-red-50 border-b border-red-200">
                  <XCircle size={36} className="text-red-600 shrink-0" />
                  <div>
                    <h2 className="text-xl font-serif font-semibold text-red-800">
                      Dokumen Ditolak / Dibatalkan
                    </h2>
                    <p className="text-sm mt-0.5 text-red-600">
                      Pengajuan dokumen ini telah resmi ditolak atau dibatalkan oleh pihak administrasi Departemen.
                    </p>
                  </div>
                </div>
              )}

              {statusType === 'invalid' && (
                <div className="px-6 py-5 flex items-center gap-4 bg-red-50 border-b border-red-200">
                  <ShieldX size={36} className="text-red-600 shrink-0" />
                  <div>
                    <h2 className="text-xl font-serif font-semibold text-red-800">
                      Dokumen Tidak Valid
                    </h2>
                    <p className="text-sm mt-0.5 text-red-600">
                      Hash tidak ditemukan, tanda tangan tidak valid, atau kode verifikasi salah.
                    </p>
                  </div>
                </div>
              )}

              {isValid && result.document && (
                <div className="p-6 space-y-6">
                  {/* Verification & Status Badge */}
                  <div className="flex items-center justify-between gap-4 border-b border-sepia-100 pb-4">
                    {result.verification_id && (
                      <div className="flex items-center gap-2 text-xs text-primary/50">
                        <Hash size={12} />
                        <span>ID Verifikasi: <span className="font-mono font-medium text-primary">{result.verification_id}</span></span>
                      </div>
                    )}
                    
                    <span className={`px-2.5 py-1 text-[10px] font-bold rounded-sm uppercase tracking-wider
                      ${statusType === 'valid' ? 'bg-emerald-100 text-emerald-800' : ''}
                      ${statusType === 'draft' ? 'bg-amber-100 text-amber-800' : ''}
                      ${statusType === 'rejected' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {docStatus === 'SELESAI' && 'Selesai & Sah'}
                      {docStatus === 'DITOLAK' && 'Ditolak'}
                      {docStatus === 'DRAFT' && 'Draf'}
                      {docStatus === 'MENUNGGU_TTD_DOSEN' && 'Menunggu TTD Dosen'}
                      {docStatus === 'MENUNGGU_PROSES_ADMIN' && 'Menunggu Proses Admin'}
                    </span>
                  </div>

                  {/* Document info */}
                  <div className="grid sm:grid-cols-2 gap-4">
                    <InfoItem icon={FileText} label="Jenis Surat" value={result.document.jenis} />
                    <InfoItem icon={Hash} label="Kode Dokumen" value={result.document.code} />
                    <InfoItem icon={Clock} label="Tanggal Dibuat" value={formatDate(result.document.created_at)} />
                    <InfoItem icon={CheckCircle} label="Tanggal Selesai" value={formatDate(result.document.completed_at)} />
                  </div>

                  {result.document.keperluan && (
                    <div className="p-3 bg-ivory border border-sepia-200 rounded-sm">
                      <p className="text-xs text-primary/50 mb-1">Keperluan</p>
                      <p className="text-sm text-primary">{result.document.keperluan}</p>
                    </div>
                  )}

                  {result.document.internal_fields && Object.keys(result.document.internal_fields).length > 0 && (
                    <div className="p-4 bg-white border border-sepia-200 rounded-sm">
                      <h3 className="text-sm font-serif font-semibold text-primary mb-3">Data Spesifik Surat</h3>
                      <div className="grid sm:grid-cols-2 gap-x-4 gap-y-4">
                        {Object.entries(result.document.internal_fields).map(([k, v]) => {
                          if (k.endsWith('_nip')) return null; // Hide redundant NIP fields
                          return (
                            <div key={k} className={v.length > 50 ? "sm:col-span-2" : ""}>
                              <p className="text-[10px] font-medium uppercase tracking-wider text-primary/40 mb-0.5">{k.replace(/_/g, ' ')}</p>
                              <p className="text-sm text-primary break-words">{v}</p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Signers timeline */}
                  {uniqueSigners.length > 0 && (
                    <div>
                      <h3 className="text-sm font-serif font-semibold text-primary mb-4 flex items-center gap-2"><User size={14} /> Penanda Tangan</h3>
                      <div className="space-y-0">
                        {uniqueSigners.map((signer, i) => (
                          <div key={i} className="flex gap-4">
                            {/* Timeline line */}
                            <div className="flex flex-col items-center">
                              <div className={`w-3 h-3 rounded-full border-2 shrink-0 ${signer.is_signed ? 'bg-emerald-500 border-emerald-500' : 'bg-white border-sepia-200'}`} />
                              {i < uniqueSigners.length - 1 && <div className="w-px flex-1 bg-sepia-200 my-1" />}
                            </div>
                            {/* Content */}
                            <div className="pb-5 -mt-0.5">
                              <p className="text-sm font-medium text-primary">{signer.name}</p>
                              <p className="text-xs text-primary/50">{signer.role}{signer.nip ? ` · ${signer.nip}` : ''}</p>
                              {signer.signed_at && <p className="text-xs text-emerald-600 mt-1">{formatDate(signer.signed_at)}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Hash */}
                  <div className="p-3 bg-ivory border border-sepia-200 rounded-sm">
                    <p className="text-xs text-primary/50 mb-1">Document Hash (SHA-256)</p>
                    <p className="text-xs font-mono text-primary/70 break-all">{result.document_hash}</p>
                  </div>

                  {/* Download Button (Only for Completed/Valid Documents) */}
                  {statusType === 'valid' && (
                    <div className="pt-2">
                      <a
                        href={`${api.defaults.baseURL || getApiBaseUrl()}/api/verify/download/${encodeURIComponent(result.document_hash || hash)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-sm transition-all shadow-sm cursor-pointer hover:shadow-md active:scale-[0.98]"
                        download
                      >
                        <Download size={16} />
                        Unduh PDF Resmi Terverifikasi
                      </a>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

function InfoItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-ivory/60 rounded-sm">
      <Icon size={14} className="text-primary/40 mt-0.5 shrink-0" />
      <div>
        <p className="text-[11px] text-primary/40 uppercase tracking-wider">{label}</p>
        <p className="text-sm text-primary font-medium mt-0.5">{value || '-'}</p>
      </div>
    </div>
  );
}
