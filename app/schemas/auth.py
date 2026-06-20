from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "employee"  # IGNORED server-side, see auth_service.register_user. Self-registration is always "employee"; admins assign other roles via /admin/users.

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True