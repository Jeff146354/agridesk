import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { Upload, FileText, Users, PenTool, ChevronRight, ChevronLeft, X, GripVertical, Check, Trash2, Search, UserPlus, Plus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDropzone } from 'react-dropzone';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import api from '../api';
import { getErrorMessage } from '../utils/error';

pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const SIGNER_COLORS = [
  { bg: 'rgba(13,148,136,0.15)', border: '#0d9488', text: '#0f766e', label: 'Teal' },
  { bg: 'rgba(217,119,6,0.15)', border: '#d97706', text: '#b45309', label: 'Amber' },
  { bg: 'rgba(124,58,237,0.15)', border: '#7c3aed', text: '#6d28d9', label: 'Violet' },
  { bg: 'rgba(225,29,72,0.15)', border: '#e11d48', text: '#be123c', label: 'Rose' },
  { bg: 'rgba(37,99,235,0.15)', border: '#2563eb', text: '#1d4ed8', label: 'Blue' },
];

const STEPS = [
  { key: 'upload', label: 'Upload Dokumen', icon: Upload },
  { key: 'signers', label: 'Penanda Tangan', icon: Users },
  { key: 'placement', label: 'Penempatan TTD', icon: PenTool },
];

/* ─────────────────────── Step Indicator ─────────────────────── */
function StepIndicator({ current }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-10">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const done = i < current;
        const active = i === current;
        return (
          <div key={step.key} className="flex items-center gap-2">
            {i > 0 && <div className={`w-8 h-px ${done ? 'bg-primary' : 'bg-sepia-200'}`} />}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${active ? 'bg-primary text-white shadow-md' : done ? 'bg-primary/10 text-primary' : 'bg-ivory-dark/60 text-primary/40'}`}>
              {done ? <Check size={14} /> : <Icon size={14} />}
              <span className="hidden sm:inline">{step.label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────── Step 1: Upload ─────────────────────── */
function StepUpload({ file, setFile, jenis, setJenis, keperluan, setKeperluan, onNext }) {
  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, [setFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
    onDropRejected: (rej) => {
      const msg = rej[0]?.errors?.[0]?.message || 'File tidak valid';
      toast.error(msg);
    },
  });

  const canProceed = file && jenis.trim() && keperluan.trim();

  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} className="space-y-8">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${isDragActive ? 'border-primary bg-primary/5 scale-[1.01]' : file ? 'border-primary/30 bg-primary/[0.02]' : 'border-sepia-200 hover:border-primary/40 hover:bg-ivory-dark/30'}`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center"><FileText size={28} className="text-primary" /></div>
            <p className="font-medium text-primary">{file.name}</p>
            <p className="text-xs text-primary/50">{(file.size / 1024).toFixed(1)} KB</p>
            <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); }} className="mt-1 text-xs text-red-600 hover:underline">Hapus &amp; pilih ulang</button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-full bg-ivory-dark flex items-center justify-center">
              <Upload size={28} className={`transition-colors ${isDragActive ? 'text-primary' : 'text-primary/30'}`} />
            </div>
            <p className="font-medium text-primary/70">Seret file PDF ke sini, atau <span className="text-primary underline underline-offset-2">pilih dari komputer</span></p>
            <p className="text-xs text-primary/40">PDF &middot; Maks 10 MB</p>
          </div>
        )}
      </div>

      {/* Meta fields */}
      <div className="grid sm:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-primary mb-2">Jenis Surat <span className="text-red-500">*</span></label>
          <input type="text" value={jenis} onChange={(e) => setJenis(e.target.value)} placeholder="contoh: Surat Rekomendasi" className="w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" />
        </div>
        <div>
          <label className="block text-sm font-medium text-primary mb-2">Keperluan <span className="text-red-500">*</span></label>
          <input type="text" value={keperluan} onChange={(e) => setKeperluan(e.target.value)} placeholder="contoh: Beasiswa LPDP 2026" className="w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" />
        </div>
      </div>

      <div className="flex justify-end">
        <button type="button" disabled={!canProceed} onClick={onNext} className="flex items-center gap-2 px-8 py-3 bg-primary text-white text-sm font-medium rounded-sm hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
          Lanjut <ChevronRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

/* ─────────────────────── Step 2: Signers ─────────────────────── */
function StepSigners({ signers, setSigners, isSequential, setIsSequential, onNext, onBack, currentUser }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const isSelfAdded = currentUser && signers.some((s) => s.user_id === currentUser.id);

  useEffect(() => {
    const kw = query.trim();
    if (!kw) { setResults([]); return; }
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await api.get('/api/auth/users/search', { params: { q: kw, limit: 8 } });
        setResults(res.data || []);
      } catch { setResults([]); }
      finally { setSearching(false); }
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  const addSigner = (user) => {
    if (signers.some((s) => s.user_id === user.id)) { toast.info('Sudah ditambahkan'); return; }
    const idx = signers.length;
    setSigners((prev) => [...prev, {
      user_id: user.id, name: user.name, email: user.email, role: user.role,
      nip: user.nip, nim: user.nim,
      signing_order: prev.length + 1,
      color: SIGNER_COLORS[idx % SIGNER_COLORS.length],
    }]);
    setQuery(''); setResults([]);
  };

  const addSelf = () => {
    if (!currentUser || isSelfAdded) return;
    addSigner({ id: currentUser.id, name: currentUser.name, email: currentUser.email, role: currentUser.role, nip: currentUser.nip, nim: currentUser.nim });
  };

  const removeSigner = (uid) => {
    setSigners((prev) => prev.filter((s) => s.user_id !== uid).map((s, i) => ({ ...s, signing_order: i + 1, color: SIGNER_COLORS[i % SIGNER_COLORS.length] })));
  };

  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} className="space-y-8">
      <div>
        <h3 className="text-lg font-serif text-primary mb-1">Tambahkan Penanda Tangan</h3>
        <p className="text-sm text-primary/60">Cari pengguna terdaftar Agridesk berdasarkan nama, email, NIP, atau NIM.</p>
      </div>

      {/* Self-sign toggle */}
      {currentUser && (
        <button
          type="button"
          onClick={isSelfAdded ? () => removeSigner(currentUser.id) : addSelf}
          className={`w-full flex items-center gap-4 p-4 rounded-sm border-2 border-dashed transition-all ${
            isSelfAdded ? 'border-primary/30 bg-primary/5' : 'border-sepia-200 hover:border-primary/40 hover:bg-ivory-dark/30'
          }`}
        >
          <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors ${
            isSelfAdded ? 'bg-primary text-white' : 'bg-ivory-dark text-primary/40'
          }`}>
            {isSelfAdded ? <Check size={18} /> : <UserPlus size={18} />}
          </div>
          <div className="text-left flex-1 min-w-0">
            <p className="text-sm font-medium text-primary">{isSelfAdded ? 'Tanda tangan Anda ditambahkan' : 'Sertakan tanda tangan saya'}</p>
            <p className="text-xs text-primary/50 mt-0.5 truncate">{currentUser.name} &middot; {currentUser.email}</p>
          </div>
          {isSelfAdded && <span className="text-xs text-primary/40 shrink-0">Klik untuk hapus</span>}
        </button>
      )}

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-primary/30" />
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Cari pengguna..." className="w-full pl-10 pr-4 py-3 bg-ivory border border-sepia-200 rounded-sm text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors" />
        {query.trim() && (
          <div className="absolute z-20 mt-1 w-full bg-white border border-sepia-200 shadow-lg rounded-sm max-h-56 overflow-auto">
            {searching && <div className="px-4 py-3 text-sm text-primary/40 italic">Mencari...</div>}
            {!searching && results.length === 0 && <div className="px-4 py-3 text-sm text-primary/40 italic">Tidak ditemukan</div>}
            {!searching && results.map((u) => (
              <button key={u.id} type="button" onClick={() => addSigner(u)} className="w-full text-left px-4 py-3 hover:bg-ivory transition-colors border-b border-sepia-200/40 last:border-0">
                <div className="font-medium text-primary text-sm">{u.name}</div>
                <div className="text-xs text-primary/50 mt-0.5">{u.role} &middot; {u.email}{u.nip ? ` · ${u.nip}` : ''}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Signer list */}
      {signers.length > 0 && (
        <div className="space-y-3">
          {signers.map((s) => (
            <div key={s.user_id} className="flex items-center gap-3 p-4 bg-white border border-sepia-200 rounded-sm">
              <div className="flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold text-white" style={{ backgroundColor: s.color.border }}>{s.signing_order}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-primary truncate">{s.name}</p>
                <p className="text-xs text-primary/50 truncate">{s.role} &middot; {s.email}</p>
              </div>
              <button type="button" onClick={() => removeSigner(s.user_id)} className="p-1.5 text-primary/30 hover:text-red-500 transition-colors"><Trash2 size={16} /></button>
            </div>
          ))}
        </div>
      )}

      {/* Sequential toggle */}
      {signers.length > 1 && (
        <label className="flex items-center gap-3 p-4 bg-ivory border border-sepia-200 rounded-sm cursor-pointer select-none">
          <input type="checkbox" checked={isSequential} onChange={(e) => setIsSequential(e.target.checked)} className="w-4 h-4 accent-primary" />
          <div>
            <p className="text-sm font-medium text-primary">Urutan tanda tangan wajib berurutan</p>
            <p className="text-xs text-primary/50 mt-0.5">Penanda tangan harus menandatangani sesuai nomor urut.</p>
          </div>
        </label>
      )}

      <div className="flex justify-between">
        <button type="button" onClick={onBack} className="flex items-center gap-2 px-6 py-3 border border-sepia-200 text-primary text-sm font-medium rounded-sm hover:bg-ivory-dark transition-colors">
          <ChevronLeft size={16} /> Kembali
        </button>
        <button type="button" disabled={signers.length === 0} onClick={onNext} className="flex items-center gap-2 px-8 py-3 bg-primary text-white text-sm font-medium rounded-sm hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
          Lanjut <ChevronRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

/* ─────────────────────── Step 3: Placement ─────────────────────── */
function StepPlacement({ file, signers, onBack, onSubmit, submitting }) {
  const [numPages, setNumPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const containerRef = useRef(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [containerWidth, setContainerWidth] = useState(600);
  // fields: array of { field_id, user_id, name, color, page_number, pos_x, pos_y, pos_width, pos_height }
  const [fields, setFields] = useState([]);
  const [dragging, setDragging] = useState(null);
  const [resizing, setResizing] = useState(null);

  const fileUrlRef = useRef(null);
  let fieldCounter = useRef(0);

  // Mouse move/up for drag & resize
  useEffect(() => {
    if (!dragging && !resizing) return;
    const handleMouseMove = (e) => {
      if (resizing) {
        const dx = e.clientX - resizing.startX;
        const dy = e.clientY - resizing.startY;
        setFields((prev) => prev.map((f) =>
          f.field_id === resizing.fieldId ? { ...f, pos_width: Math.max(100, resizing.startW + dx), pos_height: Math.max(40, resizing.startH + dy) } : f
        ));
      } else if (dragging) {
        const dx = e.clientX - dragging.startX;
        const dy = e.clientY - dragging.startY;
        setFields((prev) => prev.map((f) =>
          f.field_id === dragging.fieldId ? { ...f, pos_x: dragging.startPosX + dx, pos_y: dragging.startPosY + dy } : f
        ));
      }
    };
    const handleMouseUp = () => { setDragging(null); setResizing(null); };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => { window.removeEventListener('mousemove', handleMouseMove); window.removeEventListener('mouseup', handleMouseUp); };
  }, [dragging, resizing]);

  useEffect(() => {
    if (fileUrlRef.current) { URL.revokeObjectURL(fileUrlRef.current); fileUrlRef.current = null; }
    if (file) { const url = URL.createObjectURL(file); fileUrlRef.current = url; setFileUrl(url); } else { setFileUrl(null); }
    return () => { if (fileUrlRef.current) { URL.revokeObjectURL(fileUrlRef.current); fileUrlRef.current = null; } };
  }, [file]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => { for (const entry of entries) setContainerWidth(entry.contentRect.width); });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const pdfWidth = Math.min(containerWidth - 32, 700);

  const addField = (signer) => {
    fieldCounter.current += 1;
    setFields((prev) => [...prev, {
      field_id: `f_${signer.user_id}_${fieldCounter.current}_${Date.now()}`,
      user_id: signer.user_id, name: signer.name, color: signer.color,
      page_number: currentPage, pos_x: 50, pos_y: 50 + (prev.filter(f => f.user_id === signer.user_id).length * 30),
      pos_width: 150, pos_height: 60,
    }]);
  };

  const removeField = (fieldId) => { setFields((prev) => prev.filter((f) => f.field_id !== fieldId)); };

  const startDrag = (e, fieldId) => {
    e.stopPropagation();
    const f = fields.find((x) => x.field_id === fieldId);
    setDragging({ fieldId, startX: e.clientX, startY: e.clientY, startPosX: f.pos_x, startPosY: f.pos_y });
  };

  const startResize = (e, fieldId) => {
    e.stopPropagation();
    const f = fields.find((x) => x.field_id === fieldId);
    setResizing({ fieldId, startX: e.clientX, startY: e.clientY, startW: f.pos_width, startH: f.pos_height });
  };

  // Every signer must have at least one field
  const allPlaced = signers.every((s) => fields.some((f) => f.user_id === s.user_id));

  // When submitting, pass fields data up
  const handleSubmitWithFields = () => { onSubmit(fields); };

  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} className="space-y-6">
      <div>
        <h3 className="text-lg font-serif text-primary mb-1">Tempatkan Tanda Tangan</h3>
        <p className="text-sm text-primary/60">Klik <strong>+ Tambah</strong> untuk menambahkan area tanda tangan. Satu penanda tangan bisa memiliki beberapa area di halaman berbeda.</p>
      </div>

      {/* Signer toolbar — each signer has an "add field" button */}
      <div className="flex flex-wrap gap-2 p-3 bg-ivory border border-sepia-200 rounded-sm">
        {signers.map((s) => {
          const count = fields.filter((f) => f.user_id === s.user_id).length;
          return (
            <button key={s.user_id} type="button" onClick={() => addField(s)}
              className="flex items-center gap-2 px-3 py-2 rounded text-xs font-medium transition-all border hover:shadow-sm"
              style={{ borderColor: s.color.border, backgroundColor: s.color.bg, color: s.color.text }}
            >
              <Plus size={12} />
              {s.name.split(' ')[0]}
              {count > 0 && <span className="ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold" style={{ backgroundColor: s.color.border, color: '#fff' }}>{count}</span>}
            </button>
          );
        })}
      </div>

      {/* PDF viewer */}
      <div ref={containerRef} className="relative bg-gray-100 border border-sepia-200 rounded-sm overflow-hidden" style={{ minHeight: 500 }}>
        <div className="flex justify-center p-4">
          <div className="relative" style={{ width: pdfWidth }}>
            {fileUrl && (
              <Document file={fileUrl} onLoadSuccess={({ numPages: n }) => setNumPages(n)} loading={<div className="flex items-center justify-center h-96 text-sm text-primary/40">Memuat PDF...</div>}>
                <Page pageNumber={currentPage} width={pdfWidth} renderAnnotationLayer={false} renderTextLayer={false} />
              </Document>
            )}
            {/* Signature fields overlay */}
            {fields.filter((f) => f.page_number === currentPage).map((f) => (
              <div key={f.field_id} className="absolute flex items-start justify-between px-2 py-1 rounded border-2 text-[10px] font-medium select-none group cursor-move hover:shadow-md transition-shadow"
                style={{ left: f.pos_x, top: f.pos_y, width: f.pos_width, height: f.pos_height, borderColor: f.color.border, backgroundColor: f.color.bg, color: f.color.text }}
                onMouseDown={(e) => startDrag(e, f.field_id)}
              >
                <div className="flex flex-col truncate w-full h-full justify-center">
                  <span className="truncate">{f.name}</span>
                </div>
                <button type="button" onClick={(e) => { e.stopPropagation(); removeField(f.field_id); }} className="absolute top-1 right-1 shrink-0 hover:text-red-600 bg-white/50 rounded-sm p-0.5"><X size={12} /></button>
                <div
                  className="absolute bottom-0 right-0 w-3 h-3 cursor-nwse-resize opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ backgroundColor: f.color.border, clipPath: 'polygon(100% 0, 0 100%, 100% 100%)' }}
                  onMouseDown={(e) => startResize(e, f.field_id)}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Page nav */}
        {numPages > 1 && (
          <div className="flex items-center justify-center gap-4 py-3 bg-white/80 border-t border-sepia-200">
            <button type="button" disabled={currentPage <= 1} onClick={() => setCurrentPage((p) => p - 1)} className="px-3 py-1 text-xs border border-sepia-200 rounded disabled:opacity-30 hover:bg-ivory transition-colors"><ChevronLeft size={14} /></button>
            <span className="text-xs text-primary/60">Halaman {currentPage} / {numPages}</span>
            <button type="button" disabled={currentPage >= numPages} onClick={() => setCurrentPage((p) => p + 1)} className="px-3 py-1 text-xs border border-sepia-200 rounded disabled:opacity-30 hover:bg-ivory transition-colors"><ChevronRight size={14} /></button>
          </div>
        )}
      </div>

      <div className="flex justify-between">
        <button type="button" onClick={onBack} className="flex items-center gap-2 px-6 py-3 border border-sepia-200 text-primary text-sm font-medium rounded-sm hover:bg-ivory-dark transition-colors">
          <ChevronLeft size={16} /> Kembali
        </button>
        <button type="button" disabled={!allPlaced || submitting} onClick={handleSubmitWithFields} className="flex items-center gap-2 px-8 py-3 bg-primary text-white text-sm font-medium rounded-sm hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
          {submitting ? 'Mengirim...' : 'Kirim Dokumen'} <Check size={16} />
        </button>
      </div>
    </motion.div>
  );
}

/* ═══════════════════════ Main Wizard ═══════════════════════ */
export default function ExternalUploadWizardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [jenis, setJenis] = useState('');
  const [keperluan, setKeperluan] = useState('');
  const [signers, setSigners] = useState([]);
  const [isSequential, setIsSequential] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (fields) => {
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('jenis', jenis);
      fd.append('keperluan', keperluan);
      fd.append('is_sequential', isSequential);

      // Build configs from fields — one config per field
      const configs = fields.map((f) => {
        const signer = signers.find((s) => s.user_id === f.user_id);
        return {
          user_id: f.user_id,
          role: signer?.role || 'DOSEN',
          signing_order: signer?.signing_order || 1,
          page_number: f.page_number,
          pos_x: f.pos_x,
          pos_y: f.pos_y,
          pos_width: f.pos_width,
          pos_height: f.pos_height,
          owner_email: signer?.email || '',
        };
      });
      fd.append('signer_configs_json', JSON.stringify(configs));

      await api.post('/api/surat/external', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Dokumen berhasil dikirim!');
      navigate('/dashboard/mahasiswa');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Gagal mengirim dokumen'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Pengajuan &middot; Dokumen Eksternal</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl sm:text-4xl font-serif text-primary mb-2">Upload &amp; <span className="italic">tanda tangani.</span></h1>
            <p className="text-sm text-primary/60">Unggah dokumen PDF, tentukan penanda tangan, dan tempatkan area tanda tangan.</p>
          </div>
          <Link to="/surat/new" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Kembali
          </Link>
        </div>
      </div>

      <StepIndicator current={step} />

      <div className="bg-white border border-sepia-200 rounded-sm shadow-sm p-6 sm:p-8">
        <AnimatePresence mode="wait">
          {step === 0 && <StepUpload key="upload" file={file} setFile={setFile} jenis={jenis} setJenis={setJenis} keperluan={keperluan} setKeperluan={setKeperluan} onNext={() => setStep(1)} />}
          {step === 1 && <StepSigners key="signers" signers={signers} setSigners={setSigners} isSequential={isSequential} setIsSequential={setIsSequential} onNext={() => setStep(2)} onBack={() => setStep(0)} currentUser={user} />}
          {step === 2 && <StepPlacement key="placement" file={file} signers={signers} onBack={() => setStep(1)} onSubmit={handleSubmit} submitting={submitting} />}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
