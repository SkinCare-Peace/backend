# schemas/routine.py
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class Step(str, Enum):
    CLEANSING = "클렌징"
    CLEANSING_CARE = "클렌징 단계 추가 케어"
    TONER = "결정리"
    CONCENTRATION_CARE = "집중 케어"
    MOISTURIZING = "보습"
    SUN_CARE = "선케어"
    SLEEPING_PACK = "수면 중 보습 케어"
    MASK_PACK = "시간 투자형 집중케어"


class ProductType(BaseModel):
    name: str = Field(..., description="화장품 종류의 이름")
    sequence: int = Field(..., description="사용 순서")
    usage_time: List[str] = Field(..., description="사용 시간대")
    frequency: int = Field(..., description="사용 빈도")


class RoutineCreate(BaseModel):
    routine: List[ProductType]


class Routine(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    routine: List[ProductType]

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: lambda oid: str(oid)}
        arbitary_types_allowed = True


class UserType(str, Enum):
    LTLC = "LTLC"  # Low Time, Low Cost
    LTHC = "LTHC"  # Low Time, High Cost
    LTMC = "LTMC"  # Low Time, Medium Cost
    MTLC = "MTLC"  # Medium Time, Low Cost
    MTHC = "MTHC"  # Medium Time, High Cost
    MTMC = "MTMC"  # Medium Time, Medium Cost
    HTLC = "HTLC"  # High Time, Low Cost
    HTHC = "HTHC"  # High Time, High Cost
    HTMC = "HTMC"  # High Time, Medium Cost


ROUTINE_BY_USER_TYPE = {
    UserType.LTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
    UserType.MTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
    UserType.HTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
    UserType.LTMC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
    ],
    UserType.MTMC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
        Step.MASK_PACK,
    ],
    UserType.HTMC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
        Step.MASK_PACK,
        Step.SLEEPING_PACK,
    ],
    UserType.LTHC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
    ],
    UserType.MTHC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
        Step.MASK_PACK,
    ],
    UserType.HTHC: [
        Step.CLEANSING,
        Step.TONER,
        Step.CONCENTRATION_CARE,
        Step.MOISTURIZING,
        Step.SUN_CARE,
        Step.MASK_PACK,
        Step.SLEEPING_PACK,
    ],
}


PRODUCT_TYPES = {
    Step.CLEANSING: ProductType(
        name="클렌징폼/클렌징오일",
        sequence=1,
        usage_time=["morning", "evening"],
        frequency=1,
    ),
    Step.CLEANSING_CARE: ProductType(
        name="스크럽/필링젤",
        sequence=1,
        usage_time=["morning", "evening"],
        frequency=1,
    ),
    Step.TONER: ProductType(
        name="스킨/토너",
        sequence=2,
        usage_time=["morning", "evening"],
        frequency=1,
    ),
    Step.MASK_PACK: ProductType(
        name="마스크팩/아이팩",
        sequence=2,
        usage_time=["evening"],
        frequency=3,
    ),
    Step.CONCENTRATION_CARE: ProductType(
        name="세럼/앰플/에센스",
        sequence=3,
        usage_time=["morning", "evening"],
        frequency=1,
    ),
    Step.MOISTURIZING: ProductType(
        name="크림/로션",
        sequence=4,
        usage_time=["morning", "evening"],
        frequency=1,
    ),
    Step.SUN_CARE: ProductType(
        name="선크림/선스틱",
        sequence=5,
        usage_time=["morning"],
        frequency=1,
    ),
    Step.SLEEPING_PACK: ProductType(
        name="슬리핑팩",
        sequence=6,
        usage_time=["evening"],
        frequency=1,
    ),
}
