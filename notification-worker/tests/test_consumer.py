from app import consumer, crud
from app.config import settings


def _fields(
    ticket_id="ticket-001",
    event_id="1",
    full_name="Nguyen Van A",
    email="a@example.com",
    qr_code_path="qrcodes/ticket-001.png",
):
    return {
        b"ticket_id": ticket_id.encode(),
        b"event_id": event_id.encode(),
        b"full_name": full_name.encode(),
        b"email": email.encode(),
        b"qr_code_path": qr_code_path.encode(),
    }


def test_process_entry_creates_record_and_sends_email(db_session, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))

    consumer.process_entry(_fields())

    assert len(sent) == 1
    assert crud.get_sent_notification(db_session, "ticket-001") is not None


def test_process_entry_duplicate_skips_email(db_session, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))

    consumer.process_entry(_fields(ticket_id="ticket-002"))
    consumer.process_entry(_fields(ticket_id="ticket-002"))

    assert len(sent) == 1  # gui r k gui lai


def test_run_consumes_from_fake_redis_stream(fake_redis_client, db_session, monkeypatch):
    sent = []
    monkeypatch.setattr(consumer, "send_ticket_email", lambda *a, **kw: sent.append(a))

    fake_redis_client.xadd(
        settings.ticket_stream_name,
        {
            "ticket_id": "ticket-003",
            "event_id": "1",
            "full_name": "Nguyen Van A",
            "email": "a@example.com",
            "qr_code_path": "qrcodes/ticket-003.png",
        },
    )

    consumer.run(client=fake_redis_client, max_iterations=1)

    assert len(sent) == 1
    assert crud.get_sent_notification(db_session, "ticket-003") is not None
