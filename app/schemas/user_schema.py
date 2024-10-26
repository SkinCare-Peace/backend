# schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    email: EmailStr
    name: str
    profile_image: Optional[str]

