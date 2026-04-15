import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from elasticsearch import AsyncElasticsearch, helpers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 기반 설정 (Docker 환경 대응)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/peace")
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "products"
COLLECTION_NAME = "oliveyoung_products_integrated"

async def migrate_data():
    # MongoDB 연결
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.get_default_database()
    collection = db[COLLECTION_NAME]
    
    # Elasticsearch 연결
    es = AsyncElasticsearch(ES_URL)
    
    # 인덱스 설정 (Nori 분석기 포함)
    index_settings = {
        "settings": {
            "analysis": {
                "tokenizer": {
                    "nori_user_dict": {
                        "type": "nori_tokenizer",
                        "decompound_mode": "mixed"
                    }
                },
                "analyzer": {
                    "nori_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_user_dict",
                        "filter": [
                            "nori_readingform",
                            "lowercase"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "product_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "nori_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "brand": {
                    "type": "text",
                    "analyzer": "nori_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "ingredients": {
                    "type": "text",
                    "analyzer": "nori_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "skin_type": {"type": "keyword"},
                "category": {"type": "keyword"},
                "price": {"type": "integer"},
                "rank": {"type": "integer"},
                "image_url": {"type": "keyword", "index": False},
                "review_count": {"type": "integer"}
            }
        }
    }

    # 1. 인덱스가 없으면 생성
    if not await es.indices.exists(index=INDEX_NAME):
        logger.info(f"Creating index: {INDEX_NAME} with Nori analyzer mapping")
        await es.indices.create(index=INDEX_NAME, body=index_settings)
    
    cursor = collection.find()
    actions = []
    count = 0
    
    async for product in cursor:
        doc = {
            "_index": INDEX_NAME,
            "_id": str(product["_id"]),
            "product_id": str(product["_id"]),
            "name": product.get("name"),
            "brand": product.get("brand"),
            "ingredients": product.get("ingredients"),
            "skin_type": product.get("skin_type", "전체"),
            "category": product.get("category"),
            "price": product.get("selling_price", 0),
            "rank": product.get("rank", 999),
            "image_url": product.get("image_url"),
            "review_count": product.get("review_count", 0)
        }
        actions.append(doc)
        
        if len(actions) >= 100:
            await helpers.async_bulk(es, actions)
            count += len(actions)
            logger.info(f"Indexed {count} products...")
            actions = []
            
    if actions:
        await helpers.async_bulk(es, actions)
        count += len(actions)
        logger.info(f"Final total indexed: {count}")
        
    await es.close()
    mongo_client.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
