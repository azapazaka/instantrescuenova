from tests.conftest import USER_A


def test_new_user_gets_an_empty_profile(client):
    """A fresh account must not 500. The profile is created empty on first read."""
    response = client.get("/api/profile")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == USER_A
    assert data["name"] == ""


def test_update_profile_persists_changes(client):
    payload = {
        "name": "Азамат",
        "age": 72,
        "biological_sex": "male",
        "height_cm": 178,
        "weight_kg": 82,
        "activity_level": "Active",
        "primary_goal": "Здоровье сердца",
        "health_goals": "Больше энергии и стабильный сон",
        "known_conditions": "Гипертония",
        "injuries_or_limitations": "Колено после старой травмы",
        "dietary_preferences": "Меньше соли",
    }

    response = client.put("/api/profile", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 72
    assert data["activity_level"] == "Active"
    assert data["known_conditions"] == "Гипертония"

    # Persisted, not just echoed back.
    assert client.get("/api/profile").json()["name"] == "Азамат"


def test_update_profile_validates_required_fields(client):
    assert client.put("/api/profile", json={"age": -1}).status_code == 422


def test_update_profile_rejects_empty_name(client):
    payload = {"name": "", "activity_level": "Active", "primary_goal": "Сердце"}
    assert client.put("/api/profile", json=payload).status_code == 422
