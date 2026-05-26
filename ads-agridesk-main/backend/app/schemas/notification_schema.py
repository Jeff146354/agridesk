from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    category: str
    title: str
    message: str
    link: str | None = None
    created_at: datetime | None = None
    source_event: str | None = None
