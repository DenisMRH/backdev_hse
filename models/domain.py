from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Account(BaseModel):
    id: int
    login: str
    password: str
    is_blocked: bool


class AccountCreate(BaseModel):
    login: str
    password: str


class User(BaseModel):
    id: int
    is_verified: bool


class UserCreate(BaseModel):
    is_verified: bool = False


class Advertisement(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    category: int
    images_qty: int


class AdvertisementCreate(BaseModel):
    user_id: int
    name: str
    description: str
    category: int
    images_qty: int


class AdvertisementWithUser(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    category: int
    images_qty: int
    is_verified_seller: bool


class ModerationResult(BaseModel):
    id: int
    item_id: int
    status: str
    is_violation: Optional[bool] = None
    probability: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
