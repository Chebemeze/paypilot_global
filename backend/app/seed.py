"""
PayPilot Global — Database Seed Script
Populates the database with realistic demo data for the PayPilot Global MVP.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta

from app.database import engine, SessionLocal, Base
from app.models import (
    Employer, User, Employee, PayrollBatch, PayrollItem,
    WalletBalance, WebhookEvent, Card,
)
from app.api.auth import hash_password
from app.config import settings


def seed():
    """Seed the database with demo data."""
    # Recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ─── Employer ───────────────────────────────────────────────────────
        employer = Employer(
            id=settings.demo_employer_id,
            name="Acme Global",
            company_name="Acme Global Technologies",
        )
        db.add(employer)

        # ─── Users (platform admins) ────────────────────────────────────────
        admin = User(
            id="user-admin-001",
            employer_id=employer.id,
            email="admin@acmeglobal.com",
            full_name="Sarah Johnson",
            hashed_password=hash_password("password123"),
            role="ADMIN",
        )
        finance = User(
            id="user-finance-001",
            employer_id=employer.id,
            email="finance@acmeglobal.com",
            full_name="Michael Chen",
            hashed_password=hash_password("password123"),
            role="FINANCE",
        )
        viewer = User(
            id="user-viewer-001",
            employer_id=employer.id,
            email="viewer@acmeglobal.com",
            full_name="David Kim",
            hashed_password=hash_password("password123"),
            role="VIEWER",
        )
        db.add_all([admin, finance, viewer])

        # ─── Employees (8 seed employees) ───────────────────────────────────
        now = datetime.now(timezone.utc)

        employees = [
            Employee(
                id="emp-001",
                employer_id=employer.id,
                bmoni_user_id="bmoni_ada001",
                full_name="Ada Okafor",
                email="ada@acme.com",
                country="Nigeria",
                department="Engineering",
                role="Frontend Engineer",
                expected_salary=250000,
                preferred_currency="NGN",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "a" * 40,
                is_active=True,
            ),
            Employee(
                id="emp-002",
                employer_id=employer.id,
                bmoni_user_id="bmoni_dan002",
                full_name="Daniel Mensah",
                email="daniel@acme.com",
                country="Ghana",
                department="Design",
                role="Product Designer",
                expected_salary=800,
                preferred_currency="USD",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "b" * 40,
                is_active=True,
            ),
            Employee(
                id="emp-003",
                employer_id=employer.id,
                bmoni_user_id="bmoni_sof003",
                full_name="Sofia Ruiz",
                email="sofia@acme.com",
                country="Mexico",
                department="Support",
                role="Support Lead",
                expected_salary=12000,
                preferred_currency="MXN",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "c" * 40,
                is_active=True,
            ),
            Employee(
                id="emp-004",
                employer_id=employer.id,
                bmoni_user_id="bmoni_mar004",
                full_name="Marie Keller",
                email="marie@acme.com",
                country="Germany",
                department="Sales",
                role="Account Executive",
                expected_salary=1500,
                preferred_currency="EUR",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "d" * 40,
                is_active=True,
            ),
            Employee(
                id="emp-005",
                employer_id=employer.id,
                bmoni_user_id="bmoni_chi005",
                full_name="Chiamaka Nwosu",
                email="chiamaka@acme.com",
                country="Nigeria",
                department="Engineering",
                role="Backend Engineer",
                expected_salary=300000,
                preferred_currency="NGN",
                onboarding_status="KYC_ACTION_REQUIRED",
                kyc_status="selfie_liveness_required",
                wallet_status="pending",
                payout_wallet_address=None,
                is_active=True,
            ),
            Employee(
                id="emp-006",
                employer_id=employer.id,
                bmoni_user_id="bmoni_joh006",
                full_name="John Bello",
                email="john@acme.com",
                country="Nigeria",
                department="Engineering",
                role="Backend Engineer",
                expected_salary=400,
                preferred_currency="USD",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "f" * 40,
                payout_wallet_last_changed=now - timedelta(hours=12),  # Changed recently
                is_active=True,
            ),
            Employee(
                id="emp-007",
                employer_id=employer.id,
                bmoni_user_id="bmoni_vic007",
                full_name="Victor James",
                email="victor@acme.com",
                country="Nigeria",
                department="Operations",
                role="Operations Manager",
                expected_salary=280000,
                preferred_currency="NGN",
                onboarding_status="READY",
                kyc_status="verified",
                wallet_status="active",
                payout_wallet_address="0x" + "a" * 40,  # Same as Ada — duplicate destination
                is_active=True,
            ),
            Employee(
                id="emp-008",
                employer_id=employer.id,
                bmoni_user_id="bmoni_lin008",
                full_name="Lina Chen",
                email="lina@acme.com",
                country="Canada",
                department="Marketing",
                role="Marketing Manager",
                expected_salary=2000,
                preferred_currency="CAD",
                onboarding_status="WALLET_PENDING",
                kyc_status="verified",
                wallet_status="pending",
                payout_wallet_address=None,
                is_active=True,
            ),
        ]
        db.add_all(employees)
        db.flush()  # Ensure employees exist before FK-dependent records

        # ─── Wallet Balances ────────────────────────────────────────────────
        balances = [
            WalletBalance(
                employer_id=employer.id,
                currency="NGN",
                wallet_code="CNGN",
                balance=15000000.00,  # Sufficient
            ),
            WalletBalance(
                employer_id=employer.id,
                currency="USD",
                wallet_code="USDB",
                balance=8950.00,  # Shortfall
            ),
            WalletBalance(
                employer_id=employer.id,
                currency="EUR",
                wallet_code="EURe",
                balance=5000.00,  # Sufficient
            ),
            WalletBalance(
                employer_id=employer.id,
                currency="MXN",
                wallet_code="MEXe",
                balance=250000.00,  # Sufficient
            ),
            WalletBalance(
                employer_id=employer.id,
                currency="CAD",
                wallet_code="CADC",
                balance=500.00,  # Low / pending
            ),
            WalletBalance(
                employer_id=employer.id,
                currency="GBP",
                wallet_code="GBPe",
                balance=1000.00,  # Holding only
            ),
        ]
        db.add_all(balances)

        # ─── Payroll Batch (seed) ──────────────────────────────────────────
        batch = PayrollBatch(
            id="batch-001",
            employer_id=employer.id,
            batch_name="September 2026 Payroll",
            status="RISK_SCORING",
            total_items=8,
            total_amount_usd=12400.00,
        )
        db.add(batch)

        # ─── Payroll Items (seed) ──────────────────────────────────────────
        items = [
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-001",
                employee_name="Ada Okafor",
                employee_email="ada@acme.com",
                country="Nigeria",
                currency="NGN",
                amount=250000,
                department="Engineering",
                role="Frontend Engineer",
                payment_note="September salary",
                risk_score=5,
                risk_level="LOW",
                risk_reasons=None,
                decision="APPROVE",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-002",
                employee_name="Daniel Mensah",
                employee_email="daniel@acme.com",
                country="Ghana",
                currency="USD",
                amount=800,
                department="Design",
                role="Product Designer",
                payment_note="September salary",
                risk_score=0,
                risk_level="LOW",
                risk_reasons=None,
                decision="APPROVE",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-003",
                employee_name="Sofia Ruiz",
                employee_email="sofia@acme.com",
                country="Mexico",
                currency="MXN",
                amount=12000,
                department="Support",
                role="Support Lead",
                payment_note="September salary",
                risk_score=0,
                risk_level="LOW",
                risk_reasons=None,
                decision="APPROVE",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-004",
                employee_name="Marie Keller",
                employee_email="marie@acme.com",
                country="Germany",
                currency="EUR",
                amount=1500,
                department="Sales",
                role="Account Executive",
                payment_note="September salary",
                risk_score=0,
                risk_level="LOW",
                risk_reasons=None,
                decision="APPROVE",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-005",
                employee_name="Chiamaka Nwosu",
                employee_email="chiamaka@acme.com",
                country="Nigeria",
                currency="NGN",
                amount=300000,
                department="Engineering",
                role="Backend Engineer",
                payment_note="September salary",
                risk_score=55,
                risk_level="MEDIUM",
                risk_reasons=json.dumps([
                    "Employee is not payroll-ready (status: KYC_ACTION_REQUIRED)."
                ]),
                decision="HOLD",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-006",
                employee_name="John Bello",
                employee_email="john@acme.com",
                country="Nigeria",
                currency="USD",
                amount=4200,
                department="Engineering",
                role="Backend Engineer",
                payment_note="September salary + bonus",
                risk_score=82,
                risk_level="HIGH",
                risk_reasons=json.dumps([
                    "Payout wallet changed within the last 24 hours.",
                    "Salary is 1050% of expected salary (>150% threshold).",
                ]),
                decision="HOLD",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-007",
                employee_name="Victor James",
                employee_email="victor@acme.com",
                country="Nigeria",
                currency="NGN",
                amount=280000,
                department="Operations",
                role="Operations Manager",
                payment_note="September salary",
                risk_score=35,
                risk_level="MEDIUM",
                risk_reasons=json.dumps([
                    "Duplicate payout destination: same wallet address shared by 2 employees."
                ]),
                decision="REVIEW",
            ),
            PayrollItem(
                batch_id=batch.id,
                employer_id=employer.id,
                employee_id="emp-008",
                employee_name="Lina Chen",
                employee_email="lina@acme.com",
                country="Canada",
                currency="CAD",
                amount=2000,
                department="Marketing",
                role="Marketing Manager",
                payment_note="September salary",
                risk_score=20,
                risk_level="LOW",
                risk_reasons=json.dumps([
                    "Employee is not payroll-ready (status: WALLET_PENDING)."
                ]),
                decision="HOLD",
            ),
        ]
        db.add_all(items)

        # ─── Webhook Events (seed) ─────────────────────────────────────────
        webhooks = [
            WebhookEvent(
                employer_id=employer.id,
                event_id="evt_001",
                source_event_id="bmoni_evt_001",
                event_type="employee.linked",
                payload=json.dumps({
                    "id": "evt_001",
                    "eventType": "employee.linked",
                    "payload": {
                        "userId": "bmoni_ada001",
                        "email": "ada@acme.com",
                    },
                    "timestamp": (now - timedelta(days=14)).isoformat(),
                }),
                signature_valid=True,
                state="PROCESSED",
                processed=True,
                created_at=now - timedelta(days=14),
            ),
            WebhookEvent(
                employer_id=employer.id,
                event_id="evt_002",
                source_event_id="bmoni_evt_002",
                event_type="onboarding.completed",
                payload=json.dumps({
                    "id": "evt_002",
                    "eventType": "onboarding.completed",
                    "payload": {
                        "userId": "bmoni_ada001",
                        "status": "completed",
                    },
                    "timestamp": (now - timedelta(days=12)).isoformat(),
                }),
                signature_valid=True,
                state="PROCESSED",
                processed=True,
                created_at=now - timedelta(days=12),
            ),
            WebhookEvent(
                employer_id=employer.id,
                event_id="evt_003",
                source_event_id="bmoni_evt_003",
                event_type="kyc.action_required",
                payload=json.dumps({
                    "id": "evt_003",
                    "eventType": "kyc.action_required",
                    "payload": {
                        "userId": "bmoni_chi005",
                        "email": "chiamaka@acme.com",
                        "reason": "selfie_liveness_required",
                    },
                    "timestamp": (now - timedelta(days=2)).isoformat(),
                }),
                signature_valid=True,
                state="PROCESSED",
                processed=True,
                created_at=now - timedelta(days=2),
            ),
            WebhookEvent(
                employer_id=employer.id,
                event_id="evt_004",
                source_event_id="bmoni_evt_004",
                event_type="employee.deposit.completed",
                payload=json.dumps({
                    "id": "evt_004",
                    "eventType": "employee.deposit.completed",
                    "payload": {
                        "userId": "bmoni_dan002",
                        "amount": "10000.00",
                        "currency": "USDB",
                    },
                    "timestamp": (now - timedelta(hours=6)).isoformat(),
                }),
                signature_valid=True,
                state="PROCESSED",
                processed=True,
                created_at=now - timedelta(hours=6),
            ),
        ]
        db.add_all(webhooks)

        # ─── Cards (seed — optional) ───────────────────────────────────────
        cards = [
            Card(
                id="card-001",
                employer_id=employer.id,
                employee_id="emp-001",
                bmoni_card_id="bmoni_card_001",
                smart_wallet_id="sw_ada001",
                card_name="Ada's Payroll Card",
                card_color="#4285F4",
                currency="NGN",
                card_type="virtual",
                status="ACTIVE",
                spending_limit=100000,
                spent_amount=45000,
                is_frozen=False,
            ),
            Card(
                id="card-002",
                employer_id=employer.id,
                employee_id="emp-002",
                bmoni_card_id="bmoni_card_002",
                smart_wallet_id="sw_dan002",
                card_name="Daniel's Expense Card",
                card_color="#34A853",
                currency="USD",
                card_type="virtual",
                status="ACTIVE",
                spending_limit=500,
                spent_amount=120,
                is_frozen=False,
            ),
            Card(
                id="card-003",
                employer_id=employer.id,
                employee_id="emp-003",
                bmoni_card_id="bmoni_card_003",
                smart_wallet_id="sw_sof003",
                card_name="Sofia's Travel Card",
                card_color="#EA4335",
                currency="MXN",
                card_type="virtual",
                status="FROZEN",
                spending_limit=5000,
                spent_amount=2300,
                is_frozen=True,
            ),
        ]
        db.add_all(cards)

        db.flush()  # Ensure all FKs are valid before committing
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   Employer: {employer.company_name} ({employer.id})")
        print(f"   Users: {admin.email}, {finance.email}, {viewer.email}")
        print(f"   Employees: {len(employees)}")
        print(f"   Wallet balances: {len(balances)} currencies")
        print(f"   Payroll batch: {batch.batch_name} ({batch.total_items} items)")
        print(f"   Webhook events: {len(webhooks)}")
        print(f"   Cards: {len(cards)}")
        print()
        print("   Login credentials:")
        print(f"   Admin:  admin@acmeglobal.com / password123")
        print(f"   Finance: finance@acmeglobal.com / password123")
        print(f"   Viewer: viewer@acmeglobal.com / password123")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
