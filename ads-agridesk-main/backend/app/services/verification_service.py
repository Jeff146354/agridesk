import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.domain.enums import SuratStatus
from app.repositories.surat_repository import SuratRepository
from app.repositories.signature_repository import SignatureRepository
from app.utils.storage import storage_service


class VerificationService:
    """Public document verification service."""

    def __init__(self, db: Session):
        self.surat_repo = SuratRepository(db)
        self.sig_repo = SignatureRepository(db)

    def verify_document(self, document_hash: str) -> dict:
        surat = self.surat_repo.get_by_document_hash(document_hash)
        if not surat or surat.status != SuratStatus.SELESAI:
            return {"status": "INVALID", "surat_id": None, "jenis": None, "keperluan": None}

        year = surat.created_at.year if surat.created_at else "----"
        code = f"SR/{year}/{str(surat.id).zfill(4)}"

        # Page count from PDF via storage service
        page_count = 1
        pdf_path = surat.pdf_path or surat.file_path
        if pdf_path:
            try:
                from pypdf import PdfReader
                from io import BytesIO
                pdf_bytes = storage_service.get_file_content(pdf_path)
                page_count = len(PdfReader(BytesIO(pdf_bytes)).pages)
            except Exception as e:
                logger.error(f"Failed to read PDF page count for '{pdf_path}': {e}", exc_info=True)

        # Signer details
        signers = []
        for sig in self.sig_repo.get_by_surat_id(surat.id):
            owner = sig.owner_name or "Unknown"
            signers.append({
                "name": owner,
                "role": sig.role.value if hasattr(sig.role, "value") else str(sig.role),
                "email": sig.owner_email,
                "nip": sig.owner_nip,
                "signed_at": sig.signed_at,
                "signing_order": sig.signing_order,
                "page_number": sig.page_number,
                "is_signed": sig.is_signed(),
            })

        # Short verification ID (last 6 chars of hash, uppercased)
        verification_id = f"AGR-{document_hash[-6:].upper()}"

        return {
            "status": "VALID",
            "verification_id": verification_id,
            "document_hash": document_hash,
            "document": {
                "id": surat.id,
                "code": code,
                "jenis": surat.jenis,
                "keperluan": surat.keperluan,
                "internal_fields": surat.internal_fields,
                "is_external": surat.is_external,
                "created_at": surat.created_at,
                "completed_at": surat.updated_at,
                "page_count": page_count,
                "status": surat.status.value if hasattr(surat.status, "value") else str(surat.status),
            },
            "signers": signers,
        }

    def verify_signature(self, signature_hash: str) -> dict:
        sig = self.sig_repo.get_by_signature_hash(signature_hash)
        if not sig or not sig.is_signed():
            return {"status": "INVALID", "surat_id": None, "jenis": None, "keperluan": None}

        surat = self.surat_repo.get_by_id(sig.surat_id)
        if not surat:
            return {"status": "INVALID", "surat_id": None, "jenis": None, "keperluan": None}

        year = surat.created_at.year if surat.created_at else "----"
        code = f"SR/{year}/{str(surat.id).zfill(4)}"

        verification_id = f"SIG-{signature_hash[-6:].upper()}"

        return {
            "status": "VALID",
            "verification_id": verification_id,
            "document_hash": signature_hash,
            "document": {
                "id": surat.id,
                "code": code,
                "jenis": surat.jenis,
                "keperluan": surat.keperluan,
                "internal_fields": surat.internal_fields,
                "is_external": surat.is_external,
                "created_at": surat.created_at,
                "completed_at": surat.updated_at,
                "page_count": 1,
                "status": surat.status.value if hasattr(surat.status, "value") else str(surat.status),
            },
            "signers": [{
                "name": sig.owner_name or "Unknown",
                "role": sig.role.value if hasattr(sig.role, "value") else str(sig.role),
                "email": sig.owner_email,
                "nip": sig.owner_nip,
                "signed_at": sig.signed_at,
                "signing_order": sig.signing_order,
                "page_number": sig.page_number,
                "is_signed": sig.is_signed(),
            }],
        }

    def download_pdf(self, hash_value: str):
        from fastapi import HTTPException
        from fastapi.responses import StreamingResponse
        from io import BytesIO

        # 1. Try by document_hash
        surat = self.surat_repo.get_by_document_hash(hash_value)

        # 2. If not found, try by signature_hash
        if not surat:
            sig = self.sig_repo.get_by_signature_hash(hash_value)
            if sig and sig.is_signed():
                surat = self.surat_repo.get_by_id(sig.surat_id)

        if not surat or surat.status != SuratStatus.SELESAI:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan atau belum sah diterbitkan")

        pdf_path = surat.pdf_path
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Berkas PDF tidak tersedia")

        try:
            pdf_bytes = storage_service.get_file_content(pdf_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Berkas PDF fisik tidak ditemukan di server")

        import os
        filename = os.path.basename(pdf_path)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

