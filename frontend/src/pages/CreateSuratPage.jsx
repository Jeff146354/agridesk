import { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';
import { getErrorMessage } from '../utils/error';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const FIELD_LABELS = {
  nama_mata_kuliah: 'Nama Mata Kuliah',
  kode_mata_kuliah: 'Kode Mata Kuliah',
  semester: 'Semester',
  tahun_akademik: 'Tahun Akademik',
  alasan_pembatalan_kuliah: 'Alasan Pembatalan Kuliah',
  dosen_pembimbing: 'Dosen Pembimbing',
  ketua_program_studi_ilmu_komputer: 'Ketua Program Studi Ilmu Komputer',
};

const LECTURER_FIELD_KEYS = new Set(['dosen_pembimbing', 'ketua_program_studi_ilmu_komputer']);

function LecturerSearchField({
  label,
  placeholder,
  helperText,
  selectedLecturer,
  onSelect,
  onClear,
}) {
  const [query, setQuery] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const keyword = query.trim();
    if (!keyword) {
      setOptions([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.get('/api/auth/lecturers/search', {
          params: { q: keyword, limit: 10 },
        });
        setOptions(res.data || []);
      } catch (err) {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timeout);
  }, [query]);

  const chooseLecturer = (lecturer) => {
    onSelect(lecturer);
    setQuery('');
    setOptions([]);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-primary mb-2">{label}</label>
      <p className="text-xs text-primary/60 mb-3">{helperText}</p>
      <div className="relative">
        <input
          type="text"
          className="appearance-none block w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary sm:text-sm transition-colors"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {query.trim() && (
          <div className="absolute z-10 mt-1 w-full bg-white border border-sepia-200 shadow-lg max-h-60 rounded-sm py-1 overflow-auto sm:text-sm">
            {loading && <div className="px-4 py-3 text-sm text-primary/50 italic">Mencari dosen...</div>}
            {!loading && options.length === 0 && (
              <div className="px-4 py-3 text-sm text-primary/50 italic">Dosen tidak ditemukan</div>
            )}
            {!loading && options.map((lecturer) => (
              <button
                key={lecturer.id}
                type="button"
                className="w-full text-left px-4 py-3 hover:bg-ivory focus:bg-ivory focus:outline-none transition-colors border-b border-sepia-200/50 last:border-0"
                onClick={() => chooseLecturer(lecturer)}
              >
                <div className="font-medium text-primary">{lecturer.name}</div>
                <div className="text-xs text-primary/60 mt-0.5">{lecturer.nip || '-'} &middot; {lecturer.email}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedLecturer && (
        <div className="mt-3 inline-flex items-center px-3 py-1.5 border border-sepia-200 bg-white text-primary rounded-sm text-xs font-medium shadow-sm">
          {selectedLecturer.name}
          <button
            type="button"
            onClick={() => {
              onClear();
              setQuery('');
              setOptions([]);
            }}
            className="ml-2 shrink-0 h-4 w-4 inline-flex items-center justify-center text-primary/40 hover:text-red-600 transition-colors focus:outline-none"
          >
            &times;
          </button>
        </div>
      )}
    </div>
  );
}

export default function CreateSuratPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('internal');
  const [templates, setTemplates] = useState([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(true);
  const [selectedTemplateName, setSelectedTemplateName] = useState('');
  const [internalFields, setInternalFields] = useState({});
  const [internalLecturers, setInternalLecturers] = useState({
    dosen_pembimbing: null,
    ketua_program_studi_ilmu_komputer: null,
  });

  const [jenis, setJenis] = useState('');
  const [keperluan, setKeperluan] = useState('');
  const [lecturerQuery, setLecturerQuery] = useState('');
  const [lecturerOptions, setLecturerOptions] = useState([]);
  const [selectedLecturers, setSelectedLecturers] = useState([]);
  const [lecturerSearchLoading, setLecturerSearchLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (mode !== 'internal') return;
    const fetchTemplates = async () => {
      setIsLoadingTemplates(true);
      try {
        const res = await api.get('/api/surat/templates/internal');
        setTemplates(res.data || []);
        if (res.data?.length && !selectedTemplateName) {
          setSelectedTemplateName(res.data[0].name);
        }
      } catch (err) {
        setError(getErrorMessage(err, 'Gagal memuat jenis surat internal'));
      } finally {
        setIsLoadingTemplates(false);
      }
    };
    fetchTemplates();
  }, [mode, selectedTemplateName]);

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.name === selectedTemplateName) || null,
    [templates, selectedTemplateName]
  );

  useEffect(() => {
    const keyword = lecturerQuery.trim();
    if (!keyword) {
      setLecturerOptions([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setLecturerSearchLoading(true);
      try {
        const res = await api.get('/api/auth/lecturers/search', {
          params: { q: keyword, limit: 10 },
        });
        setLecturerOptions(res.data || []);
      } catch (err) {
        setLecturerOptions([]);
      } finally {
        setLecturerSearchLoading(false);
      }
    }, 250);

    return () => clearTimeout(timeout);
  }, [lecturerQuery]);

  const addLecturer = (lecturer) => {
    setSelectedLecturers((prev) => {
      if (prev.some((item) => item.id === lecturer.id)) return prev;
      return [...prev, lecturer];
    });
    setLecturerQuery('');
    setLecturerOptions([]);
  };

  const removeLecturer = (lecturerId) => {
    setSelectedLecturers((prev) => prev.filter((item) => item.id !== lecturerId));
  };

  const deriveKeperluanFromFields = () => {
    if (internalFields.alasan_pembatalan_kuliah?.trim()) {
      return internalFields.alasan_pembatalan_kuliah.trim();
    }
    if (internalFields.nama_mata_kuliah?.trim()) {
      return `Pembatalan mata kuliah ${internalFields.nama_mata_kuliah.trim()}`;
    }
    return 'Pengajuan surat internal';
  };

  const buildInternalPayload = () => {
    if (!selectedTemplate) {
      throw new Error('Pilih jenis surat internal terlebih dahulu');
    }

    const requiredFields = selectedTemplate.required_fields || [];
    const normalizedFields = {};
    const lecturerIds = [];

    for (const key of requiredFields) {
      if (LECTURER_FIELD_KEYS.has(key)) {
        const lecturer = internalLecturers[key];
        if (!lecturer) {
          throw new Error(`Field ${FIELD_LABELS[key]} wajib dipilih`);
        }
        normalizedFields[key] = lecturer.name;
        lecturerIds.push(lecturer.id);
        continue;
      }

      const value = (internalFields[key] || '').trim();
      if (!value) {
        throw new Error('Field ' + (FIELD_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())) + ' wajib diisi');
      }
      normalizedFields[key] = value;
    }

    return {
      jenis: selectedTemplate.name,
      keperluan: deriveKeperluanFromFields(),
      fields: normalizedFields,
      lecturer_ids: lecturerIds.length ? lecturerIds : null,
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (mode === 'internal') {
        const payload = buildInternalPayload();
        await api.post('/api/surat/internal', payload);
      } else {
        if (!file) { 
          setError('File PDF wajib diupload'); 
          setSubmitting(false); 
          return; 
        }
        const form = new FormData();
        form.append('jenis', jenis);
        form.append('keperluan', keperluan);
        if (selectedLecturers.length > 0) {
          form.append('lecturer_ids', selectedLecturers.map((item) => item.id).join(','));
        }
        form.append('file', file);
        await api.post('/api/surat/external', form);
      }
      toast.success('Surat berhasil dibuat');
      navigate('/dashboard/mahasiswa');
    } catch (err) {
      setError(getErrorMessage(err, 'Gagal membuat surat'));
    } finally {
      setSubmitting(false);
    }
  };

  const renderLecturerPicker = () => (
    <div className="pt-6 border-t border-sepia-200">
      <label className="block text-sm font-medium text-primary mb-2">Dosen Penandatangan (Opsional)</label>
      <p className="text-xs text-primary/60 mb-3">Jika surat memerlukan pengesahan dari dosen tertentu, tambahkan di sini.</p>
      <div className="relative">
        <input
          type="text"
          className="appearance-none block w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary sm:text-sm transition-colors"
          placeholder="Ketik nama atau NIP dosen..."
          value={lecturerQuery}
          onChange={(e) => setLecturerQuery(e.target.value)}
        />

        {lecturerQuery.trim() && (
          <div className="absolute z-10 mt-1 w-full bg-white border border-sepia-200 shadow-lg max-h-60 rounded-sm py-1 overflow-auto sm:text-sm">
            {lecturerSearchLoading && <div className="px-4 py-3 text-sm text-primary/50 italic">Mencari dosen...</div>}
            {!lecturerSearchLoading && lecturerOptions.length === 0 && (
              <div className="px-4 py-3 text-sm text-primary/50 italic">Dosen tidak ditemukan</div>
            )}
            {!lecturerSearchLoading && lecturerOptions.map((lecturer) => (
              <button
                key={lecturer.id}
                type="button"
                className="w-full text-left px-4 py-3 hover:bg-ivory focus:bg-ivory focus:outline-none transition-colors border-b border-sepia-200/50 last:border-0"
                onClick={() => addLecturer(lecturer)}
              >
                <div className="font-medium text-primary">{lecturer.name}</div>
                <div className="text-xs text-primary/60 mt-0.5">{lecturer.nip || '-'} &middot; {lecturer.email}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedLecturers.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {selectedLecturers.map((lecturer) => (
             <span key={lecturer.id} className="inline-flex items-center px-3 py-1.5 border border-sepia-200 bg-white text-primary rounded-sm text-xs font-medium shadow-sm">
              {lecturer.name}
              <button
                type="button"
                onClick={() => removeLecturer(lecturer.id)}
                className="ml-2 shrink-0 h-4 w-4 inline-flex items-center justify-center text-primary/40 hover:text-red-600 transition-colors focus:outline-none"
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );

  const renderPembatalanFields = () => {
    if (!selectedTemplate) return null;

    return (
      <div className="space-y-5 pt-6 border-t border-sepia-200">
        <h3 className="text-base font-serif text-primary">Detail Pembatalan</h3>
        {(selectedTemplate.required_fields || []).map((fieldKey) => {
          if (LECTURER_FIELD_KEYS.has(fieldKey)) {
            return (
              <LecturerSearchField
                key={fieldKey}
                label={FIELD_LABELS[fieldKey]}
                placeholder="Ketik nama atau NIP dosen..."
                helperText={fieldKey === 'dosen_pembimbing' ? 'Pilih dosen pembimbing dari hasil pencarian.' : 'Pilih ketua program studi dari hasil pencarian.'}
                selectedLecturer={internalLecturers[fieldKey]}
                onSelect={(lecturer) => setInternalLecturers((prev) => ({ ...prev, [fieldKey]: lecturer }))}
                onClear={() => setInternalLecturers((prev) => ({ ...prev, [fieldKey]: null }))}
              />
            );
          }

          return (
            <div key={fieldKey}>
              <label className="block text-sm font-medium text-primary mb-2">
                {FIELD_LABELS[fieldKey] || fieldKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </label>
              {fieldKey === 'alasan_pembatalan_kuliah' ? (
                <textarea
                  rows={4}
                  className="appearance-none block w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary sm:text-sm transition-colors"
                  value={internalFields[fieldKey] || ''}
                  onChange={(e) => setInternalFields((prev) => ({ ...prev, [fieldKey]: e.target.value }))}
                  required
                  placeholder="Jelaskan alasan pembatalan secara singkat dan jelas"
                />
              ) : (
                <input
                  type="text"
                  className="appearance-none block w-full px-4 py-3 bg-ivory border border-sepia-200 rounded-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary sm:text-sm transition-colors"
                  value={internalFields[fieldKey] || ''}
                  onChange={(e) => setInternalFields((prev) => ({ ...prev, [fieldKey]: e.target.value }))}
                  required
                  placeholder={fieldKey === 'semester' ? 'Contoh: 4' : fieldKey === 'tahun_akademik' ? 'Contoh: 2024/2025 Genap' : ''}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
    >
      <div className="mb-12">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Pengajuan &middot; Formulir Baru</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Penerbitan <span className="italic">dokumen baru.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Buat surat resmi menggunakan kerangka standar akademik (Internal) atau serahkan draft independen (Eksternal).
            </p>
          </div>
          <Link to="/dashboard/mahasiswa" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Kembali ke Arsip
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-900 text-sm rounded-sm">
          {error}
        </div>
      )}

      <div className="bg-white border border-sepia-200 rounded-sm shadow-sm overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-sepia-200 bg-ivory border-t border-t-transparent border-l border-l-transparent border-r border-r-transparent">
          <button
            type="button"
            className={`flex-1 py-4 px-6 text-sm font-medium text-center transition-colors border-b-2 ${mode === 'internal' ? 'bg-white text-primary border-primary' : 'text-primary/50 hover:text-primary hover:bg-white/50 border-transparent'}`}
            onClick={() => setMode('internal')}
          >
            Internal (Template Resmi)
          </button>
          <button
            type="button"
            className={`flex-1 py-4 px-6 text-sm font-medium text-center transition-colors border-b-2 ${mode === 'external' ? 'bg-white text-primary border-primary' : 'text-primary/50 hover:text-primary hover:bg-white/50 border-transparent'}`}
            onClick={() => setMode('external')}
          >
            Eksternal (Upload PDF)
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 sm:p-8">
          {mode === 'internal' && (
            <div className="space-y-8">
              <div>
                <label className="block text-base font-serif text-primary mb-4">Kerangka Dokumen</label>
                {isLoadingTemplates ? (
                  <div className="text-sm text-primary/50 italic py-4">Memuat kerangka surat...</div>
                ) : templates.length === 0 ? (
                  <div className="text-sm text-primary/50 italic py-4 border border-dashed border-sepia-200 rounded-sm p-4 bg-ivory">Belum ada kerangka dokumen (template) yang tersedia di sistem saat ini.</div>
                ) : (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {templates.map((template) => (
                      <button
                        key={template.id}
                        type="button"
                        className={`text-left p-5 border rounded-sm transition-all focus:outline-none ${selectedTemplateName === template.name ? 'bg-ivory-dark border-primary' : 'bg-white border-sepia-200 hover:border-primary/40'}`}
                        onClick={() => {
                          setSelectedTemplateName(template.name);
                          setInternalFields({});
                          setInternalLecturers({
                            dosen_pembimbing: null,
                            ketua_program_studi_ilmu_komputer: null,
                          });
                        }}
                      >
                        <span className="block text-sm font-medium text-primary mb-1">
                          {template.name}
                        </span>
                        <span className="block text-xs text-primary/60">
                          {template.description}
                        </span>
                      </button>
                    ))}
                    <div className="p-5 border rounded-sm bg-ivory-dark border-sepia-200 border-dashed opacity-90">
                      <span className="block text-sm font-medium text-primary mb-1">Coming Soon</span>
                      <span className="block text-xs text-primary/60">
                        Template surat internal lain sedang disiapkan untuk rilis berikutnya.
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {renderPembatalanFields()}
            </div>
          )}

          <div className="mt-10 pt-6 border-t border-sepia-200">
             <button
              type="submit"
              disabled={submitting}
              className="w-full flex justify-center py-4 px-6 border border-transparent rounded-sm shadow-sm text-sm font-medium tracking-wider uppercase text-white bg-primary hover:bg-primary-dark focus:outline-none disabled:opacity-50 transition-all"
            >
              {submitting ? 'Sedang memproses...' : 'Serahkan Pengajuan'}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}
