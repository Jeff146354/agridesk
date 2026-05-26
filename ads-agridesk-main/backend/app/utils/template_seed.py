from sqlalchemy.orm import Session
from app.models.surat_template import SuratTemplateModel

DEFAULT_INTERNAL_TEMPLATES = [
    {
        "jenis": "Surat Keterangan Aktif Kuliah",
        "title": "Surat Keterangan Aktif Kuliah",
        "fields": [
            {"name": "keperluan_surat_aktif", "label": "Keperluan", "type": "text"}
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

def seed_default_internal_templates(db: Session) -> bool:
    created = False
    
    for template in DEFAULT_INTERNAL_TEMPLATES:
        existing = db.query(SuratTemplateModel).filter(SuratTemplateModel.jenis == template["jenis"]).first()
        if existing:
            existing.title = template["title"]
            existing.fields = template["fields"]
            continue

        model = SuratTemplateModel(
            jenis=template["jenis"],
            title=template["title"],
            fields=template["fields"]
        )
        db.add(model)
        created = True

    db.commit()
    return created