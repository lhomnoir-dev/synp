from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    bio: str = Field(default="", max_length=500)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    bio: str | None = Field(default=None, max_length=500)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    bio: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class ApiKeyIn(BaseModel):
    provider: str = Field(min_length=1, max_length=30)
    api_key: str = Field(min_length=5)


class ApiKeyOut(BaseModel):
    provider: str
    configured: bool
