from typing import Optional, List

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.domain.enums import SuratStatus, UserRole
from app.domain.signature import Signature
from app.models.signature import SignatureModel
from app.models.surat import SuratModel


class SignatureRepository:
    """Persistence layer for Signature.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: SignatureModel) -> Signature:
        return Signature(
            id=model.id,
            surat_id=model.surat_id,
            owner_id=model.owner_id,
            role=model.role,
            image_path=model.image_path,
            signature_hash=model.signature_hash,
            signed_at=model.signed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            # Read-only display fields from ORM relationships
            surat_jenis=model.surat.jenis if model.surat else None,
            mahasiswa_name=(
                model.surat.mahasiswa.name
                if model.surat and model.surat.mahasiswa
                else None
            ),
            owner_name=model.owner.name if model.owner else None,
            owner_nip=model.owner.nip if model.owner else None,
        )

    @staticmethod
    def _apply_to_model(domain: Signature, model: SignatureModel) -> None:
        model.surat_id = domain.surat_id
        model.owner_id = domain.owner_id
        model.role = domain.role
        model.image_path = domain.image_path
        model.signature_hash = domain.signature_hash
        model.signed_at = domain.signed_at

    # ------------------------------------------------------------------
    # CRUD operations — return domain entities
    # ------------------------------------------------------------------

    def create(self, signature: Signature) -> Signature:
        model = SignatureModel()
        self._apply_to_model(signature, model)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, signature_id: int) -> Optional[Signature]:
        model = self.db.query(SignatureModel).filter(SignatureModel.id == signature_id).first()
        return self._to_domain(model) if model else None

    def get_by_surat_id(self, surat_id: int) -> List[Signature]:
        models = self.db.query(SignatureModel).filter(SignatureModel.surat_id == surat_id).all()
        return [self._to_domain(m) for m in models]

    def get_by_owner_id(self, owner_id: int) -> List[Signature]:
        models = self.db.query(SignatureModel).filter(SignatureModel.owner_id == owner_id).all()
        return [self._to_domain(m) for m in models]

    def get_pending_for_lecturer(self, lecturer_id: int) -> List[Signature]:
        models = (
            self.db.query(SignatureModel)
            .options(
                joinedload(SignatureModel.surat).joinedload(SuratModel.mahasiswa)
            )
            .join(SuratModel, SignatureModel.surat_id == SuratModel.id)
            .filter(
                SignatureModel.owner_id == lecturer_id,
                SignatureModel.signed_at.is_(None),
                SuratModel.status == SuratStatus.MENUNGGU_TTD_DOSEN,
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_signed_for_lecturer(self, lecturer_id: int) -> List[Signature]:
        models = (
            self.db.query(SignatureModel)
            .options(
                joinedload(SignatureModel.surat).joinedload(SuratModel.mahasiswa)
            )
            .join(SuratModel, SignatureModel.surat_id == SuratModel.id)
            .filter(
                SignatureModel.owner_id == lecturer_id,
                or_(
                    SignatureModel.signed_at.is_not(None),
                    SuratModel.status == SuratStatus.DITOLAK,
                ),
            )
            .order_by(SignatureModel.signed_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_unsigned_by_surat(self, surat_id: int) -> List[Signature]:
        models = (
            self.db.query(SignatureModel)
            .filter(
                SignatureModel.surat_id == surat_id,
                SignatureModel.signed_at.is_(None),
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def update(self, signature: Signature) -> Signature:
        model = self.db.query(SignatureModel).filter(SignatureModel.id == signature.id).first()
        if not model:
            from app.domain.exceptions import EntityNotFoundError
            raise EntityNotFoundError("Signature tidak ditemukan")
        self._apply_to_model(signature, model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
