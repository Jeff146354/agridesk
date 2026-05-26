from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LetterTemplate:
    """Domain entity representing an internal letter template."""

    id: Optional[int] = None
    jenis: str = ""
    title: str = ""
    fields: List[dict] = field(default_factory=list)

    def validate_fields(self, provided_fields: dict) -> List[str]:
        """Return a list of field names that are missing or blank."""
        invalid: List[str] = []
        for f in self.fields:
            name = f.get("name")
            if not name:
                continue
            value = provided_fields.get(name)
            if not isinstance(value, str) or not value.strip():
                invalid.append(name)
        return invalid