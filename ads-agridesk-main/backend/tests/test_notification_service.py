from app.domain.enums import UserRole, SuratStatus
from app.models.user import UserModel
from app.services.notification_service import NotificationService
from app.services.signature_service import SignatureService
from app.services.surat_service import SuratService
from unittest.mock import patch


def _create_user(db, *, name, email, role, nim=None, nip=None):
    user = UserModel(
        name=name,
        email=email,
        password_hash="x",
        role=role,
        nim=nim,
        nip=nip,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@patch("app.services.surat_service.SuratService._generate_final_pdf_task")
def test_student_notifications_cover_submission_and_approval(mock_generate_pdf, db):
    student = _create_user(db, name="Mahasiswa", email="mhs@u.id", role=UserRole.MAHASISWA, nim="111")
    admin = _create_user(db, name="Admin", email="admin@u.id", role=UserRole.ADMIN, nip="000")
    service = SuratService(db)

    surat = service.create_external_letter(
        mahasiswa_id=student.id,
        jenis="Surat Keterangan",
        keperluan="Keperluan",
        file_path="/fake.pdf",
    )
    service.submit_letter(surat.id, student.id)
    approved = service.approve_by_admin(surat.id, admin.id)
    assert approved.status == SuratStatus.SELESAI

    notifications = NotificationService(db).get_notifications(student.id, UserRole.MAHASISWA)
    messages = [item["message"] for item in notifications]
    assert any("sudah diajukan" in message for message in messages)
    mock_generate_pdf.assert_called_once()


def test_lecturer_notifications_include_pending_signature(db):
    student = _create_user(db, name="Mahasiswa", email="mhs2@u.id", role=UserRole.MAHASISWA, nim="222")
    lecturer = _create_user(db, name="Dosen", email="dosen@u.id", role=UserRole.DOSEN, nip="999")
    service = SuratService(db)

    surat = service.create_external_letter(
        mahasiswa_id=student.id,
        jenis="Surat Keterangan",
        keperluan="Keperluan",
        file_path="/fake.pdf",
        lecturer_ids=[lecturer.id],
    )

    notifications = NotificationService(db).get_notifications(lecturer.id, UserRole.DOSEN)
    assert any(item["source_event"] == "SIGNATURE_PENDING" for item in notifications)


def test_admin_notifications_include_pending_letters(db):
    student = _create_user(db, name="Mahasiswa", email="mhs3@u.id", role=UserRole.MAHASISWA, nim="333")
    admin = _create_user(db, name="Admin", email="admin2@u.id", role=UserRole.ADMIN, nip="001")
    service = SuratService(db)

    surat = service.create_external_letter(
        mahasiswa_id=student.id,
        jenis="Surat Keterangan",
        keperluan="Keperluan",
        file_path="/fake.pdf",
    )
    submitted = service.submit_letter(surat.id, student.id)
    assert submitted.status == SuratStatus.MENUNGGU_PROSES_ADMIN

    notifications = NotificationService(db).get_notifications(admin.id, UserRole.ADMIN)
    assert any(item["link"] == "/surat/all" for item in notifications)