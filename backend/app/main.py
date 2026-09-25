"""
PayPilot Global — FastAPI Application Entry Point
"""
from __future__ import annotations

import time
import uuid
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api.errors import register_exception_handlers
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.dashboard_routes import router as dashboard_router
from app.api.v1.employee_routes import router as employee_router
from app.api.v1.payroll_routes import router as payroll_router
from app.api.v1.forecast_routes import router as forecast_router
from app.api.v1.copilot_routes import router as copilot_router
from app.api.v1.webhook_routes import router as webhook_router
from app.api.v1.card_routes import router as card_router

# ─── Create tables ────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PayPilot Global",
    description="AI payroll operations for borderless teams using BMONI Embedded.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request ID + Logging middleware ──────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    # Stash it on request.state so exception handlers (app/api/errors.py) can
    # echo the same id back inside the error body, not just the header.
    request.state.request_id = request_id
    start = time.time()
    response: Response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response


# ─── Error handlers ───────────────────────────────────────────────────────────
# Owner: Person 1. Collapses HTTPException / validation errors / DB errors /
# unhandled crashes into one JSON envelope. See app/api/errors.py.
register_exception_handlers(app)


# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(employee_router, prefix="/api/v1")
app.include_router(payroll_router, prefix="/api/v1")
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api/v1")
app.include_router(card_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
# Note: The /webhooks/bmoni endpoint is at /api/v1/webhooks/bmoni


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy", "service": "paypilot-global"}


@app.get("/")
def root():
    return {
        "service": "PayPilot Global",
        "version": "1.0.0",
        "description": "AI payroll operations for borderless teams using BMONI Embedded.",
        "docs": "/docs",
    }
