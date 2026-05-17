from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel

from app.domain.enums import SuratStatus


class InternalLetterRequest(BaseModel):
    jenis: str
    keperluan: str
    fields: Dict[str, str]
    lecturer_ids: Optional[List[int]] = None


class ExternalLetterRequest(BaseModel):
    jenis: str
    keperluan: str
    lecturer_ids: Optional[List[int]] = None


class RejectLetterRequest(BaseModel):
    reason: str


class InternalTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    required_fields: List[str]

    model_config = {"from_attributes": True}


class SuratResponse(BaseModel):
    id: int
    mahasiswa_id: int
    mahasiswa_name: Optional[str] = None
    mahasiswa_nim: Optional[str] = None
    jenis: str
    keperluan: str
    is_external: bool
    is_sequential: bool = False
    file_path: Optional[str] = None
    internal_fields: Optional[Dict[str, str]] = None
    status: SuratStatus
    document_hash: Optional[str] = None
    pdf_path: Optional[str] = None
    qr_path: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
