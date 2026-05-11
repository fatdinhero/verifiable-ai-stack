import os, threading
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import httpx

import poisv.incident_log as _il
from poisv.incident_routes import router
from db import init_db, load_all, save_incident, delete_incident

API_KEY     = os.environ.get("POISV_API_KEY", "")
NTFY_TOPIC  = os.environ.get("POISV_NTFY_TOPIC", "")
WEBHOOK_URL = os.environ.get("POISV_WEBHOOK_URL", "")

_rate_lock = threading.Lock()
_request_counts: dict = defaultdict(list)
RATE_LIMIT = 60

def _notify_high(record):
    def _send():
        try:
            if NTFY_TOPIC:
                httpx.post(
                    f"https://ntfy.sh/{NTFY_TOPIC}",
                    content=f"Incident {record.incident_id[:16]} | claim={record.claim_id} | scon={record.scon}",
                    headers={"Title": "PoISV HIGH Incident", "Priority": "urgent", "Tags": "warning"},
                    timeout=5,
                )
            if WEBHOOK_URL:
                httpx.post(WEBHOOK_URL, json=record.model_dump(), timeout=5)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

_orig_create = _il.create_incident

def _patched_create(data):
    record = _orig_create(data)
    save_incident(record)
    if record.severity.value == "HIGH":
        _notify_high(record)
    return record

_il.create_incident = _patched_create

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _il._incident_store.update(load_all())
    yield

app = FastAPI(
    title="PoISV Incident Log API",
    description="EU AI Act Art.12/19 compliant incident logging for AI systems",
    version="1.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

OPEN_PATHS = {"/docs", "/redoc", "/openapi.json", "/metrics", "/health"}

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    path = request.url.path
    if path not in OPEN_PATHS:
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        ip = request.client.host
        now = datetime.now(timezone.utc).timestamp()
        with _rate_lock:
            _request_counts[ip] = [t for t in _request_counts[ip] if now - t < 60]
            if len(_request_counts[ip]) >= RATE_LIMIT:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded: 60 req/min"})
            _request_counts[ip].append(now)
    return await call_next(request)

@app.get("/health", include_in_schema=False)
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incidents": len(_il._incident_store),
    }

app.include_router(router, prefix="/v1")

admin = APIRouter(prefix="/v1/admin", tags=["Admin"])

@admin.delete("/incidents/{incident_id}", summary="Delete a single incident")
def admin_delete_incident(incident_id: str):
    if incident_id not in _il._incident_store:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    del _il._incident_store[incident_id]
    delete_incident(incident_id)
    return {"deleted": incident_id}

@admin.delete("/incidents", summary="Delete ALL incidents")
def admin_delete_all():
    import sqlite3
    count = len(_il._incident_store)
    _il._incident_store.clear()
    con = sqlite3.connect("/opt/poisv/data/incidents.db")
    con.execute("DELETE FROM incidents"); con.commit(); con.close()
    return {"deleted_count": count}

app.include_router(admin)