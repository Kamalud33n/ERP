from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ── MFA helpers ────────────────────────────────────────
import pyotp, secrets

def generate_mfa_secret() -> str:
    """Return a new base32 TOTP secret for a user."""
    return pyotp.random_base32()

def get_totp_uri(secret: str, username: str, issuer: str = "MedNova ERP") -> str:
    """Return the otpauth:// URI for an authenticator app."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)

def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code (±30 s window)."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)

def create_mfa_token(user_id: int) -> str:
    """
    Short-lived JWT (5 min, scope='mfa') issued after password correct
    but before TOTP verified. get_current_user rejects scope≠access.
    """
    return create_access_token(
        data={"sub": str(user_id), "scope": "mfa"},
        expires_delta=timedelta(minutes=5)
    )

def decode_mfa_token(token: str) -> int | None:
    """Decode MFA intermediate token → user_id, or None if invalid."""
    payload = decode_token(token)
    if not payload or payload.get("scope") != "mfa":
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        return None