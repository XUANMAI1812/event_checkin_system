def test_create_and_get_event(client):
    resp = client.post(
        "/events",
        json={
            "name": "Tech Talk",
            "description": "A talk about DevOps",
            "location": "Hanoi",
            "start_time": "2026-10-01T09:00:00",
            "capacity": 2,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Tech Talk"
    event_id = data["id"]

    resp2 = client.get(f"/events/{event_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == event_id


def test_get_nonexistent_event(client):
    resp = client.get("/events/9999")
    assert resp.status_code == 404
