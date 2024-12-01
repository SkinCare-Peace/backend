#core/security.py
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import jwt
from core.config import settings

SECRET_KEY = settings.token_secret
ALGORITHM = settings.token_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.exceptions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
