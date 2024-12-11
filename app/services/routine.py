# services/routine.py
from datetime import date, datetime
from math import inf
import math
import random
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from data.products_data import PRODUCTS_DATA
from schemas.routine import (
    DailyRoutineRecord,
    RoutineCreate,
    Step,
    SubProductType,
    RoutineRecord,
    Routine,
)
from db.database import get_db
from pymongo.errors import PyMongoError

db = get_db()
routine_collection = db["routines"]
routine_record_collection = db["routine_records"]


async def save_routine_record(
    user_id: str, record_date: date, usage_time: str, routine_practice: Dict[str, bool]
) -> bool:
    # records 배열 안에 {date, morning, evening} 구조를 관리
    # 만약 records 중 해당 date에 대한 문서가 없다면 추가하고,
    # 있다면 해당 usage_time에 대한 필드를 업데이트한다.
    date_as_datetime = datetime.combine(record_date, datetime.min.time())

    update_query = {
        "$set": {"user_id": user_id, "records.$[elem]." + usage_time: routine_practice}
    }

    array_filters = [{"elem.date": date_as_datetime}]
    result = await routine_record_collection.update_one(
        {"user_id": user_id, "records.date": date_as_datetime},
        update_query,
        array_filters=array_filters,
    )

    if result.modified_count == 0:
        # 해당 date에 대한 기록이 없으면 새로 추가
        new_record = {
            "date": date_as_datetime,
            "morning": routine_practice if usage_time == "morning" else {},
            "evening": routine_practice if usage_time == "evening" else {},
        }
        await routine_record_collection.update_one(
            {"user_id": user_id}, {"$push": {"records": new_record}}, upsert=True
        )

    return True


async def get_routine_records(user_id: str) -> Optional[RoutineRecord]:
    try:
        if not ObjectId.is_valid(user_id):
            return None

        # 사용자 ID로 해당 사용자의 루틴 기록 찾기
        record = await routine_record_collection.find_one({"user_id": user_id})

        if record:
            # MongoDB에서 가져온 데이터를 `RoutineRecord` 스키마에 맞게 변환
            records = [
                {
                    "date": rec["date"].date(),
                    "morning": rec.get("morning", {}),
                    "evening": rec.get("evening", {}),
                }
                for rec in record.get("records", [])
            ]
            daily_records = [DailyRoutineRecord(**rec) for rec in records]
            return RoutineRecord(user_id=user_id, records=daily_records)
        return None

    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


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


# async def get_routine(
#     time_minutes: int, money_won: int, owned_cosmetics: List[str]
# ) -> RoutineCreate:
#     from data.products_data import PRODUCTS_DATA

#     selected_products: List[SubProductType] = []
#     used_product_keys = set()

#     # PRIORITY_STEPS 순회하면서 제품 선택
#     for step, forced_key in PRIORITY_STEPS:
#         step_products = PRODUCTS_DATA.get(step, {})
#         if not step_products:
#             continue

#         if forced_key:
#             candidate_keys = [forced_key] if forced_key in step_products else []
#         else:
#             candidate_keys = [
#                 k for k in step_products.keys() if k not in used_product_keys
#             ]

#         chosen_key = None
#         chosen_product_data = None

#         for ck in candidate_keys:
#             product_data = step_products[ck]
#             ctype = product_data["name"]
#             segment_price = PRICE_SEGMENTS.get(ctype, {"mid": 10000})["mid"]

#             # 가진 제품이면 돈 차감 없음
#             needed_money = 0 if ck in owned_cosmetics else segment_price
#             needed_time = product_data["time"]

#             if needed_time <= time_minutes and needed_money <= money_won:
#                 chosen_key = ck
#                 chosen_product_data = product_data
#                 break

#         if chosen_key and chosen_product_data:
#             used_product_keys.add(chosen_key)

#             # 시간 및 돈 차감
#             deducted_time = chosen_product_data["time"]
#             # mid 구간 가격
#             product_name = chosen_product_data["name"]
#             segment_price = PRICE_SEGMENTS.get(product_name, {"mid": 10000})["mid"]
#             deducted_money = 0 if chosen_key in owned_cosmetics else int(segment_price)

#             time_minutes -= deducted_time
#             money_won -= deducted_money
#             sub_product = SubProductType(
#                 name=chosen_product_data["name"],
#                 usage_time=chosen_product_data["usage_time"],
#                 frequency=chosen_product_data["frequency"],
#                 instructions=chosen_product_data["instructions"],
#                 sequence=chosen_product_data["sequence"],
#                 time=chosen_product_data["time"],
#                 cost=deducted_money,
#             )
#             selected_products.append(sub_product)

#     final_routine = split_routine_by_time(selected_products)
#     return final_routine
