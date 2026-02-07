from typing import Optional
from pydantic import BaseModel


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
