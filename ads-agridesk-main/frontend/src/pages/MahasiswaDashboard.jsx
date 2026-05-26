import { useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { motion } from 'framer-motion';
import TableSkeleton from '../components/TableSkeleton';
import EmptyState from '../components/EmptyState';
import { useListData } from '../hooks/useListData';
import { SURAT_FILTERS,
  SURAT_FILTER_LABELS,
  SURAT_STATUS_COLORS,
  SURAT_STATUS_LABELS,
} from '../constants/suratStatus';
import { getApiBaseUrl } from '../utils/apiBaseUrl';

export default function MahasiswaDashboard() {
  const fetchLetters = useCallback(() => {
    return api.get('/api/surat/my').then((res) => res.data.items || res.data);
  }, []);

  const filterLetters = useCallback((items, keywordInput, currentFilters) => {
    const keyword = keywordInput.trim().toLowerCase();
    const status = currentFilters?.status ?? 'ALL';
    let filtered = [...items];

    if (status !== 'ALL') {
      if (status === 'MENUNGGU') {
        filtered = filtered.filter((item) => (
          item.status === 'MENUNGGU_TTD_DOSEN' || item.status === 'MENUNGGU_PROSES_ADMIN'
        ));
      } else {
        filtered = filtered.filter((item) => item.status === status);
      }
    }

    if (keyword) {
      filtered = filtered.filter((item) => {
        const haystack = [item.jenis, item.keperluan, String(item.id)].join(' ').toLowerCase();
        return haystack.includes(keyword);
      });
    }

    return filtered.sort((a, b) => b.id - a.id);
  }, []);

  const {
    items: letters,
    filtered: visibleLetters,
    loading,
    error,
    search,
    setSearch,
    filters,
    setFilters,
  } = useListData({
    fetcher: fetchLetters,
    filterFn: filterLetters,
    initialFilters: { status: 'ALL' },
    fallbackError: 'Gagal memuat data surat',
  });

  const statusFilter = filters.status ?? 'ALL';
  const setStatusFilter = (value) => {
    setFilters((prev) => ({ ...prev, status: value }));
  };

  const stats = useMemo(() => {
    return {
      menunggu: letters.filter(l => l.status === 'MENUNGGU_TTD_DOSEN' || l.status === 'MENUNGGU_PROSES_ADMIN').length,
      selesai: letters.filter(l => l.status === 'SELESAI').length,
      ditolak: letters.filter(l => l.status === 'DITOLAK').length,
    };
  }, [letters]);

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
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Arsip &middot; Pengajuan Saya</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Riwayat <span className="italic">surat Anda.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Catatan lengkap surat yang pernah Anda ajukan. Pantau status pengajuan atau unduh dokumen yang telah disetujui.
            </p>
          </div>
          <Link to="/surat/new" className="shrink-0 px-6 py-3 border border-primary text-primary hover:bg-primary hover:text-white transition-colors text-sm font-medium rounded-sm">
            Buat Pengajuan Baru
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-sm">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border border-sepia-200 rounded-sm bg-white mb-12">
        <div className="p-8 border-b md:border-b-0 md:border-r border-sepia-200 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-primary/30"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Menunggu Persetujuan</p>
          <p className="text-5xl font-serif text-primary">
            {String(stats.menunggu).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
        <div className="p-8 border-b md:border-b-0 md:border-r border-sepia-200 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-green-700"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Selesai</p>
          <p className="text-5xl font-serif text-primary">
            {String(stats.selesai).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
        <div className="p-8 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-red-700"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Ditolak</p>
          <p className="text-5xl font-serif text-primary">
            {String(stats.ditolak).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white border border-sepia-200 rounded-sm">
        <div className="p-6 border-b border-sepia-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-lg font-serif text-primary">Seluruh Catatan</h3>
            <p className="text-xs text-primary/60 mt-1">Diurutkan dari yang terbaru.</p>
          </div>
          <div className="w-full md:w-auto">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari kode, surat..."
              className="w-full md:w-64 px-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
            />
          </div>
        </div>

        {/* Filter Chips */}
        <div className="px-6 py-4 border-b border-sepia-200 flex flex-wrap gap-2">
          {SURAT_FILTERS.map((filter) => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-4 py-1.5 text-xs font-medium rounded-full border transition-colors ${
                statusFilter === filter 
                  ? 'bg-primary text-white border-primary' 
                  : 'bg-transparent text-primary/70 border-sepia-200 hover:border-primary/40'
              }`}
            >
              {SURAT_FILTER_LABELS[filter] || filter}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto hidden md:block">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory border-b border-sepia-200">
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Kode</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Surat</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Status</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Keperluan</th>
                <th className="py-4 px-6 text-right text-[10px] font-medium tracking-widest text-primary/50 uppercase">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sepia-200">
              {visibleLetters.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-0">
                    <EmptyState 
                      message={letters.length === 0 ? "Belum ada pengajuan" : "Pencarian tidak ditemukan"}
                      subMessage={letters.length === 0 ? "Anda belum mengajukan surat apapun." : "Coba kata kunci lain."}
                    />
                  </td>
                </tr>
              ) : (
                visibleLetters.map((s) => (
                  <tr key={s.id} className="hover:bg-ivory/50 transition-colors group">
                    <td className="py-5 px-6 text-xs text-primary/60 font-mono">
                      SR-2026-{String(s.id).padStart(4, '0')}
                    </td>
                    <td className="py-5 px-6">
                      <p className="text-sm font-medium text-primary">{s.jenis}</p>
                    </td>
                    <td className="py-5 px-6">
                      <span className={`inline-block px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm ${SURAT_STATUS_COLORS[s.status] || SURAT_STATUS_COLORS.DRAFT}`}>
                        {SURAT_STATUS_LABELS[s.status] || s.status}
                      </span>
                    </td>
                    <td className="py-5 px-6 text-xs text-primary/70 max-w-[200px] truncate">
                      {s.keperluan}
                    </td>
                    <td className="py-5 px-6 text-right">
                      <div className="flex justify-end gap-2">
                          <button onClick={() => {
                            const token = localStorage.getItem('token') || '';
                            const url = `${getApiBaseUrl()}/api/surat/${s.id}/pdf?token=${encodeURIComponent(token)}`;
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = `surat-${s.id}.pdf`;
                            link.target = '_blank';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                          }} className="text-xs font-medium px-4 py-1.5 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-ivory group-hover:bg-white flex items-center gap-1">
                            Unduh PDF
                          </button>
                        <Link to={`/surat/${s.id}`} className="text-xs font-medium px-4 py-1.5 bg-primary text-white hover:bg-primary-dark transition-colors rounded-sm">
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
          {visibleLetters.length === 0 ? (
            <div className="p-4">
              <EmptyState 
                message={letters.length === 0 ? "Belum ada pengajuan" : "Pencarian tidak ditemukan"}
                subMessage={letters.length === 0 ? "Anda belum mengajukan surat apapun." : "Coba kata kunci lain."}
              />
            </div>
          ) : (
            visibleLetters.map((s) => (
              <div key={s.id} className="p-4 hover:bg-ivory/50 transition-colors flex flex-col gap-3">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <span className="text-xs text-primary/60 font-mono block mb-1">
                      SR-2026-{String(s.id).padStart(4, '0')}
                    </span>
                    <p className="text-sm font-medium text-primary">{s.jenis}</p>
                  </div>
                  <span className={`shrink-0 px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm ${SURAT_STATUS_COLORS[s.status] || SURAT_STATUS_COLORS.DRAFT}`}>
                    {SURAT_STATUS_LABELS[s.status] || s.status}
                  </span>
                </div>
                
                <p className="text-xs text-primary/70 line-clamp-2">
                  {s.keperluan}
                </p>

                <div className="flex justify-end gap-2 mt-2">
                  <button onClick={() => {
                    const token = localStorage.getItem('token') || '';
                    const url = `${getApiBaseUrl()}/api/surat/${s.id}/pdf?token=${encodeURIComponent(token)}`;
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `surat-${s.id}.pdf`;
                    link.target = '_blank';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }} className="flex-1 justify-center text-xs font-medium px-4 py-2 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-ivory flex items-center gap-1">
                    Unduh PDF
                  </button>
                  <Link to={`/surat/${s.id}`} className="flex-1 text-center text-xs font-medium px-4 py-2 bg-primary text-white hover:bg-primary-dark transition-colors rounded-sm flex items-center justify-center">
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
