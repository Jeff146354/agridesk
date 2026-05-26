import os
import uuid
import logging
from typing import List, Optional, Dict, Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus, UserRole
from app.models.surat import SuratModel

logger = logging.getLogger(__name__)
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
from app.config import settings


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
                "name": t.jenis,
                "description": t.title,
                "required_fields": [f.get("name") for f in t.fields if f.get("name")],
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
        background_tasks=None,
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
        unique_id = uuid.uuid4().hex[:8]
        safe_jenis = jenis.replace(" ", "_")
        filename = f"surat_{safe_jenis}_{mahasiswa_id}_{unique_id}.pdf"
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

        # Apply specific logic for Pembatalan Mata Kuliah
        if jenis == "Surat Pembatalan Mata Kuliah":
            surat_model = self.db.query(SuratModel).filter(SuratModel.id == surat.id).first()
            if surat_model:
                surat_model.is_sequential = True
                self.db.commit()

            # Create Mahasiswa Signature
            sig_mhs = Signature(
                surat_id=surat.id,
                owner_id=mahasiswa_id,
                role=UserRole.MAHASISWA,
                page_number=1,
                pos_x=500.0,
                pos_y=780.0,
                pos_width=150.0,
                pos_height=80.0,
                signing_order=0,
            )
            # Instantly sign for Mahasiswa
            sig_hash = HashGenerator.generate_hash(f"{surat.id}:{mahasiswa_id}:MAHASISWA")
            sig_mhs.sign(mahasiswa.signature_image_path, sig_hash)
            self.signature_repo.create(sig_mhs)

            if lecturer_ids and len(lecturer_ids) >= 2:
                # Dosen Pembimbing
                sig_pembimbing = Signature(
                    surat_id=surat.id,
                    owner_id=lecturer_ids[0],
                    role=UserRole.DOSEN,
                    page_number=1,
                    pos_x=50.0,
                    pos_y=780.0,
                    pos_width=150.0,
                    pos_height=80.0,
                    signing_order=1,
                )
                self.signature_repo.create(sig_pembimbing)

                # Kaprodi
                sig_kaprodi = Signature(
                    surat_id=surat.id,
                    owner_id=lecturer_ids[1],
                    role=UserRole.DOSEN,
                    page_number=1,
                    pos_x=275.0,
                    pos_y=780.0,
                    pos_width=150.0,
                    pos_height=80.0,
                    signing_order=2,
                )
                self.signature_repo.create(sig_kaprodi)
        else:
            # Fallback for other internal templates
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
        signer_configs: Optional[List[Dict[str, Any]]] = None,
        is_sequential: bool = False,
        # Legacy fallback
        lecturer_ids: Optional[List[int]] = None,
    ) -> Surat:
        """Create an external letter with optional rich signer configuration.

        signer_configs: list of dicts with keys:
            - user_id (int)
            - role (str: "DOSEN" | "MAHASISWA" | "ADMIN")
            - signing_order (int | None)
            - page_number (int, default 1)
            - pos_x, pos_y, pos_width, pos_height (float | None)
            - owner_email (str | None)
        """
        surat = Surat(
            mahasiswa_id=mahasiswa_id,
            jenis=jenis,
            keperluan=keperluan,
            is_external=True,
            file_path=file_path,
        )

        has_signers = bool(signer_configs) or bool(lecturer_ids)
        if has_signers:
            surat.submit(has_lecturer_signatures=True)

        surat = self.surat_repo.create(surat)

        # Update is_sequential flag directly on the DB model
        if is_sequential and surat.id:
            db_model = self.db.query(SuratModel).filter(SuratModel.id == surat.id).first()
            if db_model:
                db_model.is_sequential = is_sequential
                self.db.commit()

        # Create signature records from rich signer_configs
        if signer_configs:
            for cfg in signer_configs:
                user_id = cfg.get("user_id")
                if not user_id:
                    continue
                user = self.user_repo.get_by_id(user_id)
                if not user:
                    continue
                role = UserRole(cfg.get("role", user.role.value))
                sig = Signature(
                    surat_id=surat.id,
                    owner_id=user_id,
                    role=role,
                    signing_order=cfg.get("signing_order"),
                    page_number=cfg.get("page_number", 1),
                    pos_x=cfg.get("pos_x"),
                    pos_y=cfg.get("pos_y"),
                    pos_width=cfg.get("pos_width"),
                    pos_height=cfg.get("pos_height"),
                    owner_email=cfg.get("owner_email") or user.email,
                )

                # Auto-sign if this signer is the mahasiswa who created the letter
                if user_id == mahasiswa_id:
                    sig_hash = HashGenerator.generate_hash(
                        f"{surat.id}:{mahasiswa_id}:{role.value}"
                    )
                    sig.sign(
                        user.signature_image_path or "",
                        sig_hash,
                    )

                self.signature_repo.create(sig)
        elif lecturer_ids:
            # Legacy support
            for lid in lecturer_ids:
                sig = Signature(surat_id=surat.id, owner_id=lid, role=UserRole.DOSEN)
                self.signature_repo.create(sig)

        self._log("SURAT_CREATED", mahasiswa_id, UserRole.MAHASISWA.value, surat)
        return surat

    # ------------------------------------------------------------------
    # PDF utilities
    # ------------------------------------------------------------------

    def get_page_count(self, surat_id: int, user_id: int, user_role: UserRole) -> int:
        """Return the number of pages in the uploaded PDF."""
        surat = self.get_surat_with_access_check(surat_id, user_id, user_role)
        pdf_path = surat.file_path or surat.pdf_path
        if not pdf_path:
            raise EntityNotFoundError("File PDF tidak ditemukan")
        try:
            from app.utils.storage import storage_service
            from io import BytesIO
            pdf_bytes = storage_service.get_file_content(pdf_path)
            reader = PdfReader(BytesIO(pdf_bytes))
            return len(reader.pages)
        except FileNotFoundError:
            raise EntityNotFoundError("File PDF tidak ditemukan")
        except Exception as e:
            logger.error(f"Failed to read PDF pages for surat_id {surat_id}: {e}", exc_info=True)
            return 1

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

    def approve_by_admin(self, surat_id: int, admin_id: int, background_tasks=None) -> Surat:
        surat = self._get_surat_or_raise(surat_id)

        document_hash = HashGenerator.generate_document_hash(surat.id, surat.mahasiswa_id)

        # Domain transition — validates state machine
        surat.approve(document_hash)
        surat = self.surat_repo.update(surat)

        if background_tasks:
            background_tasks.add_task(self._generate_final_pdf_task, surat.id, document_hash, admin_id)
        else:
            self._generate_final_pdf_task(surat.id, document_hash, admin_id)

        # Return immediately, file generation runs in background
        return surat

    def _generate_final_pdf_task(self, surat_id: int, document_hash: str, admin_id: int):
        from app.database import SessionLocal
        with SessionLocal() as db:
            service = SuratService(db)
            try:
                surat = service._get_surat_or_raise(surat_id)

                verification_url = f"{settings.BASE_URL}/verify/{document_hash}"
                qr_filename = f"qr_{surat.id}.png"
                qr_path = QRCodeGenerator.generate_qr_code(verification_url, qr_filename)

                source_pdf = surat.pdf_path or surat.file_path or ""
                final_filename = f"final_{surat.id}.pdf"
                signatures = service.signature_repo.get_by_surat_id(surat.id)
                final_pdf_path = PDFGenerator.generate_final_pdf(
                    source_pdf, qr_path, final_filename,
                    signatures=signatures,
                    is_external=surat.is_external,
                    document_hash=document_hash,
                )

                surat.qr_path = qr_path
                surat.pdf_path = final_pdf_path
                service.surat_repo.update(surat)
                service._log("SURAT_APPROVED", admin_id, UserRole.ADMIN.value, surat)
            except Exception as e:
                logger.error(f"Failed to generate final PDF async for surat {surat_id}: {e}", exc_info=True)

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

            # Enforce sequential order for rejection too
            surat_model = self.db.query(SuratModel).filter(SuratModel.id == surat_id).first()
            if surat_model and surat_model.is_sequential:
                next_signers = self.signature_repo.get_next_to_sign(surat_id, True)
                if not any(s.owner_id == actor_id for s in next_signers):
                    raise InvalidStateTransitionError(
                        "Belum giliran Anda. Harap tunggu penanda tangan sebelumnya."
                    )

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

    def get_surat_by_mahasiswa(self, mahasiswa_id: int, skip: int = 0, limit: int = 100) -> tuple[List[Surat], int]:
        return self.surat_repo.get_by_mahasiswa_id(mahasiswa_id, skip, limit)

    def get_pending_admin(self, skip: int = 0, limit: int = 100) -> tuple[List[Surat], int]:
        return self.surat_repo.get_pending_admin(skip, limit)

    def get_all_surat(self, skip: int = 0, limit: int = 100) -> tuple[List[Surat], int]:
        return self.surat_repo.get_all(skip, limit)

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


