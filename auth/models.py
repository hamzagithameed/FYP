"""
Pydantic models for authentication
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Model for user registration"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)  # Bcrypt limit


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Model for user response (without password)"""
    id: str
    name: str
    email: str
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserInDB(BaseModel):
    """Model for user in database"""
    id: str
    name: str
    email: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
