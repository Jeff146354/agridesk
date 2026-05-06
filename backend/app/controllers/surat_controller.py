import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import UserRole
from app.domain.user import User
from app.schemas.surat_schema import (
    InternalLetterRequest,
    InternalTemplateResponse,
    RejectLetterRequest,
    SuratResponse,
)
from app.services.surat_service import SuratService
from app.utils.dependencies import get_current_user, get_current_user_flexible, require_role
from app.utils.upload import save_pdf_upload

router = APIRouter(prefix="/api/surat", tags=["Surat"])


# --- Student endpoints ---


@router.post("/internal", response_model=SuratResponse, status_code=status.HTTP_201_CREATED)
def create_internal_letter(
    request: InternalLetterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.create_internal_letter(
        mahasiswa_id=current_user.id,
        jenis=request.jenis,
        keperluan=request.keperluan,
        fields=request.fields,
        lecturer_ids=request.lecturer_ids,
    )


@router.post("/external", response_model=SuratResponse, status_code=status.HTTP_201_CREATED)
def create_external_letter(
    jenis: str = Form(...),
    keperluan: str = Form(...),
    lecturer_ids: str = Form(default=""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    # Validate and save uploaded PDF
    file_path = save_pdf_upload(file, prefix=f"ext_{current_user.id}")

    # Parse lecturer IDs
    lid_list = None
    if lecturer_ids.strip():
        lid_list = [int(x.strip()) for x in lecturer_ids.split(",") if x.strip()]

    service = SuratService(db)
    return service.create_external_letter(
        mahasiswa_id=current_user.id,
        jenis=jenis,
        keperluan=keperluan,
        file_path=file_path,
        lecturer_ids=lid_list,
    )


@router.post("/{surat_id}/submit", response_model=SuratResponse)
def submit_letter(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.submit_letter(surat_id, current_user.id)


@router.get("/my", response_model=List[SuratResponse])
def get_my_letters(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.get_surat_by_mahasiswa(current_user.id)


@router.get("/templates/internal", response_model=List[InternalTemplateResponse])
def get_internal_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.get_internal_templates()


# --- Admin endpoints ---


@router.get("/pending", response_model=List[SuratResponse])
def get_pending_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    return service.get_pending_admin()


@router.post("/{surat_id}/approve", response_model=SuratResponse)
def approve_letter(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    return service.approve_by_admin(surat_id, current_user.id)


@router.post("/{surat_id}/reject", response_model=SuratResponse)
def reject_letter(
    surat_id: int,
    request: RejectLetterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DOSEN)),
):
    service = SuratService(db)
    return service.reject_letter(
        surat_id, current_user.id, current_user.role.value, request.reason,
    )


# --- General ---


@router.get("/all", response_model=List[SuratResponse])
def get_all_surat(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    return service.get_all_surat()


@router.get("/{surat_id}", response_model=SuratResponse)
def get_surat_detail(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SuratService(db)
    return service.get_surat_with_access_check(surat_id, current_user.id, current_user.role)


@router.get("/{surat_id}/pdf")
def view_surat_pdf(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_flexible),
):
    service = SuratService(db)
    surat = service.get_surat_with_access_check(surat_id, current_user.id, current_user.role)

    file_path = surat.pdf_path or surat.file_path
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF belum tersedia")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File PDF tidak ditemukan")

    with open(file_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{os.path.basename(file_path)}"'},
    )




@router.get("/public/stats")
def get_public_stats(db: Session = Depends(get_db)):
    from app.models.surat import SuratModel
    from sqlalchemy import func
    
    total = db.query(func.count(SuratModel.id)).scalar() or 0
    completed_letters = db.query(SuratModel).filter(SuratModel.status == "SELESAI").all()
    completed = len(completed_letters)
    
    rate = 0 if total == 0 else int((completed / total) * 100)
    
    avg_days = 0.0
    if completed > 0:
        total_seconds = sum(
            (letter.updated_at - letter.created_at).total_seconds()
            for letter in completed_letters
            if letter.updated_at and letter.created_at
        )
        avg_days = round((total_seconds / completed) / 86400, 1)
    
    return {
        "total_surat": total,
        "rata_rata_hari": avg_days,
        "tingkat_selesai": rate
    }
