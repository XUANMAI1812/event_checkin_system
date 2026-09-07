import logging

import redis
from redis.exceptions import ResponseError
from sqlalchemy.exc import IntegrityError

from . import crud, database
from .config import settings
from .notifier import send_ticket_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("notification-worker")


def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url)


def ensure_consumer_group(client: redis.Redis) -> None:
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
                "Ticket %s vua duoc ghi nhan boi 1 lan xu ly khac dung luc "
                "(duplicate delivery) - email vua gui o tren co the la ban "
                "trung, chap nhan duoc voi at-least-once delivery.",
                ticket_id,
            )
    finally:
        db.close()

    logger.info("Da gui email cho ticket %s (%s)", ticket_id, data["email"])


def run(client: "redis.Redis | None" = None, max_iterations: int | None = None) -> None:
    database.Base.metadata.create_all(bind=database.engine)
    client = client or get_redis_client()
    ensure_consumer_group(client)
    logger.info(
        "Notification worker da san sang, dang lang nghe stream '%s' (group '%s')",
        settings.ticket_stream_name,
        settings.consumer_group,
    )

    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        response = client.xreadgroup(
            settings.consumer_group,
            settings.consumer_name,
            {settings.ticket_stream_name: ">"},
            count=10,
            block=5000,
        )
        if response:
            for _stream_name, entries in response:
                for entry_id, fields in entries:
                    try:
                        process_entry(fields)
                    except Exception:
                        logger.exception(
                            "Loi xu ly message %s, se retry lan sau", entry_id
                        )
                        continue
                    client.xack(
                        settings.ticket_stream_name, settings.consumer_group, entry_id
                    )
        iterations += 1


if __name__ == "__main__":
    run()
