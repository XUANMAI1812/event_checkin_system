import jwt

from app.security import sign_ticket
from app.config import settings


def test_sign_ticket_roundtrip():
    token = sign_ticket("abc-123", event_id=1)

    with open(settings.jwt_public_key_path, "rb") as f:
        public_key = f.read()

    payload = jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])
    assert payload["ticket_id"] == "abc-123"
    assert payload["event_id"] == 1


def test_sign_ticket_rejects_wrong_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    token = sign_ticket("abc-123", event_id=1)

    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_public_pem = other_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    try:
        jwt.decode(token, other_public_pem, algorithms=[settings.jwt_algorithm])
        assert False, "should have raised InvalidSignatureError"
    except jwt.InvalidSignatureError:
        pass
