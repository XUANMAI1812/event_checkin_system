from fastapi import FastAPI

from .routers import events, registrations

app = FastAPI(title="Event Check-in System - Registration Service")

app.include_router(events.router)
app.include_router(registrations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
