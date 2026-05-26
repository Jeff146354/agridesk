from sqlalchemy.orm import Session

from app.domain.enums import UserRole
from app.domain.exceptions import DuplicateEntityError, EntityNotFoundError, ValidationError
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    """Handles registration, login and user profile operations."""

    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register(
        self,
        name: str,
        email: str,
        password: str,
        role: UserRole,
        nim: str | None = None,
        nip: str | None = None,
    ) -> User:
        if self.user_repo.get_by_email(email):
            raise DuplicateEntityError("Email sudah terdaftar")

        if role == UserRole.MAHASISWA and nim:
            if self.user_repo.get_by_nim(nim):
                raise DuplicateEntityError("NIM sudah terdaftar")
        if role in (UserRole.DOSEN, UserRole.ADMIN) and nip:
            if self.user_repo.get_by_nip(nip):
                raise DuplicateEntityError("NIP sudah terdaftar")

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            nim=nim,
            nip=nip,
        )
        return self.user_repo.create(user)

    def login(self, email: str, password: str) -> dict:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValidationError("Email atau password salah")

        # Keep JWT subject as string for standards-compliant decoding.
        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        return {
            "access_token": token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
            },
        }

    def refresh(self, refresh_token: str) -> dict:
        from app.utils.security import decode_access_token
        from app.domain.exceptions import UnauthorizedError
        
        payload = decode_access_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Refresh token tidak valid atau sudah kadaluarsa")
            
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Token tidak valid")
            
        user = self.user_repo.get_by_id(int(user_id))
        if not user:
            raise UnauthorizedError("User tidak ditemukan")
            
        new_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        new_refresh = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": new_token,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }

    def search_lecturers(self, query: str, limit: int = 10) -> list[dict]:
        lecturers = self.user_repo.search_lecturers(query, limit=limit)
        return [
            {
                "id": l.id,
                "name": l.name,
                "nip": l.nip,
                "email": l.email,
            }
            for l in lecturers
        ]

    def update_signature_image(self, user_id: int, image_path: str) -> User:
        """Update the saved signature image for a user (any role)."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User tidak ditemukan")
        user.update_signature_image(image_path)
        return self.user_repo.update(user)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User tidak ditemukan")
        return user
