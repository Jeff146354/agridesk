import pytest

from app.domain.enums import UserRole, SuratStatus
from app.domain.exceptions import UnauthorizedError, ValidationError
from app.models.user import UserModel
from app.models.surat import SuratModel
from app.models.signature import SignatureModel
from app.services.signature_service import SignatureService
from app.repositories.surat_repository import SuratRepository
from app.repositories.signature_repository import SignatureRepository


def _create_student(db) -> UserModel:
    user = UserModel(
        name="Budi", email="budi@u.id", password_hash="x",
        role=UserRole.MAHASISWA, nim="111",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_lecturer(db, email="dosen@u.id", nip="999") -> UserModel:
    user = UserModel(
        name="Dr. Sari", email=email, password_hash="x",
        role=UserRole.DOSEN, nip=nip,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_surat_with_lecturer(db, student, lecturer) -> SuratModel:
    surat = SuratModel(
        mahasiswa_id=student.id,
        jenis="test", keperluan="test",
        is_external=True, file_path="/f.pdf",
        status=SuratStatus.MENUNGGU_TTD_DOSEN,
    )
    db.add(surat)
    db.commit()
    db.refresh(surat)
    sig = SignatureModel(
        surat_id=surat.id, owner_id=lecturer.id,
        role=UserRole.DOSEN,
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return surat


class TestSignatureServiceStudent:
    def test_add_student_signature(self, db):
        student = _create_student(db)
        surat = SuratModel(
            mahasiswa_id=student.id, jenis="test", keperluan="test",
            is_external=True, file_path="/f.pdf", status=SuratStatus.DRAFT,
        )
        db.add(surat)
        db.commit()
        db.refresh(surat)

        service = SignatureService(db)
        sig = service.add_student_signature(surat.id, student.id, "/sig.png")
        assert sig.id is not None
        assert sig.role == UserRole.MAHASISWA
        assert sig.signed_at is not None
        assert sig.signature_hash is not None


class TestSignatureServiceLecturer:
    def test_sign_by_lecturer_success(self, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        surat = _create_surat_with_lecturer(db, student, lecturer)

        sig_repo = SignatureRepository(db)
        pending = sig_repo.get_pending_for_lecturer(lecturer.id)
        assert len(pending) == 1

        service = SignatureService(db)
        signed = service.sign_by_lecturer(pending[0].id, lecturer.id, "/sig.png")
        assert signed.signed_at is not None
        assert signed.signature_hash is not None

    def test_sign_wrong_lecturer_raises(self, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        other = _create_lecturer(db, email="other@u.id", nip="888")
        surat = _create_surat_with_lecturer(db, student, lecturer)

        sig_repo = SignatureRepository(db)
        pending = sig_repo.get_pending_for_lecturer(lecturer.id)

        service = SignatureService(db)
        with pytest.raises(UnauthorizedError, match="Bukan tanda tangan Anda"):
            service.sign_by_lecturer(pending[0].id, other.id, "/sig.png")

    def test_sign_already_signed_raises(self, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        surat = _create_surat_with_lecturer(db, student, lecturer)

        sig_repo = SignatureRepository(db)
        pending = sig_repo.get_pending_for_lecturer(lecturer.id)

        service = SignatureService(db)
        service.sign_by_lecturer(pending[0].id, lecturer.id, "/sig.png")

        with pytest.raises(ValidationError, match="Sudah ditandatangani"):
            service.sign_by_lecturer(pending[0].id, lecturer.id, "/sig2.png")


class TestSignatureAutoTransition:
    def test_all_signed_transitions_to_admin(self, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        surat = _create_surat_with_lecturer(db, student, lecturer)

        sig_repo = SignatureRepository(db)
        pending = sig_repo.get_pending_for_lecturer(lecturer.id)

        service = SignatureService(db)
        service.sign_by_lecturer(pending[0].id, lecturer.id, "/sig.png")

        surat_repo = SuratRepository(db)
        updated = surat_repo.get_by_id(surat.id)
        assert updated.status == SuratStatus.MENUNGGU_PROSES_ADMIN

    def test_partial_signed_stays_menunggu_ttd(self, db):
        student = _create_student(db)
        l1 = _create_lecturer(db, email="l1@u.id", nip="901")
        l2 = _create_lecturer(db, email="l2@u.id", nip="902")

        surat = SuratModel(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            is_external=True, file_path="/f.pdf",
            status=SuratStatus.MENUNGGU_TTD_DOSEN,
        )
        db.add(surat)
        db.commit()
        db.refresh(surat)

        sig1 = SignatureModel(surat_id=surat.id, owner_id=l1.id, role=UserRole.DOSEN)
        sig2 = SignatureModel(surat_id=surat.id, owner_id=l2.id, role=UserRole.DOSEN)
        db.add_all([sig1, sig2])
        db.commit()
        db.refresh(sig1)

        service = SignatureService(db)
        service.sign_by_lecturer(sig1.id, l1.id, "/sig.png")

        surat_repo = SuratRepository(db)
        updated = surat_repo.get_by_id(surat.id)
        assert updated.status == SuratStatus.MENUNGGU_TTD_DOSEN
