from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_admin
from app.models.user import User
from app.core.security import hash_password
from pydantic import BaseModel, EmailStr
from typing import Optional
import io, csv, secrets
from fastapi.responses import StreamingResponse
from datetime import datetime

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "employee"

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# Get all users
@router.get("/users", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db), current_user=Depends(get_admin)):
    return db.query(User).all()

# Create user
@router.post("/users", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    existing = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    valid_roles = ["admin", "hr_manager", "finance", "employee"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from {valid_roles}")
    user = User(
        email    = data.email,
        username = data.username,
        password = hash_password(data.password),
        role     = data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Update user role or status
@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user

# Delete user
@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}