from fastapi import FastAPI

from .routers import checkin

app = FastAPI(title="Event Check-in System - Checkin Service")

app.include_router(checkin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
