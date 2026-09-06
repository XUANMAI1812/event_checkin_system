# registration-service

FastAPI service cho Event Check-in System: tao event, dang ky nguoi tham du,
sinh & ky ve QR (JWT RS256).

## Chay local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/generate_keys.sh
cp .env.example .env   # sua DATABASE_URL cho dung
python -m scripts.init_db
uvicorn app.main:app --reload
```

## Test

```bash
pytest -v
```
