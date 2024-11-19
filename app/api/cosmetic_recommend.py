# api/recommend.py

from typing import List
from fastapi import APIRouter, HTTPException

from schemas.cosmetic_recommendation import ProductRecommendation
from services.cosmetic_recommend import recommend_cosmetics
import traceback

router = APIRouter()

function_schema = {
    "name": "generate_recommendation_reason",
    "description": "사용자의 피부 타입과 고민, 제품 정보를 기반으로 추천 이유를 생성합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "제품을 추천하는 이유",
            },
        },
        "required": ["reason"],
    },
}


@router.post("/recommend", response_model=List[ProductRecommendation])
def get_recommendations(
    user_skin_type: str,
    user_concerns: List[str],
    cosmetic_types: str,
    allergic_ingredients: List[str],
    budget: int,
):
    """
    사용자 피부 타입, 고민, 선호 화장품 종류, 알레르기 성분, 예산을 입력받아 화장품을 추천합니다.
    """
    try:
        recommendations = recommend_cosmetics(
            user_skin_type=user_skin_type,
            user_concerns=user_concerns,
            cosmetic_types=cosmetic_types,
            allergic_ingredients=allergic_ingredients,
            budget=budget,
        )

        if not recommendations:
            raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

        return recommendations

    except HTTPException as e:
        raise e

    except Exception as e:
        print(traceback.format_exc())
