# notification-worker

Background worker cho Event Check-in System: consume su kien
"ticket_created" tu Redis Stream (do registration-service publish sau khi
dang ky thanh cong), gui email kem anh QR cho nguoi tham du.

## Chay local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # sua DATABASE_URL cho dung
python -m scripts.init_db
python -m app.consumer
```

## Test

```bash
pytest -v
```
