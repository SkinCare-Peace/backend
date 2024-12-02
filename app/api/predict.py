# api/predict.py

import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.predict import predict_image
from schemas.prediction import PredictionResponse

router = APIRouter(
    prefix="/predict",
    tags=["Predict"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{area_name}", response_model=PredictionResponse)
async def predict(area_name: str, bbox: str = Form(...), file: UploadFile = File(...)):
    try:
        bbox_list = [int(x.strip()) for x in bbox.split(",")]
        result = await predict_image(area_name, file, bbox_list)
        return result
    except ValueError as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
