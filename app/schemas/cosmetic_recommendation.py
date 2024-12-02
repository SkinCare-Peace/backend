# schemas/recommendation.py

from pydantic import BaseModel, Field
from typing import Dict, List


class ProductRecommendation(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    brand: str
    selling_price: int
    link: str
    skin_type_score: float
    concern_score: float
    rank_score: float
    price_score: float
    total_score: float
    matching_ingredients: Dict[str, Dict[str, int]]
    reason: str = ""
    image_url: str

    class Config:
        allow_population_by_field_name = True
