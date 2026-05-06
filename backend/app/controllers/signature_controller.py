from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import UserRole
from app.domain.user import User
from app.schemas.signature_schema import SignatureResponse, SignatureProfileResponse
from app.services.auth_service import AuthService
from app.services.signature_service import SignatureService
from app.utils.dependencies import get_current_user, require_role
from app.utils.upload import save_signature_upload

router = APIRouter(prefix="/api/signatures", tags=["Signatures"])


@router.post("/student/{surat_id}", response_model=SignatureResponse, status_code=status.HTTP_201_CREATED)
def add_student_signature(
    surat_id: int,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    # Use uploaded signature when provided; fallback to saved signature profile.
    if file is not None:
        image_path = save_signature_upload(file, prefix=f"student_{current_user.id}_{surat_id}")
    elif current_user.signature_image_path:
        image_path = current_user.signature_image_path
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tanda tangan belum disimpan")

    service = SignatureService(db)
    return service.add_student_signature(surat_id, current_user.id, image_path)


@router.post("/lecturer/{signature_id}/sign", response_model=SignatureResponse)
def sign_by_lecturer(
    signature_id: int,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOSEN)),
):
    # Use uploaded signature when provided; fallback to saved signature profile.
    if file is not None:
        image_path = save_signature_upload(file, prefix=f"lecturer_{current_user.id}_{signature_id}")
    elif current_user.signature_image_path:
        image_path = current_user.signature_image_path
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tanda tangan belum disimpan")

    service = SignatureService(db)
    return service.sign_by_lecturer(signature_id, current_user.id, image_path)


@router.get("/me", response_model=SignatureProfileResponse)
def get_my_signature_profile(
    current_user: User = Depends(get_current_user),
):
    import hashlib
    sig_hash = None
    if current_user.signature_image_path:
        sig_hash = hashlib.md5((current_user.signature_image_path + str(current_user.updated_at)).encode('utf-8')).hexdigest()

    return {
        "has_saved_signature": bool(current_user.signature_image_path),
        "signature_image_path": current_user.signature_image_path,
        "signature_hash": sig_hash,
        "updated_at": current_user.updated_at,
    }


@router.get("/me/image")
def get_my_signature_image(
    current_user: User = Depends(get_current_user),
):
    path = current_user.signature_image_path
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tanda tangan belum disimpan")
    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File tanda tangan tidak ditemukan")
    return FileResponse(
        path,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Vary": "Authorization",
        },
    )


@router.post("/me", response_model=SignatureProfileResponse)
def save_my_signature_profile(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import hashlib
    image_path = save_signature_upload(file, prefix=f"profile_{current_user.id}")

    # Delegate persistence to service — no direct DB access in controller.
    auth_service = AuthService(db)
    updated_user = auth_service.update_signature_image(current_user.id, image_path)

    sig_hash = hashlib.md5((updated_user.signature_image_path + str(updated_user.updated_at)).encode('utf-8')).hexdigest() if updated_user.signature_image_path else None

    return {
        "has_saved_signature": bool(updated_user.signature_image_path),
        "signature_image_path": updated_user.signature_image_path,
        "signature_hash": sig_hash,
        "updated_at": updated_user.updated_at,
    }


@router.get("/pending", response_model=List[SignatureResponse])
def get_pending_signatures(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOSEN)),
):
    service = SignatureService(db)
    return service.get_pending_for_lecturer(current_user.id)


@router.get("/signed", response_model=List[SignatureResponse])
def get_signed_signatures(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOSEN)),
):
    service = SignatureService(db)
    return service.get_signed_for_lecturer(current_user.id)


@router.get("/surat/{surat_id}", response_model=List[SignatureResponse])
def get_signatures_for_surat(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SignatureService(db)
    return service.get_signatures_for_surat(surat_id)
