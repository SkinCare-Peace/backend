# api/detect_acne.py

import traceback
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.detect_acne import detect_acne
from PIL import Image
import io
import base64


class AcneDetectionResponse(BaseModel):
    processed_image: str  # Base64로 인코딩된 이미지 문자열
    score: int  # 여드름 감지 점수


router = APIRouter(
    prefix="/acne_detection",
    tags=["Acne Detection"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=AcneDetectionResponse)
async def detect_acne_endpoint(bbox: str = Form(...), file: UploadFile = File(...)):
    """
    여드름 감지를 수행하는 엔드포인트입니다.
    """
    try:
        # 업로드된 파일 읽기
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        bbox_list = [int(x.strip()) for x in bbox.split(",")]
        # 여드름 감지 함수 호출
        result_image, score = detect_acne(image, bbox_list)

        # 처리된 이미지를 Base64로 인코딩
        buffered = io.BytesIO()
        result_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return AcneDetectionResponse(processed_image=img_str, score=score)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")
