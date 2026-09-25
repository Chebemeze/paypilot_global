"""
PayPilot Global — Wallet Funding Forecast Engine
Calculates payroll runway per currency.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.models import WalletBalance, PayrollItem, PayrollBatch
from app.services.risk_engine import CURRENCY_TO_WALLET


def compute_wallet_forecasts(
    db: Session,
    employer_id: str,
    batch_id: Optional[str] = None,
) -> List[dict]:
    """
    For each currency, compute:
    - current wallet balance
    - payroll obligation
    - surplus/shortfall
    - suggested top-up
    - readiness status
    """
    # Get wallet balances
    balances = db.query(WalletBalance).filter(
        WalletBalance.employer_id == employer_id
    ).all()
    balance_map = {b.currency: b.balance for b in balances}

    # Get payroll obligations
    if batch_id:
        items = db.query(PayrollItem).filter(
            PayrollItem.batch_id == batch_id,
            PayrollItem.is_deleted == False,
        ).all()
    else:
        # Use the most recent batch
        latest_batch = db.query(PayrollBatch).filter(
            PayrollBatch.employer_id == employer_id
        ).order_by(PayrollBatch.created_at.desc()).first()
        if not latest_batch:
            return _empty_forecasts(balance_map)
        items = db.query(PayrollItem).filter(
            PayrollItem.batch_id == latest_batch.id,
            PayrollItem.is_deleted == False,
        ).all()

    # Aggregate obligations by currency
    obligations: Dict[str, float] = {}
    for item in items:
        if item.decision in ("HOLD", "REJECT"):
            continue
        obligations[item.currency] = obligations.get(item.currency, 0) + item.amount

    # Compute forecast per currency
    forecasts = []
    all_currencies = set(list(balance_map.keys()) + list(obligations.keys()))

    for currency in all_currencies:
        wallet_code = CURRENCY_TO_WALLET.get(currency, currency)
        balance = balance_map.get(currency, 0.0)
        required = obligations.get(currency, 0.0)
        diff = balance - required

        if diff < 0:
            status = "SHORTFALL"
            message = (
                f"{wallet_code} wallet will be short by {_fmt_currency(abs(diff), currency)} "
                f"for this payroll batch."
            )
        elif balance < required * 0.2 and required > 0:
            status = "LOW"
            message = (
                f"{wallet_code} wallet balance is low. "
                f"Consider topping up before payroll."
            )
        else:
            status = "SUFFICIENT"
            message = (
                f"{wallet_code} wallet has sufficient balance for payroll."
            )

        forecasts.append({
            "currency": currency,
            "wallet_code": wallet_code,
            "balance": balance,
            "required": required,
            "shortfall": max(0, -diff),
            "surplus": max(0, diff),
            "status": status,
            "message": message,
        })

    return forecasts


def _empty_forecasts(balance_map: Dict[str, float]) -> List[dict]:
    forecasts = []
    for currency, balance in balance_map.items():
        wallet_code = CURRENCY_TO_WALLET.get(currency, currency)
        forecasts.append({
            "currency": currency,
            "wallet_code": wallet_code,
            "balance": balance,
            "required": 0,
            "shortfall": 0,
            "surplus": balance,
            "status": "SUFFICIENT",
            "message": f"{wallet_code} wallet has no pending payroll obligation.",
        })
    return forecasts


def compute_overall_runway_status(forecasts: List[dict]) -> str:
    """Compute overall runway status from forecasts."""
    shortfalls = [f for f in forecasts if f["status"] == "SHORTFALL"]
    lows = [f for f in forecasts if f["status"] == "LOW"]

    if shortfalls:
        return "CRITICAL"
    elif lows:
        return "WARNING"
    return "SAFE"


def _fmt_currency(amount: float, currency: str) -> str:
    symbols = {"NGN": "₦", "USD": "$", "EUR": "€", "CAD": "C$", "MXN": "MX$", "GBP": "£"}
    symbol = symbols.get(currency, "")
    return f"{symbol}{amount:,.2f}"
