from typing import Optional

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import UserRole
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT and return the authenticated ``User`` domain entity."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Token tidak valid"}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Token tidak valid"}},
        )
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Token tidak valid"}},
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User tidak ditemukan"}},
        )
    return user


def get_current_user_from_token(token_str: str, db: Session) -> User:
    """Shared logic: validate token string and return User domain entity."""
    payload = decode_access_token(token_str)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Token tidak valid"}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User tidak ditemukan")
    return user


def get_current_user_flexible(
    request: Request,
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Accept token from Authorization header OR ?token= query param.
    Used for endpoints that need to be embedded in <iframe> (e.g. PDF viewer).
    """
    # Try query param first (iframe scenario)
    if token:
        return get_current_user_from_token(token, db)
    # Fall back to Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return get_current_user_from_token(auth_header[7:], db)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "INVALID_TOKEN", "message": "Token tidak valid"}},
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: UserRole):
    """FastAPI dependency that enforces role-based access."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "UNAUTHORIZED", "message": "Akses ditolak"}},
            )
        return current_user
    return role_checker

