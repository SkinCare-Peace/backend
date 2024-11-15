# api/recommend.py

from typing import List
from fastapi import APIRouter, HTTPException

from schemas.recommendation import ProductRecommendation
from services.cosmetic_recommend import recommend_cosmetics


router = APIRouter()


@router.post("/recommend", response_model=List[ProductRecommendation])
def get_recommendations(
    user_skin_type: str,
    user_concerns: List[str],
    preferred_cosmetic_types: List[str],
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
            preferred_cosmetic_types=preferred_cosmetic_types,
            allergic_ingredients=allergic_ingredients,
            budget=budget,
        )

        if not recommendations:
            raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

        return recommendations

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
