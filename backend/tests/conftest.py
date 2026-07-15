import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./test_caspian_care.db"
os.environ["AI_MODE"] = "mock"
os.environ["ENABLE_DEMO_MODE"] = "true"
os.environ["DEVICE_EVENT_COOLDOWN_SECONDS"] = "60"


@pytest.fixture()
def client():
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
