import csv
import asyncio
from elasticsearch import AsyncElasticsearch, helpers
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRODUCT_CSV = "backend/app/data/products_with_ing_formatted_kor.csv"
ING_CSV = "backend/app/data/ingredient_functions.csv"
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "products"

def load_ingredient_functions():
    ing_map = {}
    if not os.path.exists(ING_CSV):
        logger.error(f"Ingredient functions CSV not found: {ING_CSV}")
        return ing_map

    with open(ING_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kor_name = row.get("Korean Name", "").strip()
            functions = row.get("Functions", "").strip()
            if kor_name and functions:
                ing_map[kor_name] = functions
    return ing_map

async def migrate_enriched_csv():
    es = AsyncElasticsearch(ES_URL)
    
    if not os.path.exists(PRODUCT_CSV):
        logger.error(f"Product CSV file not found: {PRODUCT_CSV}")
        return

    ing_map = load_ingredient_functions()
    logger.info(f"Loaded {len(ing_map)} ingredient function mappings.")

    actions = []
    count = 0
    
    with open(PRODUCT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Price cleaning
            price_str = row.get("price", "0").replace(",", "")
            try:
                price = int(price_str)
            except ValueError:
                price = 0
                
            # Rank cleaning
            rank_str = row.get("rank", "999")
            try:
                rank = int(rank_str)
            except ValueError:
                rank = 999

            # Ingredients and Effects
            ingredients_str = row.get("ingredients", "")
            ingredients_list = [i.strip() for i in ingredients_str.split("|") if i.strip()]
            
            effects_set = set()
            for ing in ingredients_list:
                # Basic cleaning for matching (remove percentages if any)
                clean_ing = ing.split("(")[0].strip()
                if clean_ing in ing_map:
                    # Functions are often like "SKIN CONDITIONING | SOLVENT"
                    funcs = [f.strip() for f in ing_map[clean_ing].split("|")]
                    effects_set.update(funcs)
            
            effects_str = " | ".join(sorted(list(effects_set)))

            doc = {
                "_index": INDEX_NAME,
                "name": row.get("name"),
                "brand": row.get("brand"),
                "category": row.get("category"),
                "price": price,
                "rank": rank,
                "ingredients": ingredients_str,
                "effects": effects_str,
                "skin_type": "전체", # CSV doesn't have this, default to all
                "source": "csv_enriched"
            }
            actions.append(doc)
            
            if len(actions) >= 500:
                await helpers.async_bulk(es, actions)
                count += len(actions)
                logger.info(f"Indexed {count} products...")
                actions = []
                
    if actions:
        await helpers.async_bulk(es, actions)
        count += len(actions)
        logger.info(f"Final total indexed: {count}")
        
    await es.close()

if __name__ == "__main__":
    asyncio.run(migrate_enriched_csv())
