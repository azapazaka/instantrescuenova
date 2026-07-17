"""Auth is the boundary every other test's isolation depends on."""

import pytest

PROTECTED = [
    ("get", "/api/profile"),
    ("get", "/api/checkins"),
    ("get", "/api/recommendations"),
    ("get", "/api/health-documents"),
    ("get", "/api/heart-rate/live"),
    ("get", "/api/emergency-contacts"),
    ("get", "/api/fall-incidents"),
    ("get", "/api/devices"),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_routes_reject_anonymous(anon_client, method, path):
    response = getattr(anon_client, method)(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_health_endpoint_is_public(anon_client):
    response = anon_client.get("/api/health")
    assert response.status_code == 200
    # No key is configured in tests, so the app must report mock rather than
    # claim to be running a real model.
    assert response.json()["ai_mode"] == "mock"


def test_malformed_bearer_token_is_rejected(anon_client):
    response = anon_client.get("/api/profile", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] in {"INVALID_TOKEN", "NOT_AUTHENTICATED"}


def test_non_bearer_authorization_is_rejected(anon_client):
    response = anon_client.get("/api/profile", headers={"Authorization": "Basic abc123"})
    assert response.status_code == 401
