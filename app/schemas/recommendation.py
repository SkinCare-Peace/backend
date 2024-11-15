# schemas/recommendation.py

from pydantic import BaseModel
from typing import List


class ProductRecommendation(BaseModel):
    name: str
    brand: str
    selling_price: int
    link: str
    skin_type_score: float
    concern_score: float
    rank_score: float
    price_score: float
    total_score: float
    matching_ingredients: List[str]
