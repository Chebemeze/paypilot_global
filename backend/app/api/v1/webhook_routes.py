"""
PayPilot Global — Webhook API Routes
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import WebhookEvent
from app.schemas import WebhookEventResponse, WebhookSimulateRequest, PaginatedResponse
from app.api.auth import get_employer_id
from app.services.webhook_service import process_incoming_webhook, verify_webhook_signature
from app.services.bmoni_client import sign_webhook_payload

router = APIRouter(tags=["Webhooks"])


@router.post("/webhooks/bmoni")
async def receive_webhook(
    request: Request,
    x_webhook_signature: str = Header(default="", alias="X-Webhook-Signature"),
    x_webhook_id: str = Header(default="", alias="X-Webhook-Id"),
    x_source_event_id: str = Header(default="", alias="X-Source-Event-Id"),
    db: Session = Depends(get_db),
):
    """
    Receive and verify a BMONI webhook event.
    Returns 401 for invalid signatures.
    """
    raw_body = await request.body()

    if not x_webhook_signature:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Signature header.")

    # Verify signature
    sig_valid = verify_webhook_signature(raw_body, x_webhook_signature)
    if not sig_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    # Process the event
    event = process_incoming_webhook(
        db=db,
        raw_body=raw_body,
        signature=x_webhook_signature,
        event_id=x_webhook_id or str(uuid.uuid4()),
        source_event_id=x_source_event_id or None,
    )

    return {"received": True, "event_id": event.id, "state": event.state}


@router.post("/webhooks/simulate")
def simulate_webhook(
    req: WebhookSimulateRequest,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """
    Simulate a BMONI webhook event for demo/testing purposes.
    Signs the payload with the demo webhook secret.
    """
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Webhook simulation only available in demo mode.")

    # Build event payload
    event_payload = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "eventType": req.event_type,
        "payload": req.payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Create raw body and sign it consistently
    raw_body = json.dumps(event_payload, sort_keys=True).encode("utf-8")
    signature = sign_webhook_payload(event_payload, settings.bmoni_webhook_secret)
    event = process_incoming_webhook(
        db=db,
        raw_body=raw_body,
        signature=signature,
        event_id=event_payload["id"],
        source_event_id=event_payload["id"],
    )

    return {
        "status": "simulated",
        "event_id": event.id,
        "event_type": req.event_type,
        "state": event.state,
        "signature": signature,
    }


@router.get("/webhooks/events", response_model=PaginatedResponse)
def list_webhook_events(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """List webhook events with pagination."""
    query = db.query(WebhookEvent).filter(
        WebhookEvent.employer_id == employer_id,
    )
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    items = query.order_by(WebhookEvent.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    events = []
    for e in items:
        try:
            payload = json.loads(e.payload) if isinstance(e.payload, str) else e.payload
        except (json.JSONDecodeError, TypeError):
            payload = {}
        events.append(WebhookEventResponse(
            id=e.id,
            event_id=e.event_id,
            source_event_id=e.source_event_id,
            event_type=e.event_type,
            payload=payload,
            signature_valid=e.signature_valid,
            state=e.state,
            processed=e.processed,
            error_message=e.error_message,
            created_at=e.created_at,
        ))

    return PaginatedResponse(
        items=events,
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )
