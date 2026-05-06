import { useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { useListData } from '../hooks/useListData';
import {
  SURAT_FILTERS,
  SURAT_FILTER_LABELS,
  SURAT_STATUS_COLORS,
  SURAT_STATUS_LABELS,
} from '../constants/suratStatus';

export default function AllSuratPage() {
  const fetchLetters = useCallback(() => {
    return api.get('/api/surat/all').then((res) => res.data);
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
        const haystack = [
          item.jenis,
          item.keperluan,
          item.mahasiswa_nim,
          item.mahasiswa_name,
          String(item.id),
        ].join(' ').toLowerCase();
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
    fallbackError: 'Gagal memuat arsip surat',
  });

  const statusFilter = filters.status ?? 'ALL';
  const setStatusFilter = (value) => {
    setFilters((prev) => ({ ...prev, status: value }));
  };

  const statusLabels = { ...SURAT_STATUS_LABELS, SELESAI: 'Diterima' };
  const filterLabels = { ...SURAT_FILTER_LABELS, SELESAI: 'Diterima' };

  const resetFilters = () => {
    setSearch('');
    setFilters((prev) => ({ ...prev, status: 'ALL' }));
  };

  const summary = useMemo(() => {
    return {
      pending: letters.filter((item) => item.status === 'MENUNGGU_TTD_DOSEN' || item.status === 'MENUNGGU_PROSES_ADMIN').length,
      done: letters.filter((item) => item.status === 'SELESAI').length,
      rejected: letters.filter((item) => item.status === 'DITOLAK').length,
    };
  }, [letters]);

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-pulse flex space-x-4">
        <div className="h-12 w-12 bg-sepia-200 rounded-sm"></div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Arsip &middot; Semua Rekaman</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Riwayat <span className="italic">surat terbit.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Catatan lengkap seluruh surat yang pernah diajukan dalam sistem. Dapat diekspor untuk keperluan audit internal maupun laporan tahunan dekanat.
            </p>
          </div>
          <Link to="/dashboard/admin" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Ke Antrean Pending
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
            {String(summary.pending).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
        <div className="p-8 border-b md:border-b-0 md:border-r border-sepia-200 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-green-700"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Diterima</p>
          <p className="text-5xl font-serif text-primary">
            {String(summary.done).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
        <div className="p-8 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-red-700"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Ditolak</p>
          <p className="text-5xl font-serif text-primary">
            {String(summary.rejected).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white border border-sepia-200 rounded-sm">
        <div className="p-6 border-b border-sepia-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h3 className="text-lg font-serif text-primary">Seluruh Catatan</h3>
            <p className="text-xs text-primary/60 mt-1">Diurutkan dari yang terbaru. Klik baris untuk melihat detail.</p>
          </div>
          <div className="w-full md:w-auto flex items-center gap-3">
            <div className="relative w-full md:w-64">
              <svg className="absolute left-3 top-2.5 w-4 h-4 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari surat, pemohon, atau kode"
                className="w-full pl-9 pr-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
              />
            </div>
            <button onClick={resetFilters} className="text-xs font-medium text-primary hover:text-primary-dark whitespace-nowrap">
              Setel ulang
            </button>
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
              {filterLabels[filter] || filter}
            </button>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory border-b border-sepia-200">
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Kode</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Surat</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Pemohon</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Status</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Waktu Update</th>
                <th className="py-4 px-6 text-right text-[10px] font-medium tracking-widest text-primary/50 uppercase">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sepia-200">
              {visibleLetters.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-sm text-primary/50 italic">
                    Tidak ada catatan yang ditemukan.
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
                      <p className="text-sm font-medium text-primary">{s.mahasiswa_name || '-'}</p>
                      <p className="text-[10px] text-primary/60 mt-0.5">{s.mahasiswa_nim || '-'}</p>
                    </td>
                    <td className="py-5 px-6">
                      <span className={`inline-block px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm ${SURAT_STATUS_COLORS[s.status] || SURAT_STATUS_COLORS.DRAFT}`}>
                        {statusLabels[s.status] || s.status}
                      </span>
                    </td>
                    <td className="py-5 px-6 text-xs text-primary/70">
                      {s.updated_at ? new Date(s.updated_at).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }) : '-'}
                    </td>
                    <td className="py-5 px-6 text-right">
                      <Link to={`/surat/${s.id}`} className="text-xs font-medium px-4 py-1.5 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-white shadow-sm">
                        Detail
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
