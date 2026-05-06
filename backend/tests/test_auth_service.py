import pytest

from app.domain.enums import UserRole
from app.domain.exceptions import DuplicateEntityError, ValidationError
from app.services.auth_service import AuthService


class TestAuthService:
    def test_register_student(self, db):
        service = AuthService(db)
        user = service.register(
            name="Budi",
            email="budi@university.ac.id",
            password="password123",
            role=UserRole.MAHASISWA,
            nim="12345678",
        )
        assert user.id is not None
        assert user.name == "Budi"
        assert user.role == UserRole.MAHASISWA
        assert user.nim == "12345678"

    def test_register_lecturer(self, db):
        service = AuthService(db)
        user = service.register(
            name="Dr. Sari",
            email="sari@university.ac.id",
            password="password123",
            role=UserRole.DOSEN,
            nip="198001012000",
        )
        assert user.role == UserRole.DOSEN
        assert user.nip == "198001012000"

    def test_register_duplicate_email_raises(self, db):
        service = AuthService(db)
        service.register(
            name="Budi", email="budi@university.ac.id",
            password="pw", role=UserRole.MAHASISWA, nim="111",
        )
        with pytest.raises(DuplicateEntityError, match="Email sudah terdaftar"):
            service.register(
                name="Budi2", email="budi@university.ac.id",
                password="pw", role=UserRole.MAHASISWA, nim="222",
            )

    def test_register_duplicate_nim_raises(self, db):
        service = AuthService(db)
        service.register(
            name="A", email="a@u.id", password="pw",
            role=UserRole.MAHASISWA, nim="111",
        )
        with pytest.raises(DuplicateEntityError, match="NIM sudah terdaftar"):
            service.register(
                name="B", email="b@u.id", password="pw",
                role=UserRole.MAHASISWA, nim="111",
            )

    def test_login_success(self, db):
        service = AuthService(db)
        service.register(
            name="Budi", email="budi@u.id", password="secret",
            role=UserRole.MAHASISWA, nim="111",
        )
        result = service.login("budi@u.id", "secret")
        assert result["access_token"]
        assert result["token_type"] == "bearer"
        assert result["user"]["role"] == "MAHASISWA"

    def test_login_wrong_password_raises(self, db):
        service = AuthService(db)
        service.register(
            name="Budi", email="budi@u.id", password="secret",
            role=UserRole.MAHASISWA, nim="111",
        )
        with pytest.raises(ValidationError, match="Email atau password salah"):
            service.login("budi@u.id", "wrong")

    def test_login_nonexistent_email_raises(self, db):
        service = AuthService(db)
        with pytest.raises(ValidationError, match="Email atau password salah"):
            service.login("no@u.id", "pw")
