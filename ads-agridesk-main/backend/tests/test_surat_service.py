import pytest
from unittest.mock import patch

from app.domain.enums import UserRole, SuratStatus
from app.domain.exceptions import (
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedError,
    ValidationError,
)
from app.models.user import UserModel
from app.models.surat import SuratModel
from app.services.surat_service import SuratService


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


def _create_admin(db) -> UserModel:
    user = UserModel(
        name="Admin", email="admin@u.id", password_hash="x",
        role=UserRole.ADMIN, nip="000",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestSuratServiceInternalLetter:
    @patch("app.services.surat_service.PDFGenerator.generate_from_template", return_value="/fake/path.pdf")
    def test_create_internal_no_lecturer(self, mock_pdf, db):
        student = _create_student(db)
        service = SuratService(db)
        surat = service.create_internal_letter(
            mahasiswa_id=student.id,
            jenis="pembatalan_mk",
            keperluan="Batalkan MK",
            fields={"mata_kuliah": "Algoritma"},
        )
        assert surat.id is not None
        assert surat.status == SuratStatus.DRAFT
        assert surat.is_external is False

    @patch("app.services.surat_service.PDFGenerator.generate_from_template", return_value="/fake/path.pdf")
    def test_create_internal_with_lecturer_sets_menunggu_ttd(self, mock_pdf, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        service = SuratService(db)
        surat = service.create_internal_letter(
            mahasiswa_id=student.id,
            jenis="izin_penelitian",
            keperluan="Penelitian",
            fields={"judul": "AI"},
            lecturer_ids=[lecturer.id],
        )
        assert surat.status == SuratStatus.MENUNGGU_TTD_DOSEN


class TestSuratServiceExternalLetter:
    def test_create_external_draft(self, db):
        student = _create_student(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="surat_keterangan",
            keperluan="Keperluan lain",
            file_path="/uploads/file.pdf",
        )
        assert surat.status == SuratStatus.DRAFT
        assert surat.is_external is True

    def test_create_external_with_lecturer(self, db):
        student = _create_student(db)
        lecturer = _create_lecturer(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="surat_keterangan",
            keperluan="Keperluan lain",
            file_path="/uploads/file.pdf",
            lecturer_ids=[lecturer.id],
        )
        assert surat.status == SuratStatus.MENUNGGU_TTD_DOSEN


class TestSuratServiceSubmit:
    def test_submit_without_lecturer_goes_to_admin(self, db):
        student = _create_student(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            file_path="/fake.pdf",
        )
        result = service.submit_letter(surat.id, student.id)
        assert result.status == SuratStatus.MENUNGGU_PROSES_ADMIN

    def test_submit_wrong_owner_raises(self, db):
        student = _create_student(db)
        other = UserModel(
            name="Lain", email="other@u.id", password_hash="x",
            role=UserRole.MAHASISWA, nim="222",
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            file_path="/fake.pdf",
        )
        with pytest.raises(UnauthorizedError, match="Bukan surat Anda"):
            service.submit_letter(surat.id, other.id)


class TestSuratServiceApproval:
    @patch("app.services.surat_service.SuratService._generate_final_pdf_task")
    def test_approve_sets_selesai(self, mock_generate_pdf, db):
        student = _create_student(db)
        admin = _create_admin(db)
        service = SuratService(db)

        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            file_path="/fake.pdf",
        )
        submitted = service.submit_letter(surat.id, student.id)
        assert submitted.status == SuratStatus.MENUNGGU_PROSES_ADMIN

        result = service.approve_by_admin(surat.id, admin.id)
        assert result.status == SuratStatus.SELESAI
        mock_generate_pdf.assert_called_once()

    def test_approve_wrong_status_raises(self, db):
        student = _create_student(db)
        admin = _create_admin(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            file_path="/fake.pdf",
        )
        # Still DRAFT, not MENUNGGU_PROSES_ADMIN
        with pytest.raises(InvalidStateTransitionError):
            service.approve_by_admin(surat.id, admin.id)


class TestSuratServiceReject:
    def test_reject_sets_ditolak(self, db):
        student = _create_student(db)
        admin = _create_admin(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test", keperluan="test",
            file_path="/fake.pdf",
        )
        service.submit_letter(surat.id, student.id)

        result = service.reject_letter(surat.id, admin.id, UserRole.ADMIN.value, "Dokumen tidak lengkap")
        assert result.status == SuratStatus.DITOLAK
        assert result.rejection_reason == "Dokumen tidak lengkap"

    def test_dosen_can_reject_own_pending_signature(self, db):
        student = _create_student(db)
        dosen = _create_lecturer(db)
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test",
            keperluan="test",
            file_path="/fake.pdf",
            lecturer_ids=[dosen.id],
        )

        result = service.reject_letter(surat.id, dosen.id, UserRole.DOSEN.value, "Perlu revisi lampiran")
        assert result.status == SuratStatus.DITOLAK
        assert result.rejection_reason == "Perlu revisi lampiran"

    def test_dosen_cannot_reject_not_assigned_pending_signature(self, db):
        student = _create_student(db)
        assigned_dosen = _create_lecturer(db, email="assigned@u.id", nip="901")
        other_dosen = _create_lecturer(db, email="other@u.id", nip="902")
        service = SuratService(db)
        surat = service.create_external_letter(
            mahasiswa_id=student.id,
            jenis="test",
            keperluan="test",
            file_path="/fake.pdf",
            lecturer_ids=[assigned_dosen.id],
        )

        with pytest.raises(UnauthorizedError, match="bukan pending tanda tangan Anda"):
            service.reject_letter(surat.id, other_dosen.id, UserRole.DOSEN.value, "Tidak sesuai")
