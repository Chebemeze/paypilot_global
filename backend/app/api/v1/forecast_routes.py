"""
PayPilot Global — Forecast API Routes
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PayrollRunwayResponse, ForecastItem
from app.api.auth import get_employer_id
from app.services.forecast_engine import compute_wallet_forecasts, compute_overall_runway_status

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/payroll-runway", response_model=PayrollRunwayResponse)
def payroll_runway(
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Compute wallet funding forecast across all currencies."""
    forecasts_raw = compute_wallet_forecasts(db, employer_id)
    forecasts = [ForecastItem(**f) for f in forecasts_raw]
    overall = compute_overall_runway_status(forecasts_raw)

    return PayrollRunwayResponse(
        forecasts=forecasts,
        overall_status=overall,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/batch/{batch_id}", response_model=PayrollRunwayResponse)
def batch_forecast(
    batch_id: str,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Compute wallet funding forecast for a specific batch."""
    forecasts_raw = compute_wallet_forecasts(db, employer_id, batch_id=batch_id)
    forecasts = [ForecastItem(**f) for f in forecasts_raw]
    overall = compute_overall_runway_status(forecasts_raw)

    return PayrollRunwayResponse(
        forecasts=forecasts,
        overall_status=overall,
        generated_at=datetime.now(timezone.utc),
    )
