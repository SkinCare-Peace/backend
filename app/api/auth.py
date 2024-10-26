#api/auth.py
from fastapi import APIRouter, HTTPException
from services.auth import google_login_url, google_callback_service

router = APIRouter()

@router.get("/auth/login")
async def google_login():
    url = google_login_url()
    return {"url": url}

@router.post("/auth/callback")
async def google_callback(code: str):
    try:
        result = await google_callback_service(code)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))