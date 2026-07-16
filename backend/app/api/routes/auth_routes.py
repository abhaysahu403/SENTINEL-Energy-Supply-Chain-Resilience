from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import datetime as dt

from app.db.database import get_db
from app.db.user_model import User
from app.auth.security import hash_password, verify_password, create_access_token, new_user_id
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: str | None = None
    role: str = "executive_viewer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    allowed_roles = {"procurement_manager", "policy_desk", "executive_viewer", "admin"}
    role = payload.role if payload.role in allowed_roles else "executive_viewer"
    user = User(
        id=new_user_id(),
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role,
        organization=payload.organization,
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.id, user.role, user.email)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    user.last_login = dt.datetime.utcnow()
    db.commit()
    token = create_access_token(user.id, user.role, user.email)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "organization": current_user.organization,
    }
