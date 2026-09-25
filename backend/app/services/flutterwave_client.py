"""
PayPilot Global — Flutterwave Client
Handles all Flutterwave API interactions for multi-currency operations.
"""
from __future__ import annotations

import uuid
import hashlib
import hmac
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from app.config import settings


class FlutterwaveClient:
    """
    Flutterwave REST API client.
    In DEMO_MODE, returns mock data. In production, calls the real API.
    """

    def __init__(self):
        self.base_url = settings.flutterwave_base_url
        self.secret_key = settings.flutterwave_secret_key
        self.public_key = settings.flutterwave_public_key
        self.demo_mode = settings.demo_mode

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    # ─── User / Customer Management ─────────────────────────────────────────

    async def create_customer(self, email: str, name: str, phone: str = None) -> dict:
        """POST /customers — Create a Flutterwave customer."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": f"flw_cust_{uuid.uuid4().hex[:12]}",
                    "email": email,
                    "name": name,
                    "phone_number": phone,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/customers",
                headers=self._headers(),
                json={
                    "email": email,
                    "name": name,
                    "phone_number": phone or "",
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_customer(self, customer_id: str) -> dict:
        """GET /customers/{id} — Get customer details."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": customer_id,
                    "email": "demo@example.com",
                    "name": "Demo User",
                    "accounts": [
                        {"currency": "NGN", "balance": 5000000.00},
                        {"currency": "USD", "balance": 15000.00},
                    ]
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers/{customer_id}",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    # ─── Virtual Account Operations ─────────────────────────────────────────

    async def create_virtual_account(self, customer_id: str, currency: str = "NGN") -> dict:
        """POST /virtual-account-numbers — Create a virtual account."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "response_code": "02",
                    "response_message": "Virtual account created successfully",
                    "order_ref": f"VA_{uuid.uuid4().hex[:12]}",
                    "account_number": f"{uuid.uuid4().int % 10**10:010d}",
                    "bank_name": "Flutterwave Virtual Bank",
                    "currency": currency,
                    "customer_id": customer_id,
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/virtual-account-numbers",
                headers=self._headers(),
                json={
                    "customer_id": customer_id,
                    "currency": currency,
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_virtual_accounts(self, customer_id: str) -> dict:
        """GET /virtual-account-numbers — List virtual accounts."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": [
                    {
                        "account_number": "0123456789",
                        "bank_name": "Flutterwave Virtual Bank",
                        "currency": "NGN",
                        "customer_id": customer_id,
                    },
                    {
                        "account_number": "9876543210",
                        "bank_name": "Flutterwave Virtual Bank",
                        "currency": "USD",
                        "customer_id": customer_id,
                    }
                ]
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/virtual-account-numbers",
                headers=self._headers(),
                params={"customer_id": customer_id}
            )
            response.raise_for_status()
            return response.json()

    # ─── Wallet / Balance Operations ────────────────────────────────────────

    async def get_wallet_balances(self, customer_id: str) -> dict:
        """GET /balances — Get wallet balances for a customer."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": [
                    {"currency": "NGN", "balance": 15000000.00, "available_balance": 15000000.00},
                    {"currency": "USD", "balance": 8950.00, "available_balance": 8950.00},
                    {"currency": "EUR", "balance": 5000.00, "available_balance": 5000.00},
                    {"currency": "GBP", "balance": 3000.00, "available_balance": 3000.00},
                    {"currency": "GHS", "balance": 25000.00, "available_balance": 25000.00},
                    {"currency": "ZAR", "balance": 45000.00, "available_balance": 45000.00},
                ]
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/balances",
                headers=self._headers(),
                params={"customer_id": customer_id}
            )
            response.raise_for_status()
            return response.json()

    # ─── Transfer Operations ────────────────────────────────────────────────

    async def initiate_transfer(
        self,
        amount: float,
        currency: str,
        account_number: str,
        bank_code: str,
        beneficiary_name: str,
        reference: str = None
    ) -> dict:
        """POST /transfers — Initiate a transfer."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": f"flw_trans_{uuid.uuid4().hex[:12]}",
                    "account_number": account_number,
                    "bank_code": bank_code,
                    "bank_name": "Demo Bank",
                    "beneficiary_name": beneficiary_name,
                    "currency": currency,
                    "amount": amount,
                    "fee": 10.00,
                    "status": "successful",
                    "reference": reference or f"ref_{uuid.uuid4().hex[:12]}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transfers",
                headers=self._headers(),
                json={
                    "account_number": account_number,
                    "amount": amount,
                    "currency": currency,
                    "beneficiary_name": beneficiary_name,
                    "bank_code": bank_code,
                    "tx_ref": reference or f"tx_{uuid.uuid4().hex[:12]}",
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_transfer(self, transfer_id: str) -> dict:
        """GET /transfers/{id} — Get transfer status."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": transfer_id,
                    "status": "successful",
                    "amount": 50000.00,
                    "currency": "NGN",
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transfers/{transfer_id}",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    async def bulk_transfer(self, transfers: List[Dict]) -> dict:
        """POST /bulk-transfers — Initiate bulk transfers."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "batch_id": f"batch_{uuid.uuid4().hex[:12]}",
                    "transfers": [
                        {
                            "id": f"flw_trans_{uuid.uuid4().hex[:12]}",
                            "status": "successful",
                            "amount": t["amount"],
                            "currency": t["currency"],
                        }
                        for t in transfers
                    ],
                    "total_amount": sum(t["amount"] for t in transfers),
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bulk-transfers",
                headers=self._headers(),
                json={"transfers": transfers}
            )
            response.raise_for_status()
            return response.json()

    # ─── Card Operations ────────────────────────────────────────────────────

    async def issue_card(
        self,
        customer_id: str,
        card_type: str = "virtual",
        currency: str = "USD",
        amount: float = 10.00,
        first_name: str = None,
        last_name: str = None
    ) -> dict:
        """POST /cards — Issue a virtual card."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": f"flw_card_{uuid.uuid4().hex[:12]}",
                    "card_number": f"5399********{uuid.uuid4().hex[:4]}",
                    "cvv": "***",
                    "expiry": "12/28",
                    "card_type": card_type,
                    "currency": currency,
                    "amount": amount,
                    "customer_id": customer_id,
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/cards",
                headers=self._headers(),
                json={
                    "customer_id": customer_id,
                    "card_type": card_type,
                    "currency": currency,
                    "amount": amount,
                    "first_name": first_name or "Demo",
                    "last_name": last_name or "User",
                }
            )
            response.raise_for_status()
            return response.json()

    async def list_cards(self, customer_id: str) -> dict:
        """GET /cards — List cards for a customer."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": [
                    {
                        "id": f"flw_card_{i}",
                        "card_number": f"5399********{i:04d}",
                        "card_type": "virtual",
                        "currency": "USD",
                        "status": "active",
                        "customer_id": customer_id,
                    }
                    for i in range(1, 3)
                ]
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/cards",
                headers=self._headers(),
                params={"customer_id": customer_id}
            )
            response.raise_for_status()
            return response.json()

    async def freeze_card(self, card_id: str, freeze: bool = True) -> dict:
        """PUT /cards/{id}/status/freeze — Freeze/unfreeze a card."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": card_id,
                    "status": "frozen" if freeze else "active",
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/cards/{card_id}/status/freeze",
                headers=self._headers(),
                json={"status_action": "freeze" if freeze else "unfreeze"}
            )
            response.raise_for_status()
            return response.json()

    async def set_card_limit(self, card_id: str, amount: float) -> dict:
        """PUT /cards/{id} — Update card spending limit."""
        if self.demo_mode:
            return {
                "status": "success",
                "data": {
                    "id": card_id,
                    "amount": amount,
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/cards/{card_id}",
                headers=self._headers(),
                json={"amount": amount}
            )
            response.raise_for_status()
            return response.json()

    # ─── FX Rate Operations ─────────────────────────────────────────────────

    async def get_exchange_rate(self, from_currency: str, to_currency: str, amount: float) -> dict:
        """GET /transfers/rates — Get exchange rate."""
        if self.demo_mode:
            # Mock rates for demo
            rates = {
                ("USD", "NGN"): 1580.00,
                ("EUR", "NGN"): 1720.00,
                ("GBP", "NGN"): 2010.00,
                ("NGN", "USD"): 0.000633,
                ("NGN", "EUR"): 0.000581,
            }
            rate = rates.get((from_currency, to_currency), 1.0)
            return {
                "status": "success",
                "data": {
                    "rate": rate,
                    "original_amount": amount,
                    "converted_amount": amount * rate,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                }
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transfers/rates",
                headers=self._headers(),
                params={
                    "amount": amount,
                    "destination_currency": to_currency,
                    "source_currency": from_currency,
                }
            )
            response.raise_for_status()
            return response.json()

    # ─── Webhook Verification ───────────────────────────────────────────────

    def verify_webhook_signature(self, signature: str, payload: bytes) -> bool:
        """
        Verify Flutterwave webhook signature.
        Flutterwave sends signature in 'verif-hash' header.
        """
        if self.demo_mode:
            expected = sign_webhook_payload(json.loads(payload), settings.flutterwave_webhook_secret)
            return hmac.compare_digest(signature, expected)
        
        # In production, Flutterwave uses a different verification method
        # The signature should match the secret hash configured in dashboard
        return signature == settings.flutterwave_webhook_secret


def sign_webhook_payload(payload: dict, secret: str) -> str:
    """
    Sign a webhook payload for demo simulator.
    Returns hex-encoded HMAC-SHA256.
    """
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(
        secret.encode("utf-8"), raw, hashlib.sha256
    ).hexdigest()


# Singleton instance
flutterwave_client = FlutterwaveClient()
