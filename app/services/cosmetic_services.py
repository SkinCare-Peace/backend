# services/cosmetic_services.py

import unicodedata
from bson import ObjectId
from typing import List, Optional
from fastapi import HTTPException
from elasticsearch import AsyncElasticsearch
import os
import logging

logger = logging.getLogger(__name__)

# ES 설정: 환경 변수에서 URL을 가져오고, 없으면 기본값 사용
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
# 로컬(Non-Docker) 환경에서 실행 시 localhost로 접근해야 할 경우를 위한 처리
if not os.getenv("DOCKER_ENV") and "elasticsearch" in ES_URL and not os.path.exists("/.dockerenv"):
    ES_URL = "http://localhost:9200"

es = AsyncElasticsearch(ES_URL)

def normalize_text(text: str) -> str:
    """
    문자열 정규화
    """
    return unicodedata.normalize("NFC", text)


async def search_cosmetics(db, query: str, limit: int) -> List[dict]:
    """
    Elasticsearch를 이용한 화장품 이름 검색 (Nori 분석기 활용)
    """
    q_normalized = normalize_text(query)

    try:
        # ES 검색 쿼리: 이름, 브랜드, 성분, 효능에서 검색
        search_query = {
            "query": {
                "multi_match": {
                    "query": q_normalized,
                    "fields": ["name^3", "brand^2", "ingredients", "effects^2"],
                    "type": "best_fields",
                    "operator": "or"
                }
            },
            "sort": [
                {"rank": {"order": "asc"}},
                {"_score": {"order": "desc"}}
            ],
            "size": limit
        }

        # 인덱스 존재 여부 먼저 확인 (에러 방지)
        if not await es.indices.exists(index="products"):
            logger.error("ES Index 'products' does not exist.")
            raise HTTPException(status_code=404, detail="제품 데이터 인덱스가 생성되지 않았습니다. 마이그레이션 스크립트를 실행해 주세요.")

        response = await es.search(index="products", body=search_query)
        hits = response["hits"]["hits"]

        if not hits:
            return []

        results = []
        for hit in hits:
            source = hit["_source"]
            image_url = source.get("image_url")
            if not image_url or image_url == "N/A":
                image_url = "https://via.placeholder.com/150?text=No+Image"
            elif image_url.startswith("//"):
                image_url = f"https:{image_url}"

            results.append({
                "_id": hit["_id"],
                "name": source.get("name"),
                "brand": source.get("brand"),
                "image_url": image_url,
                "selling_price": source.get("price"),
                "volume": source.get("volume", "N/A"),
            })

        return results

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"ES Search Error: {str(e)}")
        # 구체적인 에러 메시지를 포함하여 반환 (디버깅용)
        raise HTTPException(status_code=500, detail=f"검색 서비스 장애: {str(e)}")


async def search_by_id(db, product_id: str) -> dict:
    """
    ID로 화장품 검색 (ES Get API 활용)
    """
    try:
        response = await es.get(index="products", id=product_id)
        source = response["_source"]
        
        image_url = source.get("image_url")
        if not image_url or image_url == "N/A":
            image_url = "https://via.placeholder.com/150?text=No+Image"
        elif image_url.startswith("//"):
            image_url = f"https:{image_url}"

        return {
            "_id": response["_id"],
            "name": source.get("name"),
            "brand": source.get("brand"),
            "image_url": image_url,
            "selling_price": source.get("price"),
            "volume": source.get("volume", "N/A"),
        }
    except Exception:
        raise HTTPException(status_code=404, detail="해당 ID의 제품을 찾을 수 없습니다.")
