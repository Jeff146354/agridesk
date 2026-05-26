from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set

from app.domain.enums import SuratStatus
from app.domain.exceptions import InvalidStateTransitionError, ValidationError


# Valid state-transition map — enforced by every status change.
_VALID_TRANSITIONS: Dict[SuratStatus, Set[SuratStatus]] = {
    SuratStatus.DRAFT: {
        SuratStatus.MENUNGGU_TTD_DOSEN,
        SuratStatus.MENUNGGU_PROSES_ADMIN,
    },
    SuratStatus.MENUNGGU_TTD_DOSEN: {
        SuratStatus.MENUNGGU_PROSES_ADMIN,
        SuratStatus.DITOLAK,
    },
    SuratStatus.MENUNGGU_PROSES_ADMIN: {
        SuratStatus.SELESAI,
        SuratStatus.DITOLAK,
    },
    SuratStatus.SELESAI: set(),
    SuratStatus.DITOLAK: set(),
}


@dataclass
class Surat:
    """Core domain entity representing an academic letter request."""

    id: Optional[int] = None
    mahasiswa_id: Optional[int] = None
    jenis: str = ""
    keperluan: str = ""
    is_external: bool = False
    is_sequential: bool = False
    file_path: Optional[str] = None
    internal_fields: Optional[Dict[str, str]] = None
    status: SuratStatus = SuratStatus.DRAFT
    document_hash: Optional[str] = None
    pdf_path: Optional[str] = None
    qr_path: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Read-only display fields populated by the repository layer.
    mahasiswa_name: Optional[str] = None
    mahasiswa_nim: Optional[str] = None

    # ------------------------------------------------------------------
    # State-machine helpers
    # ------------------------------------------------------------------

    def can_transition_to(self, new_status: SuratStatus) -> bool:
        """Return *True* if *new_status* is a valid next state."""
        return new_status in _VALID_TRANSITIONS.get(self.status, set())

    def _transition_to(self, new_status: SuratStatus) -> None:
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Tidak dapat mengubah status dari {self.status.value} ke {new_status.value}"
            )
        self.status = new_status

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def submit(self, has_lecturer_signatures: bool) -> None:
        """Submit the letter for review.

        Transitions to MENUNGGU_TTD_DOSEN when lecturer signatures are
        required, or directly to MENUNGGU_PROSES_ADMIN otherwise.
        """
        target = (
            SuratStatus.MENUNGGU_TTD_DOSEN
            if has_lecturer_signatures
            else SuratStatus.MENUNGGU_PROSES_ADMIN
        )
        self._transition_to(target)

    def advance_to_admin(self) -> None:
        """All lecturers have signed — move to admin review."""
        self._transition_to(SuratStatus.MENUNGGU_PROSES_ADMIN)

    def approve(self, document_hash: str, qr_path: Optional[str] = None, final_pdf_path: Optional[str] = None) -> None:
        """Admin approves the letter and attaches final artefacts."""
        self._transition_to(SuratStatus.SELESAI)
        self.document_hash = document_hash
        if qr_path:
            self.qr_path = qr_path
        if final_pdf_path:
            self.pdf_path = final_pdf_path

    def reject(self, reason: str) -> None:
        """Reject the letter with a mandatory reason."""
        if not reason or not reason.strip():
            raise ValidationError("Alasan penolakan wajib diisi")
        self._transition_to(SuratStatus.DITOLAK)
        self.rejection_reason = reason.strip()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def attach_pdf(self, pdf_path: str) -> None:
        self.pdf_path = pdf_path

    def set_document_hash(self, hash_value: str) -> None:
        self.document_hash = hash_value

    def attach_qr(self, qr_path: str) -> None:
        self.qr_path = qr_path

    def is_completed(self) -> bool:
        return self.status == SuratStatus.SELESAI
