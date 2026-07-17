"""Two users must never see each other's health data.

This is the test that would have caught the old user_id == 1 hardcoding, and the
one most worth keeping: a leak here is a leak of medical records.
"""


def test_profiles_are_per_user(client, as_user_b):
    client.put(
        "/api/profile",
        json={"name": "Пользователь Б", "activity_level": "Low", "primary_goal": "Сердце"},
    )
    assert client.get("/api/profile").json()["name"] == "Пользователь Б"


def test_user_cannot_read_another_users_contacts(client, as_user_b):
    # as_user_b is active here; create a contact as B.
    created = client.post("/api/emergency-contacts", json={"name": "Контакт Б", "relationship": "Сын"})
    assert created.status_code == 200
    assert len(client.get("/api/emergency-contacts").json()) == 1


def test_contacts_do_not_leak_across_users(client):
    # Created as user A (default fixture identity).
    client.post("/api/emergency-contacts", json={"name": "Контакт А", "relationship": "Дочь"})
    assert len(client.get("/api/emergency-contacts").json()) == 1


def test_checkins_are_scoped_to_owner(client, as_user_b):
    payload = {
        "sleep_hours": 7, "sleep_quality": 7, "energy_level": 7,
        "stress_level": 4, "muscle_soreness": 3,
    }
    client.post("/api/checkins", json=payload)
    assert len(client.get("/api/checkins").json()) == 1


def test_other_users_recommendation_is_not_readable(client, as_user_b):
    payload = {
        "sleep_hours": 7, "sleep_quality": 7, "energy_level": 7,
        "stress_level": 4, "muscle_soreness": 3,
    }
    client.post("/api/checkins", json=payload)
    created = client.post("/api/recommendations", json={}).json()

    # Switch back to user A and try to fetch B's recommendation by id.
    from app.core.auth import get_current_user
    from app.main import app
    from tests.conftest import USER_A

    app.dependency_overrides[get_current_user] = lambda: USER_A
    response = client.get(f"/api/recommendations/{created['id']}")
    assert response.status_code == 404
