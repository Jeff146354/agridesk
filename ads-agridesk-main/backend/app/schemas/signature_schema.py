from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.enums import UserRole


class SignatureResponse(BaseModel):
    id: int
    surat_id: int
    owner_id: int
    role: UserRole
    image_path: Optional[str] = None
    signature_hash: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    surat_jenis: Optional[str] = None
    mahasiswa_name: Optional[str] = None
    owner_name: Optional[str] = None
    owner_nip: Optional[str] = None

    model_config = {"from_attributes": True}


class SignatureProfileResponse(BaseModel):
    has_saved_signature: bool
    signature_image_path: Optional[str] = None
    signature_hash: Optional[str] = None
    updated_at: Optional[datetime] = None
