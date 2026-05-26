from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    actor_id = Column(Integer, nullable=True)
    actor_role = Column(String, nullable=True)
    target_type = Column(String, nullable=True)
    target_id = Column(Integer, nullable=True)
    status = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
