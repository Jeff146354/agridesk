from app.domain.enums import SuratStatus
from app.models.surat import SuratModel
from app.models.user import UserModel
from app.domain.enums import UserRole
from app.services.verification_service import VerificationService


def _create_surat(db, doc_hash=None, status=SuratStatus.SELESAI) -> SuratModel:
    user = UserModel(
        name="Budi", email="budi@u.id", password_hash="x",
        role=UserRole.MAHASISWA, nim="111",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    surat = SuratModel(
        mahasiswa_id=user.id, jenis="test", keperluan="test",
        is_external=True, file_path="/f.pdf", status=status,
        document_hash=doc_hash,
    )
    db.add(surat)
    db.commit()
    db.refresh(surat)
    return surat


class TestVerificationService:
    def test_valid_document(self, db):
        surat = _create_surat(db, doc_hash="abc123", status=SuratStatus.SELESAI)
        service = VerificationService(db)
        result = service.verify_document("abc123")
        assert result["status"] == "VALID"
        assert result["document"]["id"] == surat.id

    def test_invalid_hash(self, db):
        service = VerificationService(db)
        result = service.verify_document("nonexistent")
        assert result["status"] == "INVALID"

    def test_document_not_selesai_is_invalid(self, db):
        _create_surat(db, doc_hash="abc123", status=SuratStatus.DRAFT)
        service = VerificationService(db)
        result = service.verify_document("abc123")
        assert result["status"] == "INVALID"
