from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.utils.limiter import limiter

from app.database import get_db
from app.domain.enums import UserRole
from app.domain.user import User
from app.schemas.user_schema import (
    LecturerSearchResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserSearchResponse,
    RefreshRequest,
    RefreshTokenResponse,
)
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
def register(req: Request, request: UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.register(
        name=request.name,
        email=request.email,
        password=request.password,
        role=request.role,
        nim=request.nim,
        nip=request.nip,
    )
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(req: Request, request: UserLoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(email=request.email, password=request.password)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.refresh(request.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/lecturers/search", response_model=List[LecturerSearchResponse])
def search_lecturers(
    q: str = Query(default="", min_length=0),
    limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    service = AuthService(db)
    return service.search_lecturers(q, limit=limit)


@router.get("/users/search", response_model=List[UserSearchResponse])
def search_users(
    q: str = Query(default="", min_length=0),
    limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
):
    """Search all registered users for signer selection in external document wizard."""
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    users = repo.search_users(q, limit=limit, exclude_id=current_user.id)
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "nim": u.nim,
            "nip": u.nip,
        }
        for u in users
    ]
