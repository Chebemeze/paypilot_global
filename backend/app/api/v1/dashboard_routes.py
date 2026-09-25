"""
PayPilot Global — Dashboard API Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee, PayrollBatch, PayrollItem, WalletBalance, WebhookEvent
from app.schemas import DashboardSummary, WalletBalanceResponse, ForecastItem, WebhookEventResponse
from app.api.auth import get_employer_id
from app.services.forecast_engine import compute_wallet_forecasts

import json

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """
    Return the full dashboard summary: employee counts, risk items,
    wallet balances, forecasts, and recent webhook events.
    """
    # Employee counts
    active_employees = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
    )
    total_employees = active_employees.count()
    ready_employees = active_employees.filter(Employee.onboarding_status == "READY").count()
    stuck_employees = total_employees - ready_employees

    # Latest batch info
    latest_batch = db.query(PayrollBatch).filter(
        PayrollBatch.employer_id == employer_id,
    ).order_by(PayrollBatch.created_at.desc()).first()

    high_risk_items = 0
    safety_score = None
    safety_label = None
    if latest_batch:
        high_risk_items = db.query(PayrollItem).filter(
            PayrollItem.batch_id == latest_batch.id,
            PayrollItem.risk_level == "HIGH",
            PayrollItem.is_deleted == False,
        ).count()
        safety_score = latest_batch.safety_score
        safety_label = latest_batch.safety_label

    # Payroll totals by currency (from latest batch)
    payroll_totals = {}
    if latest_batch:
        items = db.query(PayrollItem).filter(
            PayrollItem.batch_id == latest_batch.id,
            PayrollItem.is_deleted == False,
        ).all()
        for item in items:
            payroll_totals[item.currency] = payroll_totals.get(item.currency, 0) + item.amount

    # Wallet balances
    balances = db.query(WalletBalance).filter(
        WalletBalance.employer_id == employer_id,
    ).all()
    wallet_balances = [WalletBalanceResponse.model_validate(b) for b in balances]

    # Forecasts
    forecasts_raw = compute_wallet_forecasts(db, employer_id)
    forecast_shortfalls = [
        ForecastItem(**f) for f in forecasts_raw if f["status"] == "SHORTFALL"
    ]

    # Recent webhook events
    recent_events = db.query(WebhookEvent).filter(
        WebhookEvent.employer_id == employer_id,
    ).order_by(WebhookEvent.created_at.desc()).limit(10).all()

    recent_webhooks = []
    for e in recent_events:
        try:
            payload = json.loads(e.payload) if isinstance(e.payload, str) else e.payload
        except (json.JSONDecodeError, TypeError):
            payload = {}
        recent_webhooks.append(WebhookEventResponse(
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

    return DashboardSummary(
        total_employees=total_employees,
        ready_employees=ready_employees,
        stuck_employees=stuck_employees,
        high_risk_items=high_risk_items,
        safety_score=safety_score,
        safety_label=safety_label,
        payroll_totals_by_currency=payroll_totals,
        wallet_balances=wallet_balances,
        forecast_shortfalls=forecast_shortfalls,
        recent_webhooks=recent_webhooks,
    )
