import os
import uuid
from app.config import settings


class StorageService:
    """
    Local-filesystem storage service.

    Files are stored under UPLOAD_DIR (default: "uploads/").
    USE_S3 is intentionally kept as a no-op flag so that the old
    environment variable doesn't cause a startup error, but we no
    longer connect to MinIO / S3 at all — the mini-pc stores
    everything on /disk/data-01/tristan/data-agd/uploads via a
    Docker bind-mount into /app/uploads inside the container.
    """

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR or "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)

    def upload_file(self, file_content: bytes, original_filename: str) -> str:
        """Save *file_content* to the upload directory and return the relative path."""
        ext = original_filename.split(".")[-1] if "." in original_filename else "bin"
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)
        return filepath

    def get_file_content(self, path_or_key: str) -> bytes:
        """Return the raw bytes for the given file path."""
        # Normalise: strip leading slashes so we don't leave the uploads dir.
        if path_or_key.startswith("/"):
            path_or_key = path_or_key.lstrip("/")

        # Accept both "uploads/xxx.pdf" and bare "xxx.pdf"
        if os.path.isabs(path_or_key) or path_or_key.startswith(self.upload_dir):
            filepath = path_or_key
        else:
            filepath = os.path.join(self.upload_dir, path_or_key)

        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                return f.read()

        raise FileNotFoundError(f"File not found in storage: {path_or_key}")

    def file_exists(self, path_or_key: str) -> bool:
        """Return True if the file exists on disk."""
        try:
            self.get_file_content(path_or_key)
            return True
        except FileNotFoundError:
            return False


storage_service = StorageService()
