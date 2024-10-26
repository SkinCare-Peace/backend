# config/settings.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    checkpoint_dir: str = "checkpoint"
    mongo_uri: str
    token_secret: str
    token_algorithm: str
    token_expire_minutes: int = 30
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    class Config:
        env_file = ".env"


settings = Settings()