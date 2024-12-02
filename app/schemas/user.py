from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


# MongoDB ObjectId를 Pydantic에서 처리하기 위한 커스텀 필드
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    email: EmailStr
    name: str
    profile_picture_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    skin_type: Optional[str] = None
    skin_concerns: Optional[List[str]] = None


class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    skin_type: Optional[str] = None
    skin_concerns: Optional[List[str]] = None
    avoid_ingredients: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True


class UserRoutine(BaseModel):
    user: User
    routine: List[str]

    class Config:
        allow_population_by_field_name = True
