"""
PayPilot Global — Payroll API Routes
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Header, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import PayrollBatch, PayrollItem, User
from app.schemas import (
    PayrollBatchResponse, PayrollItemResponse, PayrollBatchDetailResponse,
    PaginatedResponse, PayrollApproveRequest,
)
from app.api.auth import get_employer_id, get_current_user
from app.services.payroll_service import (
    validate_and_create_batch, run_risk_scoring, approve_batch, simulate_disbursement,
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.post("/upload")
async def upload_payroll_csv(
    file: UploadFile = File(...),
    batch_name: Optional[str] = Form(None),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Upload a payroll CSV for validation and batch creation."""
    # Check file size
    content = await file.read()
    if len(content) > settings.csv_max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.csv_max_size_mb}MB limit.")

    csv_content = content.decode("utf-8")

    batch, errors = validate_and_create_batch(
        db=db,
        employer_id=employer_id,
        csv_content=csv_content,
        batch_name=batch_name,
    )

    if batch is None:
        raise HTTPException(status_code=422, detail={"errors": errors})

    return {
        "batch": PayrollBatchResponse.model_validate(batch),
        "validation_errors": errors,
    }


@router.get("/batches", response_model=PaginatedResponse)
def list_batches(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """List payroll batches with pagination."""
    query = db.query(PayrollBatch).filter(
        PayrollBatch.employer_id == employer_id,
    )
    total = query.count()
    total_pages = max(1, (total + limit - 1) // limit)
    items = query.order_by(PayrollBatch.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedResponse(
        items=[PayrollBatchResponse.model_validate(b) for b in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.get("/batches/{batch_id}", response_model=PayrollBatchDetailResponse)
def get_batch(
    batch_id: str,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Get batch detail with all items, currency totals, and risk summary."""
    batch = db.query(PayrollBatch).filter(
        PayrollBatch.id == batch_id,
        PayrollBatch.employer_id == employer_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == batch_id,
        PayrollItem.is_deleted == False,
    ).all()

    # Currency totals
    currency_totals = {}
    risk_summary = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    decision_summary = {"APPROVE": 0, "HOLD": 0, "REVIEW": 0, "REJECT": 0}

    for item in items:
        currency_totals[item.currency] = currency_totals.get(item.currency, 0) + item.amount
        if item.risk_level:
            risk_summary[item.risk_level] = risk_summary.get(item.risk_level, 0) + 1
        if item.decision:
            decision_summary[item.decision] = decision_summary.get(item.decision, 0) + 1

    item_responses = []
    for item in items:
        reasons = json.loads(item.risk_reasons) if item.risk_reasons else []
        validation_errors = json.loads(item.validation_errors) if item.validation_errors else []
        item_responses.append(PayrollItemResponse(
            id=item.id,
            batch_id=item.batch_id,
            employee_id=item.employee_id,
            employee_name=item.employee_name,
            employee_email=item.employee_email,
            country=item.country,
            currency=item.currency,
            amount=item.amount,
            department=item.department,
            role=item.role,
            payment_note=item.payment_note,
            risk_score=item.risk_score,
            risk_level=item.risk_level,
            risk_reasons=reasons,
            decision=item.decision,
            decision_reason=item.decision_reason,
            validation_errors=validation_errors,
            created_at=item.created_at,
        ))

    return PayrollBatchDetailResponse(
        batch=PayrollBatchResponse.model_validate(batch),
        items=item_responses,
        currency_totals=currency_totals,
        risk_summary=risk_summary,
        decision_summary=decision_summary,
    )


@router.post("/batches/{batch_id}/score-risk", response_model=PayrollBatchResponse)
def score_risk(
    batch_id: str,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Run risk scoring on a payroll batch."""
    try:
        batch = run_risk_scoring(db, employer_id, batch_id)
        return PayrollBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batches/{batch_id}/approve", response_model=PayrollBatchResponse)
def approve(
    batch_id: str,
    body: PayrollApproveRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a payroll batch with per-item decisions."""
    try:
        batch = approve_batch(
            db=db,
            employer_id=user.employer_id,
            user_id=user.id,
            batch_id=batch_id,
            item_decisions=body.item_decisions,
            override_reason=body.override_reason,
            idempotency_key=idempotency_key,
        )
        return PayrollBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/simulate-disbursement")
def simulate_disburse(
    batch_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Simulate payroll disbursement (demo mode only)."""
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Simulated disbursement is only available in demo mode.")

    try:
        result = simulate_disbursement(
            db=db,
            employer_id=employer_id,
            batch_id=batch_id,
            idempotency_key=idempotency_key,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
