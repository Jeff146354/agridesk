from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.domain.enums import SuratStatus, UserRole
from app.models.audit_log import AuditLogModel
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.signature_repository import SignatureRepository
from app.repositories.surat_repository import SuratRepository
from app.domain.signature import Signature
from app.domain.surat import Surat


class NotificationService:
    """Builds user-facing notifications from existing workflow data.

    The project already records audit logs for important surat/signature
    events, so this service derives notifications on demand instead of
    introducing a separate persisted notification table.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_repo = AuditLogRepository(db)
        self.surat_repo = SuratRepository(db)
        self.signature_repo = SignatureRepository(db)

    def get_notifications(self, user_id: int, role: UserRole, limit: int = 8) -> List[dict]:
        if role == UserRole.MAHASISWA:
            return self._for_student(user_id, limit)
        if role == UserRole.DOSEN:
            return self._for_lecturer(user_id, limit)
        return self._for_admin(limit)

    def _for_student(self, user_id: int, limit: int) -> List[dict]:
        notifications: list[dict] = []
        surat_list, _ = self.surat_repo.get_by_mahasiswa_id(user_id, limit=limit)
        surat_list = sorted(
            surat_list,
            key=lambda surat: surat.updated_at or surat.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        for surat in surat_list:
            logs = self.audit_repo.get_by_target("surat", surat.id)
            relevant_logs = [
                log for log in logs
                if log.event_name in {"SURAT_SUBMITTED", "SURAT_READY_ADMIN", "SURAT_APPROVED", "SURAT_REJECTED", "SIGNATURE_ADDED"}
            ]
            if not relevant_logs and surat.status == SuratStatus.DRAFT:
                continue
            if not relevant_logs:
                notifications.append(self._build_item(
                    category="surat",
                    title=f"Surat {surat.jenis}",
                    message=self._status_message_for_student(surat),
                    link=f"/surat/{surat.id}",
                    source_event=surat.status.value if hasattr(surat.status, "value") else str(surat.status),
                    created_at=surat.updated_at or surat.created_at,
                ))
                continue

            for log in relevant_logs[:2]:
                notifications.append(self._notification_from_log(log, surat=surat, audience="student"))

        return notifications[:limit]

    def _for_lecturer(self, user_id: int, limit: int) -> List[dict]:
        notifications: list[dict] = []
        pending = self.signature_repo.get_pending_for_lecturer(user_id)
        signed = self.signature_repo.get_signed_for_lecturer(user_id)

        for signature in pending:
            notifications.append({
                "id": signature.id or len(notifications) + 1,
                "category": "signature",
                "title": "Tanda tangan menunggu Anda",
                "message": f"Surat {signature.surat_jenis or '-'} dari {signature.mahasiswa_name or 'mahasiswa'} menunggu tanda tangan Anda.",
                "link": "/surat/all-dosen",
                "created_at": signature.created_at,
                "source_event": "SIGNATURE_PENDING",
            })

        for signature in signed[:3]:
            if signature.signed_at:
                title = "Tanda tangan sudah tercatat"
                message = f"Anda sudah menandatangani surat {signature.surat_jenis or '-'} dari {signature.mahasiswa_name or 'mahasiswa'}."
                source_event = "SIGNATURE_ADDED"
            else:
                title = "Pengajuan Surat Ditolak"
                message = f"Surat {signature.surat_jenis or '-'} dari {signature.mahasiswa_name or 'mahasiswa'} telah ditolak dan tidak memerlukan tanda tangan Anda."
                source_event = "SURAT_REJECTED"

            notifications.append({
                "id": (signature.id or 0) + 100000,
                "category": "signature",
                "title": title,
                "message": message,
                "link": "/surat/all-dosen",
                "created_at": signature.signed_at or signature.updated_at,
                "source_event": source_event,
            })

        notifications.sort(key=lambda item: item.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return notifications[:limit]

    def _for_admin(self, limit: int) -> List[dict]:
        notifications: list[dict] = []
        pending, _ = self.surat_repo.get_pending_admin(limit=limit)
        for surat in pending:
            notifications.append({
                "id": surat.id or len(notifications) + 1,
                "category": "surat",
                "title": "Surat menunggu persetujuan admin",
                "message": f"Surat {surat.jenis} dari {surat.mahasiswa_name or 'mahasiswa'} menunggu persetujuan admin.",
                "link": "/surat/all",
                "created_at": surat.updated_at or surat.created_at,
                "source_event": "SURAT_SUBMITTED",
            })

        recent_logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.event_name.in_(["SURAT_SUBMITTED", "SURAT_READY_ADMIN", "SURAT_APPROVED", "SURAT_REJECTED"])
        ).order_by(AuditLogModel.created_at.desc()).limit(limit).all()

        for log in recent_logs:
            surat = self.surat_repo.get_by_id(log.target_id) if log.target_id else None
            if not surat:
                continue
            notifications.append(self._notification_from_log(log, surat=surat, audience="admin"))

        notifications.sort(key=lambda item: item.get("created_at") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return notifications[:limit]

    def _notification_from_log(self, log, surat: Surat, audience: str) -> dict:
        if log.event_name == "SURAT_SUBMITTED":
            title = "Surat berhasil diajukan"
            message = f"Surat {surat.jenis} dari {surat.mahasiswa_name or 'mahasiswa'} sudah diajukan."
            link = "/surat/all" if audience == "admin" else f"/surat/{surat.id}"
            category = "surat"
        elif log.event_name == "SURAT_READY_ADMIN":
            title = "Surat siap diproses admin"
            message = f"Semua tanda tangan dosen untuk surat {surat.jenis} sudah lengkap."
            link = "/surat/all"
            category = "process"
        elif log.event_name == "SURAT_APPROVED":
            title = "Surat disetujui admin"
            message = f"Surat {surat.jenis} dari {surat.mahasiswa_name or 'mahasiswa'} sudah di-acc admin."
            link = f"/surat/{surat.id}"
            category = "status"
        elif log.event_name == "SURAT_REJECTED":
            title = "Surat ditolak"
            message = f"Surat {surat.jenis} dari {surat.mahasiswa_name or 'mahasiswa'} ditolak."
            link = f"/surat/{surat.id}"
            category = "status"
        else:
            title = "Tanda tangan surat tercatat"
            actor = "dosen" if log.actor_role == UserRole.DOSEN.value else "mahasiswa"
            message = f"Tanda tangan {actor} untuk surat {surat.jenis} sudah masuk."
            link = f"/surat/{surat.id}"
            category = "signature"

        return self._build_item(
            category=category,
            title=title,
            message=message,
            link=link,
            source_event=log.event_name,
            created_at=log.created_at,
            source_id=log.id or surat.id or 0,
        )

    def _status_message_for_student(self, surat: Surat) -> str:
        status = surat.status.value if hasattr(surat.status, "value") else str(surat.status)
        if status == "MENUNGGU_TTD_DOSEN":
            return f"Surat {surat.jenis} sedang menunggu tanda tangan dosen."
        if status == "MENUNGGU_PROSES_ADMIN":
            return f"Surat {surat.jenis} sudah diajukan dan menunggu proses admin."
        if status == "SELESAI":
            return f"Surat {surat.jenis} sudah selesai dan siap diunduh."
        if status == "DITOLAK":
            return f"Surat {surat.jenis} ditolak."
        return f"Status surat {surat.jenis} saat ini: {status}."

    def _build_item(
        self,
        *,
        category: str,
        title: str,
        message: str,
        link: str | None,
        source_event: str,
        created_at: datetime | None,
        source_id: int | None = None,
    ) -> dict:
        item_id = source_id or int((created_at or datetime.now(timezone.utc)).timestamp())
        return {
            "id": item_id,
            "category": category,
            "title": title,
            "message": message,
            "link": link,
            "created_at": created_at,
            "source_event": source_event,
        }
