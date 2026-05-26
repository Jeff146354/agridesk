import os
import uuid
from typing import Set

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.domain.exceptions import InternalError

ALLOWED_PDF_EXTENSIONS: Set[str] = {".pdf"}
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg"}

ALLOWED_PDF_MIMES: Set[str] = {"application/pdf"}
ALLOWED_IMAGE_MIMES: Set[str] = {"image/png", "image/jpeg"}

MAX_PDF_SIZE: int = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE: int = 2 * 1024 * 1024  # 2 MB


def _get_extension(filename: str | None) -> str:
    if not filename:
        return ""
    return os.path.splitext(filename)[1].lower()


def _validate_upload(
    file: UploadFile,
    allowed_extensions: Set[str],
    allowed_mimes: Set[str],
    max_size: int,
) -> bytes:
    ext = _get_extension(file.filename)
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ekstensi file tidak diizinkan. Gunakan: {', '.join(allowed_extensions)}",
        )

    content_type = file.content_type or ""
    if content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipe MIME tidak diizinkan: {content_type}",
        )

    try:
        data = file.file.read()
    except OSError as exc:
        raise InternalError("Gagal membaca file upload") from exc
    if len(data) > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ukuran file melebihi batas maksimum ({max_mb:.0f} MB)",
        )

    return data


def _sanitize_prefix(prefix: str) -> str:
    safe = "".join(ch for ch in prefix if ch.isalnum() or ch in {"_", "-"})
    return safe or "file"


def _safe_subdir(subdir: str) -> str:
    base_dir = os.path.abspath(settings.UPLOAD_DIR)
    target_dir = os.path.abspath(os.path.join(base_dir, subdir))
    if target_dir != base_dir and not target_dir.startswith(base_dir + os.sep):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direktori upload tidak valid",
        )
    return os.path.relpath(target_dir, base_dir)


def _safe_filename(prefix: str, ext: str) -> str:
    return f"{_sanitize_prefix(prefix)}_{uuid.uuid4().hex}{ext}"


def save_pdf_upload(file: UploadFile, prefix: str, subdir: str = "external") -> str:
    data = _validate_upload(file, ALLOWED_PDF_EXTENSIONS, ALLOWED_PDF_MIMES, MAX_PDF_SIZE)
    ext = _get_extension(file.filename)
    filename = _safe_filename(prefix, ext)
    
    try:
        from app.utils.storage import storage_service
        s3_key = storage_service.upload_file(data, filename)
        return s3_key
    except Exception as exc:
        raise InternalError("Gagal menyimpan file upload ke Storage") from exc


def save_signature_upload(file: UploadFile, prefix: str) -> str:
    data = _validate_upload(file, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_IMAGE_MIMES, MAX_IMAGE_SIZE)
    ext = _get_extension(file.filename)
    filename = _safe_filename(prefix, ext)
    
    try:
        from app.utils.storage import storage_service
        s3_key = storage_service.upload_file(data, filename)
        return s3_key
    except Exception as exc:
        raise InternalError("Gagal menyimpan file upload ke Storage") from exc
