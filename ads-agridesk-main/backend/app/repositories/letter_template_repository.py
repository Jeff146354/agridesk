import json
from typing import Optional, List

from sqlalchemy.orm import Session

from app.domain.letter_template import LetterTemplate
from app.models.surat_template import SuratTemplateModel


class LetterTemplateRepository:
    """Persistence layer for LetterTemplate.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: SuratTemplateModel) -> LetterTemplate:
        fields_list: List[dict] = []
        if model.fields:
            if isinstance(model.fields, list):
                fields_list = model.fields
            elif isinstance(model.fields, str):
                try:
                    fields_list = json.loads(model.fields)
                except json.JSONDecodeError:
                    pass
            elif isinstance(model.fields, dict):
                fields_list = [model.fields]

        return LetterTemplate(
            id=model.id,
            jenis=model.jenis,
            title=model.title,
            fields=fields_list,
        )

    # ------------------------------------------------------------------
    # Query operations — return domain entities
    # ------------------------------------------------------------------

    def get_internal_templates(self) -> List[LetterTemplate]:
        models = (
            self.db.query(SuratTemplateModel)
            .order_by(SuratTemplateModel.id.asc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_name(self, jenis: str) -> Optional[LetterTemplate]:
        model = (
            self.db.query(SuratTemplateModel)
            .filter(SuratTemplateModel.jenis == jenis)
            .first()
        )
        return self._to_domain(model) if model else None
