# schemas/cosmetics.py

from pydantic import BaseModel, Field
from typing import Dict, List


class ProductBase(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    brand: str
    img_url: str = ""

    class Config:
        populate_by_name = True


class ProductRecommendation(ProductBase):
    selling_price: int
    link: str
    skin_type_score: float
    concern_score: float
    rank_score: float
    price_score: float
    total_score: float
    matching_ingredients: Dict[str, Dict[str, int]]
    reason: str = ""


class CosmeticSearchResult(ProductBase):
    price: int = Field(..., alias="selling_price")
    volume: str
