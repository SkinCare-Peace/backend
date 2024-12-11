# services/user.py
from typing import Optional, List
from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument
from schemas.routine import Routine
from schemas.user import UserCreate, UserUpdate, User
from datetime import datetime
from pymongo.errors import PyMongoError
from db.database import get_db

db = get_db()
user_collection = db["users"]


async def create_user(user_create: UserCreate) -> User:
    try:
        user_dict = user_create.model_dump(by_alias=True)
        user_dict["created_at"] = datetime.now()
        user_dict["updated_at"] = datetime.now()

        # 해시된 비밀번호를 hashed_password 필드에 저장하고 password 필드는 제거
        user_dict["hashed_password"] = user_dict.pop("password")
        result = await user_collection.insert_one(user_dict)
        created_user = await user_collection.find_one({"_id": result.inserted_id})
        if created_user:
            created_user["_id"] = str(created_user["_id"])
            return User(**created_user)
        else:
            raise Exception("User creation failed")

    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def get_user_by_id(user_id: str) -> Optional[User]:
    try:
        if not ObjectId.is_valid(user_id):
            return None
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            if "routine" in user and user["routine"] is not None:
                user["routine"] = Routine(**user["routine"])
            return User(**user)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def get_user_by_email(email: str) -> Optional[User]:
    try:
        user = await user_collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
            if "routine" in user and user["routine"] is not None:
                user["routine"] = Routine(**user["routine"])
            return User(**user)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def update_user(user_id: str, user_update: UserUpdate) -> Optional[User]:
    try:
        if not ObjectId.is_valid(user_id):
            return None
        update_data = user_update.model_dump(exclude_unset=True, by_alias=True)
        if "password" in update_data:
            update_data["hashed_password"] = update_data.pop("password")
        update_data["updated_at"] = datetime.now()

        result = await user_collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )
        if result.modified_count == 1:
            updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
            if updated_user:
                updated_user["_id"] = str(updated_user["_id"])
                return User(**updated_user)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def delete_user(user_id: str) -> bool:
    try:
        if not ObjectId.is_valid(user_id):
            return False
        result = await user_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def add_owned_cosmetic(user_id: str, cosmetic_id: str) -> Optional[User]:
    try:
        if not ObjectId.is_valid(user_id):
            return None

        # 1. 화장품 정보 조회
        cosmetic = await db["oliveyoung_products_integrated"].find_one(
            {"_id": ObjectId(cosmetic_id)}
        )
        if not cosmetic:
            raise HTTPException(status_code=404, detail="Cosmetic not found")

        cosmetic_types = cosmetic.get("cosmetic_type", [])
        if not cosmetic_types:
            raise HTTPException(status_code=400, detail="Cosmetic type is missing")

        # 2. 사용자 문서 업데이트를 위한 $addToSet 준비
        add_to_set_fields = {
            f"owned_cosmetics.{ct}": cosmetic_id for ct in cosmetic_types
        }

        # 3. 사용자 문서 업데이트
        result = await db["users"].update_one(
            {"_id": ObjectId(user_id)}, {"$addToSet": add_to_set_fields}
        )

        if result.modified_count == 1:
            updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
            if updated_user:
                updated_user["_id"] = str(updated_user["_id"])
                # `owned_cosmetics`의 ObjectId를 문자열로 변환
                if (
                    "owned_cosmetics" in updated_user
                    and updated_user["owned_cosmetics"]
                ):
                    for ct, ids in updated_user["owned_cosmetics"].items():
                        updated_user["owned_cosmetics"][ct] = [str(oid) for oid in ids]
                return User(**updated_user)
        return None
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


async def remove_owned_cosmetic(user_id: str, cosmetic_id: str) -> Optional[User]:
    """
    사용자가 보유한 화장품 목록에서 특정 화장품을 제거합니다.
    """
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None

    owned_cosmetics = user.get("owned_cosmetics", {})
    for category, cosmetics_list in owned_cosmetics.items():
        if cosmetic_id in cosmetics_list:
            owned_cosmetics[category] = [
                cosmetic for cosmetic in cosmetics_list if cosmetic != cosmetic_id
            ]

    updated_user = await user_collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"owned_cosmetics": owned_cosmetics}},
        return_document=ReturnDocument.AFTER,
    )

    if updated_user:
        updated_user["_id"] = str(updated_user["_id"])
        return User(**updated_user)

    return None
