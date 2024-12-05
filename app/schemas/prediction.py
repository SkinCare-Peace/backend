# schemas/prediction.py
from pydantic import BaseModel
from typing import Dict, List, Optional


class PredictionResponse(BaseModel):
    classification_probabilities: Optional[Dict[str, List[float]]] = None
    regression_values: Optional[Dict[str, float]] = None
