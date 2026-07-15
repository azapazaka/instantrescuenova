def test_get_profile_returns_seeded_demo_profile(client):
    response = client.get("/api/profile")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Азамат"
    assert data["user_id"] == 1


def test_update_profile_persists_changes(client):
    payload = {
        "name": "Азамат",
        "age": 42,
        "biological_sex": "male",
        "height_cm": 178,
        "weight_kg": 82,
        "activity_level": "Active",
        "primary_goal": "Улучшение восстановления",
        "health_goals": "Больше энергии и стабильный сон",
        "known_conditions": "",
        "injuries_or_limitations": "Колено после старой травмы",
        "dietary_preferences": "Меньше сахара",
    }

    response = client.put("/api/profile", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 42
    assert data["activity_level"] == "Active"
    assert data["injuries_or_limitations"] == "Колено после старой травмы"


def test_update_profile_validates_required_fields(client):
    response = client.put("/api/profile", json={"age": -1})

    assert response.status_code == 422
