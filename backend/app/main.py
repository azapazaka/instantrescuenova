from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import health_documents, heart_rate, profile, recommendations, safety, telegram
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.errors import api_error_response
from app.schemas.common import HealthResponse
from app.services import telegram_bot

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Postgres schema is owned by Supabase migrations. create_all only fills in
    # SQLite for local runs and tests; on Postgres the tables already exist and
    # this is a no-op rather than a competing source of truth.
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from app.services.rag import index_corpus

        result = index_corpus(db)
        print(f"[rag] indexed {result['chunks']} chunks ({result['mode']} mode)")
    except Exception as exc:
        # A missing embedding model must not stop the API from booting.
        print(f"[rag] corpus indexing skipped: {exc}")
    finally:
        db.close()

    telegram_bot.start()
    try:
        yield
    finally:
        await telegram_bot.stop()


app = FastAPI(title="Instant Rescue API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return api_error_response(exc)


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        ai_mode=settings.ai_mode,
        app_env=settings.app_env,
        telegram_bot_username=settings.telegram_bot_username,
        telegram_configured=bool(
            settings.telegram_bot_token
            and (settings.telegram_polling_enabled or settings.telegram_webhook_secret)
        ),
    )


app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(health_documents.router)
app.include_router(heart_rate.router)
app.include_router(safety.router)
app.include_router(telegram.router)
