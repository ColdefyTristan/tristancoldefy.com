import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    EMAIL_TOKEN_SECRET: str
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
