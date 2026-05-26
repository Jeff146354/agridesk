import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query, BackgroundTasks
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
    PaginatedSuratResponse,
)
from app.services.surat_service import SuratService
from app.utils.dependencies import get_current_user, get_current_user_flexible, require_role
from app.utils.upload import save_pdf_upload

router = APIRouter(prefix="/api/surat", tags=["Surat"])


# --- Student endpoints ---


@router.post("/internal", response_model=SuratResponse, status_code=status.HTTP_201_CREATED)
def create_internal_letter(
    request: InternalLetterRequest,
    background_tasks: BackgroundTasks,
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
        background_tasks=background_tasks,
    )


@router.post("/external", response_model=SuratResponse, status_code=status.HTTP_201_CREATED)
def create_external_letter(
    jenis: str = Form(...),
    keperluan: str = Form(...),
    lecturer_ids: str = Form(default=""),
    signer_configs_json: str = Form(default=""),
    is_sequential: bool = Form(default=False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    import json
    # Validate and save uploaded PDF
    file_path = save_pdf_upload(file, prefix=f"ext_{current_user.id}")

    # Parse rich signer configs (new wizard format)
    signer_configs = None
    if signer_configs_json.strip():
        try:
            signer_configs = json.loads(signer_configs_json)
        except (json.JSONDecodeError, ValueError):
            signer_configs = None

    # Legacy: parse plain lecturer IDs
    lid_list = None
    if not signer_configs and lecturer_ids.strip():
        lid_list = [int(x.strip()) for x in lecturer_ids.split(",") if x.strip()]

    service = SuratService(db)
    return service.create_external_letter(
        mahasiswa_id=current_user.id,
        jenis=jenis,
        keperluan=keperluan,
        file_path=file_path,
        signer_configs=signer_configs,
        is_sequential=is_sequential,
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


@router.get("/my", response_model=PaginatedSuratResponse)
def get_my_letters(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    skip = (page - 1) * size
    items, total = service.get_surat_by_mahasiswa(current_user.id, skip=skip, limit=size)
    return PaginatedSuratResponse(items=items, total=total, page=page, size=size)


@router.get("/{surat_id}/page-count")
def get_surat_page_count(
    surat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SuratService(db)
    count = service.get_page_count(surat_id, current_user.id, current_user.role)
    return {"page_count": count}


@router.get("/templates/internal", response_model=List[InternalTemplateResponse])
def get_internal_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.get_internal_templates()


# --- Admin endpoints ---


@router.get("/pending", response_model=PaginatedSuratResponse)
def get_pending_admin(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    skip = (page - 1) * size
    items, total = service.get_pending_admin(skip=skip, limit=size)
    return PaginatedSuratResponse(items=items, total=total, page=page, size=size)


@router.post("/{surat_id}/approve", response_model=SuratResponse)
def approve_letter(
    surat_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    return service.approve_by_admin(surat_id, current_user.id, background_tasks)


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


@router.get("/all", response_model=PaginatedSuratResponse)
def get_all_surat(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = SuratService(db)
    skip = (page - 1) * size
    items, total = service.get_all_surat(skip=skip, limit=size)
    return PaginatedSuratResponse(items=items, total=total, page=page, size=size)


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

    file_key = surat.pdf_path or surat.file_path
    if not file_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF belum tersedia")
    
    try:
        from app.utils.storage import storage_service
        pdf_bytes = storage_service.get_file_content(file_key)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File PDF tidak ditemukan di storage")

    # Get signed signatures to overlay onto the PDF
    from app.repositories.signature_repository import SignatureRepository
    sig_repo = SignatureRepository(db)
    signatures = sig_repo.get_by_surat_id(surat_id)
    signed_sigs = [s for s in signatures if s.is_signed() and s.image_path and s.pos_x is not None and s.pos_y is not None]

    if signed_sigs:
        from app.utils.pdf_generator import PDFGenerator
        pdf_bytes = PDFGenerator.overlay_signatures_on_pdf(
            pdf_path_or_bytes=pdf_bytes,
            signatures=signed_sigs,
            document_hash=surat.document_hash,
        )

    filename = os.path.basename(file_key) if "/" in file_key else file_key
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )




@router.get("/public/stats")
def get_public_stats(db: Session = Depends(get_db)):
    from app.models.surat import SuratModel
    from app.models.signature import SignatureModel
    from sqlalchemy import func
    
    completed_letters = db.query(SuratModel).filter(SuratModel.status == "SELESAI").all()
    dokumen_terbit = len(completed_letters)
    
    tanda_tangan = db.query(func.count(SignatureModel.id)).filter(SignatureModel.signed_at.isnot(None)).scalar() or 0
    
    avg_hours = 0.0
    if dokumen_terbit > 0:
        total_seconds = sum(
            (letter.updated_at - letter.created_at).total_seconds()
            for letter in completed_letters
            if letter.updated_at and letter.created_at
        )
        avg_hours = round((total_seconds / dokumen_terbit) / 3600, 1)
    
    return {
        "dokumen_terbit": dokumen_terbit,
        "tanda_tangan": tanda_tangan,
        "rata_rata_jam": avg_hours
    }
