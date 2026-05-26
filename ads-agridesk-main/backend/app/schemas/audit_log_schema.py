from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    event_name: str
    actor_id: Optional[int] = None
    actor_role: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    status: Optional[str] = None
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedAuditLogResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int
