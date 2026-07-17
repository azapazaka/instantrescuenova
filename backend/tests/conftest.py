import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Tests run against SQLite with no Supabase and no Groq: the point is to test our
# logic, not the vendors. AI therefore runs in mock mode here by construction.
os.environ["DATABASE_URL"] = "sqlite:///./test_instant_rescue.db"
os.environ["GROQ_API_KEY"] = ""
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_POLLING_ENABLED"] = "false"
os.environ["ENABLE_DEMO_MODE"] = "true"
os.environ["DEVICE_EVENT_COOLDOWN_SECONDS"] = "60"
os.environ["HR_SOURCE"] = "simulated"

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture()
def client():
    """Client authenticated as USER_A, with JWT verification stubbed out.

    Overriding the dependency (rather than minting real tokens) keeps the tests
    offline. Token verification itself is covered separately in test_auth.py.
    """
    from app.core.auth import get_current_user
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_current_user] = lambda: USER_A
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def as_user_b(client):
    """Switch the existing client to a second user, to prove data isolation."""
    from app.core.auth import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: USER_B
    yield client
    app.dependency_overrides[get_current_user] = lambda: USER_A


@pytest.fixture()
def anon_client():
    """Client with real auth wired in, so protected routes must return 401."""
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
