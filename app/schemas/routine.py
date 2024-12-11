# schemas/routine.py
import datetime
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Dict
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


class RoutineRecordRequest(BaseModel):
    user_id: str = Field(..., description="사용자 _id")
    date: datetime.date = Field(..., description="루틴 실천 날짜")
    usage_time: str = Field(..., description="사용 시간대")
    routine_practice: Dict[str, bool] = Field(..., description="루틴 실천 여부")


class DailyRoutineRecord(BaseModel):
    date: datetime.date
    morning: Dict[str, bool] = {}
    evening: Dict[str, bool] = {}


class RoutineRecord(BaseModel):
    user_id: str
    records: List[DailyRoutineRecord]


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


# 각 Step 별 공통 sequence
STEP_SEQUENCE = {
    Step.CLEANSING: 1,
    Step.CLEANSING_CARE: 1,
    Step.TONER: 2,
    Step.MASK_PACK: 2,
    Step.CONCENTRATION_CARE: 3,
    Step.MOISTURIZING: 4,
    Step.SUN_CARE: 5,
    Step.SLEEPING_PACK: 6,
}


class SubProductType(BaseModel):
    name: str = Field(..., description="하위 화장품 종류의 이름")
    usage_time: List[str] = Field(..., description="사용 시간대")
    frequency: int = Field(..., description="사용 빈도")
    instructions: str = Field(..., description="사용 방법")
    sequence: int = Field(..., description="전체 제품 사용 시 고려되는 사용 순서")
    time: int = Field(..., description="소요 시간(분)")


class ProductCategory(BaseModel):
    step: Step
    sub_types: List[SubProductType]


class RoutineCreate(BaseModel):
    morning_routine: List[SubProductType]
    evening_routine: List[SubProductType]


class Routine(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    morning_routine: List[SubProductType]
    evening_routine: List[SubProductType]

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: lambda oid: str(oid)}
        arbitrary_types_allowed = True


# ROUTINE_BY_USER_TYPE = {
#     UserType.LTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
#     UserType.MTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
#     UserType.HTLC: [Step.CLEANSING, Step.MOISTURIZING, Step.SUN_CARE],
#     UserType.LTMC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#     ],
#     UserType.MTMC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#         Step.MASK_PACK,
#     ],
#     UserType.HTMC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#         Step.MASK_PACK,
#         Step.SLEEPING_PACK,
#     ],
#     UserType.LTHC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#     ],
#     UserType.MTHC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#         Step.MASK_PACK,
#     ],
#     UserType.HTHC: [
#         Step.CLEANSING,
#         Step.TONER,
#         Step.CONCENTRATION_CARE,
#         Step.MOISTURIZING,
#         Step.SUN_CARE,
#         Step.MASK_PACK,
#         Step.SLEEPING_PACK,
#     ],
# }
