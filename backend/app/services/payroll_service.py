"""
PayPilot Global — Payroll Service
Handles CSV upload, validation, batch creation, approval, and simulated disbursement.
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PayrollBatch, PayrollItem, Employee, AuditLog, IdempotencyKey
from app.services.risk_engine import (
    score_payroll_items, calculate_batch_safety_score,
    SUPPORTED_CURRENCIES, CURRENCY_TO_WALLET
)
from app.services.forecast_engine import compute_wallet_forecasts


# ─── CSV Validation ───────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {"employee_name", "email", "country", "currency", "amount"}
OPTIONAL_COLUMNS = {"department", "role", "payment_note"}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


def validate_and_create_batch(
    db: Session,
    employer_id: str,
    csv_content: str,
    batch_name: Optional[str] = None,
) -> Tuple[PayrollBatch, List[str]]:
    """
    Parse CSV, validate rows, create batch and items.
    Returns (batch, errors).
    """
    errors = []
    rows = []

    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_content))

    # Check required columns
    if reader.fieldnames:
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            return None, [f"Missing required columns: {', '.join(missing)}"]

    # Read rows with streaming limit
    row_count = 0
    for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
        row_count += 1
        if row_count > settings.csv_max_rows:
            errors.append(f"CSV exceeds maximum of {settings.csv_max_rows} rows.")
            break

        row_errors = _validate_row(row, row_num)
        if row_errors:
            errors.extend(row_errors)
        else:
            rows.append(row)

    if not rows and errors:
        return None, errors

    # Create batch
    if not batch_name:
        batch_name = f"Payroll {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

    batch = PayrollBatch(
        employer_id=employer_id,
        batch_name=batch_name,
        status="VALIDATING",
        total_items=len(rows),
    )
    db.add(batch)
    db.flush()

    # Load existing employees for this employer
    existing_employees = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
    ).all()
    employees_map = {e.email: e for e in existing_employees}

    # Create payroll items
    for row in rows:
        email = row["email"].strip().lower()
        employee = employees_map.get(email)

        item = PayrollItem(
            batch_id=batch.id,
            employer_id=employer_id,
            employee_id=employee.id if employee else None,
            employee_name=row["employee_name"].strip(),
            employee_email=email,
            country=row["country"].strip(),
            currency=row["currency"].strip().upper(),
            amount=float(row["amount"]),
            department=row.get("department", "").strip() or None,
            role=row.get("role", "").strip() or None,
            payment_note=row.get("payment_note", "").strip() or None,
        )
        db.add(item)

    batch.status = "VALIDATED"
    db.commit()
    db.refresh(batch)

    return batch, errors


def _validate_row(row: dict, row_num: int) -> List[str]:
    """Validate a single CSV row."""
    errors = []

    # Required fields
    if not row.get("employee_name", "").strip():
        errors.append(f"Row {row_num}: employee_name is required.")
    if not row.get("email", "").strip():
        errors.append(f"Row {row_num}: email is required.")
    if not row.get("country", "").strip():
        errors.append(f"Row {row_num}: country is required.")
    if not row.get("currency", "").strip():
        errors.append(f"Row {row_num}: currency is required.")

    # Email format (basic)
    email = row.get("email", "").strip()
    if email and "@" not in email:
        errors.append(f"Row {row_num}: Invalid email format '{email}'.")

    # Currency check
    currency = row.get("currency", "").strip().upper()
    if currency and currency not in SUPPORTED_CURRENCIES:
        errors.append(
            f"Row {row_num}: Unsupported currency '{currency}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
        )

    # Amount check
    try:
        amount = float(row.get("amount", 0))
        if amount <= 0:
            errors.append(f"Row {row_num}: Amount must be positive, got {amount}.")
    except (ValueError, TypeError):
        errors.append(f"Row {row_num}: Invalid amount '{row.get('amount')}'.")

    return errors


# ─── Risk Scoring ─────────────────────────────────────────────────────────────

def run_risk_scoring(db: Session, employer_id: str, batch_id: str) -> PayrollBatch:
    """Score all items in a batch for risk."""
    batch = db.query(PayrollBatch).filter(
        PayrollBatch.id == batch_id,
        PayrollBatch.employer_id == employer_id,
    ).first()
    if not batch:
        raise ValueError("Batch not found")

    batch.status = "RISK_SCORING"
    db.commit()

    items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == batch_id,
        PayrollItem.is_deleted == False,
    ).all()

    employees = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
    ).all()

    # Score items
    scored_items = score_payroll_items(items, employees)

    # Compute batch safety score
    forecasts = compute_wallet_forecasts(db, employer_id, batch_id)
    safety_score, safety_label = calculate_batch_safety_score(scored_items, employees, forecasts)

    batch.safety_score = safety_score
    batch.safety_label = safety_label
    batch.status = "READY_FOR_REVIEW"

    # Calculate totals
    total_usd = 0.0
    for item in scored_items:
        # Rough USD conversion for display
        rate = {"NGN": 0.00065, "USD": 1.0, "EUR": 1.08, "CAD": 0.74, "MXN": 0.058, "GBP": 1.27}
        usd_amount = item.amount * rate.get(item.currency, 1.0)
        total_usd += usd_amount

    batch.total_amount_usd = round(total_usd, 2)
    db.commit()
    db.refresh(batch)

    return batch


# ─── Approval ─────────────────────────────────────────────────────────────────

def approve_batch(
    db: Session,
    employer_id: str,
    user_id: str,
    batch_id: str,
    item_decisions: dict,
    override_reason: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> PayrollBatch:
    """
    Approve a payroll batch with per-item decisions.
    Uses idempotency key to prevent duplicate approvals.
    """
    # Check idempotency
    if idempotency_key:
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.employer_id == employer_id,
            IdempotencyKey.key == idempotency_key,
        ).first()
        if existing:
            return db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()

    batch = db.query(PayrollBatch).filter(
        PayrollBatch.id == batch_id,
        PayrollBatch.employer_id == employer_id,
    ).first()
    if not batch:
        raise ValueError("Batch not found")

    # Apply item decisions
    items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == batch_id,
        PayrollItem.is_deleted == False,
    ).all()

    for item in items:
        if item.id in item_decisions:
            new_decision = item_decisions[item.id]
            if new_decision in ("APPROVE", "HOLD", "REVIEW", "REJECT"):
                old_decision = item.decision
                item.decision = new_decision
                if new_decision != old_decision:
                    # Log the override
                    audit = AuditLog(
                        employer_id=employer_id,
                        user_id=user_id,
                        action="ITEM_DECISION_OVERRIDE",
                        resource_type="payroll_item",
                        resource_id=item.id,
                        details=json.dumps({
                            "old_decision": old_decision,
                            "new_decision": new_decision,
                            "override_reason": override_reason,
                        }),
                    )
                    db.add(audit)

    # Check for high-risk approvals that need override reason
    high_risk_approved = [
        i for i in items
        if i.risk_level == "HIGH" and i.decision == "APPROVE"
    ]
    if high_risk_approved and not override_reason:
        raise ValueError(
            "High-risk items are being approved. An override reason is required."
        )

    batch.status = "APPROVED"
    batch.approved_by = user_id
    batch.approved_at = datetime.now(timezone.utc)

    # Log approval
    audit = AuditLog(
        employer_id=employer_id,
        user_id=user_id,
        action="BATCH_APPROVED",
        resource_type="payroll_batch",
        resource_id=batch_id,
        details=json.dumps({
            "safety_score": batch.safety_score,
            "total_items": batch.total_items,
            "override_reason": override_reason,
        }),
    )
    db.add(audit)

    # Record idempotency key
    if idempotency_key:
        idem = IdempotencyKey(
            employer_id=employer_id,
            key=idempotency_key,
            endpoint=f"POST /api/v1/payroll/batches/{batch_id}/approve",
            response_code=200,
        )
        db.add(idem)

    db.commit()
    db.refresh(batch)
    return batch


# ─── Simulated Disbursement ───────────────────────────────────────────────────

def simulate_disbursement(
    db: Session,
    employer_id: str,
    batch_id: str,
    idempotency_key: Optional[str] = None,
) -> dict:
    """
    Simulate sending approved payroll items.
    In demo mode, marks items as completed without calling BMONI.
    """
    # Check idempotency
    if idempotency_key:
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.employer_id == employer_id,
            IdempotencyKey.key == idempotency_key,
        ).first()
        if existing:
            return {"status": "already_processed", "batch_id": batch_id}

    batch = db.query(PayrollBatch).filter(
        PayrollBatch.id == batch_id,
        PayrollBatch.employer_id == employer_id,
    ).first()
    if not batch:
        raise ValueError("Batch not found")

    if batch.status != "APPROVED":
        raise ValueError(f"Batch must be APPROVED to disburse. Current status: {batch.status}")

    batch.status = "PROCESSING"
    db.commit()

    items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == batch_id,
        PayrollItem.decision == "APPROVE",
        PayrollItem.is_deleted == False,
    ).all()

    processed = 0
    failed = 0
    for item in items:
        # Simulate: in production, would call BMONI create_transfer_or_payment_proposal
        processed += 1

    batch.status = "COMPLETED"

    # Record idempotency key
    if idempotency_key:
        idem = IdempotencyKey(
            employer_id=employer_id,
            key=idempotency_key,
            endpoint=f"POST /api/v1/payroll/batches/{batch_id}/simulate-disbursement",
            response_code=200,
        )
        db.add(idem)

    db.commit()

    return {
        "status": "completed",
        "batch_id": batch_id,
        "processed": processed,
        "failed": failed,
        "total": len(items),
    }
