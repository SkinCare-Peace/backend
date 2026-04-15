import asyncio
from elasticsearch import AsyncElasticsearch
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

async def create_index():
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
                "effects": {
                    "type": "text",
                    "analyzer": "nori_analyzer"
                },
                "category": {"type": "keyword"},
                "skin_types": {"type": "keyword"},
                "concerns": {"type": "keyword"},
                "price": {"type": "integer"},
                "rank": {"type": "integer"},
                "image_url": {"type": "keyword", "index": False},
                "review_count": {"type": "integer"}
            }
        }
    }

    if await es.indices.exists(index=INDEX_NAME):
        logger.info(f"Index {INDEX_NAME} already exists. Deleting and recreating...")
        await es.indices.delete(index=INDEX_NAME)
    
    await es.indices.create(index=INDEX_NAME, body=index_settings)
    logger.info(f"Index {INDEX_NAME} created successfully with Nori analyzer.")
    await es.close()

if __name__ == "__main__":
    asyncio.run(create_index())
