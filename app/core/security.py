# app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Request
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- NEW FUNCTION ADDED HERE ---
def get_current_user_from_cookie(request: Request):
    """
    Reads the 'access_token' cookie, decodes it, and returns the user data (payload).
    Returns None if no token is found or if it's invalid.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        # The token is stored as "Bearer eyJhbGci..."
        # We need to split the "Bearer " part from the actual token
        scheme, _, param = token.partition(" ")
        
        # If the split didn't work (no space), assume the whole thing is the token
        if not param:
            param = scheme
            
        payload = jwt.decode(param, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload # Returns dict like {'sub': 'user@email.com', 'role': 'buyer'}
    except JWTError:
        return None