def test_create_checkin_and_generate_mock_recommendation(client):
    checkin_payload = {
        "sleep_hours": 6.0,
        "sleep_quality": 6,
        "energy_level": 5,
        "stress_level": 7,
        "muscle_soreness": 4,
        "pain_or_discomfort": "",
        "planned_activity": "Легкая тренировка",
        "notes": "Много работы",
    }

    checkin_response = client.post("/api/checkins", json=checkin_payload)
    assert checkin_response.status_code == 200
    checkin_id = checkin_response.json()["id"]

    recommendation_response = client.post(
        "/api/recommendations", json={"checkin_id": checkin_id}
    )

    assert recommendation_response.status_code == 200
    result = recommendation_response.json()["structured_result"]
    assert result["readiness"]["level"] in ["low", "moderate", "high"]
    assert result["movement"]["intensity"] in ["low", "moderate", "high"]
    assert "summary" in result


def test_recommendations_history_contains_generated_result(client):
    client.post(
        "/api/checkins",
        json={
            "sleep_hours": 8,
            "sleep_quality": 8,
            "energy_level": 8,
            "stress_level": 3,
            "muscle_soreness": 2,
        },
    )
    client.post("/api/recommendations", json={})

    response = client.get("/api/recommendations")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["recommendation_type"] == "daily_plan"
