from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    EMAIL_TOKEN_SECRET: str
    FRONTEND_BASE_URL: str = "https://tristancoldefy.com"
    DATABASE_URL: str

    WEBHOOK_SECRET: Optional[str] = None

    N8N_WEBHOOK_ARTICLES: Optional[str] = None
    N8N_WEBHOOK_SUMMARY: Optional[str] = None

    SES_SMTP_HOST: Optional[str] = None
    SES_SMTP_PORT: int = 587
    SES_SMTP_USER: Optional[str] = None
    SES_SMTP_PASS: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    session_cookie_secure: bool = False


settings = Settings()
