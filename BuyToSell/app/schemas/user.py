from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from app.models.user import UserRole
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[UserRole] = UserRole.CUSTOMER

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=255)
    role: Optional[UserRole] = None

class UserOut(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    
    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
