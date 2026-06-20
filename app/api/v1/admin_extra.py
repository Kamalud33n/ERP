from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_admin
from app.models.user import User
from app.core.security import hash_password
from pydantic import BaseModel, EmailStr
import io, csv, secrets
from fastapi.responses import StreamingResponse
from datetime import datetime

router = APIRouter()

VALID_ROLES = ["admin", "hr_manager", "finance", "employee"]

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# --- Audit helpers ---

def ensure_audit_table(db: Session):
    db.execute(text('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    '''))
    db.commit()


def log_audit(db: Session, user_id: Optional[int], action: str, details: str = ""):
    ensure_audit_table(db)
    db.execute(text("INSERT INTO audit_logs (user_id, action, details, created_at) VALUES (:uid, :act, :det, :now)"),
               {"uid": user_id, "act": action, "det": details, "now": datetime.utcnow()})
    db.commit()

# Get single user
@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Search / paginate users
@router.get("/users/search")
def search_users(q: Optional[str] = None, page: int = 1, per_page: int = 20, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    query = db.query(User)
    if q:
        qlike = f"%{q}%"
        query = query.filter((User.username.ilike(qlike)) | (User.email.ilike(qlike)))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "items": items}

# Reset password (admin-driven)
class ResetPasswordIn(BaseModel):
    new_password: Optional[str] = None

@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, payload: ResetPasswordIn, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_pw = payload.new_password or secrets.token_urlsafe(8)
    user.password = hash_password(new_pw)
    db.commit()
    log_audit(db, current_user.id if current_user else None, "reset_password", f"reset password for user {user.id}")
    return {"message": "Password reset", "temporary_password": new_pw}

# Invite user (creates inactive user with temporary password)
class InviteIn(BaseModel):
    email: EmailStr
    role: str = "employee"
    username: Optional[str] = None

@router.post("/users/invite")
def invite_user(payload: InviteIn, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from {VALID_ROLES}")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    tmp_pw = secrets.token_urlsafe(8)
    username = payload.username or payload.email.split("@")[0]
    i = 1
    base = username
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{i}"
        i += 1
    user = User(email=payload.email, username=username, password=hash_password(tmp_pw), role=payload.role, is_active=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, current_user.id if current_user else None, "invite_user", f"invited {user.email}")
    return {"message": "User invited", "temporary_password": tmp_pw, "username": username}

@router.get("/roles")
def list_roles():
    return {"roles": VALID_ROLES}

@router.get("/audit/logs")
def get_audit_logs(page: int = 1, per_page: int = 50, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    ensure_audit_table(db)
    offset = (page - 1) * per_page
    rows = db.execute(text("SELECT id, user_id, action, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT :lim OFFSET :off"), {"lim": per_page, "off": offset}).fetchall()
    total = db.execute(text("SELECT COUNT(1) FROM audit_logs")).scalar()
    items = [dict(r) for r in rows]
    return {"total": total, "page": page, "per_page": per_page, "items": items}

@router.get("/users/export")
def export_users(db: Session = Depends(get_db), current_user=Depends(get_admin)):
    users = db.query(User).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "email", "role", "is_active"])
    for u in users:
        writer.writerow([u.id, u.username, u.email, u.role, bool(u.is_active)])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})

@router.post("/users/import")
async def import_users(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_admin)):
    content = (await file.read()).decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    created = []
    skipped = []
    for row in reader:
        email = (row.get('email') or '').strip()
        username = (row.get('username') or '').strip()
        role = (row.get('role') or 'employee').strip()
        password = (row.get('password') or '').strip()
        if not email or not username:
            skipped.append({'row': row, 'reason': 'missing email/username'})
            continue
        if role not in VALID_ROLES:
            skipped.append({'row': row, 'reason': 'invalid role'})
            continue
        if db.query(User).filter((User.email == email) | (User.username == username)).first():
            skipped.append({'row': row, 'reason': 'already exists'})
            continue
        pw = password or secrets.token_urlsafe(8)
        user = User(email=email, username=username, password=hash_password(pw), role=role, is_active=False)
        db.add(user)
        db.commit()
        db.refresh(user)
        created.append({'id': user.id, 'email': user.email, 'username': user.username})
        log_audit(db, current_user.id if current_user else None, 'import_user', f'Imported {user.email}')
    return {"created": created, "skipped": skipped}
