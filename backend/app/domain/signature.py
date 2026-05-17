from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.domain.enums import UserRole
from app.domain.exceptions import UnauthorizedError, ValidationError


@dataclass
class Signature:
    """Domain entity representing a signature on a letter."""

    id: Optional[int] = None
    surat_id: Optional[int] = None
    owner_id: Optional[int] = None
    role: UserRole = UserRole.MAHASISWA
    image_path: Optional[str] = None
    signature_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Signature placement
    page_number: int = 1
    signing_order: Optional[int] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_width: Optional[float] = 120.0
    pos_height: Optional[float] = 60.0
    owner_email: Optional[str] = None

    # Read-only display fields populated by the repository layer.
    surat_jenis: Optional[str] = None
    mahasiswa_name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_nip: Optional[str] = None

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def sign(self, image_path: str, signature_hash: str) -> None:
        """Sign this signature record.

        Validates that it has not been signed yet, then records the
        image, hash and timestamp.
        """
        if self.is_signed():
            raise ValidationError("Sudah ditandatangani")
        self.image_path = image_path
        self.signed_at = datetime.now(timezone.utc)
        self.signature_hash = signature_hash

    def validate_owner(self, user_id: int) -> None:
        """Raise if *user_id* is not the owner of this signature."""
        if self.owner_id != user_id:
            raise UnauthorizedError("Bukan tanda tangan Anda")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def is_signed(self) -> bool:
        return self.signed_at is not None

