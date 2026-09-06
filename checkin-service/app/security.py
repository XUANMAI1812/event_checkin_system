import jwt

from .config import settings


def _read_public_key() -> bytes:
    with open(settings.jwt_public_key_path, "rb") as f:
        return f.read()


def verify_ticket(token: str) -> dict:
    """Verify chu ky JWT bang public key, tra ve payload
    (ticket_id, event_id, iat, exp)

    Neu token khong hop le, ham nay se raise:
    - jwt.ExpiredSignatureError neu qua han (exp)
    - jwt.InvalidSignatureError neu ky sai key (ve gia mao)
    Ca hai deu la con cua jwt.InvalidTokenError, router se bat va tra 401.
    """
    public_key = _read_public_key()
    return jwt.decode(token, public_key, algorithms=[settings.jwt_algorithm])
