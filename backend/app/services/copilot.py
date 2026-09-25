"""
PayPilot Global — Deterministic AI Payroll Copilot
Answers payroll operations questions using computed facts, not LLM hallucination.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import (
    Employee, PayrollBatch, PayrollItem, WalletBalance, WebhookEvent
)
from app.services.forecast_engine import compute_wallet_forecasts, compute_overall_runway_status
from app.services.risk_engine import CURRENCY_TO_WALLET


def answer_copilot_question(db: Session, employer_id: str, question: str) -> dict:
    """
    Deterministic copilot — computes facts from the database,
    then generates a structured answer with evidence and actions.
    """
    q = question.lower().strip()

    # Route to the appropriate handler
    if _matches(q, ["can we run payroll", "run payroll today", "payroll ready"]):
        return _answer_can_run_payroll(db, employer_id)
    elif _matches(q, ["who is not ready", "not ready", "stuck employees", "who's not ready"]):
        return _answer_who_not_ready(db, employer_id)
    elif _matches(q, ["high risk", "risky employees", "risk"]):
        return _answer_high_risk(db, employer_id)
    elif _matches(q, ["short", "shortfall", "wallet is short", "insufficient"]):
        return _answer_wallet_short(db, employer_id)
    elif _matches(q, ["summarize batch", "batch summary", "this payroll"]):
        return _answer_batch_summary(db, employer_id)
    elif _matches(q, ["draft reminder", "reminders for", "kyc reminder", "send reminder"]):
        return _answer_draft_reminders(db, employer_id)
    elif _matches(q, ["wallet balance", "balances", "how much"]):
        return _answer_wallet_balances(db, employer_id)
    elif _matches(q, ["webhook", "recent events", "events"]):
        return _answer_recent_events(db, employer_id)
    else:
        return _answer_default(db, employer_id, question)


def _matches(question: str, keywords: list[str]) -> bool:
    return any(kw in question for kw in keywords)


# ─── Individual Answer Generators ─────────────────────────────────────────────

def _answer_can_run_payroll(db: Session, employer_id: str) -> dict:
    forecasts = compute_wallet_forecasts(db, employer_id)
    stuck = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
        Employee.onboarding_status != "READY",
    ).count()

    latest_batch = db.query(PayrollBatch).filter(
        PayrollBatch.employer_id == employer_id
    ).order_by(PayrollBatch.created_at.desc()).first()

    high_risk = 0
    if latest_batch:
        high_risk = db.query(PayrollItem).filter(
            PayrollItem.batch_id == latest_batch.id,
            PayrollItem.risk_level == "HIGH",
            PayrollItem.is_deleted == False,
        ).count()

    shortfalls = [f for f in forecasts if f["status"] == "SHORTFALL"]
    currencies = [f["currency"] for f in forecasts if f["required"] > 0]
    ready_currencies = [f["currency"] for f in forecasts if f["status"] == "SUFFICIENT" and f["required"] > 0]

    # Build answer
    if not shortfalls and high_risk == 0 and stuck == 0:
        answer = "Yes, payroll can run. All wallets are funded, all employees are ready, and no high-risk items detected."
    elif shortfalls and high_risk > 0:
        answer = (
            f"Not yet. {', '.join(f['currency'] for f in shortfalls)} wallet(s) have shortfalls, "
            f"and {high_risk} high-risk payroll item(s) need attention. "
            f"Fix these before running payroll."
        )
    elif shortfalls:
        answer = (
            f"Partially. {', '.join(ready_currencies)} payroll can run, but "
            f"{', '.join(f['currency'] for f in shortfalls)} has a shortfall. "
            f"Top up the wallet before processing those payments."
        )
    elif high_risk > 0:
        answer = (
            f"Partially. Wallets are funded, but {high_risk} high-risk employee(s) "
            f"should be held for manual review before processing."
        )
    elif stuck > 0:
        answer = (
            f"Partially. {stuck} employee(s) are not yet payroll-ready. "
            f"Their payments will need to be skipped or held."
        )
    else:
        answer = "Yes, payroll can run. All conditions are met."

    evidence = []
    if shortfalls:
        for f in shortfalls:
            evidence.append(f"{f['currency']} wallet shortfall: {_fmt(f['shortfall'], f['currency'])}")
    if high_risk > 0:
        evidence.append(f"{high_risk} high-risk payroll item(s) detected")
    if stuck > 0:
        evidence.append(f"{stuck} employee(s) not payroll-ready")
    if ready_currencies:
        evidence.append(f"Ready currencies: {', '.join(ready_currencies)}")

    actions = []
    for f in shortfalls:
        actions.append(f"Top up {f['wallet_code']} wallet by {_fmt(f['shortfall'], f['currency'])}")
    if high_risk > 0:
        actions.append("Hold high-risk items for manual review")
    if stuck > 0:
        actions.append("Send onboarding reminders to stuck employees")
    if not actions:
        actions.append("Proceed with payroll approval")

    warnings = [
        "Do not mark payments complete until a verified webhook or confirmed BMONI response exists."
    ]
    if high_risk > 0:
        warnings.append("High-risk items require override reason before approval.")

    return {
        "answer": answer,
        "evidence": evidence,
        "actions": actions,
        "warnings": warnings,
    }


def _answer_who_not_ready(db: Session, employer_id: str) -> dict:
    stuck = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
        Employee.onboarding_status != "READY",
    ).all()

    if not stuck:
        return {
            "answer": "All employees are payroll-ready. No one is stuck.",
            "evidence": [f"{db.query(Employee).filter(Employee.employer_id == employer_id, Employee.is_active == True, Employee.deleted_at == None).count()} active employees, all READY"],
            "actions": [],
            "warnings": [],
        }

    names = [f"{e.full_name} ({e.onboarding_status})" for e in stuck]
    return {
        "answer": f"{len(stuck)} employee(s) are not yet ready for payroll.",
        "evidence": names,
        "actions": [f"Send reminder to {e.full_name}" for e in stuck[:3]],
        "warnings": ["Non-ready employees will be automatically held during payroll processing."],
    }


def _answer_high_risk(db: Session, employer_id: str) -> dict:
    latest_batch = db.query(PayrollBatch).filter(
        PayrollBatch.employer_id == employer_id
    ).order_by(PayrollBatch.created_at.desc()).first()

    if not latest_batch:
        return {
            "answer": "No payroll batch found. Upload a payroll CSV first.",
            "evidence": [],
            "actions": ["Upload payroll CSV"],
            "warnings": [],
        }

    high_risk_items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == latest_batch.id,
        PayrollItem.risk_level == "HIGH",
        PayrollItem.is_deleted == False,
    ).all()

    if not high_risk_items:
        return {
            "answer": "No high-risk payroll items detected. All items are LOW or MEDIUM risk.",
            "evidence": [f"Batch: {latest_batch.batch_name}"],
            "actions": [],
            "warnings": [],
        }

    items_info = []
    for item in high_risk_items:
        import json
        reasons = json.loads(item.risk_reasons) if item.risk_reasons else []
        items_info.append(f"{item.employee_name}: score {item.risk_score} — {'; '.join(reasons[:2])}")

    return {
        "answer": f"{len(high_risk_items)} high-risk payroll item(s) detected. These should be held for manual review.",
        "evidence": items_info,
        "actions": ["Hold high-risk items for manual review", "Investigate payout wallet changes"],
        "warnings": ["Do not approve high-risk items without an override reason."],
    }


def _answer_wallet_short(db: Session, employer_id: str) -> dict:
    forecasts = compute_wallet_forecasts(db, employer_id)
    shortfalls = [f for f in forecasts if f["status"] == "SHORTFALL"]

    if not shortfalls:
        return {
            "answer": "No wallet shortfalls. All wallets have sufficient balance for the current payroll.",
            "evidence": [f"{f['currency']}: {_fmt(f['surplus'], f['currency'])} surplus" for f in forecasts if f["required"] > 0],
            "actions": [],
            "warnings": [],
        }

    return {
        "answer": f"{len(shortfalls)} wallet(s) have shortfalls that will prevent payroll processing.",
        "evidence": [f"{f['currency']}: {_fmt(f['shortfall'], f['currency'])} short" for f in shortfalls],
        "actions": [f"Top up {f['wallet_code']} by {_fmt(f['shortfall'], f['currency'])}" for f in shortfalls],
        "warnings": ["Payments cannot be processed from underfunded wallets."],
    }


def _answer_batch_summary(db: Session, employer_id: str) -> dict:
    latest_batch = db.query(PayrollBatch).filter(
        PayrollBatch.employer_id == employer_id
    ).order_by(PayrollBatch.created_at.desc()).first()

    if not latest_batch:
        return {
            "answer": "No payroll batch found. Upload a CSV to create one.",
            "evidence": [],
            "actions": ["Upload payroll CSV"],
            "warnings": [],
        }

    items = db.query(PayrollItem).filter(
        PayrollItem.batch_id == latest_batch.id,
        PayrollItem.is_deleted == False,
    ).all()

    # Currency totals
    totals = {}
    for item in items:
        totals[item.currency] = totals.get(item.currency, 0) + item.amount

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for item in items:
        if item.risk_level:
            risk_counts[item.risk_level] = risk_counts.get(item.risk_level, 0) + 1

    evidence = [
        f"Batch: {latest_batch.batch_name}",
        f"Total items: {len(items)}",
        f"Safety score: {latest_batch.safety_score or 'Not calculated'} ({latest_batch.safety_label or 'N/A'})",
    ] + [f"{cur}: {totals[cur]:,.2f}" for cur in totals]

    return {
        "answer": (
            f"Batch '{latest_batch.batch_name}' has {len(items)} items across "
            f"{len(totals)} currencies. "
            f"Safety score: {latest_batch.safety_score or 'N/A'} ({latest_batch.safety_label or 'pending'}). "
            f"Risk breakdown: {risk_counts['LOW']} low, {risk_counts['MEDIUM']} medium, {risk_counts['HIGH']} high."
        ),
        "evidence": evidence,
        "actions": ["Review medium and high-risk items", "Approve or hold as needed"],
        "warnings": [],
    }


def _answer_draft_reminders(db: Session, employer_id: str) -> dict:
    stuck = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.is_active == True,
        Employee.deleted_at == None,
        Employee.onboarding_status.in_(["KYC_ACTION_REQUIRED", "KYC_PENDING", "LINKED", "INVITED"]),
    ).all()

    if not stuck:
        return {
            "answer": "No employees need KYC reminders at this time.",
            "evidence": [],
            "actions": [],
            "warnings": [],
        }

    reminders = []
    for emp in stuck:
        reminders.append(
            f"To: {emp.email}\n"
            f"Subject: Complete your salary wallet setup\n\n"
            f"Hi {emp.full_name.split()[0]},\n\n"
            f"Your salary wallet setup is in progress. Please open the BMONI app and "
            f"complete any pending verification steps so we can process your payroll.\n\n"
            f"Thank you!"
        )

    return {
        "answer": f"Drafted {len(stuck)} reminder(s) for employees stuck in onboarding/KYC.",
        "evidence": [f"{e.full_name}: {e.onboarding_status}" for e in stuck],
        "actions": [f"Send reminder to {e.email}" for e in stuck],
        "warnings": ["Review reminders before sending — messages are templates."],
    }


def _answer_wallet_balances(db: Session, employer_id: str) -> dict:
    balances = db.query(WalletBalance).filter(
        WalletBalance.employer_id == employer_id
    ).all()

    if not balances:
        return {
            "answer": "No wallet balances found. Wallets may not be provisioned yet.",
            "evidence": [],
            "actions": ["Check BMONI wallet provisioning status"],
            "warnings": [],
        }

    evidence = [f"{b.wallet_code} ({b.currency}): {_fmt(b.balance, b.currency)}" for b in balances]
    return {
        "answer": f"You have {len(balances)} wallet(s) with balances.",
        "evidence": evidence,
        "actions": [],
        "warnings": [],
    }


def _answer_recent_events(db: Session, employer_id: str) -> dict:
    events = db.query(WebhookEvent).filter(
        WebhookEvent.employer_id == employer_id,
    ).order_by(WebhookEvent.created_at.desc()).limit(5).all()

    if not events:
        return {
            "answer": "No recent webhook events.",
            "evidence": [],
            "actions": ["Simulate a webhook event to test the integration"],
            "warnings": [],
        }

    evidence = [
        f"{e.event_type} — {e.state} — {e.created_at.strftime('%Y-%m-%d %H:%M')}"
        for e in events
    ]
    return {
        "answer": f"{len(events)} recent webhook event(s) received.",
        "evidence": evidence,
        "actions": [],
        "warnings": [],
    }


def _answer_default(db: Session, employer_id: str, question: str) -> dict:
    return {
        "answer": (
            "I can help with payroll operations questions. Try asking:\n"
            "• 'Can we run payroll today?'\n"
            "• 'Who is not ready?'\n"
            "• 'Which employees are high risk?'\n"
            "• 'Which currency wallet is short?'\n"
            "• 'Summarize this payroll batch.'\n"
            "• 'Draft reminders for employees stuck in KYC.'"
        ),
        "evidence": [],
        "actions": [],
        "warnings": [],
    }


def _fmt(amount: float, currency: str) -> str:
    symbols = {"NGN": "₦", "USD": "$", "EUR": "€", "CAD": "C$", "MXN": "MX$", "GBP": "£"}
    symbol = symbols.get(currency, "")
    return f"{symbol}{amount:,.2f}"
