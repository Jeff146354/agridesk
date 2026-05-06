from typing import List

from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus, UserRole
from app.domain.exceptions import EntityNotFoundError
from app.domain.signature import Signature
from app.repositories.signature_repository import SignatureRepository
from app.repositories.surat_repository import SuratRepository
from app.services.audit_log_service import AuditLogService
from app.utils.hash_generator import HashGenerator


class SignatureService:
    """Orchestration layer for signature operations.

    Domain validation (ownership, double-sign) lives in the ``Signature``
    entity; this service coordinates persistence and workflow side-effects.
    """

    def __init__(self, db: Session):
        self.db = db
        self.signature_repo = SignatureRepository(db)
        self.surat_repo = SuratRepository(db)
        self.audit_service = AuditLogService(db)

    def add_student_signature(
        self,
        surat_id: int,
        student_id: int,
        image_path: str,
    ) -> Signature:
        sig_hash = HashGenerator.generate_hash(f"{surat_id}:{student_id}:MAHASISWA")

        signature = Signature(
            surat_id=surat_id,
            owner_id=student_id,
            role=UserRole.MAHASISWA,
        )
        signature.sign(image_path, sig_hash)

        signature = self.signature_repo.create(signature)

        self.audit_service.log_event(
            "SIGNATURE_ADDED", student_id, UserRole.MAHASISWA.value,
            "surat", surat_id, "SIGNED",
        )
        return signature

    def sign_by_lecturer(
        self,
        signature_id: int,
        lecturer_id: int,
        image_path: str,
    ) -> Signature:
        signature = self.signature_repo.get_by_id(signature_id)
        if not signature:
            raise EntityNotFoundError("Signature record tidak ditemukan")

        # Domain validation — ownership & double-sign guard
        signature.validate_owner(lecturer_id)

        sig_hash = HashGenerator.generate_hash(
            f"{signature.surat_id}:{lecturer_id}:DOSEN"
        )
        signature.sign(image_path, sig_hash)

        signature = self.signature_repo.update(signature)

        # Auto-advance surat when all lecturers have signed
        if self._all_lecturers_signed(signature.surat_id):
            surat = self.surat_repo.get_by_id(signature.surat_id)
            if surat and surat.status == SuratStatus.MENUNGGU_TTD_DOSEN:
                surat.advance_to_admin()
                self.surat_repo.update(surat)
                self.audit_service.log_event(
                    "SURAT_READY_ADMIN",
                    lecturer_id,
                    UserRole.DOSEN.value,
                    "surat",
                    signature.surat_id,
                    SuratStatus.MENUNGGU_PROSES_ADMIN.value,
                )

        self.audit_service.log_event(
            "SIGNATURE_ADDED", lecturer_id, UserRole.DOSEN.value,
            "surat", signature.surat_id, "SIGNED",
        )
        return signature

    def _all_lecturers_signed(self, surat_id: int) -> bool:
        unsigned = self.signature_repo.get_unsigned_by_surat(surat_id)
        return not any(s.role == UserRole.DOSEN for s in unsigned)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_pending_for_lecturer(self, lecturer_id: int) -> List[Signature]:
        return self.signature_repo.get_pending_for_lecturer(lecturer_id)

    def get_signed_for_lecturer(self, lecturer_id: int) -> List[Signature]:
        return self.signature_repo.get_signed_for_lecturer(lecturer_id)

    def get_signatures_for_surat(self, surat_id: int) -> List[Signature]:
        return self.signature_repo.get_by_surat_id(surat_id)
