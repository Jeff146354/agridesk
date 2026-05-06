from sqlalchemy.orm import Session

from app.models.letter_template import LetterTemplateModel


DEFAULT_INTERNAL_TEMPLATES = [
    {
        "name": "Surat Pembatalan Mata Kuliah",
        "description": "Surat pengajuan pembatalan mata kuliah tertentu.",
        "template_path": "templates/surat_pembatalan_mata_kuliah.pdf",
        "required_fields": '["nama_mata_kuliah", "kode_mata_kuliah", "semester", "tahun_akademik", "alasan_pembatalan_kuliah", "dosen_pembimbing", "ketua_program_studi_ilmu_komputer"]',
    }
]


def seed_default_internal_templates(db: Session) -> bool:
    """Insert default internal templates if they are missing.

    Returns True when at least one template was added.
    """
    created = False
    changed = False
    existing_names = {
        name for (name,) in db.query(LetterTemplateModel.name).all()
    }

    for template in DEFAULT_INTERNAL_TEMPLATES:
        existing = (
            db.query(LetterTemplateModel)
            .filter(LetterTemplateModel.name == template["name"])
            .first()
        )
        if existing:
            existing.description = template["description"]
            existing.template_path = template["template_path"]
            existing.required_fields = template["required_fields"]
            changed = True
            continue

        if template["name"] in existing_names:
            continue

        db.add(LetterTemplateModel(**template))
        created = True

    if created or changed:
        db.commit()

    return created