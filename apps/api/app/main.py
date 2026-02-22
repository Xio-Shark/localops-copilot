from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.routes import plans, projects, runs, search
from app.api.v1.ws import runs_ws

app = FastAPI(title="LocalOps Copilot API", version="0.1.0")

app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(runs.router)
app.include_router(search.router)
app.include_router(runs_ws.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
