from pathlib import Path
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agridesk"
    SECRET_KEY: str = None  # Wajib set di .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads"

    # Public URL for generating QR codes that are scannable from mobile
    BASE_URL: str = "https://drive.hq.idenx.id"

    # Storage — defaults to local filesystem (False = no S3/MinIO)
    USE_S3: bool = False

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


try:
    settings = Settings()
    if not settings.SECRET_KEY or settings.SECRET_KEY.strip() == "" or settings.SECRET_KEY == "change-this-secret-key-in-production":
        raise ValueError("SECRET_KEY must be set to a secure value in your environment or .env file.")
except Exception as e:
    import sys
    print("\n" + "=" * 80, file=sys.stderr)
    print("CRITICAL CONFIGURATION ERROR: SECRET_KEY IS MISSING!", file=sys.stderr)
    print("Please configure SECRET_KEY in your backend/.env file with a secure random string.", file=sys.stderr)
    print("Example: SECRET_KEY=" + secrets.token_urlsafe(32), file=sys.stderr)
    print("=" * 80 + "\n", file=sys.stderr)
    raise RuntimeError("Application startup aborted due to missing SECRET_KEY.") from e

