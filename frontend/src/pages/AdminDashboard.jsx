import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';
import { getErrorMessage } from '../utils/error';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import TableSkeleton from '../components/TableSkeleton';
import EmptyState from '../components/EmptyState';

const STATUS_LABEL = {
  DRAFT: 'Draft',
  MENUNGGU_TTD_DOSEN: 'Menunggu Dosen',
  MENUNGGU_PROSES_ADMIN: 'Menunggu Admin',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
};

const STATUS_COLORS = {
  DRAFT: 'bg-sepia-200 text-primary border-transparent',
  MENUNGGU_TTD_DOSEN: 'bg-ivory-dark text-primary border-sepia-200',
  MENUNGGU_PROSES_ADMIN: 'bg-ivory-dark text-primary border-sepia-200',
  SELESAI: 'bg-primary/5 text-primary border-primary/20',
  DITOLAK: 'bg-red-50 text-red-900 border-red-200',
};

export default function AdminDashboard() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('id_desc');

  const load = () => {
    api.get('/api/surat/pending')
      .then((res) => setPending(res.data))
      .catch(err => setError(getErrorMessage(err, 'Gagal memuat antrean pending')))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const visiblePending = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    let items = [...pending];

    if (keyword) {
      items = items.filter((item) => {
        const haystack = [item.jenis, item.keperluan, item.mahasiswa_nim, String(item.id)].join(' ').toLowerCase();
        return haystack.includes(keyword);
      });
    }

    items.sort((a, b) => {
      if (sortBy === 'id_asc') return a.id - b.id;
      if (sortBy === 'jenis_asc') return String(a.jenis || '').localeCompare(String(b.jenis || ''), 'id');
      return b.id - a.id;
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
        <p className="text-[10px] tracking-widest text-primary/50 uppercase mb-4">Antrean &middot; Persetujuan Akhir</p>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-serif text-primary mb-3">
              Meja <span className="italic">Administrasi.</span>
            </h1>
            <p className="text-sm text-primary/70 leading-relaxed">
              Surat-surat di bawah ini telah ditandatangani dan menunggu pengesahan resmi (penerbitan nomor surat dan stempel digital).
            </p>
          </div>
          <Link to="/surat/all" className="shrink-0 px-6 py-3 border border-sepia-200 text-primary hover:border-primary transition-colors text-sm font-medium rounded-sm bg-ivory">
            Lihat Arsip Lengkap
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
            <p className="text-xs text-primary/60 mt-1">Perlu tindakan segera.</p>
          </div>
          <div className="w-full md:w-auto flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari NIM, surat..."
              className="w-full sm:w-64 px-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
            />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full sm:w-auto px-4 py-2 bg-ivory border border-sepia-200 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-sm transition-colors"
            >
              <option value="id_desc">Terbaru</option>
              <option value="id_asc">Terlama</option>
              <option value="jenis_asc">Jenis Surat</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory border-b border-sepia-200">
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Kode</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Surat & Pemohon</th>
                <th className="py-4 px-6 text-[10px] font-medium tracking-widest text-primary/50 uppercase">Keperluan</th>
                <th className="py-4 px-6 text-right text-[10px] font-medium tracking-widest text-primary/50 uppercase">Tindakan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sepia-200">
              {visiblePending.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-0">
                    <EmptyState 
                      message={pending.length === 0 ? "Meja kerja bersih" : "Pencarian tidak ditemukan"}
                      subMessage={pending.length === 0 ? "Tidak ada surat yang perlu disahkan." : "Coba kata kunci lain."}
                    />
                  </td>
                </tr>
              ) : (
                visiblePending.map((s) => (
                  <tr key={s.id} className="hover:bg-ivory/50 transition-colors group">
                    <td className="py-5 px-6 text-xs text-primary/60 font-mono">
                      SR-2026-{String(s.id).padStart(4, '0')}
                    </td>
                    <td className="py-5 px-6">
                      <p className="text-sm font-medium text-primary">{s.jenis}</p>
                      <p className="text-xs text-primary/60 mt-1">{s.mahasiswa_name || s.mahasiswa_nim}</p>
                    </td>
                    <td className="py-5 px-6 text-xs text-primary/70 max-w-[200px] truncate">
                      {s.keperluan}
                    </td>
                    <td className="py-5 px-6 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => {
                          const token = localStorage.getItem('token') || '';
                          const url = `http://127.0.0.1:8000/api/surat/${s.id}/pdf?token=${encodeURIComponent(token)}`;
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
      </div>
    </motion.div>
  );
}
