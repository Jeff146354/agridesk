import json
from typing import Optional, List

from sqlalchemy.orm import Session

from app.domain.letter_template import LetterTemplate
from app.models.letter_template import LetterTemplateModel


class LetterTemplateRepository:
    """Persistence layer for LetterTemplate.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: LetterTemplateModel) -> LetterTemplate:
        required_fields: List[str] = []
        if model.required_fields:
            try:
                parsed = json.loads(model.required_fields)
                if isinstance(parsed, list):
                    required_fields = [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass

        return LetterTemplate(
            id=model.id,
            name=model.name,
            description=model.description or "",
            template_path=model.template_path,
            required_fields=required_fields,
        )

    # ------------------------------------------------------------------
    # Query operations — return domain entities
    # ------------------------------------------------------------------

    def get_internal_templates(self) -> List[LetterTemplate]:
        models = (
            self.db.query(LetterTemplateModel)
            .order_by(LetterTemplateModel.id.asc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_name(self, name: str) -> Optional[LetterTemplate]:
        model = (
            self.db.query(LetterTemplateModel)
            .filter(LetterTemplateModel.name == name)
            .first()
        )
        return self._to_domain(model) if model else None
