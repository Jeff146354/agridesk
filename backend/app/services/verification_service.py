from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus
from app.repositories.surat_repository import SuratRepository


class VerificationService:
    """Public document verification service."""

    def __init__(self, db: Session):
        self.surat_repo = SuratRepository(db)

    def verify_document(self, document_hash: str) -> dict:
        surat = self.surat_repo.get_by_document_hash(document_hash)
        if surat and surat.status == SuratStatus.SELESAI:
            return {
                "status": "VALID",
                "surat_id": surat.id,
                "jenis": surat.jenis,
                "keperluan": surat.keperluan,
            }
        return {"status": "INVALID"}
