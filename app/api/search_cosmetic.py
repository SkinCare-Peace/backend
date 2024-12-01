# api/search_cosmetic.py

import unicodedata
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from typing import List
from db.database import db
from pydantic import BaseModel, Field

router = APIRouter()


class CosmeticSearchResult(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    brand: str
    image_url: str = ""


def normalize_text(text):
    return unicodedata.normalize("NFC", text)


@router.get("/cosmetics", response_model=List[CosmeticSearchResult])
def search_cosmetics_by_name(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, gt=0),
):
    """
    화장품 이름으로 검색합니다.
    """
    # 검색어 정규화
    q_normalized = normalize_text(q)

    # 텍스트 검색 및 결과 처리
    pipeline = [
        {"$match": {"name": {"$regex": q_normalized, "$options": "i"}}},
        {"$sort": {"rank": 1}},  # rank를 기준으로 오름차순 정렬
        {
            "$group": {
                "_id": "$name",  # 이름으로 그룹화하여 중복 제거
                "doc": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$doc"}},
        {"$limit": limit},  # 결과 개수 제한
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "brand": 1,
                "image_url": 1,
            }
        },
    ]

    cursor = db["oliveyoung_products"].aggregate(pipeline)
    results = list(cursor)

    if not results:
        raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

    for result in results:
        result["_id"] = str(result["_id"])

    return results


@router.get("/cosmetics/{product_id}", response_model=CosmeticSearchResult)
def search_by_id(product_id: str):
    """
    화장품 ID로 검색합니다.
    """
    # MongoDB ObjectId로 변환
    try:
        object_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    # ID로 검색
    product = db["oliveyoung_products"].find_one(
        {"_id": object_id},
        {"_id": 1, "name": 1, "brand": 1, "image_url": 1},
    )

    if not product:
        raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

    # ObjectId를 문자열로 변환
    product["_id"] = str(product["_id"])

    return product
