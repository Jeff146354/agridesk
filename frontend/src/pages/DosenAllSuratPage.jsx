import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const STATUS_STYLE = {
  MENUNGGU_TTD: 'bg-ivory-dark text-primary border-sepia-200',
  SUDAH_TTD: 'bg-primary/5 text-primary border-primary/20',
  DITOLAK: 'bg-red-50 text-red-900 border-red-200',
};

export default function DosenAllSuratPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const resetFilters = () => {
    setSearch('');
    setStatusFilter('ALL');
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.get('/api/signatures/pending'),
      api.get('/api/signatures/signed'),
    ])
      .then(([pendingRes, signedRes]) => {
        const pendingRows = (pendingRes.data || []).map((sig) => ({
          ...sig,
          statusLabel: 'MENUNGGU_TTD',
        }));
        const signedRows = (signedRes.data || []).map((sig) => ({
          ...sig,
          statusLabel: sig.signed_at ? 'SUDAH_TTD' : 'DITOLAK',
        }));

        const merged = [...pendingRows, ...signedRows];
        const uniqueBySignature = Array.from(new Map(merged.map((item) => [item.id, item])).values());

        uniqueBySignature.sort((a, b) => {
          const aTime = a.signed_at ? new Date(a.signed_at).getTime() : 0;
          const bTime = b.signed_at ? new Date(b.signed_at).getTime() : 0;
          if (aTime !== bTime) return bTime - aTime;
          return b.id - a.id;
        });

        setRows(uniqueBySignature);
      })
      .finally(() => setLoading(false));
  }, []);

  const summary = useMemo(() => {
    return {
      pending: rows.filter((r) => r.statusLabel === 'MENUNGGU_TTD').length,
      signed: rows.filter((r) => r.statusLabel === 'SUDAH_TTD').length,
      rejected: rows.filter((r) => r.statusLabel === 'DITOLAK').length,
    };
  }, [rows]);

  const visibleRows = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    let items = [...rows];

    if (statusFilter !== 'ALL') {
      items = items.filter((item) => item.statusLabel === statusFilter);
    }

    if (keyword) {
      items = items.filter((item) => {
        const haystack = [item.surat_jenis, item.mahasiswa_name, String(item.surat_id)].join(' ').toLowerCase();
        return haystack.includes(keyword);
      });
    }

    return items;
  }, [rows, search, statusFilter]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-pulse flex space-x-4">
          <div className="h-12 w-12 bg-sepia-200 rounded-sm"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-12">
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Arsip &middot; Tugas Dosen</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Riwayat <span className="italic">penugasan.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Catatan lengkap seluruh surat yang pernah melewati meja Anda. Baik yang sudah ditandatangani maupun yang ditolak.
            </p>
          </div>
          <Link to="/dashboard/dosen" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Ke Antrean Pending
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border border-sepia-200 rounded-sm bg-white mb-12">
        <div className="p-8 border-b md:border-b-0 md:border-r border-sepia-200 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-primary/30"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Menunggu TTD</p>
          <p className="text-5xl font-serif text-primary">
            {String(summary.pending).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
          </p>
        </div>
        <div className="p-8 border-b md:border-b-0 md:border-r border-sepia-200 relative">
          <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-green-700"></div>
          <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Sudah TTD</p>
          <p className="text-5xl font-serif text-primary">
            {String(summary.signed).padStart(2, '0')}<span className="text-sm font-sans text-primary/50 ml-2">surat</span>
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
                placeholder="Cari surat, pemohon..."
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
          {['ALL', 'SUDAH_TTD', 'DITOLAK', 'MENUNGGU_TTD'].map(filter => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-4 py-1.5 text-xs font-medium rounded-full border transition-colors ${
                statusFilter === filter 
                  ? 'bg-primary text-white border-primary' 
                  : 'bg-transparent text-primary/70 border-sepia-200 hover:border-primary/40'
              }`}
            >
              {filter === 'ALL' ? 'Semua' : filter === 'SUDAH_TTD' ? 'Sudah TTD' : filter === 'DITOLAK' ? 'Ditolak' : 'Menunggu'}
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
              {visibleRows.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-sm text-primary/50 italic">
                    Tidak ada catatan yang ditemukan.
                  </td>
                </tr>
              ) : (
                visibleRows.map((sig) => (
                  <tr key={sig.id} className="hover:bg-ivory/50 transition-colors group">
                    <td className="py-5 px-6 text-xs text-primary/60 font-mono">
                      SR-2026-{String(sig.surat_id).padStart(4, '0')}
                    </td>
                    <td className="py-5 px-6">
                      <p className="text-sm font-medium text-primary">{sig.surat_jenis || '-'}</p>
                    </td>
                    <td className="py-5 px-6">
                      <p className="text-sm font-medium text-primary">{sig.mahasiswa_name || '-'}</p>
                    </td>
                    <td className="py-5 px-6">
                      <span className={`inline-block px-2.5 py-1 text-[10px] font-medium tracking-wider uppercase border rounded-sm ${STATUS_STYLE[sig.statusLabel]}`}>
                        {sig.statusLabel === 'MENUNGGU_TTD' ? 'Menunggu' : sig.statusLabel === 'SUDAH_TTD' ? 'Selesai TTD' : 'Ditolak'}
                      </span>
                    </td>
                    <td className="py-5 px-6 text-xs text-primary/70">
                      {sig.signed_at ? new Date(sig.signed_at).toLocaleString('id-ID', { dateStyle: 'long', timeStyle: 'short' }) : '-'}
                    </td>
                    <td className="py-5 px-6 text-right">
                      <Link to={`/surat/${sig.surat_id}`} className="text-xs font-medium px-4 py-1.5 border border-sepia-200 text-primary hover:border-primary transition-colors rounded-sm bg-white shadow-sm">
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
