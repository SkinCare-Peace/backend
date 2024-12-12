# main.py
import logging
import traceback
from fastapi.responses import JSONResponse
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from api import (
    cosmetics,
    predict_resnet,
    routine,
    user,
    detect_acne,
    statistics,
    notifications,
)

from services.model_loader import load_models
from services.routine_generate import init_price_segments

app = FastAPI()

app.include_router(predict_resnet.router)
app.include_router(routine.router)
app.include_router(cosmetics.router)
app.include_router(user.router)
app.include_router(detect_acne.router)
app.include_router(statistics.router)
app.include_router(notifications.router)

# 로거 설정
logger = logging.getLogger("detailed_exception_logger")
logger.setLevel(logging.ERROR)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# 파일 핸들러 설정
file_handler = logging.FileHandler("detailed_exceptions.log", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# 핸들러 추가
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# 모든 예외를 핸들링하는 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc

    # 요청 정보 수집
    request_info = f"Request Method: {request.method}\n"
    request_info += f"Request URL: {request.url}\n"
    request_info += f"Request Headers: {dict(request.headers)}\n"
    try:
        body = await request.body()
        request_info += f"Request Body: {body.decode('utf-8')}\n"
    except Exception as body_exc:
        request_info += f"Request Body: Could not retrieve due to {str(body_exc)}\n"

    # 예외 정보 수집
    error_message = f"Exception occurred:\n{request_info}\n"
    error_message += f"Details: {str(exc)}\n"
    error_message += "Traceback:\n"
    error_message += "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )

    # 로그를 콘솔 및 파일에 출력
    logger.error(error_message)

    # 클라이언트에 반환할 응답
    return JSONResponse(
        status_code=500,
        content={"message": "알 수 없는 에러"},
    )


@app.on_event("startup")
async def startup_event():
    # 서버 시작 시 평균 단가 계산 함수 호출
    await init_price_segments()


if __name__ == "__main__":
    load_models()
    uvicorn.run(app, host="127.0.0.1", port=8000)
