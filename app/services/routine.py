# services/routine.py
from datetime import date, datetime
from typing import List, Optional, Tuple

from bson import ObjectId
from data.products_data import PRODUCTS_DATA
from schemas.routine import (
    RoutineCreate,
    Step,
    SubProductType,
    RoutineRecord,
    UserType,
    Routine,
)
from db.database import get_db
from pymongo.errors import PyMongoError

db = get_db()
routine_collection = db["routines"]
routine_record_collection = db["routine_records"]


async def save_routine_record(user_id: str, date: date) -> bool:
    try:
        date_as_datetime = datetime.combine(date, datetime.min.time())
        if not ObjectId.is_valid(user_id):
            return False
        await routine_record_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"dates": date_as_datetime}},
            upsert=True,
        )
        return True
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def get_routine_records(user_id: str) -> Optional[RoutineRecord]:
    try:
        if not ObjectId.is_valid(user_id):
            return None
        record = await routine_record_collection.find_one({"user_id": user_id})
        if record:
            record["dates"] = [d.date() for d in record["dates"]]
            return RoutineRecord(**record)
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


def get_steps_by_user_type(user_type: UserType) -> List[Tuple[Step, Optional[str]]]:
    # Tuple[Step, Optional[str]] 형태로 반환
    # (Step, product_key)
    # product_key가 None이면 어떤 제품이든 선택 가능
    # product_key가 특정 값이면 해당 제품을 강제로 선택

    if user_type in [UserType.LTLC, UserType.MTLC, UserType.HTLC]:
        return [
            (Step.CLEANSING, "cleansing_foam"),  # CLEANSING에 대해 특정 제품 추천
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
        ]
    elif user_type == UserType.LTMC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
        ]
    elif user_type == UserType.MTMC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
            (Step.MASK_PACK, None),
        ]
    elif user_type == UserType.HTMC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
            (Step.MASK_PACK, None),
            (Step.SLEEPING_PACK, None),
        ]
    elif user_type == UserType.LTHC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
        ]
    elif user_type == UserType.MTHC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
            (Step.MASK_PACK, None),
        ]
    elif user_type == UserType.HTHC:
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.TONER, None),
            (Step.CONCENTRATION_CARE, None),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
            (Step.MASK_PACK, None),
            (Step.SLEEPING_PACK, None),
        ]
    else:
        # 기본값 혹은 예외 처리
        return [
            (Step.CLEANSING, "cleansing_foam"),
            (Step.MOISTURIZING, None),
            (Step.SUN_CARE, None),
        ]


def get_routine(time_minutes, money_won) -> RoutineCreate:
    user_type = get_user_type(get_time_level(time_minutes), get_money_level(money_won))
    step_product_pairs = get_steps_by_user_type(user_type)

    # CLEANSING 단계 인덱스
    cleansing_indices = [
        i for i, (st, pk) in enumerate(step_product_pairs) if st == Step.CLEANSING
    ]

    # CLEANSING이 3회 이상이면 예외
    if len(cleansing_indices) > 2:
        raise ValueError("CLEANSING step can only appear once or twice.")

    # CLEANSING이 두 번이라면 하나는 foam, 하나는 None이라고 가정
    # foam이 뒤에 오도록 순서 보장
    if len(cleansing_indices) == 2:
        # 두 CLEANSING 단계 정보
        first_idx, second_idx = cleansing_indices
        first_step, first_key = step_product_pairs[first_idx]
        second_step, second_key = step_product_pairs[second_idx]

        # foam이 뒤에 있어야 함
        # 만약 foam이 앞에 있면 순서 변경
        if first_key == "cleansing_foam":
            # 순서 뒤집기:두 번째를 foam으로
            step_list = list(step_product_pairs)
            step_list[first_idx], step_list[second_idx] = (second_step, second_key), (
                first_step,
                first_key,
            )
            step_product_pairs = step_list

    selected_products: List[SubProductType] = []
    chosen_keys_by_step = {}  # 이미 선택한 제품 키

    for step, product_key in step_product_pairs:
        step_products = PRODUCTS_DATA[step]
        used_keys = chosen_keys_by_step.get(step, set())

        if product_key is not None:
            if product_key not in step_products:
                # 지정된 key가 없으면 다른 제품 선택
                available_keys = [k for k in step_products.keys() if k not in used_keys]
                if not available_keys:
                    raise ValueError(f"No available products for step {step}")
                chosen_key = available_keys[0]
                chosen_product_data = step_products[chosen_key]
            else:
                chosen_key = product_key
                chosen_product_data = step_products[chosen_key]
        else:
            # product_key가 None이면 이전에 사용 안한 제품 중 하나 선택
            available_keys = [k for k in step_products.keys() if k not in used_keys]
            if not available_keys:
                raise ValueError(f"No available products for step {step} (all used)")
            chosen_key = available_keys[0]
            chosen_product_data = step_products[chosen_key]

        sub_product = SubProductType(
            name=chosen_product_data["name"],
            usage_time=chosen_product_data["usage_time"],
            frequency=chosen_product_data["frequency"],
            instructions=chosen_product_data["instructions"],
            sequence=chosen_product_data["sequence"],
        )
        selected_products.append(sub_product)

        if step not in chosen_keys_by_step:
            chosen_keys_by_step[step] = set()
        chosen_keys_by_step[step].add(chosen_key)

    final_routine = split_routine_by_time(selected_products)
    return final_routine


def split_routine_by_time(products: List[SubProductType]) -> RoutineCreate:
    morning_products = []
    evening_products = []

    # 아침, 저녁 나누기
    for p in products:
        if "morning" in p.usage_time:
            morning_products.append(p)
        if "evening" in p.usage_time:
            evening_products.append(p)

    # sequence로 정렬
    morning_products.sort(key=lambda x: x.sequence)
    evening_products.sort(key=lambda x: x.sequence)

    # 리스트 그대로 반환 (순서가 sort로 보장됨)
    return RoutineCreate(
        morning_routine=morning_products, evening_routine=evening_products
    )
