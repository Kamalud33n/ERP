from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserOut,
    MFASetupOut, MFAVerifyRequest, MFALoginRequest, LoginResponse,
)
from app.services.auth_service import (
    register_user, login_user, mfa_login,
    setup_mfa, confirm_mfa, disable_mfa,
)

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, data)

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Step 1. MFA disabled → returns access_token directly.
    MFA enabled → returns mfa_required=True + mfa_token (call /mfa-login next).
    """
    return login_user(db, data)

@router.post("/mfa-login", response_model=LoginResponse)
def login_mfa(data: MFALoginRequest, db: Session = Depends(get_db)):
    """Step 2 of MFA login. Supply mfa_token + 6-digit TOTP code."""
    return mfa_login(db, data.mfa_token, data.otp_code)

@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user

@router.post("/mfa-setup", response_model=MFASetupOut)
def mfa_setup(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Generate TOTP secret + provisioning URI. Scan with Google Authenticator / Authy."""
    return setup_mfa(db, current_user.id)

@router.post("/mfa-confirm")
def mfa_confirm(data: MFAVerifyRequest, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    """Activate MFA by verifying the first code after setup."""
    return confirm_mfa(db, current_user.id, data.otp_code)

@router.post("/mfa-disable")
def mfa_disable(data: MFAVerifyRequest, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    """Disable MFA (requires current OTP to confirm intent)."""
    return disable_mfa(db, current_user.id, data.otp_code)