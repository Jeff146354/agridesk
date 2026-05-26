"""
Centralised audit-logging service.

Replaces the duplicated ``_log_event`` helpers that previously existed in
both ``SuratService`` and ``SignatureService``.
"""

from sqlalchemy.orm import Session

from app.domain.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    """Single-responsibility service for recording audit trail events."""

    def __init__(self, db: Session):
        self.audit_repo = AuditLogRepository(db)

    def log_event(
        self,
        event_name: str,
        actor_id: int,
        actor_role: str,
        target_type: str,
        target_id: int,
        status: str,
        metadata_json: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog.log_event(
            event_name=event_name,
            actor_id=actor_id,
            actor_role=actor_role,
            target_type=target_type,
            target_id=target_id,
            status=status,
            metadata_json=metadata_json,
            ip_address=ip_address,
        )
        return self.audit_repo.create(log)

    def get_logs(self, skip: int = 0, limit: int = 20) -> tuple[list[AuditLog], int]:
        logs = self.audit_repo.get_all(skip, limit)
        total = self.audit_repo.count_all()
        return logs, total
