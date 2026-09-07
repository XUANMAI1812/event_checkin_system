import logging

import redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url)
    return _redis_client


def publish_ticket_created(
    ticket_id: str, event_id: int, full_name: str, email: str, qr_code_path: str
) -> None:
    try:
        client = get_redis_client()
        client.xadd(
            settings.ticket_stream_name,
            {
                "ticket_id": ticket_id,
                "event_id": str(event_id),
                "full_name": full_name,
                "email": email,
                "qr_code_path": qr_code_path,
            },
        )
    except RedisError:
        logger.warning(
            "Khong publish duoc ticket_created cho ticket_id=%s (Redis loi) - "
            "ve van tao thanh cong nhung nguoi tham du se khong nhan duoc "
            "email tu dong.",
            ticket_id,
        )
