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


@router.get("/my", response_model=List[SuratResponse])
def get_my_letters(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = SuratService(db)
    return service.get_surat_by_mahasiswa(current_user.id)


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

    # Get signed signatures to overlay onto the PDF
    from app.repositories.signature_repository import SignatureRepository
    sig_repo = SignatureRepository(db)
    signatures = sig_repo.get_by_surat_id(surat_id)
    signed_sigs = [s for s in signatures if s.is_signed() and s.image_path and s.pos_x is not None and s.pos_y is not None]

    if not signed_sigs:
        # No signatures to overlay, serve raw PDF
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
    else:
        # Overlay signature images onto PDF pages
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.units import cm
        from io import BytesIO

        reader = PdfReader(file_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        # Group signatures by page
        sigs_by_page = {}
        for sig in signed_sigs:
            pg = (sig.page_number or 1) - 1  # 0-indexed
            sigs_by_page.setdefault(pg, []).append(sig)

        for page_idx, page_sigs in sigs_by_page.items():
            if page_idx >= len(writer.pages):
                continue
            target_page = writer.pages[page_idx]
            page_width = float(target_page.mediabox.width)
            page_height = float(target_page.mediabox.height)

            overlay_buf = BytesIO()
            overlay = rl_canvas.Canvas(overlay_buf, pagesize=(page_width, page_height))

            for sig in page_sigs:
                if not sig.image_path or not os.path.exists(sig.image_path):
                    continue
                # Convert from screen coords (top-left origin) to PDF coords (bottom-left origin)
                # The wizard stores pos_x/pos_y relative to the rendered page width.
                # We need to scale from the rendered width (≈700px) to actual PDF points.
                # PDF A4 width ≈ 595 points. Scale factor = pdf_width / rendered_width
                rendered_width = 700  # approximate rendered width used in the wizard
                scale = page_width / rendered_width

                # Bounding box of the signature slot
                box_x = sig.pos_x * scale
                box_y = page_height - (sig.pos_y * scale) - (sig.pos_height * scale)
                box_w = sig.pos_width * scale
                box_h = sig.pos_height * scale

                # Stamp frame dimensions (shrink to fit within text without colliding)
                pdf_w = box_w * 0.95
                pdf_h = box_h * 0.75
                pdf_x = box_x + (box_w - pdf_w) / 2
                pdf_y = box_y + (box_h - pdf_h) / 2

                try:
                    # DRAW DIGITAL SIGNATURE STAMP
                    # 1. Background and Border
                    overlay.setFillColorRGB(1, 1, 1, 0.8) # semi-transparent white background
                    overlay.rect(pdf_x, pdf_y, pdf_w, pdf_h, fill=1, stroke=0)
                    
                    overlay.setStrokeColorRGB(0.2, 0.2, 0.2)
                    overlay.setLineWidth(0.7)
                    overlay.rect(pdf_x, pdf_y, pdf_w, pdf_h, fill=0, stroke=1)

                    # 2. QR Code
                    from app.utils.qr_generator import QRCodeGenerator
                    from app.config import settings
                    qr_filename = f"sig_qr_{sig.id}.png"
                    qr_path = os.path.join(settings.UPLOAD_DIR, "qr_codes", qr_filename)
                    if not os.path.exists(qr_path):
                        # Link to document verifier if approved, else a generic signature verifier
                        url = f"/verify/{surat.document_hash}" if surat.document_hash else f"/verify-sig/{sig.signature_hash}"
                        QRCodeGenerator.generate_qr_code(url, qr_filename)
                    
                    qr_padding = 4 * scale
                    qr_size = pdf_h - (qr_padding * 2)
                    qr_x = pdf_x + qr_padding
                    qr_y = pdf_y + qr_padding
                    
                    if os.path.exists(qr_path):
                        overlay.drawImage(
                            qr_path, qr_x, qr_y,
                            width=qr_size, height=qr_size,
                            preserveAspectRatio=True, mask="auto"
                        )
                    
                    # 3. Text right of QR code
                    text_x = qr_x + qr_size + qr_padding
                    text_y = pdf_y + pdf_h - (8 * scale)
                    
                    overlay.setFillColorRGB(0.2, 0.2, 0.2)
                    overlay.setFont("Helvetica", 3.8 * scale)
                    overlay.drawString(text_x, text_y, "Ditandatangani secara elektronik oleh:")
                    
                    overlay.setFont("Helvetica-Bold", 4.2 * scale)
                    owner_name = (sig.owner_name or "Sistem Agridesk")[:25]
                    overlay.drawString(text_x, text_y - (5.5 * scale), owner_name)
                    
                    # 4. The actual signature image
                    sig_img_h = pdf_h - (18 * scale)
                    sig_img_w = pdf_w - qr_size - (3 * qr_padding)
                    sig_img_y = pdf_y + (4 * scale)
                    overlay.drawImage(
                        sig.image_path,
                        text_x, sig_img_y,
                        width=sig_img_w, height=sig_img_h,
                        preserveAspectRatio=True, mask="auto"
                    )

                    # 5. Bottom text
                    overlay.setFont("Helvetica", 3.5 * scale)
                    overlay.drawRightString(pdf_x + pdf_w - (4 * scale), pdf_y + (3 * scale), "agridesk.ipb.ac.id")

                except Exception:
                    pass  # Skip broken images

            overlay.save()
            overlay_buf.seek(0)
            overlay_reader = PdfReader(overlay_buf)
            if overlay_reader.pages:
                target_page.merge_page(overlay_reader.pages[0])

        output_buf = BytesIO()
        writer.write(output_buf)
        pdf_bytes = output_buf.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{os.path.basename(file_path)}"'},
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
