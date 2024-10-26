# schemas/prediction.py
from pydantic import BaseModel
from typing import Dict, Optional

class PredictionResponse(BaseModel):
    predicted_class: Optional[int] = None
    predicted_label: Optional[str] = None
    classification_probabilities: Optional[Dict[str, float]] = None
    regression_values: Optional[Dict[str, float]] = None
