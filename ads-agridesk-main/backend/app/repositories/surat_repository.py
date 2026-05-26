import json
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus
from app.domain.exceptions import EntityNotFoundError
from app.domain.surat import Surat
from app.models.surat import SuratModel


class SuratRepository:
    """Persistence layer for Surat.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: SuratModel) -> Surat:
        internal_fields: Optional[dict] = None
        if model.internal_fields_raw:
            try:
                parsed = json.loads(model.internal_fields_raw)
                if isinstance(parsed, dict):
                    internal_fields = {str(k): str(v) for k, v in parsed.items()}
            except (json.JSONDecodeError, TypeError):
                pass

        return Surat(
            id=model.id,
            mahasiswa_id=model.mahasiswa_id,
            jenis=model.jenis,
            keperluan=model.keperluan,
            is_external=model.is_external,
            is_sequential=model.is_sequential,
            file_path=model.file_path,
            internal_fields=internal_fields,
            status=model.status,
            document_hash=model.document_hash,
            pdf_path=model.pdf_path,
            qr_path=model.qr_path,
            rejection_reason=model.rejection_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
            # Read-only display fields from ORM relationships
            mahasiswa_name=model.mahasiswa.name if model.mahasiswa else None,
            mahasiswa_nim=model.mahasiswa.nim if model.mahasiswa else None,
        )

    @staticmethod
    def _apply_to_model(domain: Surat, model: SuratModel) -> None:
        model.mahasiswa_id = domain.mahasiswa_id
        model.jenis = domain.jenis
        model.keperluan = domain.keperluan
        model.is_external = domain.is_external
        model.is_sequential = domain.is_sequential
        model.file_path = domain.file_path
        model.internal_fields_raw = (
            json.dumps(domain.internal_fields, ensure_ascii=False)
            if domain.internal_fields
            else None
        )
        model.status = domain.status
        model.document_hash = domain.document_hash
        model.pdf_path = domain.pdf_path
        model.qr_path = domain.qr_path
        model.rejection_reason = domain.rejection_reason

    # ------------------------------------------------------------------
    # CRUD operations — return domain entities
    # ------------------------------------------------------------------

    def create(self, surat: Surat) -> Surat:
        model = SuratModel()
        self._apply_to_model(surat, model)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, surat_id: int) -> Optional[Surat]:
        model = self.db.query(SuratModel).filter(SuratModel.id == surat_id).first()
        return self._to_domain(model) if model else None

    def get_by_mahasiswa_id(self, mahasiswa_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Surat], int]:
        query = self.db.query(SuratModel).filter(SuratModel.mahasiswa_id == mahasiswa_id)
        total = query.count()
        models = query.offset(skip).limit(limit).all()
        return [self._to_domain(m) for m in models], total

    def get_by_status(self, status: SuratStatus, skip: int = 0, limit: int = 100) -> Tuple[List[Surat], int]:
        query = self.db.query(SuratModel).filter(SuratModel.status == status)
        total = query.count()
        models = query.offset(skip).limit(limit).all()
        return [self._to_domain(m) for m in models], total

    def get_by_document_hash(self, document_hash: str) -> Optional[Surat]:
        model = self.db.query(SuratModel).filter(SuratModel.document_hash == document_hash).first()
        return self._to_domain(model) if model else None

    def get_pending_admin(self, skip: int = 0, limit: int = 100) -> Tuple[List[Surat], int]:
        return self.get_by_status(SuratStatus.MENUNGGU_PROSES_ADMIN, skip, limit)

    def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Surat], int]:
        query = self.db.query(SuratModel)
        total = query.count()
        models = query.offset(skip).limit(limit).all()
        return [self._to_domain(m) for m in models], total

    def update(self, surat: Surat) -> Surat:
        model = self.db.query(SuratModel).filter(SuratModel.id == surat.id).first()
        if not model:
            raise EntityNotFoundError("Surat tidak ditemukan")
        self._apply_to_model(surat, model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def delete(self, surat_id: int) -> bool:
        model = self.db.query(SuratModel).filter(SuratModel.id == surat_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
