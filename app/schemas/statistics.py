from pydantic import BaseModel, Field
import datetime
from typing import Dict


class Score(BaseModel):
    acne: int = Field(..., description="여드름 점수")
    moisture: int = Field(..., description="수분 점수")
    pigmentation: int = Field(..., description="색소침착 점수")
    wrinkle: int = Field(..., description="주름 점수")
    pore: int = Field(..., description="모공 점수")
    elasticity: int = Field(..., description="탄력 점수")


class StatisticsRequest(BaseModel):
    user_id: str = Field(..., description="사용자 _id")
    date: datetime.date = Field(..., description="통계 날짜")
    scores: Score = Field(..., description="통계 점수")


class StatisticsRespond(BaseModel):
    user_id: str = Field(..., description="사용자 _id")
    statistics: Dict[datetime.date, Score] = Field(..., description="통계 날짜별 점수")
