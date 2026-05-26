from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AuditLog:
    id: Optional[int] = None
    event_name: str = ""
    actor_id: Optional[int] = None
    actor_role: str = ""
    target_type: str = ""
    target_id: Optional[int] = None
    status: str = ""
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    @staticmethod
    def log_event(
        event_name: str,
        actor_id: int,
        actor_role: str,
        target_type: str,
        target_id: int,
        status: str,
        metadata_json: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> "AuditLog":
        return AuditLog(
            event_name=event_name,
            actor_id=actor_id,
            actor_role=actor_role,
            target_type=target_type,
            target_id=target_id,
            status=status,
            metadata_json=metadata_json,
            ip_address=ip_address,
        )
