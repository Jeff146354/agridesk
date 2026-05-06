from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus, UserRole
from app.domain.exceptions import (
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedError,
    ValidationError,
)
from app.domain.surat import Surat
from app.domain.signature import Signature
from app.repositories.surat_repository import SuratRepository
from app.repositories.user_repository import UserRepository
from app.repositories.letter_template_repository import LetterTemplateRepository
from app.repositories.signature_repository import SignatureRepository
from app.services.audit_log_service import AuditLogService
from app.utils.hash_generator import HashGenerator
from app.utils.qr_generator import QRCodeGenerator
from app.utils.pdf_generator import PDFGenerator


class SuratService:
    """Orchestration layer for the letter workflow.

    All business rules live in the ``Surat`` domain entity;
    this service coordinates repositories, external utilities
    and the audit trail.
    """

    def __init__(self, db: Session):
        self.db = db
        self.surat_repo = SuratRepository(db)
        self.user_repo = UserRepository(db)
        self.template_repo = LetterTemplateRepository(db)
        self.signature_repo = SignatureRepository(db)
        self.audit_service = AuditLogService(db)

    # ------------------------------------------------------------------
    # Template queries
    # ------------------------------------------------------------------

    def get_internal_templates(self) -> List[dict]:
        templates = self.template_repo.get_internal_templates()
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "required_fields": t.required_fields,
            }
            for t in templates
        ]

    # ------------------------------------------------------------------
    # Letter creation
    # ------------------------------------------------------------------

    def create_internal_letter(
        self,
        mahasiswa_id: int,
        jenis: str,
        keperluan: str,
        fields: dict,
        lecturer_ids: Optional[List[int]] = None,
    ) -> Surat:
        self._validate_internal_fields(jenis, fields)

        mahasiswa = self.user_repo.get_by_id(mahasiswa_id)
        if not mahasiswa:
            raise EntityNotFoundError("Mahasiswa tidak ditemukan")

        enriched_fields = {
            "nama": mahasiswa.name,
            "nim": mahasiswa.nim or "-",
            **fields,
        }

        # Generate PDF from template
        filename = f"surat_{jenis}_{mahasiswa_id}.pdf"
        pdf_path = PDFGenerator.generate_from_template(
            jenis,
            enriched_fields,
            filename,
            signature_path=mahasiswa.signature_image_path,
        )

        # Build domain entity
        surat = Surat(
            mahasiswa_id=mahasiswa_id,
            jenis=jenis,
            keperluan=keperluan,
            is_external=False,
            pdf_path=pdf_path,
            internal_fields=fields,
        )

        # Auto-submit if lecturers are provided
        if lecturer_ids:
            surat.submit(has_lecturer_signatures=True)

        surat = self.surat_repo.create(surat)

        # Create signature placeholders for lecturers
        if lecturer_ids:
            for lid in lecturer_ids:
                sig = Signature(surat_id=surat.id, owner_id=lid, role=UserRole.DOSEN)
                self.signature_repo.create(sig)

        self._log("SURAT_CREATED", mahasiswa_id, UserRole.MAHASISWA.value, surat)
        return surat

    def create_external_letter(
        self,
        mahasiswa_id: int,
        jenis: str,
        keperluan: str,
        file_path: str,
        lecturer_ids: Optional[List[int]] = None,
    ) -> Surat:
        surat = Surat(
            mahasiswa_id=mahasiswa_id,
            jenis=jenis,
            keperluan=keperluan,
            is_external=True,
            file_path=file_path,
        )

        if lecturer_ids:
            surat.submit(has_lecturer_signatures=True)

        surat = self.surat_repo.create(surat)

        if lecturer_ids:
            for lid in lecturer_ids:
                sig = Signature(surat_id=surat.id, owner_id=lid, role=UserRole.DOSEN)
                self.signature_repo.create(sig)

        self._log("SURAT_CREATED", mahasiswa_id, UserRole.MAHASISWA.value, surat)
        return surat

    # ------------------------------------------------------------------
    # Workflow transitions
    # ------------------------------------------------------------------

    def submit_letter(self, surat_id: int, mahasiswa_id: int) -> Surat:
        surat = self._get_surat_or_raise(surat_id)
        if surat.mahasiswa_id != mahasiswa_id:
            raise UnauthorizedError("Bukan surat Anda")

        unsigned = self.signature_repo.get_unsigned_by_surat(surat_id)
        has_lecturers = any(s.role == UserRole.DOSEN for s in unsigned)

        surat.submit(has_lecturer_signatures=has_lecturers)
        surat = self.surat_repo.update(surat)

        self._log("SURAT_SUBMITTED", mahasiswa_id, UserRole.MAHASISWA.value, surat)
        return surat

    def approve_by_admin(self, surat_id: int, admin_id: int) -> Surat:
        surat = self._get_surat_or_raise(surat_id)

        # Generate artefacts
        document_hash = HashGenerator.generate_document_hash(surat.id, surat.mahasiswa_id)

        verification_url = f"/verify/{document_hash}"
        qr_filename = f"qr_{surat.id}.png"
        qr_path = QRCodeGenerator.generate_qr_code(verification_url, qr_filename)

        source_pdf = surat.pdf_path or surat.file_path or ""
        final_filename = f"final_{surat.id}.pdf"
        signed_images = [
            s.image_path
            for s in self.signature_repo.get_by_surat_id(surat.id)
            if s.is_signed() and s.image_path
        ]
        final_pdf_path = PDFGenerator.generate_final_pdf(
            source_pdf, qr_path, final_filename, signature_paths=signed_images,
        )

        # Domain transition — validates state machine
        surat.approve(document_hash, qr_path, final_pdf_path)
        surat = self.surat_repo.update(surat)

        self._log("SURAT_APPROVED", admin_id, UserRole.ADMIN.value, surat)
        return surat

    def reject_letter(
        self, surat_id: int, actor_id: int, actor_role: str, reason: str,
    ) -> Surat:
        surat = self._get_surat_or_raise(surat_id)

        # Extra guard for dosen rejection
        if actor_role == UserRole.DOSEN.value:
            if surat.status != SuratStatus.MENUNGGU_TTD_DOSEN:
                raise InvalidStateTransitionError(
                    "Dosen hanya dapat menolak surat pada status menunggu TTD dosen"
                )
            signatures = self.signature_repo.get_by_surat_id(surat_id)
            is_pending_assignee = any(
                s.owner_id == actor_id
                and s.role == UserRole.DOSEN
                and not s.is_signed()
                for s in signatures
            )
            if not is_pending_assignee:
                raise UnauthorizedError("Surat ini bukan pending tanda tangan Anda")

        # Domain transition — validates reason and state machine
        surat.reject(reason)
        surat = self.surat_repo.update(surat)

        self._log("SURAT_REJECTED", actor_id, actor_role, surat)
        return surat

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_surat_by_id(self, surat_id: int) -> Optional[Surat]:
        return self.surat_repo.get_by_id(surat_id)

    def get_surat_with_access_check(
        self, surat_id: int, user_id: int, user_role: UserRole,
    ) -> Surat:
        """Fetch a surat and enforce role-based access control."""
        surat = self._get_surat_or_raise(surat_id)

        if user_role == UserRole.MAHASISWA and surat.mahasiswa_id != user_id:
            raise UnauthorizedError("Akses ditolak")

        if user_role == UserRole.DOSEN:
            signatures = self.signature_repo.get_by_surat_id(surat_id)
            if not any(s.owner_id == user_id for s in signatures):
                raise UnauthorizedError("Akses ditolak")

        # ADMIN can access all
        return surat

    def get_surat_by_mahasiswa(self, mahasiswa_id: int) -> List[Surat]:
        return self.surat_repo.get_by_mahasiswa_id(mahasiswa_id)

    def get_pending_admin(self) -> List[Surat]:
        return self.surat_repo.get_pending_admin()

    def get_all_surat(self) -> List[Surat]:
        return self.surat_repo.get_all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_surat_or_raise(self, surat_id: int) -> Surat:
        surat = self.surat_repo.get_by_id(surat_id)
        if not surat:
            raise EntityNotFoundError("Surat tidak ditemukan")
        return surat

    def _validate_internal_fields(self, jenis: str, fields: dict) -> None:
        template = self.template_repo.get_by_name(jenis)
        if not template:
            if self.template_repo.get_internal_templates():
                raise ValidationError("Jenis surat internal tidak terdaftar")
            return

        # Delegate validation to domain entity
        invalid = template.validate_fields(fields)
        if invalid:
            raise ValidationError(f"Field wajib belum diisi: {', '.join(invalid)}")

    def _log(self, event: str, actor_id: int, actor_role: str, surat: Surat) -> None:
        self.audit_service.log_event(
            event_name=event,
            actor_id=actor_id,
            actor_role=actor_role,
            target_type="surat",
            target_id=surat.id,
            status=surat.status.value,
        )
