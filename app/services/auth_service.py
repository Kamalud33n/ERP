from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.employee import Employee
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password, verify_password, create_access_token,
    generate_mfa_secret, get_totp_uri, verify_totp,
    create_mfa_token, decode_mfa_token,
)

def register_user(db: Session, data: RegisterRequest) -> User:
    existing = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    user = User(email=data.email, username=data.username,
                password=hash_password(data.password), role="employee")
    db.add(user); db.commit(); db.refresh(user)
    employee = Employee(user_id=user.id, first_name=data.username, last_name="",
                        phone="", department="Unassigned", designation="Employee",
                        salary=0.0, join_date=None)
    db.add(employee); db.commit()
    return user

def login_user(db: Session, data: LoginRequest) -> dict:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # MFA enabled → return intermediate token, not the real one
    if user.mfa_enabled and user.mfa_secret:
        return {"mfa_required": True, "mfa_token": create_mfa_token(user.id), "username": user.username}

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role,
            "username": user.username, "mfa_required": False}


def mfa_login(db: Session, mfa_token: str, otp_code: str) -> dict:
    """Step 2 — validate intermediate token + TOTP, issue real access token."""
    user_id = decode_mfa_token(mfa_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired MFA token. Please log in again.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")
    if not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not configured")
    if not verify_totp(user.mfa_secret, otp_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid OTP code. Check your authenticator app.")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role,
            "username": user.username, "mfa_required": False}


def setup_mfa(db: Session, user_id: int) -> dict:
    """Generate secret, store it (not yet active), return provisioning URI."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    secret = generate_mfa_secret()
    user.mfa_secret  = secret
    user.mfa_enabled = False   # activated only after confirm_mfa
    db.commit()
    return {
        "otp_uri": get_totp_uri(secret, user.username),
        "secret":  secret,
        "message": "Scan the QR code with your authenticator app, then call POST /auth/mfa-confirm."
    }


def confirm_mfa(db: Session, user_id: int, otp_code: str) -> dict:
    """Verify first code after setup → activate MFA."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="Run POST /auth/mfa-setup first")
    if not verify_totp(user.mfa_secret, otp_code):
        raise HTTPException(status_code=400, detail="OTP code incorrect — please try again")
    user.mfa_enabled = True
    db.commit()
    return {"message": "MFA activated successfully. Future logins will require your authenticator code."}


def disable_mfa(db: Session, user_id: int, otp_code: str) -> dict:
    """Disable MFA after verifying current OTP."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled on this account")
    if not verify_totp(user.mfa_secret, otp_code):
        raise HTTPException(status_code=400, detail="OTP code incorrect")
    user.mfa_enabled = False
    user.mfa_secret  = None
    db.commit()
    return {"message": "MFA has been disabled."}