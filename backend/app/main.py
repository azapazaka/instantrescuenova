from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import ecg_analysis, profile, recommendations, safety
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine, ensure_schema_compatibility
from app.core.errors import api_error_response
from app.schemas.common import HealthResponse
from app.services.seed import ensure_demo_profile


settings = get_settings()
app = FastAPI(title="Caspian Care API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return api_error_response(exc)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    db = SessionLocal()
    try:
        ensure_demo_profile(db)
    finally:
        db.close()


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", ai_mode=settings.ai_mode, app_env=settings.app_env)


app.include_router(profile.router)
app.include_router(recommendations.router)
app.include_router(ecg_analysis.router)
app.include_router(safety.router)
