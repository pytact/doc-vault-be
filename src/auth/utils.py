"""Authentication utilities."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from src.auth.config import auth_settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    role: str,
    family_id: Optional[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token with required claims."""
    if expires_delta is None:
        expires_delta = timedelta(seconds=auth_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    
    expire = datetime.utcnow() + expires_delta
    
    # JWT payload with required claims
    payload = {
        "sub": user_id,  # User ID (REQUIRED)
        "role": role,  # User role (REQUIRED)
        "family_id": family_id,  # Family ID, null for SuperAdmin (REQUIRED)
        "exp": int(expire.timestamp()),  # Expiration timestamp (REQUIRED)
        "iat": int(datetime.utcnow().timestamp()),  # Issued at timestamp (RECOMMENDED)
        "jti": str(uuid4()),  # JWT ID (RECOMMENDED)
    }
    
    return jwt.encode(payload, auth_settings.SECRET_KEY, algorithm=auth_settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[auth_settings.ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
