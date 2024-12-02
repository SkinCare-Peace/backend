# services/cosmetic_services.py

import unicodedata
from bson import ObjectId
from typing import List, Optional
from fastapi import HTTPException


def normalize_text(text: str) -> str:
    """
    문자열 정규화
    """
    return unicodedata.normalize("NFC", text)


async def search_cosmetics(db, query: str, limit: int) -> List[dict]:
    """
    화장품 이름으로 검색
    """
    q_normalized = normalize_text(query)

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
                "selling_price": 1,
                "volume": 1,
            }
        },
    ]

    cursor = db["oliveyoung_products"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    if not results:
        raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")
    results = [{**result, "_id": str(result["_id"])} for result in results]

    return results


async def search_by_id(db, product_id: str) -> dict:
    """
    ID로 화장품 검색
    """
    try:
        object_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")

    product = await db["oliveyoung_products"].find_one(
        {"_id": object_id},
        {
            "_id": 1,
            "name": 1,
            "brand": 1,
            "image_url": 1,
            "selling_price": 1,
            "volume": 1,
        },
    )

    if not product:
        raise HTTPException(status_code=404, detail="조건에 맞는 제품이 없습니다.")

    product["_id"] = str(product["_id"])
    return product
