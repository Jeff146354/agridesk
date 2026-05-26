import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.surat_template import SuratTemplateModel

INTERNAL_TEMPLATES = [
    {
        "jenis": "Surat Keterangan Aktif Kuliah",
        "title": "Surat Keterangan Aktif Kuliah",
        "fields": [
            {"name": "keperluan_surat_aktif", "label": "Keperluan", "type": "text"}
        ]
    },
    {
        "jenis": "Surat Pengantar Magang",
        "title": "Surat Pengantar Magang / PKL",
        "fields": [
            {"name": "mitra", "label": "Nama Mitra", "type": "text"},
            {"name": "alamat_mitra", "label": "Alamat Mitra", "type": "text"},
            {"name": "posisi", "label": "Posisi/Bagian", "type": "text"},
            {"name": "durasi", "label": "Durasi (Bulan)", "type": "number"}
        ]
    },
    {
        "jenis": "Surat Izin Penelitian",
        "title": "Surat Izin Penelitian",
        "fields": [
            {"name": "judul_penelitian", "label": "Judul Penelitian", "type": "text"},
            {"name": "lokasi", "label": "Lokasi Penelitian", "type": "text"}
        ]
    },
    {
        "jenis": "Surat Pembatalan Mata Kuliah",
        "title": "Surat Pembatalan Mata Kuliah (SPMK)",
        "fields": [
            {"name": "nama_mata_kuliah", "label": "Nama Mata Kuliah", "type": "text"},
            {"name": "kode_mata_kuliah", "label": "Kode MK", "type": "text"},
            {"name": "semester", "label": "Semester", "type": "number"},
            {"name": "tahun_akademik", "label": "Tahun Akademik", "type": "text"},
            {"name": "alasan_pembatalan_kuliah", "label": "Alasan Pembatalan", "type": "text"}
        ]
    }
]

def seed():
    with SessionLocal() as db:
        for t in INTERNAL_TEMPLATES:
            existing = db.query(SuratTemplateModel).filter_by(jenis=t["jenis"]).first()
            if not existing:
                model = SuratTemplateModel(
                    jenis=t["jenis"],
                    title=t["title"],
                    fields=t["fields"]
                )
                db.add(model)
        db.commit()
        print("Templates seeded successfully!")

if __name__ == "__main__":
    seed()
