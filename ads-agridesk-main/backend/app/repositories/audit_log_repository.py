from typing import List

from sqlalchemy.orm import Session

from app.domain.audit_log import AuditLog
from app.models.audit_log import AuditLogModel


class AuditLogRepository:
    """Persistence layer for AuditLog.  Translates between domain entities and ORM models."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            event_name=model.event_name,
            actor_id=model.actor_id,
            actor_role=model.actor_role,
            target_type=model.target_type,
            target_id=model.target_id,
            status=model.status,
            metadata_json=model.metadata_json,
            ip_address=model.ip_address,
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_to_model(domain: AuditLog, model: AuditLogModel) -> None:
        model.event_name = domain.event_name
        model.actor_id = domain.actor_id
        model.actor_role = domain.actor_role
        model.target_type = domain.target_type
        model.target_id = domain.target_id
        model.status = domain.status
        model.metadata_json = domain.metadata_json
        model.ip_address = domain.ip_address

    # ------------------------------------------------------------------
    # CRUD operations — return domain entities
    # ------------------------------------------------------------------

    def create(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel()
        self._apply_to_model(log, model)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_target(self, target_type: str, target_id: int) -> List[AuditLog]:
        models = (
            self.db.query(AuditLogModel)
            .filter(
                AuditLogModel.target_type == target_type,
                AuditLogModel.target_id == target_id,
            )
            .order_by(AuditLogModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_all(self, skip: int = 0, limit: int = 20) -> List[AuditLog]:
        models = (
            self.db.query(AuditLogModel)
            .order_by(AuditLogModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def count_all(self) -> int:
        return self.db.query(AuditLogModel).count()
