# schemas/user.py
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from passlib.context import CryptContext

from schemas.routine import Routine

# 비밀번호 암호화를 위한 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserBase(BaseModel):
    email: EmailStr
    age: int
    name: str


class UserCreate(UserBase):
    password: str

    @field_validator("password", mode="before")
    def hash_password(cls, value: str) -> str:
        return pwd_context.hash(value)  # 해시화된 비밀번호 반환


class UserUpdate(BaseModel):
    name: Optional[str] = None
    skin_type: Optional[str] = None
    skin_concerns: Optional[List[str]] = None
    has_sensitive_skin: Optional[bool] = None
    avoid_ingredients: Optional[List[str]] = None
    owend_cosmetics: Optional[List[str]] = None
    routine_id: Optional[str] = None
    bsti: Optional[str] = None
    password: Optional[str] = None  # 업데이트 시 비밀번호 변경 가능

    @field_validator("password", mode="before")
    def hash_password(cls, value: Optional[str]) -> Optional[str]:
        if value:
            if len(value) < 8:
                raise ValueError("Password must be at least 8 characters long")
            return pwd_context.hash(value)
        return value


class User(UserBase):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    skin_type: Optional[str] = None
    skin_concerns: Optional[List[str]] = None
    has_sensitive_skin: Optional[bool] = None
    avoid_ingredients: Optional[List[str]] = None
    owned_cosmetics: Optional[List[str]] = None
    routine_id: Optional[str] = None
    bsti: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    hashed_password: str  # 저장된 해시 비밀번호 필드 추가

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: lambda oid: str(oid)}
