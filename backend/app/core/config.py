from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./instant_rescue.db"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # AI
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    rag_top_k: int = 5

    # Documents
    max_pdf_upload_mb: int = 20
    max_pdf_pages: int = 10

    # Heart rate
    hr_source: str = "simulated"
    hr_sample_interval_seconds: int = 5
    hr_window_minutes: int = 5

    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = "InstantRescueBot"
    telegram_polling_enabled: bool = True
    telegram_webhook_secret: str = ""

    # Safety
    device_event_cooldown_seconds: int = 60
    enable_demo_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def ai_mode(self) -> str:
        """Real LLM only when a key is present, otherwise deterministic mock."""
        return "groq" if self.groq_api_key else "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
