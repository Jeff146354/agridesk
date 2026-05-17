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
            # Placement fields
            page_number=model.page_number if model.page_number is not None else 1,
            signing_order=model.signing_order,
            pos_x=model.pos_x,
            pos_y=model.pos_y,
            pos_width=model.pos_width,
            pos_height=model.pos_height,
            owner_email=model.owner_email,
            # Read-only display fields from ORM relationships
            surat_jenis=model.surat.jenis if model.surat else None,
            mahasiswa_name=(
                model.surat.mahasiswa.name
                if model.surat and model.surat.mahasiswa
                else None
            ),
            owner_name=model.owner.name if model.owner else None,
            owner_nip=model.owner.nip or model.owner.nim if model.owner else None,
        )

    @staticmethod
    def _apply_to_model(domain: Signature, model: SignatureModel) -> None:
        model.surat_id = domain.surat_id
        model.owner_id = domain.owner_id
        model.role = domain.role
        model.image_path = domain.image_path
        model.signature_hash = domain.signature_hash
        model.signed_at = domain.signed_at
        model.page_number = domain.page_number if domain.page_number is not None else 1
        model.signing_order = domain.signing_order
        model.pos_x = domain.pos_x
        model.pos_y = domain.pos_y
        model.pos_width = domain.pos_width
        model.pos_height = domain.pos_height
        model.owner_email = domain.owner_email

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
        models = (
            self.db.query(SignatureModel)
            .filter(SignatureModel.surat_id == surat_id)
            .order_by(
                SignatureModel.signing_order.asc().nulls_last(),
                SignatureModel.id.asc(),
            )
            .all()
        )
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
            .order_by(
                SignatureModel.signing_order.asc().nulls_last(),
                SignatureModel.id.asc(),
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_signature_hash(self, signature_hash: str) -> Optional[Signature]:
        model = self.db.query(SignatureModel).filter(SignatureModel.signature_hash == signature_hash).first()
        return self._to_domain(model) if model else None

    def get_next_to_sign(self, surat_id: int, is_sequential: bool) -> List[Signature]:
        """Return the next signer(s) based on sequential or parallel mode."""
        unsigned = self.get_unsigned_by_surat(surat_id)
        if not unsigned:
            return []
        if not is_sequential:
            return unsigned  # all can sign simultaneously
        # Sequential: only return signer(s) with the lowest signing_order
        min_order = min(
            (s.signing_order for s in unsigned if s.signing_order is not None),
            default=None,
        )
        if min_order is None:
            return unsigned
        return [s for s in unsigned if s.signing_order == min_order]

    def update(self, signature: Signature) -> Signature:
        model = self.db.query(SignatureModel).filter(SignatureModel.id == signature.id).first()
        if not model:
            from app.domain.exceptions import EntityNotFoundError
            raise EntityNotFoundError("Signature tidak ditemukan")
        self._apply_to_model(signature, model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

