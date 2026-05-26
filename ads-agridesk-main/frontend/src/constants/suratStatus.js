export const SURAT_STATUS_LABELS = {
  DRAFT: 'Draft',
  MENUNGGU_TTD_DOSEN: 'Menunggu Dosen',
  MENUNGGU_PROSES_ADMIN: 'Menunggu Admin',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
};

export const SURAT_STATUS_COLORS = {
  DRAFT: 'bg-sepia-200 text-primary border-transparent',
  MENUNGGU_TTD_DOSEN: 'bg-ivory-dark text-primary border-sepia-200',
  MENUNGGU_PROSES_ADMIN: 'bg-ivory-dark text-primary border-sepia-200',
  SELESAI: 'bg-primary/5 text-primary border-primary/20',
  DITOLAK: 'bg-red-50 text-red-900 border-red-200',
};

export const SURAT_FILTERS = ['ALL', 'SELESAI', 'DITOLAK', 'MENUNGGU'];

export const SURAT_FILTER_LABELS = {
  ALL: 'Semua',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
  MENUNGGU: 'Menunggu',
};
