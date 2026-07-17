from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/instant_rescue.db")
os.environ.setdefault("SUPABASE_URL", "https://xvujfxwdzlfkatozoesm.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "sb_publishable_dwxGpf8zCFgRwdvXQuPhfQ_2YZQX9VA")
os.environ.setdefault("TELEGRAM_POLLING_ENABLED", "false")

from app.main import app  # noqa: E402
