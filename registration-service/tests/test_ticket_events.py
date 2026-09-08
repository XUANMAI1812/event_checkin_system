from app import events


def test_publish_ticket_created_adds_to_stream(fake_redis):
    events.publish_ticket_created(
        ticket_id="ticket-xyz",
        event_id=1,
        full_name="Nguyen Van A",
        email="a@example.com",
        qr_code_path="qrcodes/ticket-xyz.png",
    )

    entries = fake_redis.xrange(events.settings.ticket_stream_name)
    assert len(entries) == 1
    _entry_id, fields = entries[0]
    assert fields[b"ticket_id"] == b"ticket-xyz"
    assert fields[b"email"] == b"a@example.com"
