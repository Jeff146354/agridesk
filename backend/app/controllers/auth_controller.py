from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import UserRole
from app.domain.user import User
from app.schemas.user_schema import (
    LecturerSearchResponse,
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
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
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(email=request.email, password=request.password)


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
