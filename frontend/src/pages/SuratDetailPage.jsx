import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { getErrorMessage } from '../utils/error';
import { toast } from 'sonner';

const STATUS_LABEL = {
  DRAFT: 'Draft',
  MENUNGGU_TTD_DOSEN: 'Menunggu Dosen',
  MENUNGGU_PROSES_ADMIN: 'Menunggu Admin',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
};

const FIELD_LABELS = {
  keperluan_surat_aktif: 'Keperluan Surat Aktif',
  mata_kuliah_yang_dibatalkan: 'Mata Kuliah yang Dibatalkan',
  alasan_pembatalan_kuliah: 'Alasan Pembatalan Kuliah',
  nama_mata_kuliah: 'Nama Mata Kuliah',
  kode_mata_kuliah: 'Kode Mata Kuliah',
  semester: 'Semester',
  tahun_akademik: 'Tahun Akademik',
  dosen_pembimbing: 'Dosen Pembimbing',
  ketua_program_studi_ilmu_komputer: 'Ketua Program Studi Ilmu Komputer',
};

export default function SuratDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [surat, setSurat] = useState(null);
  const [signatures, setSignatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    try {
      const [suratRes, sigRes] = await Promise.all([
        api.get('/api/surat/' + id),
        api.get('/api/signatures/surat/' + id),
      ]);
      setSurat(suratRes.data);
      setSignatures(sigRes.data);
    } catch (err) {
      setError(getErrorMessage(err, 'Gagal memuat data surat'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleSubmit = async () => {
    try {
      await api.post('/api/surat/' + id + '/submit');
      toast.success('Surat berhasil diajukan');
      load();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Gagal submit'));
    }
  };

  const handleStudentSign = async () => {
    try {
      const form = new FormData();
      await api.post('/api/signatures/student/' + id, form);
      toast.success('Draft berhasil ditandatangani');
      load();
    } catch (err) {
      const message = getErrorMessage(err, 'Gagal menandatangani');
      if (message.toLowerCase().includes('belum disimpan')) {
        toast.warning('Simpan dulu tanda tangan Anda di menu Tanda Tangan');
        return;
      }
      toast.error(message);
    }
  };

  // Find the pending signature for this dosen
  const myPendingSignature = user?.role === 'DOSEN'
    ? signatures.find(s => s.owner_id === user.id && !s.signed_at)
    : null;

  const handleDosenSign = async () => {
    if (!myPendingSignature) return;
    setActionLoading(true);
    try {
      const form = new FormData();
      await api.post(`/api/signatures/lecturer/${myPendingSignature.id}/sign`, form);
      toast.success('Surat berhasil ditandatangani');
      load();
    } catch (err) {
      const message = getErrorMessage(err, 'Gagal menandatangani');
      if (message.toLowerCase().includes('belum disimpan')) {
        toast.warning('Simpan dulu tanda tangan Anda di menu Tanda Tangan');
        return;
      }
      toast.error(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDosenReject = async () => {
    if (!rejectReason.trim()) {
      toast.warning('Isi alasan penolakan terlebih dahulu');
      return;
    }
    setActionLoading(true);
    try {
      await api.post(`/api/surat/${id}/reject`, { reason: rejectReason });
      toast.success('Surat berhasil ditolak');
      setShowRejectModal(false);
      load();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Gagal menolak surat'));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-pulse flex space-x-4">
        <div className="h-12 w-12 bg-sepia-200 rounded-sm"></div>
      </div>
    </div>
  );

  if (error || !surat) return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-sm text-sm">
        {error || 'Surat tidak ditemukan.'}
      </div>
    </div>
  );

  const internalFields = surat.internal_fields || {};
  const internalFieldEntries = Object.entries(internalFields).filter(([, value]) => String(value || '').trim());
  const dateStr = surat.created_at ? new Date(surat.created_at).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }) : 'Tanggal tidak tersedia';
  
  // Kode dokumen: ambil dari ID surat sesuai format database (YYYY/ID padded)
  const year = surat.created_at ? new Date(surat.created_at).getFullYear() : new Date().getFullYear();
  const kodeSurat = `SR/${year}/${String(surat.id).padStart(4, '0')}`;

  const signedCount = signatures.filter(s => s.signed_at).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      
      {/* Header Section */}
      <div className="mb-12">
        <button onClick={() => navigate(-1)} className="flex items-center text-xs tracking-widest text-primary/60 hover:text-primary uppercase mb-8 transition-colors">
          <svg className="w-3 h-3 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Kembali
        </button>

        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
          <div className="max-w-3xl">
            <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Pengajuan &middot; {kodeSurat}</p>
            <h1 className="text-4xl font-serif text-primary mb-2">
              {surat.jenis}
            </h1>
            <p className="text-xl font-serif italic text-primary/70 mb-4">
              untuk {surat.keperluan.length > 50 ? surat.keperluan.substring(0, 50) + '...' : surat.keperluan}
            </p>
            <p className="text-sm text-primary/70">
              Diajukan oleh <span className="font-medium text-primary">{surat.mahasiswa_name || surat.mahasiswa_nim}</span> &middot; {dateStr}
            </p>
          </div>

          <div className="flex flex-col items-start lg:items-end gap-2">
            <span className={`px-4 py-1.5 text-xs font-medium rounded-full border ${
              surat.status === 'SELESAI' ? 'bg-primary/5 border-primary/20 text-primary' : 
              surat.status === 'DITOLAK' ? 'bg-red-50 border-red-200 text-red-700' : 
              'bg-ivory-dark border-sepia-200 text-primary'
            }`}>
              {STATUS_LABEL[surat.status]}
            </span>
            {/* Lihat PDF button — tampil untuk semua role jika ada PDF */}
            {(surat.pdf_path || surat.file_path) && (
              <Link
                to={`/surat/${surat.id}/pdf`}
                className="flex items-center gap-1.5 text-xs text-primary border border-sepia-200 hover:border-primary bg-white px-3 py-2 rounded-sm transition-colors mt-1"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                Lihat PDF
              </Link>
            )}
            {surat.status === 'SELESAI' && (
              <Link to={`/surat/${surat.id}/pdf`} className="text-xs text-primary underline decoration-primary/30 hover:decoration-primary">
                Unduh PDF Resmi
              </Link>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Rejection Banner */}
          {surat.status === 'DITOLAK' && (
            <div className="bg-red-50 border border-red-200 rounded-sm p-6">
              <div className="flex items-start gap-4">
                <div className="shrink-0 mt-1">
                  <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <div>
                  <h3 className="text-base font-serif text-red-800 mb-1">Pengajuan Ditolak</h3>
                  <p className="text-sm text-red-700 font-medium mb-2">Alasan Penolakan:</p>
                  <p className="text-sm text-red-600 bg-white/50 p-3 rounded border border-red-100 whitespace-pre-wrap">
                    {surat.rejection_reason || 'Tidak ada alasan spesifik yang diberikan.'}
                  </p>
                  {user.role === 'MAHASISWA' && (
                    <p className="text-xs text-red-500 mt-4 italic">Silakan buat pengajuan baru dengan memperbaiki data sesuai catatan di atas.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Rincian Pengajuan */}
          <div className="bg-white border border-sepia-200 rounded-sm">
            <div className="p-6 border-b border-sepia-200 flex justify-between items-center bg-ivory/30">
              <h3 className="text-base font-serif text-primary">Rincian Pengajuan</h3>
              <span className="text-[10px] tracking-widest text-primary/50 uppercase">Data Pemohon</span>
            </div>
            <div className="divide-y divide-sepia-200">
              <div className="flex flex-col sm:flex-row sm:items-center p-6 gap-2 sm:gap-6">
                <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase">Jenis Surat</div>
                <div className="w-full sm:w-2/3 text-sm font-medium text-primary">{surat.jenis}</div>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center p-6 gap-2 sm:gap-6">
                <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase">Kode Dokumen</div>
                <div className="w-full sm:w-2/3 text-sm font-mono text-primary/80">{kodeSurat}</div>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center p-6 gap-2 sm:gap-6">
                <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase">Nama Mahasiswa</div>
                <div className="w-full sm:w-2/3 text-sm text-primary">{surat.mahasiswa_name || '-'}</div>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center p-6 gap-2 sm:gap-6">
                <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase">NIM</div>
                <div className="w-full sm:w-2/3 text-sm text-primary">{surat.mahasiswa_nim || '-'}</div>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center p-6 gap-2 sm:gap-6">
                <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase">Tipe Dokumen</div>
                <div className="w-full sm:w-2/3 text-sm text-primary">{surat.is_external ? 'Eksternal (PDF Upload)' : 'Internal (Template Sistem)'}</div>
              </div>
            </div>
          </div>

          {/* Uraian Keperluan */}
          <div className="bg-white border border-sepia-200 rounded-sm">
            <div className="p-6 border-b border-sepia-200 flex justify-between items-center bg-ivory/30">
              <h3 className="text-base font-serif text-primary">Uraian Keperluan</h3>
              <span className="text-[10px] tracking-widest text-primary/50 uppercase">Disusun Pemohon</span>
            </div>
            <div className="p-6">
              <p className="text-sm text-primary/80 leading-relaxed whitespace-pre-wrap">
                {surat.keperluan}
              </p>
            </div>
          </div>

          {/* Internal Fields */}
          {internalFieldEntries.length > 0 && (
            <div className="bg-white border border-sepia-200 rounded-sm">
              <div className="p-6 border-b border-sepia-200 flex justify-between items-center bg-ivory/30">
                <h3 className="text-base font-serif text-primary">Data Spesifik Form</h3>
                <span className="text-[10px] tracking-widest text-primary/50 uppercase">Lampiran</span>
              </div>
              <div className="divide-y divide-sepia-200">
                {internalFieldEntries.map(([key, value]) => (
                  <div key={key} className="flex flex-col sm:flex-row sm:items-start p-6 gap-2 sm:gap-6">
                    <div className="w-full sm:w-1/3 text-xs tracking-widest text-primary/50 uppercase pt-1">
                      {FIELD_LABELS[key] || key.replace(/_/g, ' ')}
                    </div>
                    <div className="w-full sm:w-2/3 text-sm text-primary leading-relaxed">{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hash / Security */}
          {surat.document_hash && (
            <div className="bg-ivory border border-sepia-200 rounded-sm p-6 flex items-start gap-4">
              <div className="shrink-0 mt-1">
                <svg className="w-5 h-5 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <div>
                <h4 className="text-xs font-bold tracking-widest text-primary/60 uppercase mb-1">Integritas Dokumen</h4>
                <p className="text-xs text-primary/70 mb-2">Dokumen ini dilindungi kriptografi. Perubahan sekecil apapun akan merusak verifikasi.</p>
                <div className="text-[10px] font-mono text-primary/50 bg-white/50 p-2 rounded border border-sepia-200 break-all">
                  SHA256: {surat.document_hash}
                </div>
              </div>
            </div>
          )}

          {/* Actions for Mahasiswa Draft */}
          {user.role === 'MAHASISWA' && surat.status === 'DRAFT' && (
            <div className="flex gap-4 pt-4">
              <button type="button" onClick={handleStudentSign} className="px-6 py-3 border border-sepia-200 text-primary hover:border-primary bg-white transition-colors text-sm font-medium rounded-sm">
                Tandatangani Draft
              </button>
              <button type="button" onClick={handleSubmit} className="px-6 py-3 bg-primary text-white hover:bg-primary-dark transition-colors text-sm font-medium rounded-sm">
                Ajukan Surat
              </button>
            </div>
          )}

          {/* Actions for Dosen — tampil hanya jika ada pending signature milik dosen ini */}
          {user.role === 'DOSEN' && myPendingSignature && surat.status === 'MENUNGGU_TTD_DOSEN' && (
            <div className="bg-white border border-sepia-200 rounded-sm p-6">
              <p className="text-xs tracking-widest text-primary/50 uppercase mb-4">Tindakan Anda Diperlukan</p>
              <p className="text-sm text-primary/70 mb-6 leading-relaxed">
                Surat ini menunggu persetujuan Anda. Tinjau isi surat sebelum mengambil tindakan.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleDosenSign}
                  disabled={actionLoading}
                  className="flex items-center gap-2 px-6 py-3 bg-primary text-white hover:bg-primary-dark transition-colors text-sm font-medium rounded-sm disabled:opacity-60"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  {actionLoading ? 'Memproses...' : 'Setuju & Tanda Tangan'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRejectModal(true)}
                  disabled={actionLoading}
                  className="flex items-center gap-2 px-6 py-3 border border-red-200 text-red-700 hover:bg-red-50 transition-colors text-sm font-medium rounded-sm disabled:opacity-60"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  Tolak Pengajuan
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Timeline */}
        <div className="lg:col-span-1">
          <div className="bg-ivory border border-sepia-200 rounded-sm sticky top-28">
            {/* Header: split menjadi 2 baris agar tidak nabrak */}
            <div className="p-6 border-b border-sepia-200">
              <div className="flex justify-between items-start gap-2">
                <h3 className="text-base font-serif text-primary leading-tight">Alur Tanda Tangan</h3>
                <span className="text-[10px] tracking-widest text-primary/50 uppercase whitespace-nowrap shrink-0">
                  {signedCount} dari {signatures.length}
                </span>
              </div>
            </div>
            
            <div className="p-6">
              {signatures.length === 0 ? (
                <p className="text-sm text-primary/50 italic text-center py-4">Belum ada alur persetujuan.</p>
              ) : (
                <div className="relative border-l border-sepia-200 ml-3 space-y-8">
                  {signatures.map((sig, index) => {
                    const isSigned = !!sig.signed_at;
                    const isMe = user.role === 'DOSEN' && sig.owner_id === user.id;
                    return (
                      <div key={sig.id} className="relative pl-6">
                        {/* Timeline Node */}
                        <div className={`absolute -left-[13px] top-1 w-6 h-6 rounded-full border-2 flex items-center justify-center bg-white ${
                          isSigned ? 'border-primary' : isMe ? 'border-amber-400' : 'border-sepia-200 text-primary/40'
                        }`}>
                          {isSigned ? (
                            <div className="w-2.5 h-2.5 rounded-full bg-primary"></div>
                          ) : isMe ? (
                            <div className="w-2.5 h-2.5 rounded-full bg-amber-400"></div>
                          ) : (
                            <div className="w-1.5 h-1.5 rounded-full bg-sepia-300"></div>
                          )}
                        </div>

                        <div>
                          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-1">
                            {sig.role === 'DOSEN' ? 'Dosen' : sig.role}
                            {isMe && <span className="ml-1 text-amber-600 normal-case not-italic font-medium">(Anda)</span>}
                          </p>
                          <p className={`text-sm font-medium ${isSigned ? 'text-primary' : 'text-primary/70'}`}>
                            {sig.role === 'DOSEN' ? (sig.owner_name || 'Dosen Pembimbing') : sig.role}
                          </p>
                          
                          <div className="mt-2">
                            {isSigned ? (
                              <div>
                                <p className="text-xs text-primary/80">Disetujui</p>
                                <p className="text-[10px] text-primary/50 mt-0.5 font-mono">
                                  {new Date(sig.signed_at).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' })}
                                </p>
                              </div>
                            ) : surat.status === 'DITOLAK' ? (
                              <p className="text-xs text-red-500/70 italic">Dibatalkan</p>
                            ) : (
                              <p className="text-xs text-primary/50 italic">Menunggu Tanda Tangan</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Final Admin Step (Virtual) */}
                  {surat.status === 'DITOLAK' ? (
                    <div className="relative pl-6 mt-4">
                      <div className="absolute -left-[13px] top-1 w-6 h-6 rounded-full border-2 flex items-center justify-center bg-white border-red-500">
                        <svg className="w-3 h-3 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                      </div>
                      <div>
                        <p className="text-[10px] tracking-widest text-red-500 uppercase mb-1">Pengajuan Ditolak</p>
                        <p className="text-sm font-medium text-red-700">Proses Dihentikan</p>
                      </div>
                    </div>
                  ) : (
                    <div className="relative pl-6">
                      <div className={`absolute -left-[13px] top-1 w-6 h-6 rounded-full border-2 flex items-center justify-center bg-white ${
                        surat.status === 'SELESAI' ? 'border-primary' : 'border-sepia-200 text-primary/40'
                      }`}>
                        {surat.status === 'SELESAI' ? (
                          <div className="w-2.5 h-2.5 rounded-full bg-primary"></div>
                        ) : (
                          <div className="w-1.5 h-1.5 rounded-full bg-sepia-300"></div>
                        )}
                      </div>
                      <div>
                        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-1">Admin Program Studi</p>
                        <p className={`text-sm font-medium ${surat.status === 'SELESAI' ? 'text-primary' : 'text-primary/70'}`}>Penerbitan Surat</p>
                        <div className="mt-2">
                          {surat.status === 'SELESAI' ? (
                            <p className="text-xs text-primary/80">Surat Diterbitkan</p>
                          ) : (
                            <p className="text-xs text-primary/50 italic">Menunggu Proses</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
          <div className="bg-white border border-sepia-200 rounded-sm p-8 max-w-md w-full shadow-2xl">
            <h2 className="text-xl font-serif text-primary mb-2">Tolak Pengajuan</h2>
            <p className="text-sm text-primary/70 mb-6">
              Berikan alasan penolakan yang jelas agar mahasiswa dapat memperbaiki pengajuannya.
            </p>
            <textarea
              rows={4}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Contoh: Data NIM tidak sesuai, harap periksa kembali..."
              className="w-full px-4 py-3 border border-sepia-200 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm text-sm text-primary resize-none"
            />
            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={() => { setShowRejectModal(false); setRejectReason(''); }}
                className="flex-1 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm"
              >
                Batal
              </button>
              <button
                type="button"
                onClick={handleDosenReject}
                disabled={actionLoading}
                className="flex-1 py-3 bg-red-700 text-white hover:bg-red-800 transition-colors text-sm font-medium rounded-sm disabled:opacity-60"
              >
                {actionLoading ? 'Memproses...' : 'Konfirmasi Tolak'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
