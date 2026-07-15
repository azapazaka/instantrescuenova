from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./caspian_care.db"
    ai_mode: str = "mock"
    ai_api_key: str = ""
    ai_model: str = ""
    max_pdf_upload_mb: int = 20
    max_ecg_pdf_pages: int = 10
    delete_pdf_after_analysis: bool = True
    telegram_bot_token: str = ""
    telegram_bot_username: str = "CaspianCareBot"
    device_event_cooldown_seconds: int = 60
    enable_demo_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
