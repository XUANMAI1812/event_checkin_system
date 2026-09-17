import fakeredis
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import events
from app.config import settings
from app.database import Base, get_db
from app.main import app

# Test dung SQLite in-memory, tach biet hoan toan khoi DB that (Postgres).
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def test_keys(tmp_path, monkeypatch):
    """Sinh cap khoa RSA tam cho moi test - khong phu thuoc
    keys/private_key.pem that (nam trong .gitignore, CI khong co san)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_key_path = tmp_path / "private_key.pem"
    public_key_path = tmp_path / "public_key.pem"
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)
    monkeypatch.setattr(settings, "jwt_private_key_path", str(private_key_path))
    monkeypatch.setattr(settings, "jwt_public_key_path", str(public_key_path))


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    """Thay redis client that (app/events.py) bang fakeredis (in-memory) khi
    chay test - tranh yeu cau Redis that phai dang chay o may chay test/CI."""
    client = fakeredis.FakeStrictRedis()
    monkeypatch.setattr(events, "_redis_client", client)
    return client


@pytest.fixture
def client():
    return TestClient(app)
