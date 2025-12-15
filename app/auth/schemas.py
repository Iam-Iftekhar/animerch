# app/auth/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "buyer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str