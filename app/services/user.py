# services/user.py
from core.security import decode_access_token
from schemas.user import User

from pymongo.errors import DuplicateKeyError
from db.database import get_db

# MongoDB 설정
db = get_db()
users_collection = db["users"]


# MongoDB에 사용자를 추가
async def add_user(user_data: User):
    try:
        user = await users_collection.insert_one(user_data.model_dump())
        return user.inserted_id
    except DuplicateKeyError:
        return None


# 이메일로 사용자 검색
async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    return user


# 사용자 정보 업데이트
async def update_user(email: str, data: dict):
    updated_user = await users_collection.update_one({"email": email}, {"$set": data})
    return updated_user


async def get_current_user(token: str):
    payload = decode_access_token(token)
    if payload is None:
        raise Exception("Could not validate credentials")
    email = payload.get("sub")

    if email is None:
        raise Exception("Could not validate credentials")

    user = await get_user_by_email(email)
    if user is None:
        raise Exception("User not found")

    return user
