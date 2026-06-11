from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.employee import Employee
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token

def register_user(db: Session, data: RegisterRequest) -> User:
    existing = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    valid_roles = ["admin", "hr_manager", "finance", "employee"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from {valid_roles}")

    # Create user
    user = User(
        email    = data.email,
        username = data.username,
        password = hash_password(data.password),
        role     = data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto create employee profile for all roles
    employee = Employee(
        user_id     = user.id,
        first_name  = data.username,
        last_name   = "",
        phone       = "",
        department  = "Unassigned",
        designation = data.role.replace("_", " ").title(),
        salary      = 0.0,
        join_date   = None
    )
    db.add(employee)
    db.commit()

    return user

def login_user(db: Session, data: LoginRequest) -> dict:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user.role,
        "username":     user.username
    }