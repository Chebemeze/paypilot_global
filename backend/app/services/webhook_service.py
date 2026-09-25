"""
PayPilot Global — Webhook Service
Handles webhook receipt, verification, deduplication, and async processing.
"""
from __future__ import annotations

import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import WebhookEvent, Employee


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature against the configured webhook secret.
    Uses constant-time comparison.
    """
    secret = settings.bmoni_webhook_secret.encode("utf-8")
    expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def process_incoming_webhook(
    db: Session,
    raw_body: bytes,
    signature: str,
    event_id: str,
    source_event_id: Optional[str],
) -> WebhookEvent:
    """
    Process an incoming webhook:
    1. Verify signature
    2. Deduplicate by source_event_id
    3. Persist event
    4. Return the event (processing happens in background)
    """
    # Verify signature
    sig_valid = verify_webhook_signature(raw_body, signature)
    if not sig_valid:
        # Still persist the event but mark as invalid
        event = WebhookEvent(
            event_id=event_id,
            source_event_id=source_event_id,
            event_type="unknown",
            payload=raw_body.decode("utf-8", errors="replace"),
            signature_valid=False,
            state="RECEIVED",
            processed=False,
            error_message="Invalid webhook signature — event rejected.",
        )
        db.add(event)
        db.commit()
        return event

    # Parse payload
    payload = json.loads(raw_body)
    event_type = payload.get("eventType", "unknown")

    # Deduplicate
    if source_event_id:
        existing = db.query(WebhookEvent).filter(
            WebhookEvent.source_event_id == source_event_id
        ).first()
        if existing:
            existing.state = "DUPLICATE_IGNORED"
            db.commit()
            return existing

    # Create event
    event = WebhookEvent(
        employer_id=settings.demo_employer_id,
        event_id=event_id,
        source_event_id=source_event_id,
        event_type=event_type,
        payload=raw_body.decode("utf-8"),
        signature_valid=True,
        state="VERIFIED",
        processed=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Process event asynchronously (in demo mode, do it inline)
    _process_event(db, event, payload)

    return event


def _process_event(db: Session, event: WebhookEvent, payload: dict) -> None:
    """Process a verified webhook event and update employee state."""
    try:
        event.state = "QUEUED"
        db.commit()

        event_type = event.event_type
        event_payload = payload.get("payload", {})

        if event_type == "employee.linked":
            _handle_employee_linked(db, event_payload)
        elif event_type == "onboarding.completed":
            _handle_onboarding_completed(db, event_payload)
        elif event_type == "onboarding.failed":
            _handle_onboarding_failed(db, event_payload)
        elif event_type == "kyc.action_required":
            _handle_kyc_action_required(db, event_payload)
        elif event_type == "employee.deposit.completed":
            _handle_deposit_completed(db, event_payload)
        elif event_type == "employee.withdrawal.completed":
            _handle_withdrawal_completed(db, event_payload)
        else:
            # Unknown event type — still mark as processed
            pass

        event.state = "PROCESSED"
        event.processed = True
        db.commit()

    except Exception as e:
        event.state = "FAILED"
        event.error_message = str(e)
        db.commit()


def _handle_employee_linked(db: Session, payload: dict) -> None:
    user_id = payload.get("userId")
    if user_id:
        emp = db.query(Employee).filter(
            Employee.bmoni_user_id == user_id,
            Employee.employer_id == settings.demo_employer_id,
        ).first()
        if emp and emp.onboarding_status == "INVITED":
            emp.onboarding_status = "LINKED"
            db.commit()


def _handle_onboarding_completed(db: Session, payload: dict) -> None:
    user_id = payload.get("userId")
    if user_id:
        emp = db.query(Employee).filter(
            Employee.bmoni_user_id == user_id,
            Employee.employer_id == settings.demo_employer_id,
        ).first()
        if emp:
            emp.onboarding_status = "READY"
            emp.wallet_status = "active"
            db.commit()


def _handle_onboarding_failed(db: Session, payload: dict) -> None:
    user_id = payload.get("userId")
    reason = payload.get("reason", "unknown")
    if user_id:
        emp = db.query(Employee).filter(
            Employee.bmoni_user_id == user_id,
            Employee.employer_id == settings.demo_employer_id,
        ).first()
        if emp:
            emp.onboarding_status = "KYC_ACTION_REQUIRED"
            emp.kyc_status = reason
            db.commit()


def _handle_kyc_action_required(db: Session, payload: dict) -> None:
    user_id = payload.get("userId")
    reason = payload.get("reason", "unknown")
    if user_id:
        emp = db.query(Employee).filter(
            Employee.bmoni_user_id == user_id,
            Employee.employer_id == settings.demo_employer_id,
        ).first()
        if emp:
            emp.onboarding_status = "KYC_ACTION_REQUIRED"
            emp.kyc_status = reason
            db.commit()


def _handle_deposit_completed(db: Session, payload: dict) -> None:
    # In production, update wallet balance
    pass


def _handle_withdrawal_completed(db: Session, payload: dict) -> None:
    # In production, update wallet balance
    pass
