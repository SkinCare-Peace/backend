# services/routine.py
from typing import Optional

from bson import ObjectId
from schemas.routine import (
    PRODUCT_TYPES,
    RoutineCreate,
    UserType,
    ROUTINE_BY_USER_TYPE,
    Routine,
)
from db.database import get_db
from pymongo.errors import PyMongoError

db = get_db()
routine_collection = db["routines"]


async def create_routine(routine: RoutineCreate) -> Routine:
    try:
        routine_dict = routine.model_dump(by_alias=True)
        result = await routine_collection.insert_one(routine_dict)
        created_routine = await routine_collection.find_one({"_id": result.inserted_id})
        if created_routine:
            created_routine["_id"] = str(created_routine["_id"])
            return Routine(**created_routine)
        else:
            raise Exception("Routine creation failed")
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def get_routine_by_id(routine_id: str) -> Optional[Routine]:
    try:
        if not ObjectId.is_valid(routine_id):
            return None
        routine = await routine_collection.find_one({"_id": ObjectId(routine_id)})
        if routine:
            routine["_id"] = str(routine["_id"])
            return Routine(**routine)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def update_routine(routine_id: str, routine: Routine) -> Optional[Routine]:
    try:
        if not ObjectId.is_valid(routine_id):
            return None
        routine_dict = routine.model_dump(exclude_unset=True, by_alias=True)
        result = await routine_collection.update_one(
            {"_id": ObjectId(routine_id)}, {"$set": routine_dict}
        )
        if result.modified_count == 1:
            updated_routine = await routine_collection.find_one(
                {"_id": ObjectId(routine_id)}
            )
            if updated_routine:
                updated_routine["_id"] = str(updated_routine["_id"])
                return Routine(**updated_routine)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def delete_routine(routine_id: str) -> bool:
    try:
        if not ObjectId.is_valid(routine_id):
            return False
        result = await routine_collection.delete_one({"_id": ObjectId(routine_id)})
        return result.deleted_count == 1
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


def get_time_level(time_minutes):
    if time_minutes < 5:
        return "low"
    elif time_minutes <= 20:
        return "medium"
    else:
        return "high"


def get_money_level(money_won):
    if money_won < 50000:
        return "low"
    elif money_won <= 100000:
        return "medium"
    else:
        return "high"


def get_user_type(time_level, money_level) -> UserType:
    if time_level == "low" and money_level == "low":
        return UserType.LTLC
    elif time_level == "low" and money_level == "medium":
        return UserType.LTMC
    elif time_level == "low" and money_level == "high":
        return UserType.LTHC
    elif time_level == "medium" and money_level == "low":
        return UserType.MTLC
    elif time_level == "medium" and money_level == "medium":
        return UserType.MTMC
    elif time_level == "medium" and money_level == "high":
        return UserType.MTHC
    elif time_level == "high" and money_level == "low":
        return UserType.HTLC
    elif time_level == "high" and money_level == "medium":
        return UserType.HTMC
    elif time_level == "high" and money_level == "high":
        return UserType.HTHC
    else:
        raise ValueError("Invalid time_level or money_level")


async def get_routine(time_minutes, money_won) -> Routine:
    time_level = get_time_level(time_minutes)
    money_level = get_money_level(money_won)
    user_type = get_user_type(time_level, money_level)
    routine_list = ROUTINE_BY_USER_TYPE[user_type]

    routine = RoutineCreate(routine=[PRODUCT_TYPES[step] for step in routine_list])
    return await create_routine(routine)
