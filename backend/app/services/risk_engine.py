"""
PayPilot Global — Payroll Risk Engine
Scores individual payroll items and batches for fraud/operational risk.
Uses O(n) duplicate detection with hash maps.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from collections import Counter

from app.models import PayrollItem, Employee


# ─── Currency mapping ─────────────────────────────────────────────────────────

CURRENCY_TO_WALLET = {
    "NGN": "CNGN",
    "USD": "USDB",
    "EUR": "EURe",
    "CAD": "CADC",
    "MXN": "MEXe",
    "GBP": "GBPe",
}

SUPPORTED_CURRENCIES = set(CURRENCY_TO_WALLET.keys())


# ─── Risk Signals ─────────────────────────────────────────────────────────────

def _check_salary_explosion(item: PayrollItem, employee: Optional[Employee]) -> Optional[str]:
    """Salary amount exceeds expected salary by more than 50%."""
    if employee and employee.expected_salary and employee.expected_salary > 0:
        if item.amount > employee.expected_salary * 1.5:
            pct = int((item.amount / employee.expected_salary) * 100)
            return f"Salary is {pct}% of expected salary (>{150}% threshold)."
    return None


def _check_wallet_changed_recently(employee: Optional[Employee]) -> Optional[str]:
    """Payout wallet changed within the last 24 hours."""
    if employee and employee.payout_wallet_last_changed:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        if employee.payout_wallet_last_changed.replace(tzinfo=timezone.utc) > cutoff:
            return "Payout wallet changed within the last 24 hours."
    return None


def _check_duplicate_destinations(
    items: List[PayrollItem],
) -> Dict[str, List[str]]:
    """Same destination appears for multiple employees — O(n) with Counter."""
    email_counter: Counter = Counter()
    email_to_names: Dict[str, List[str]] = {}
    for item in items:
        email_counter[item.employee_email] += 1
        email_to_names.setdefault(item.employee_email, []).append(item.employee_name)

    duplicates = {}
    for email, count in email_counter.items():
        if count > 1:
            names = email_to_names[email]
            duplicates[email] = [
                f"Duplicate email '{email}' appears {count} times in batch "
                f"(employees: {', '.join(names)})."
            ]
    return duplicates


def _check_duplicate_payout_address(
    items: List[PayrollItem], employees_map: Dict[str, Optional[Employee]]
) -> Dict[str, List[str]]:
    """Same payout wallet address for different employees."""
    address_to_emails: Dict[str, List[str]] = {}
    for item in items:
        emp = employees_map.get(item.employee_email)
        if emp and emp.payout_wallet_address:
            addr = emp.payout_wallet_address
            address_to_emails.setdefault(addr, []).append(item.employee_email)

    duplicates = {}
    for addr, emails in address_to_emails.items():
        unique_emails = list(set(emails))
        if len(unique_emails) > 1:
            for email in unique_emails:
                duplicates[email] = [
                    f"Duplicate payout destination: same wallet address shared "
                    f"by {len(unique_emails)} employees."
                ]
    return duplicates


def _check_new_employee_high_amount(
    item: PayrollItem, employee: Optional[Employee]
) -> Optional[str]:
    """New employee receives amount above role band."""
    if employee and employee.role:
        # Role bands (simplified for demo)
        role_bands = {
            "Frontend Engineer": 500000,
            "Backend Engineer": 550000,
            "Product Designer": 400000,
            "Product Manager": 600000,
            "Support Lead": 350000,
            "Account Executive": 450000,
            "Support Agent": 250000,
        }
        band = role_bands.get(item.role)
        if band and item.amount > band * 1.3:
            return f"New employee amount exceeds {item.role} role band by >30%."
    return None


def _check_off_cycle(employee: Optional[Employee]) -> Optional[str]:
    """Payment is outside normal payroll cycle — check if it's not month-end."""
    now = datetime.now(timezone.utc)
    # Simple heuristic: if not within 3 days of month end, flag as off-cycle
    days_to_end = (now.replace(day=1, month=now.month % 12 + 1) - timedelta(days=1)).day - now.day
    if days_to_end > 5:
        return "Payment is outside normal payroll cycle."
    return None


def _check_employee_not_ready(employee: Optional[Employee]) -> Optional[str]:
    """Employee is not fully onboarded."""
    if employee and employee.onboarding_status != "READY":
        return f"Employee is not payroll-ready (status: {employee.onboarding_status})."
    return None


def _check_employee_suspended(employee: Optional[Employee]) -> Optional[str]:
    """Employee is suspended or inactive."""
    if employee and (not employee.is_active or employee.onboarding_status == "SUSPENDED"):
        return "Employee is suspended or inactive."
    return None


def _check_currency_mismatch(item: PayrollItem, employee: Optional[Employee]) -> Optional[str]:
    """Country/currency mismatch."""
    mismatches = {
        "Nigeria": ["NGN", "USD"],
        "Ghana": ["USD"],
        "Mexico": ["MXN"],
        "Germany": ["EUR"],
        "Canada": ["CAD"],
    }
    if employee:
        allowed = mismatches.get(item.country, [])
        if allowed and item.currency not in allowed:
            return f"Currency {item.currency} is not typical for {item.country}."
    return None


def _check_large_bonus(item: PayrollItem) -> Optional[str]:
    """Large first-time bonus/manual adjustment."""
    if item.payment_note:
        note = item.payment_note.lower()
        bonus_keywords = ["bonus", "adjustment", "one-time", "retroactive"]
        if any(kw in note for kw in bonus_keywords) and item.amount > 1000:
            return f"Large payment flagged as '{item.payment_note}'."
    return None


# ─── Main Risk Scoring ────────────────────────────────────────────────────────

def score_payroll_items(
    items: List[PayrollItem],
    employees: List[Employee],
) -> List[PayrollItem]:
    """
    Score each payroll item for risk. Returns items with risk_score, risk_level,
    and risk_reasons populated.
    """
    employees_map = {e.email: e for e in employees}

    # O(n) duplicate detection
    duplicate_emails = _check_duplicate_destinations(items)
    duplicate_addresses = _check_duplicate_payout_address(items, employees_map)

    for item in items:
        reasons = []
        employee = employees_map.get(item.employee_email)

        # Run all checks
        checks = [
            _check_salary_explosion(item, employee),
            _check_wallet_changed_recently(employee),
            _check_new_employee_high_amount(item, employee),
            _check_off_cycle(employee),
            _check_employee_not_ready(employee),
            _check_employee_suspended(employee),
            _check_currency_mismatch(item, employee),
            _check_large_bonus(item),
        ]

        for check in checks:
            if check:
                reasons.append(check)

        # Add duplicate reasons
        if item.employee_email in duplicate_emails:
            reasons.extend(duplicate_emails[item.employee_email])
        if item.employee_email in duplicate_addresses:
            reasons.extend(duplicate_addresses[item.employee_email])

        # Calculate score
        score = _calculate_risk_score(reasons)
        level = _score_to_level(score)

        item.risk_score = score
        item.risk_level = level
        item.risk_reasons = json.dumps(reasons) if reasons else None

        # Auto-assign decision
        if level == "HIGH":
            item.decision = "HOLD"
        elif level == "MEDIUM":
            item.decision = "REVIEW"
        else:
            if employee and employee.onboarding_status != "READY":
                item.decision = "HOLD"
            else:
                item.decision = "APPROVE"

    return items


def _calculate_risk_score(reasons: List[str]) -> int:
    """Calculate risk score from 0-100 based on reasons."""
    score = 0
    for reason in reasons:
        reason_lower = reason.lower()
        if "wallet changed" in reason_lower:
            score += 30
        elif "exceeds expected salary" in reason_lower or "exceeds" in reason_lower:
            score += 25
        elif "duplicate" in reason_lower and "payout" in reason_lower:
            score += 30
        elif "duplicate" in reason_lower:
            score += 20
        elif "suspended" in reason_lower or "inactive" in reason_lower:
            score += 25
        elif "not payroll-ready" in reason_lower:
            score += 20
        elif "currency" in reason_lower and "not typical" in reason_lower:
            score += 15
        elif "off-cycle" in reason_lower or "outside normal" in reason_lower:
            score += 10
        elif "bonus" in reason_lower or "adjustment" in reason_lower:
            score += 15
        else:
            score += 10

    return min(score, 100)


def _score_to_level(score: int) -> str:
    """Convert numeric score to risk level."""
    if score >= 70:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"


# ─── Batch Safety Score ───────────────────────────────────────────────────────

def calculate_batch_safety_score(
    items: List[PayrollItem],
    employees: List[Employee],
    forecasts: Optional[list] = None,
) -> Tuple[int, str]:
    """
    Calculate batch-level Payroll Safety Score (0-100).
    Returns (score, label).
    """
    high_count = sum(1 for i in items if i.risk_level == "HIGH")
    medium_count = sum(1 for i in items if i.risk_level == "MEDIUM")
    stuck_count = sum(1 for e in employees if e.onboarding_status != "READY")
    shortfall_count = 0
    if forecasts:
        shortfall_count = sum(1 for f in forecasts if f.get("status") == "SHORTFALL")

    # Duplicate destination count
    email_counter = Counter(i.employee_email for i in items)
    duplicate_count = sum(1 for c in email_counter.values() if c > 1)

    # Critical validation errors
    critical_count = 0
    for item in items:
        if item.validation_errors:
            try:
                errors = json.loads(item.validation_errors)
                critical_count += len(errors)
            except (json.JSONDecodeError, TypeError):
                pass

    score = 100
    score -= high_count * 12
    score -= medium_count * 5
    score -= stuck_count * 7
    score -= shortfall_count * 10
    score -= duplicate_count * 15
    score -= critical_count * 20

    score = max(0, min(100, score))

    if score >= 85:
        label = "SAFE_TO_RUN"
    elif score >= 60:
        label = "REVIEW_REQUIRED"
    else:
        label = "BLOCKED"

    return score, label
