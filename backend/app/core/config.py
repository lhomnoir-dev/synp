import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Synp API"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    database_url: str = os.getenv("DATABASE_URL")

    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")

    encryption_key: str = ""
    cors_origins: List[str] = os.getenv("CORES_ORIGINS")

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
