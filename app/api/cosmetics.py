# api/cosmetic.py

from fastapi import APIRouter, HTTPException, Query
from typing import List
from db.database import get_db
from schemas.cosmetics import ProductRecommendation
from services.cosmetic_recommend import recommend_cosmetics
import traceback
from schemas.cosmetics import CosmeticSearchResult
from services.cosmetic_services import search_by_id, search_cosmetics

router = APIRouter(
    prefix="/cosmetics",
    tags=["Cosmetics"],
    responses={404: {"description": "Not found"}},
)
db = get_db()


@router.get("/", response_model=List[CosmeticSearchResult])
async def search_cosmetics_by_name(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, gt=0),
):
    """
    화장품 이름으로 검색합니다.
    """
    return await search_cosmetics(db, q, limit)


@router.get("/{product_id}", response_model=CosmeticSearchResult)
async def search_cosmetic_by_id(product_id: str):
    """
    화장품 ID로 검색합니다.
    """
    return await search_by_id(db, product_id)


@router.post("/recommendation", response_model=List[ProductRecommendation])
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
