# services/auth.py
from core.security import create_access_token
from schemas.user import User
import httpx
from services.user import get_user_by_email, add_user
from core.config import settings

GOOGLE_CLIENT_ID = settings.google_client_id
GOOGLE_CLIENT_SECRET = settings.google_client_secret
GOOGLE_REDIRECT_URI = settings.google_redirect_uri
GOOGLE_TOKEN_URL = settings.google_token_url
GOOGLE_USERINFO_URL = settings.google_userinfo_url


def google_login_url():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return google_auth_url


async def google_callback_service(code: str):
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
        token_json = token_response.json()

        if "access_token" not in token_json:
            raise Exception("Failed to obtain access token")

        access_token = token_json["access_token"]

        # 사용자 정보 요청
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        userinfo = userinfo_response.json()

        if "email" not in userinfo:
            raise Exception("Failed to obtain user info")

        # 데이터베이스에서 사용자 검색 또는 생성
        user = await get_user_by_email(userinfo["email"])

        if user is None:
            new_user = User(
                email=userinfo["email"],
                name=userinfo["name"],
                profile_image=userinfo.get("picture"),
            )
            user_id = await add_user(new_user)
            if user_id is None:
                raise Exception("User already exists")

        # JWT 토큰 생성
        jwt_token = create_access_token(data={"sub": userinfo["email"]})
        return {"access_token": jwt_token, "token_type": "bearer", "user": userinfo}
