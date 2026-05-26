from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.verification_schema import VerificationResponse
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/api/verify", tags=["Verification"])


@router.get("/{document_hash}", response_model=VerificationResponse)
def verify_document(document_hash: str, db: Session = Depends(get_db)):
    service = VerificationService(db)
    return service.verify_document(document_hash)

@router.get("/sig/{signature_hash}", response_model=VerificationResponse)
def verify_signature(signature_hash: str, db: Session = Depends(get_db)):
    service = VerificationService(db)
    return service.verify_signature(signature_hash)

@router.get("/download/{hash_value}")
def download_verified_pdf(hash_value: str, db: Session = Depends(get_db)):
    service = VerificationService(db)
    return service.download_pdf(hash_value)

