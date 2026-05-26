from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel


class SignerInfo(BaseModel):
    name: str
    role: str
    email: Optional[str] = None
    nip: Optional[str] = None
    signed_at: Optional[datetime] = None
    signing_order: Optional[int] = None
    page_number: int = 1
    is_signed: bool = False


class DocumentInfo(BaseModel):
    id: int
    code: str
    jenis: str
    keperluan: str
    is_external: bool
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    page_count: int = 1
    internal_fields: Optional[Any] = None
    status: Optional[str] = None


class VerificationResponse(BaseModel):
    status: str  # VALID | INVALID | TAMPERED
    verification_id: Optional[str] = None
    document: Optional[DocumentInfo] = None
    signers: Optional[List[SignerInfo]] = None
    document_hash: Optional[str] = None
    # Legacy fields for backward compatibility
    surat_id: Optional[int] = None
    jenis: Optional[str] = None
    keperluan: Optional[str] = None
