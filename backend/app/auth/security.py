"""
Real authentication primitives: bcrypt password hashing + JWT access tokens.
No mock auth here -- this is what a production deployment would run,
just pointed at whatever SECRET_KEY / issuer you configure via env vars.
"""
import os
import datetime as dt
import uuid

from passlib.context import CryptContext
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SENTINEL_JWT_SECRET", "dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SENTINEL_JWT_EXPIRE_MIN", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def new_user_id() -> str:
    return f"usr_{uuid.uuid4().hex[:12]}"


def create_access_token(user_id: str, role: str, email: str) -> str:
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": dt.datetime.utcnow(),
        "iss": "sentinel-platform",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
