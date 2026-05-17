from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.domain.enums import UserRole


class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    nim: Optional[str] = None
    nip: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    nim: Optional[str] = None
    nip: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class LecturerSearchResponse(BaseModel):
    id: int
    name: str
    nip: Optional[str] = None
    email: str


class UserSearchResponse(BaseModel):
    """Used by /api/auth/users/search for the external signing wizard."""
    id: int
    name: str
    email: str
    role: str
    nim: Optional[str] = None
    nip: Optional[str] = None
