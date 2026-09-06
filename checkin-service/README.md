# checkin-service

FastAPI service cho Event Check-in System: verify ve JWT khi quet
QR, danh dau check-in, chan quet trung.

## Chay local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # sua DATABASE_URL cho dung
cp /path/to/registration-service/keys/public_key.pem keys/public_key.pem
python -m scripts.init_db
uvicorn app.main:app --port 8001 --reload
```

## Test

```bash
pytest -v
```
