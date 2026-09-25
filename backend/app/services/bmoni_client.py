"""
PayPilot Global — Mock BMONI Client
Returns realistic BMONI-shaped responses for demo mode.
In production, each method would call the BMONI REST API.
"""
from __future__ import annotations

import uuid
import hashlib
import hmac
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.config import settings


class BmoniClient:
    """
    BMONI REST API client.
    In DEMO_MODE, returns mock data. In production, calls the real API.
    """

    def __init__(self):
        self.base_url = settings.bmoni_base_url
        self.api_key = settings.bmoni_api_key
        self.demo_mode = settings.demo_mode

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    # ─── Employee / User Management ─────────────────────────────────────────

    async def create_user(self, employer_id: str) -> dict:
        """POST /v1/users — Create a BMONI user."""
        if self.demo_mode:
            return {
                "bmoniUserId": f"bmoni_{uuid.uuid4().hex[:12]}",
                "status": "created",
            }
        # Production: httpx POST to self.base_url + "/v1/users"
        raise NotImplementedError("Production BMONI client not yet wired")

    async def invite_employee(self, email: str, full_name: str, country: str) -> dict:
        """Invite employee to BMONI app via partner flow."""
        if self.demo_mode:
            return {
                "inviteId": f"inv_{uuid.uuid4().hex[:12]}",
                "status": "sent",
                "email": email,
            }
        raise NotImplementedError

    async def get_onboarding_status(self, bmoni_user_id: str) -> dict:
        """GET /v1/users/{userId}/onboarding/status"""
        if self.demo_mode:
            return {
                "userId": bmoni_user_id,
                "currencies": {
                    "USD": {"status": "active", "walletAddress": f"0x{uuid.uuid4().hex[:40]}"},
                    "NGN": {"status": "active", "walletAddress": f"0x{uuid.uuid4().hex[:40]}"},
                },
            }
        raise NotImplementedError

    # ─── Wallet Operations ──────────────────────────────────────────────────

    async def get_user_wallets(self, bmoni_user_id: str) -> dict:
        """GET /v1/users/{userId}/smart-wallets/account/wallets"""
        if self.demo_mode:
            return {
                "wallets": [
                    {"id": f"sw_{uuid.uuid4().hex[:8]}", "currency": "USDB", "status": "active"},
                    {"id": f"sw_{uuid.uuid4().hex[:8]}", "currency": "CNGN", "status": "active"},
                ]
            }
        raise NotImplementedError

    async def get_wallet_balances(self, bmoni_user_id: str) -> dict:
        """GET /v1/users/{userId}/smart-wallets/account/balances"""
        if self.demo_mode:
            return {
                "balances": [
                    {"currency": "USDB", "balance": "15000.00"},
                    {"currency": "CNGN", "balance": "5000000.00"},
                ]
            }
        raise NotImplementedError

    async def get_virtual_account_details(self, bmoni_user_id: str, currency: str) -> dict:
        """GET /v1/users/{userId}/vba/{currency}"""
        if self.demo_mode:
            return {
                "status": "active",
                "currency": currency,
                "accountNumber": "0123456789",
                "routingNumber": "021000021",
                "bankName": "BMONI Virtual Bank",
            }
        raise NotImplementedError

    # ─── Transfer / Proposal Operations ─────────────────────────────────────

    async def create_transfer_or_payment_proposal(
        self, bmoni_user_id: str, smart_wallet_id: str, proposal: dict
    ) -> dict:
        """POST /v1/users/{userId}/smart-wallets/{smartWalletId}/proposals"""
        if self.demo_mode:
            return {
                "data": {
                    "proposal": {
                        "id": f"prop_{uuid.uuid4().hex[:12]}",
                        "status": "PENDING_APPROVALS",
                    }
                }
            }
        raise NotImplementedError

    async def approve_proposal(
        self, bmoni_user_id: str, proposal_id: str
    ) -> dict:
        """POST /v1/users/{userId}/smart-wallets/proposals/{proposalId}/approve"""
        if self.demo_mode:
            return {"status": "PENDING_SIGNATURES"}
        raise NotImplementedError

    async def get_sign_payload(
        self, bmoni_user_id: str, proposal_id: str
    ) -> dict:
        """GET /v1/users/{userId}/smart-wallets/proposals/{proposalId}/sign-payload"""
        if self.demo_mode:
            return {
                "hashToSign": f"0x{hashlib.sha256(uuid.uuid4().bytes).hexdigest()}",
                "deadline": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            }
        raise NotImplementedError

    async def submit_signature(
        self, bmoni_user_id: str, proposal_id: str, signature: str
    ) -> dict:
        """POST /v1/users/{userId}/smart-wallets/proposals/{proposalId}/sign"""
        if self.demo_mode:
            return {"status": "EXECUTING"}
        raise NotImplementedError

    # ─── Card Operations ────────────────────────────────────────────────────

    async def list_cards(self, bmoni_user_id: str, smart_wallet_id: str) -> dict:
        """GET /v1/users/{userId}/smart-wallets/{smartWalletId}/cards"""
        if self.demo_mode:
            return {"cards": []}
        raise NotImplementedError

    async def set_card_limit(
        self, bmoni_user_id: str, card_id: str, limit: float
    ) -> dict:
        """PUT /v1/users/{userId}/smart-wallets/{smartWalletId}/cards/{cardId}/limits"""
        if self.demo_mode:
            return {"status": "updated", "spendingLimit": str(limit)}
        raise NotImplementedError

    async def freeze_or_unfreeze_card(
        self, bmoni_user_id: str, card_id: str, freeze: bool
    ) -> dict:
        """PUT /v1/users/{userId}/smart-wallets/{smartWalletId}/cards/{cardId}/freeze"""
        if self.demo_mode:
            return {"status": "frozen" if freeze else "unfrozen"}
        raise NotImplementedError


# ─── Webhook Signature Verification ────────────────────────────────────────

def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify BMONI webhook signature using HMAC-SHA256.
    Uses constant-time comparison to prevent timing attacks.
    """
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def sign_webhook_payload(payload: dict, secret: str) -> str:
    """
    Sign a webhook payload (for demo simulator).
    Returns hex-encoded HMAC-SHA256.
    """
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(
        secret.encode("utf-8"), raw, hashlib.sha256
    ).hexdigest()


bmoni_client = BmoniClient()
