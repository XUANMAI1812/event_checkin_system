import os
from datetime import datetime, timedelta, timezone

import jwt
import qrcode

from .config import settings


def _read_key(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def sign_ticket(ticket_id: str, event_id: int, expires_days: int = 30) -> str:
    """Sign a ticket JWT with the service RSA private key"""
    private_key = _read_key(settings.jwt_private_key_path)
    now = datetime.now(timezone.utc)
    payload = {
        "ticket_id": ticket_id,
        "event_id": event_id,
        "iat": now,
        "exp": now + timedelta(days=expires_days),
    }
    return jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)


def verify_ticket(token: str) -> dict:
    """Verify a ticket JWT with the service RSA public key"""
    public_key = _read_key(settings.jwt_public_key_path)
    return jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])


def generate_qr_code(data: str, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img = qrcode.make(data)
    img.save(out_path)
    return out_path
