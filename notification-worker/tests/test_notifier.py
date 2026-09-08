from email.message import EmailMessage

from app.notifier import send_ticket_email


def test_send_ticket_email_builds_and_sends(tmp_path, monkeypatch):
    qr_path = tmp_path / "ticket-001.png"
    qr_path.write_bytes(b"fake-png-bytes")

    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def send_message(self, msg: EmailMessage):
            sent_messages.append(msg)

    monkeypatch.setattr("app.notifier.smtplib.SMTP", FakeSMTP)

    send_ticket_email("a@example.com", "Nguyen Van A", "ticket-001", str(qr_path))

    assert len(sent_messages) == 1
    msg = sent_messages[0]
    assert msg["To"] == "a@example.com"
    assert msg.get_content_type() == "multipart/mixed"
