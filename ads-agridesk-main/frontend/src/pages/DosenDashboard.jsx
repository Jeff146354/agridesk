import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { getErrorMessage } from '../utils/error';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import TableSkeleton from '../components/TableSkeleton';
import EmptyState from '../components/EmptyState';
import { getApiBaseUrl } from '../utils/apiBaseUrl';

export default function DosenDashboard() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('surat_desc');

  const load = () => {
    setLoading(true);
    api.get('/api/signatures/pending')
      .then((pendingRes) => {
        // Group by surat_id to prevent redundant list items when a Dosen has multiple signature fields for one surat
        const uniqueItems = new Map();
        (pendingRes.data || []).forEach(item => {
          if (!uniqueItems.has(item.surat_id)) {
            uniqueItems.set(item.surat_id, item);
          }
        });
        setPending(Array.from(uniqueItems.values()));
      })
      .catch((err) => setError(getErrorMessage(err, 'Gagal memuat daftar antrean')))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const visiblePending = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    let items = [...pending];

    if (keyword) {
      items = items.filter((item) => {
        const haystack = [item.surat_jenis, item.mahasiswa_name, String(item.surat_id)].join(' ').toLowerCase();
        return haystack.includes(keyword);
      });
    }

    items.sort((a, b) => {
      if (sortBy === 'surat_asc') return Number(a.surat_id || 0) - Number(b.surat_id || 0);
      if (sortBy === 'jenis_asc') return String(a.surat_jenis || '').localeCompare(String(b.surat_jenis || ''), 'id');
      return Number(b.surat_id || 0) - Number(a.surat_id || 0);
    });

    return items;
  }, [pending, search, sortBy]);



  if (loading) return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <TableSkeleton rows={4} />
    </div>
  );

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
    >
      <div className="mb-12">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Antrean &middot; Tanda Tangan</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Meja <span className="italic">Kerja Anda.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Daftar surat yang memerlukan peninjauan dan tanda tangan digital Anda sebelum diproses lebih lanjut oleh pihak fakultas.
            </p>
          </div>
          <Link to="/surat/all-dosen" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Lihat Semua Riwayat
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-sm">
          {error}
        </div>
      )}

      {/* Table Section */}
      <div className="bg-white border border-sepia-200 rounded-sm">
        <div className="p-6 border-b border-sepia-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-lg font-serif text-primary">Tumpukan Map ({pending.length})</h3>
            <p className="text-xs text-primary/60 mt-1">Perlu ditandatangani segera.</p>
          </div>
          <div className="w-full md:w-auto flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari mahasiswa, surat..."
              className="w-full sm:w-64 px-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
            />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full sm:w-auto px-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
            >
              <option value="surat_desc">Terbaru</option>
              <option value="surat_asc">Terlama</option>
              <option value="jenis_asc">Jenis Surat</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory border-b border-sepia-200">
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Kode</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Surat & Pemohon</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Status</th>
                <th className="py-4 px-6 text-right text-[10px] font-medium tracking-widest text-primary/50 uppercase">Tindakan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sepia-200">
              {visiblePending.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-0">
                    <EmptyState 
                      message={pending.length === 0 ? "Meja kerja bersih" : "Pencarian tidak ditemukan"}
                      subMessage={pending.length === 0 ? "Tidak ada surat yang menunggu tanda tangan." : "Coba kata kunci lain."}
                    />
                  </td>
                </tr>
              ) : (
                visiblePending.map((sig) => (
                  <tr key={sig.id} className="hover:bg-ivory/50 transition-colors group">
                    <td className="py-5 px-6 text-xs text-primary/60 font-mono">
                      SR-2026-{String(sig.surat_id).padStart(4, '0')}
                    </td>
                    <td className="py-5 px-6">
                      <p className="text-sm font-medium text-primary">{sig.surat_jenis || '-'}</p>
                      <p className="text-xs text-primary/60 mt-1">{sig.mahasiswa_name || '-'}</p>
                    </td>
                    <td className="py-5 px-6">
                      <span className="inline-block px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm bg-ivory-dark text-primary border-sepia-200">
                        Menunggu Tanda Tangan
                      </span>
                    </td>
                    <td className="py-5 px-6 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => {
                          const token = localStorage.getItem('token') || '';
                          const url = `${getApiBaseUrl()}/api/surat/${sig.surat_id}/pdf?token=${encodeURIComponent(token)}`;
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `surat-${sig.surat_id}.pdf`;
                          link.target = '_blank';
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }} className="text-xs font-medium px-4 py-1.5 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-ivory group-hover:bg-white flex items-center gap-1">
                          Unduh PDF
                        </button>
                        <Link to={`/surat/${sig.surat_id}`} className="text-xs font-medium px-4 py-1.5 bg-primary text-white hover:bg-primary-dark transition-colors rounded-sm">
                          Detail
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile List View */}
        <div className="md:hidden flex flex-col divide-y divide-sepia-200">
          {visiblePending.length === 0 ? (
            <div className="p-4">
              <EmptyState 
                message={pending.length === 0 ? "Meja kerja bersih" : "Pencarian tidak ditemukan"}
                subMessage={pending.length === 0 ? "Tidak ada surat yang menunggu tanda tangan." : "Coba kata kunci lain."}
              />
            </div>
          ) : (
            visiblePending.map((sig) => (
              <div key={sig.id} className="p-4 hover:bg-ivory/50 transition-colors flex flex-col gap-3">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <span className="text-xs text-primary/60 font-mono block mb-1">
                      SR-2026-{String(sig.surat_id).padStart(4, '0')}
                    </span>
                    <p className="text-sm font-medium text-primary">{sig.surat_jenis || '-'}</p>
                    <p className="text-xs text-primary/60 mt-1">{sig.mahasiswa_name || '-'}</p>
                  </div>
                  <span className="shrink-0 px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm bg-ivory-dark text-primary border-sepia-200">
                    Menunggu Ttd
                  </span>
                </div>

                <div className="flex justify-end gap-2 mt-2">
                  <button onClick={() => {
                    const token = localStorage.getItem('token') || '';
                    const url = `${getApiBaseUrl()}/api/surat/${sig.surat_id}/pdf?token=${encodeURIComponent(token)}`;
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `surat-${sig.surat_id}.pdf`;
                    link.target = '_blank';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }} className="flex-1 justify-center text-xs font-medium px-4 py-2 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-ivory flex items-center gap-1">
                    Unduh PDF
                  </button>
                  <Link to={`/surat/${sig.surat_id}`} className="flex-1 text-center text-xs font-medium px-4 py-2 bg-primary text-white hover:bg-primary-dark transition-colors rounded-sm flex items-center justify-center">
                    Detail
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </motion.div>
  );
}
