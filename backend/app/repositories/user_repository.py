from typing import Optional, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.enums import UserRole
from app.domain.exceptions import EntityNotFoundError
from app.domain.user import User
from app.models.user import UserModel


class UserRepository:
    """Persistence layer for User.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            nim=model.nim,
            nip=model.nip,
            signature_image_path=model.signature_image_path,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _apply_to_model(domain: User, model: UserModel) -> None:
        model.name = domain.name
        model.email = domain.email
        model.password_hash = domain.password_hash
        model.role = domain.role
        model.nim = domain.nim
        model.nip = domain.nip
        model.signature_image_path = domain.signature_image_path

    # ------------------------------------------------------------------
    # CRUD operations — return domain entities
    # ------------------------------------------------------------------

    def create(self, user: User) -> User:
        model = UserModel()
        self._apply_to_model(user, model)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(model) if model else None

    def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(model) if model else None

    def get_by_nim(self, nim: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.nim == nim).first()
        return self._to_domain(model) if model else None

    def get_by_nip(self, nip: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.nip == nip).first()
        return self._to_domain(model) if model else None

    def get_all(self) -> List[User]:
        models = self.db.query(UserModel).all()
        return [self._to_domain(m) for m in models]

    def get_lecturers(self) -> List[User]:
        models = self.db.query(UserModel).filter(UserModel.role == UserRole.DOSEN).all()
        return [self._to_domain(m) for m in models]

    def search_lecturers(self, keyword: str, limit: int = 10) -> List[User]:
        query = self.db.query(UserModel).filter(UserModel.role == UserRole.DOSEN)
        if keyword.strip():
            pattern = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    UserModel.name.ilike(pattern),
                    UserModel.nip.ilike(pattern),
                )
            )
        models = query.order_by(UserModel.name.asc()).limit(limit).all()
        return [self._to_domain(m) for m in models]

    def update(self, user: User) -> User:
        model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not model:
            raise EntityNotFoundError("User tidak ditemukan")
        self._apply_to_model(user, model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def delete(self, user_id: int) -> bool:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
