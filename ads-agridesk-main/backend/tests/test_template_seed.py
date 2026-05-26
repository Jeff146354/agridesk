from app.utils.template_seed import seed_default_internal_templates
from app.models.surat_template import SuratTemplateModel

def test_seed_default_internal_templates_inserts_missing_template(db):
    created = seed_default_internal_templates(db)

    templates = db.query(SuratTemplateModel).all()
    assert created is True
    assert len(templates) == 2
    assert templates[1].jenis == "Surat Pembatalan Mata Kuliah"

def test_seed_default_internal_templates_is_idempotent(db):
    first = seed_default_internal_templates(db)
    second = seed_default_internal_templates(db)

    templates = db.query(SuratTemplateModel).all()
    assert first is True
    assert second is False
    assert len(templates) == 2