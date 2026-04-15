# api/cosmetic.py

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List
from db.database import get_db
from schemas.cosmetics import ProductRecommendation, ReasonRequest
from services.cosmetic_recommend import get_gpt_response, recommend_cosmetics
import traceback
from schemas.cosmetics import CosmeticSearchResult
from services.cosmetic_services import search_by_id, search_cosmetics
from data.oliveyoung import run_sync_crawler
from scripts.migrate_to_es import migrate_data

router = APIRouter(
    prefix="/cosmetics",
    tags=["Cosmetics"],
    responses={404: {"description": "Not found"}},
)
db = get_db()


@router.post("/sync")
async def sync_cosmetic_data(background_tasks: BackgroundTasks):
    """
    올리브영 데이터 크롤링 및 Elasticsearch 인덱싱을 트리거합니다.
    백그라운드에서 실행되도록 설정합니다.
    """
    async def run_sync_process():
        try:
            print("Starting data sync process...")
            # 1. 크롤링 및 이미지 주소 보정
            await run_sync_crawler()
            # 2. ES 인덱싱
            await migrate_data()
            print("Data sync process completed successfully.")
        except Exception as e:
            print(f"Error during sync process: {e}")
            traceback.print_exc()

    background_tasks.add_task(run_sync_process)
    return {"message": "Sync process started in background"}


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
async def get_recommendations(
    user_skin_type: str = "전체",
    user_concerns: List[str] = [],
    cosmetic_types: str = "",
    allergic_ingredients: List[str] = [],
    budget: int = 1000000,
):
    """
    사용자 피부 타입, 고민, 선호 화장품 종류, 알레르기 성분, 예산을 입력받아 화장품을 추천합니다.
    """
    if not user_skin_type:
        user_skin_type = "전체"
    try:
        recommendations = await recommend_cosmetics(
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
        # print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendation/reason", response_model=str)
async def get_recommendation_reason(request: ReasonRequest):
    """
    화장품 추천 이유를 생성합니다.
    """
    return await get_gpt_response(
        request.name,
        request.brand,
        request.skin_type_score,
        request.concern_score,
        request.rank_score,
        request.price_score,
        request.matching_ingredients,
        request.user_skin_type,
        request.user_concerns,
    )
