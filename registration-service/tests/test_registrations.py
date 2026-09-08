import os

from app import events


def _create_event(client, capacity=1):
    resp = client.post(
        "/events",
        json={
            "name": "Workshop",
            "description": "desc",
            "location": "HCMC",
            "start_time": "2026-11-01T09:00:00",
            "capacity": capacity,
        },
    )
    return resp.json()["id"]


def test_register_attendee_success(client, fake_redis):
    event_id = _create_event(client, capacity=2)

    resp = client.post(
        f"/events/{event_id}/register",
        json={"full_name": "Nguyen Van A", "email": "a@example.com"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["ticket_id"]
    assert os.path.exists(data["qr_code_path"])

    # dang ky thanh cong phai publish 1 event ticketcreated len
    # Redis stream cho notification worker tieu thu
    entries = fake_redis.xrange(events.settings.ticket_stream_name)
    assert len(entries) == 1


def test_register_event_full(client):
    event_id = _create_event(client, capacity=1)

    r1 = client.post(
        f"/events/{event_id}/register",
        json={"full_name": "A", "email": "a@example.com"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/events/{event_id}/register",
        json={"full_name": "B", "email": "b@example.com"},
    )
    assert r2.status_code == 400


def test_register_event_not_found(client):
    resp = client.post(
        "/events/9999/register",
        json={"full_name": "A", "email": "a@example.com"},
    )
    assert resp.status_code == 404
