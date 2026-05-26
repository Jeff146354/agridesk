from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.enums import UserRole


@dataclass
class User:
    """Core domain entity representing a system user."""

    id: Optional[int] = None
    name: str = ""
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.MAHASISWA
    nim: Optional[str] = None
    nip: Optional[str] = None
    signature_image_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Role queries
    # ------------------------------------------------------------------

    def is_mahasiswa(self) -> bool:
        return self.role == UserRole.MAHASISWA

    def is_dosen(self) -> bool:
        return self.role == UserRole.DOSEN

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def get_identifier(self) -> Optional[str]:
        """Return NIM for students, NIP for lecturers/admins."""
        if self.is_mahasiswa():
            return self.nim
        return self.nip

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def update_signature_image(self, path: str) -> None:
        """Set or replace the saved signature image."""
        self.signature_image_path = path
