import os

import fakeredis
import pytest
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database, models
from app.config import settings

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    return TestingSessionLocal()


@pytest.fixture
def fake_redis_client():
    url = os.environ.get("TEST_REDIS_URL")
    if url:
        client = redis.from_url(url)
        client.flushdb()
        yield client
        client.flushdb()
        client.close()
    else:
        yield fakeredis.FakeStrictRedis()


@pytest.fixture(autouse=True)
def fast_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "heartbeat_path", str(tmp_path / "heartbeat"))
    monkeypatch.setattr(settings, "read_block_ms", 10)
