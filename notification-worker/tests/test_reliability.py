import os
import time

import pytest

from app import consumer, crud
from app.config import settings

requires_real_redis = pytest.mark.skipif(
    not os.environ.get("TEST_REDIS_URL"),
    reason="fakeredis khong dem lan giao, dat TEST_REDIS_URL de chay tren Redis that",
)


def _add_ticket(client, ticket_id="ticket-001"):
    return client.xadd(
        settings.ticket_stream_name,
        {
            "ticket_id": ticket_id,
            "event_id": "1",
            "full_name": "Nguyen Van A",
            "email": "a@example.com",
            "qr_code_path": f"qrcodes/{ticket_id}.png",
        },
    )


def _deliver_without_ack(client):
    """Doc message nhung khong XACK (gia lap worker crash)"""
    consumer.ensure_consumer_group(client)
    return client.xreadgroup(
        settings.consumer_group,
        settings.consumer_name,
        {settings.ticket_stream_name: ">"},
        count=10,
    )


def _pending_count(client) -> int:
    return client.xpending(settings.ticket_stream_name, settings.consumer_group)[
        "pending"
    ]


def _always_fail(*args, **kwargs):
    raise RuntimeError("SMTP down")


def test_touch_heartbeat_creates_and_refreshes_file():
    consumer.touch_heartbeat()
    assert os.path.exists(settings.heartbeat_path)

    os.utime(settings.heartbeat_path, (0, 0))
    consumer.touch_heartbeat()
    assert time.time() - os.path.getmtime(settings.heartbeat_path) < 5


def test_run_touches_heartbeat(fake_redis_client):
    consumer.run(client=fake_redis_client, max_iterations=1)
    assert os.path.exists(settings.heartbeat_path)


def test_reclaim_stale_processes_pending_entry(fake_redis_client, db_session, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))
    monkeypatch.setattr(settings, "reclaim_min_idle_ms", 0)

    _add_ticket(fake_redis_client, "ticket-101")
    _deliver_without_ack(fake_redis_client)
    assert _pending_count(fake_redis_client) == 1

    assert consumer.reclaim_stale(fake_redis_client) == 1

    assert len(sent) == 1
    assert crud.get_sent_notification(db_session, "ticket-101") is not None
    assert _pending_count(fake_redis_client) == 0


def test_reclaim_stale_skips_recently_delivered_entry(fake_redis_client, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))
    monkeypatch.setattr(settings, "reclaim_min_idle_ms", 60_000)

    _add_ticket(fake_redis_client, "ticket-102")
    _deliver_without_ack(fake_redis_client)

    assert consumer.reclaim_stale(fake_redis_client) == 0
    assert sent == []
    assert _pending_count(fake_redis_client) == 1


@requires_real_redis
def test_poison_message_dead_lettered_by_real_delivery_counter(
    fake_redis_client, monkeypatch
):
    monkeypatch.setattr(consumer, "send_ticket_email", _always_fail)
    monkeypatch.setattr(settings, "reclaim_min_idle_ms", 0)
    monkeypatch.setattr(settings, "max_deliveries", 3)

    _add_ticket(fake_redis_client, "ticket-106")
    _deliver_without_ack(fake_redis_client)

    for _ in range(3):
        consumer.reclaim_stale(fake_redis_client)

    dead = fake_redis_client.xrange(settings.dead_letter_stream_name)
    assert len(dead) == 1
    assert int(dead[0][1][b"deliveries"]) == 4
    assert _pending_count(fake_redis_client) == 0


def test_run_recovers_pending_entry_on_startup(fake_redis_client, db_session, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))
    monkeypatch.setattr(settings, "reclaim_min_idle_ms", 0)

    _add_ticket(fake_redis_client, "ticket-104")
    _deliver_without_ack(fake_redis_client)

    consumer.run(client=fake_redis_client, max_iterations=1)

    assert len(sent) == 1
    assert crud.get_sent_notification(db_session, "ticket-104") is not None
    assert _pending_count(fake_redis_client) == 0


def test_failed_entry_stays_pending_until_reclaimed(fake_redis_client, monkeypatch):
    monkeypatch.setattr(consumer, "send_ticket_email", _always_fail)
    _add_ticket(fake_redis_client, "ticket-105")

    consumer.run(client=fake_redis_client, max_iterations=1)

    assert _pending_count(fake_redis_client) == 1
