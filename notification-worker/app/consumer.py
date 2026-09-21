import logging
import time
from pathlib import Path

import redis
from redis.exceptions import ResponseError
from sqlalchemy.exc import IntegrityError

from . import crud, database
from .config import settings
from .notifier import send_ticket_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("notification-worker")


def get_redis_client() -> redis.Redis:
    # Redis treo -> TimeoutError -> worker thoat -> Docker restart
    return redis.from_url(
        settings.redis_url, socket_timeout=settings.redis_socket_timeout_seconds
    )


def ensure_consumer_group(client: redis.Redis) -> None:
    """Tao consumer group; id="0" doc ca message cu, mkstream tao stream neu chua co"""
    try:
        client.xgroup_create(
            settings.ticket_stream_name, settings.consumer_group, id="0", mkstream=True
        )
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def _decode(fields: dict) -> dict:
    return {k.decode(): v.decode() for k, v in fields.items()}


def process_entry(fields: dict) -> None:
    """Gui email truoc, ghi DB sau: crash giua 2 buoc chi gui trung, khong mat email"""
    data = _decode(fields)
    ticket_id = data["ticket_id"]

    db = database.SessionLocal()
    try:
        already_sent = crud.get_sent_notification(db, ticket_id) is not None
    finally:
        db.close()

    if already_sent:
        logger.info(
            "Ticket %s da gui notification roi, bo qua (duplicate delivery)",
            ticket_id,
        )
        return

    send_ticket_email(data["email"], data["full_name"], ticket_id, data["qr_code_path"])

    db = database.SessionLocal()
    try:
        try:
            crud.create_sent_notification(db, ticket_id, data["email"])
        except IntegrityError:
            db.rollback()
            logger.info(
                "Ticket %s da duoc lan xu ly khac ghi nhan, email co the trung",
                ticket_id,
            )
    finally:
        db.close()

    logger.info("Da gui email cho ticket %s (%s)", ticket_id, data["email"])


def touch_heartbeat() -> None:
    try:
        Path(settings.heartbeat_path).touch()
    except OSError:
        logger.warning("Khong ghi duoc heartbeat %s", settings.heartbeat_path)


def handle_entry(client: redis.Redis, entry_id: bytes, fields: dict) -> None:
    """Thanh cong -> XACK. Loi -> de pending, reclaim_stale se xu ly lai"""
    touch_heartbeat()
    try:
        process_entry(fields)
    except Exception:
        logger.exception(
            "Loi xu ly message %s, se reclaim sau %s ms",
            entry_id,
            settings.reclaim_min_idle_ms,
        )
        return
    client.xack(settings.ticket_stream_name, settings.consumer_group, entry_id)


def _times_delivered(client: redis.Redis, entry_id: bytes) -> int:
    rows = client.xpending_range(
        settings.ticket_stream_name,
        settings.consumer_group,
        min=entry_id,
        max=entry_id,
        count=1,
    )
    # fakeredis khong tra time delivered -> 0
    return rows[0].get("times_delivered", 0) if rows else 0


def dead_letter(
    client: redis.Redis, entry_id: bytes, fields: dict, deliveries: int
) -> None:
    """Chep sang stream dead letter roi XACK"""
    client.xadd(
        settings.dead_letter_stream_name,
        {
            **fields,
            b"original_id": entry_id,
            b"deliveries": str(deliveries).encode(),
        },
    )
    client.xack(settings.ticket_stream_name, settings.consumer_group, entry_id)
    logger.error(
        "Message %s that bai sau %d lan giao, da chuyen sang stream '%s'",
        entry_id,
        deliveries,
        settings.dead_letter_stream_name,
    )


def reclaim_stale(client: redis.Redis) -> int:
    """Lay lai message pending qua han (XAUTOCLAIM, toi da 100/luot) va xu ly lai.
    Qua max_deliveries lan giao thi chuyen sang dead-letter"""
    _next_id, entries = client.xautoclaim(
        settings.ticket_stream_name,
        settings.consumer_group,
        settings.consumer_name,
        min_idle_time=settings.reclaim_min_idle_ms,
        start_id="0-0",
        count=100,
    )[:2]
    for entry_id, fields in entries:
        deliveries = _times_delivered(client, entry_id)
        if deliveries > settings.max_deliveries:
            dead_letter(client, entry_id, fields, deliveries)
            continue
        logger.warning("Reclaim message %s (lan giao thu %d)", entry_id, deliveries)
        handle_entry(client, entry_id, fields)
    return len(entries)


def run(client: "redis.Redis | None" = None, max_iterations: int | None = None) -> None:
    """Vong lap chinh (max_iterations chi de test)"""
    database.Base.metadata.create_all(bind=database.engine)
    client = client or get_redis_client()
    ensure_consumer_group(client)
    logger.info(
        "Notification worker da san sang, dang lang nghe stream '%s' (group '%s')",
        settings.ticket_stream_name,
        settings.consumer_group,
    )

    last_reclaim = float("-inf")  # reclaim ngay khi khoi dong
    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        touch_heartbeat()
        if time.monotonic() - last_reclaim >= settings.reclaim_interval_seconds:
            reclaim_stale(client)
            last_reclaim = time.monotonic()

        response = client.xreadgroup(
            settings.consumer_group,
            settings.consumer_name,
            {settings.ticket_stream_name: ">"},
            count=10,
            block=settings.read_block_ms,
        )
        if response:
            for _stream_name, entries in response:
                for entry_id, fields in entries:
                    handle_entry(client, entry_id, fields)
        iterations += 1


if __name__ == "__main__":
    run()
