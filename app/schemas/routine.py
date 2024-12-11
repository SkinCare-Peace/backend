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
    cost: int = Field(..., description="루틴 생성 시 할당된 비용")


class ProductCategory(BaseModel):
    step: Step
    sub_types: List[SubProductType]


class RoutineCreateRequest(BaseModel):
    time_minutes: int = Field(..., description="소요 시간(분)")
    money_won: int = Field(..., description="비용(원)")
    owned_cosmetics: List[str] = Field(..., description="보유 화장품 종류 리스트")


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
