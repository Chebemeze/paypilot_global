"""
PayPilot Global — SQLAlchemy Models
All ORM models for the PayPilot Global platform.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Employer(Base):
    __tablename__ = "employers"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(100), nullable=False)
    company_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    users = relationship("User", back_populates="employer", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="employer", cascade="all, delete-orphan")


class User(Base):
    """Platform user — an employer-side admin/finance/viewer account."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="VIEWER")  # ADMIN, FINANCE, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    employer = relationship("Employer", back_populates="users")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False)
    bmoni_user_id = Column(String(100), nullable=True, index=True)  # Deprecated - kept for backward compatibility
    flutterwave_customer_id = Column(String(100), nullable=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    country = Column(String(50), nullable=False)
    department = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    expected_salary = Column(Float, nullable=True)
    preferred_currency = Column(String(10), nullable=False)  # NGN, USD, EUR, CAD, MXN, GBP
    onboarding_status = Column(String(50), nullable=False, default="INVITED")
    kyc_status = Column(String(50), nullable=True)
    wallet_status = Column(String(50), nullable=True)
    payout_wallet_address = Column(String(255), nullable=True)
    payout_wallet_last_changed = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    employer = relationship("Employer", back_populates="employees")

    __table_args__ = (
        Index("ix_employees_employer_status", "employer_id", "onboarding_status"),
        Index("ix_employees_employer_email", "employer_id", "email", unique=True),
        Index("ix_employees_employer_created", "employer_id", "created_at"),
    )


class PayrollBatch(Base):
    __tablename__ = "payroll_batches"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False, index=True)
    batch_name = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT")
    total_items = Column(Integer, default=0)
    total_amount_usd = Column(Float, default=0.0)
    safety_score = Column(Integer, nullable=True)
    safety_label = Column(String(50), nullable=True)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    items = relationship("PayrollItem", back_populates="batch", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_batches_employer_created", "employer_id", "created_at"),
    )


class PayrollItem(Base):
    __tablename__ = "payroll_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    batch_id = Column(String(36), ForeignKey("payroll_batches.id"), nullable=False, index=True)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    employee_name = Column(String(100), nullable=False)
    employee_email = Column(String(255), nullable=False)
    country = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    department = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    payment_note = Column(Text, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    risk_reasons = Column(Text, nullable=True)  # JSON array stored as text
    decision = Column(String(20), nullable=True)  # APPROVE, HOLD, REVIEW, REJECT
    decision_reason = Column(Text, nullable=True)
    validation_errors = Column(Text, nullable=True)  # JSON array stored as text
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    batch = relationship("PayrollBatch", back_populates="items")

    __table_args__ = (
        Index("ix_items_batch_risk", "batch_id", "risk_level"),
        Index("ix_items_batch_decision", "batch_id", "decision"),
    )


class WalletBalance(Base):
    __tablename__ = "wallet_balances"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False, index=True)
    currency = Column(String(10), nullable=False)  # NGN, USD, EUR, CAD, MXN, GBP
    wallet_code = Column(String(20), nullable=False)  # CNGN, USDB, EURe, CADC, MEXe, GBPe
    balance = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=True, index=True)
    event_id = Column(String(100), nullable=False)
    source_event_id = Column(String(100), nullable=True, unique=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)  # JSON stored as text
    signature_valid = Column(Boolean, default=False)
    state = Column(String(50), nullable=False, default="RECEIVED")
    processed = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_webhooks_event_type_created", "event_type", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)  # JSON stored as text
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_employer_created", "employer_id", "created_at"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False)
    key = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=False)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_idempotency_employer_key", "employer_id", "key", unique=True),
    )


class Card(Base):
    __tablename__ = "cards"

    id = Column(String(36), primary_key=True, default=_uuid)
    employer_id = Column(String(36), ForeignKey("employers.id"), nullable=False, index=True)
    employee_id = Column(String(36), ForeignKey("employees.id"), nullable=True)
    bmoni_card_id = Column(String(100), nullable=True)  # Deprecated - kept for backward compatibility
    flutterwave_card_id = Column(String(100), nullable=True)
    smart_wallet_id = Column(String(100), nullable=True)
    card_name = Column(String(100), nullable=False)
    card_color = Column(String(20), nullable=False, default="#4285F4")
    currency = Column(String(10), nullable=False)
    card_type = Column(String(20), nullable=False, default="virtual")
    status = Column(String(20), nullable=False, default="ACTIVE")
    spending_limit = Column(Float, nullable=True)
    spent_amount = Column(Float, nullable=False, default=0.0)
    is_frozen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
