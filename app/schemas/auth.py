from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[str] = "employee"  # ignored server-side

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

class MFASetupOut(BaseModel):
    otp_uri: str
    secret:  str
    message: str

class MFAVerifyRequest(BaseModel):
    otp_code: str   # 6-digit TOTP

class MFALoginRequest(BaseModel):
    mfa_token: str
    otp_code:  str

class LoginResponse(BaseModel):
    """
    mfa_required=False → access_token present, login complete.
    mfa_required=True  → mfa_token present, call POST /auth/mfa-login next.
    """
    access_token: Optional[str] = None
    token_type:   str           = "bearer"
    role:         Optional[str] = None
    username:     Optional[str] = None
    mfa_required: bool          = False
    mfa_token:    Optional[str] = None