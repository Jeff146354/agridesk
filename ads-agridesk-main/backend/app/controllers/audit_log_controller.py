from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import UserRole
from app.schemas.audit_log_schema import PaginatedAuditLogResponse
from app.services.audit_log_service import AuditLogService
from app.utils.dependencies import get_current_user, require_role

router = APIRouter()

@router.get(
    "/",
    response_model=PaginatedAuditLogResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve system audit logs. Only accessible by ADMIN.
    """
    audit_service = AuditLogService(db)
    logs, total = audit_service.get_logs(skip=skip, limit=limit)
    
    # Map domain entities to schemas manually to ensure correct types
    from app.schemas.audit_log_schema import AuditLogResponse
    items = [
        AuditLogResponse(
            id=log.id,
            event_name=log.event_name,
            actor_id=log.actor_id,
            actor_role=log.actor_role,
            target_type=log.target_type,
            target_id=log.target_id,
            status=log.status,
            metadata_json=log.metadata_json,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]
    
    return PaginatedAuditLogResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )
