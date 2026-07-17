from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("APP_ENV", "production")
if os.environ.get("VERCEL") and not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL must be configured in Vercel production environment")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/instant_rescue.db")
os.environ.setdefault("SUPABASE_URL", "https://xvujfxwdzlfkatozoesm.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "sb_publishable_dwxGpf8zCFgRwdvXQuPhfQ_2YZQX9VA")
os.environ.setdefault("TELEGRAM_POLLING_ENABLED", "false")

from app.main import app  # noqa: E402

DIST = ROOT / "frontend" / "dist"
if not DIST.exists():
    DIST = ROOT / "app" / "frontend" / "dist"

if DIST.exists():
    from fastapi.responses import FileResponse  # noqa: E402
    from fastapi.staticfiles import StaticFiles  # noqa: E402

    assets = DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{path:path}", include_in_schema=False)
    def serve_spa(path: str = ""):
        return FileResponse(DIST / "index.html")
