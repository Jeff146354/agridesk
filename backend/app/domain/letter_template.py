from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LetterTemplate:
    """Domain entity representing an internal letter template."""

    id: Optional[int] = None
    name: str = ""
    description: str = ""
    template_path: str = ""
    required_fields: List[str] = field(default_factory=list)

    def get_template(self) -> str:
        return self.template_path

    def validate_fields(self, provided_fields: dict) -> List[str]:
        """Return a list of field names that are missing or blank."""
        invalid: List[str] = []
        for f in self.required_fields:
            value = provided_fields.get(f)
            if not isinstance(value, str) or not value.strip():
                invalid.append(f)
        return invalid
