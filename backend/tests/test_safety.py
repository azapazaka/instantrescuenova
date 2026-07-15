def test_create_contact_generates_pairing_code(client):
    response = client.post(
        "/api/emergency-contacts",
        json={"name": "Мама", "relationship": "Семья"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting"
    assert len(data["pairing_code"]) == 6


def test_device_event_requires_valid_token(client):
    created = client.post("/api/devices", json={"name": "Demo Band"})
    device = created.json()

    response = client.post(
        f"/api/devices/{device['device_id']}/fall-events",
        headers={"Authorization": "Bearer wrong-token"},
        json={
            "event_timestamp": "2026-07-15T18:42:00Z",
            "confidence": 0.91,
            "sensor_data": {"impact_g": 3.1},
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_DEVICE_TOKEN"


def test_valid_device_event_creates_incident_and_cooldown_blocks_repeat(client):
    created = client.post("/api/devices", json={"name": "Demo Band"})
    device = created.json()
    payload = {
        "event_timestamp": "2026-07-15T18:42:00Z",
        "confidence": 0.91,
        "sensor_data": {"freefall_g": 0.32, "impact_g": 3.1},
    }

    first = client.post(
        f"/api/devices/{device['device_id']}/fall-events",
        headers={"Authorization": f"Bearer {device['device_secret']}"},
        json=payload,
    )
    second = client.post(
        f"/api/devices/{device['device_id']}/fall-events",
        headers={"Authorization": f"Bearer {device['device_secret']}"},
        json=payload,
    )

    assert first.status_code == 200
    assert first.json()["status"] == "detected"
    assert second.status_code == 409
    assert second.json()["error"]["code"] in ["DUPLICATE_EVENT", "EVENT_COOLDOWN"]


def test_demo_simulate_fall_uses_incident_flow(client):
    response = client.post("/api/demo/simulate-fall")

    assert response.status_code == 200
    assert response.json()["status"] == "detected"

    history = client.get("/api/fall-incidents")
    assert len(history.json()) == 1
