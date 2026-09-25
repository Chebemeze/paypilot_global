"""
PayPilot Global — Pydantic Schemas
All request/response schemas for the PayPilot Global API.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


# ─── Shared validation helpers ────────────────────────────────────────────────
# NOTE: we validate email with a regex rather than pydantic's EmailStr so the
# project does not need the extra `email-validator` dependency. If the team ever
# adds it to requirements.txt, swap these for EmailStr.

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

#: Currencies PayPilot can actually pay out in (see Employee.preferred_currency).
SUPPORTED_CURRENCIES = {"NGN", "USD", "EUR", "GBP", "CAD", "MXN", "KES", "GHS", "ZAR"}


def normalize_email(value: str) -> str:
    """Trim, lowercase and validate an email address."""
    email = (value or "").strip().lower()
    if not email:
        raise ValueError("Email is required.")
    if len(email) > 255:
        raise ValueError("Email must be 255 characters or fewer.")
    if not EMAIL_RE.match(email):
        raise ValueError(f"'{value}' is not a valid email address.")
    return email


def normalize_currency(value: str) -> str:
    """Uppercase and check a currency code against the supported list."""
    code = (value or "").strip().upper()
    if code not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"'{value}' is not a supported currency. "
            f"Supported: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
        )
    return code


#: Full country names -> ISO-3166 alpha-2, so imported spreadsheets that say
#: "Nigeria" work as well as API calls that say "NG".
#: Person 2's payroll CSV importer accepts full names too — this is the shared
#: lookup so both importers agree on what "Ivory Coast" means.
COUNTRY_NAME_TO_ISO = {
    # Africa
    "NIGERIA": "NG", "GHANA": "GH", "KENYA": "KE", "SOUTH AFRICA": "ZA",
    "EGYPT": "EG", "MOROCCO": "MA", "TANZANIA": "TZ", "UGANDA": "UG",
    "RWANDA": "RW", "ETHIOPIA": "ET", "SENEGAL": "SN", "CAMEROON": "CM",
    "IVORY COAST": "CI", "COTE D'IVOIRE": "CI", "CÔTE D'IVOIRE": "CI",
    "ZAMBIA": "ZM", "ZIMBABWE": "ZW", "BOTSWANA": "BW", "NAMIBIA": "NA",
    "TUNISIA": "TN", "ALGERIA": "DZ", "ANGOLA": "AO", "MOZAMBIQUE": "MZ",
    # Americas
    "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "USA": "US",
    "U.S.": "US", "U.S.A.": "US", "AMERICA": "US",
    "CANADA": "CA", "MEXICO": "MX", "BRAZIL": "BR", "ARGENTINA": "AR",
    "COLOMBIA": "CO", "CHILE": "CL", "PERU": "PE",
    # Europe
    "UNITED KINGDOM": "GB", "UK": "GB", "GREAT BRITAIN": "GB",
    "ENGLAND": "GB", "SCOTLAND": "GB", "WALES": "GB",
    "GERMANY": "DE", "FRANCE": "FR", "SPAIN": "ES", "ITALY": "IT",
    "NETHERLANDS": "NL", "THE NETHERLANDS": "NL", "HOLLAND": "NL",
    "BELGIUM": "BE", "PORTUGAL": "PT", "IRELAND": "IE", "POLAND": "PL",
    "SWEDEN": "SE", "NORWAY": "NO", "DENMARK": "DK", "FINLAND": "FI",
    "SWITZERLAND": "CH", "AUSTRIA": "AT", "GREECE": "GR",
    "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "ROMANIA": "RO", "UKRAINE": "UA",
    # Asia-Pacific & Middle East
    "INDIA": "IN", "CHINA": "CN", "JAPAN": "JP", "SOUTH KOREA": "KR",
    "KOREA": "KR", "SINGAPORE": "SG", "MALAYSIA": "MY", "INDONESIA": "ID",
    "PHILIPPINES": "PH", "THE PHILIPPINES": "PH", "VIETNAM": "VN",
    "THAILAND": "TH", "PAKISTAN": "PK", "BANGLADESH": "BD",
    "AUSTRALIA": "AU", "NEW ZEALAND": "NZ",
    "UNITED ARAB EMIRATES": "AE", "UAE": "AE", "SAUDI ARABIA": "SA",
    "ISRAEL": "IL", "TURKEY": "TR", "TÜRKIYE": "TR",
}


def normalize_country(value: str) -> str:
    """Normalise a country to an ISO-3166 alpha-2 code.

    Accepts either the code itself ("ng", "NG") or a common full name
    ("Nigeria", "united states", "UK"). Full names are accepted because real HR
    spreadsheets almost never contain ISO codes.
    """
    raw = (value or "").strip()
    if not raw:
        raise ValueError(
            "Country is required. Use a 2-letter ISO code (e.g. NG) or a country name."
        )

    upper = raw.upper()

    # Check the alias table FIRST, before the 2-letter shortcut. Some common
    # abbreviations are two letters but are NOT the ISO code: people write "UK"
    # for the United Kingdom, whose actual ISO-3166 alpha-2 code is "GB".
    # Returning "UK" unchanged would store a code no payment provider accepts.
    mapped = COUNTRY_NAME_TO_ISO.get(upper)
    if mapped:
        return mapped

    # Otherwise, any 2-letter alphabetic value is taken as an ISO code.
    if len(upper) == 2 and upper.isalpha():
        return upper

    raise ValueError(
        f"'{value}' is not a recognised country. "
        "Use a 2-letter ISO code (e.g. NG, US, GB) or a common country name "
        "(e.g. Nigeria, United States, United Kingdom)."
    )


# ─── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any] = []
    page: int = 1
    limit: int = 50
    total: int = 0
    total_pages: int = 0
    # Convenience flags so the frontend can enable/disable its pager buttons
    # without recomputing the arithmetic on every render.
    has_next: bool = False
    has_prev: bool = False
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


def paginate(items: List[Any], page: int, limit: int, total: int) -> "PaginatedResponse":
    """Build a PaginatedResponse with all the derived fields filled in."""
    total_pages = max(1, (total + limit - 1) // limit) if limit else 1
    return PaginatedResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_page=page + 1 if page < total_pages else None,
        prev_page=page - 1 if page > 1 else None,
    )


# ─── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 0  # seconds until the token expires
    user: "UserResponse"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 0


class LogoutResponse(BaseModel):
    status: str = "logged_out"
    message: str = "Token revoked successfully."


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangePasswordResponse(BaseModel):
    status: str = "password_changed"
    message: str = "Password updated. Please log in again."


class UserResponse(BaseModel):
    id: str
    employer_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_employees: int
    ready_employees: int
    stuck_employees: int
    high_risk_items: int
    safety_score: Optional[int] = None
    safety_label: Optional[str] = None
    payroll_totals_by_currency: dict[str, float] = {}
    wallet_balances: list["WalletBalanceResponse"] = []
    forecast_shortfalls: list["ForecastItem"] = []
    recent_webhooks: list["WebhookEventResponse"] = []


# ─── Employee ──────────────────────────────────────────────────────────────────

class EmployeeResponse(BaseModel):
    id: str
    full_name: str
    email: str
    country: str
    department: Optional[str] = None
    role: Optional[str] = None
    expected_salary: Optional[float] = None
    preferred_currency: str
    bmoni_user_id: Optional[str] = None
    onboarding_status: str
    kyc_status: Optional[str] = None
    wallet_status: Optional[str] = None
    payout_wallet_address: Optional[str] = None
    payout_wallet_last_changed: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeCreateRequest(BaseModel):
    """Payload for POST /employees and POST /employees/invite.

    Field constraints mirror the database column limits in models.py so a bad
    request is rejected with a clear 422 instead of blowing up as a 500 when
    MySQL refuses an over-long value.
    """

    full_name: str = Field(
        ..., min_length=2, max_length=100,
        description="Employee's full legal name.",
        examples=["Chidi Okonkwo"],
    )
    email: str = Field(
        ..., max_length=255,
        description="Work email. Must be unique per employer.",
        examples=["chidi@acmeglobal.com"],
    )
    country: str = Field(
        ...,
        description="2-letter ISO country code. Validated by _validate_country.",
        examples=["NG"],
    )
    preferred_currency: str = Field(
        default="USD", max_length=10,
        description=f"Payout currency. One of: {', '.join(sorted(SUPPORTED_CURRENCIES))}.",
        examples=["NGN"],
    )
    department: Optional[str] = Field(
        default=None, max_length=100, examples=["Engineering"],
    )
    role: Optional[str] = Field(
        default=None, max_length=100,
        description="Job title (not a permission role).",
        examples=["Backend Engineer"],
    )
    expected_salary: Optional[float] = Field(
        default=None, gt=0, le=1_000_000_000,
        description="Gross salary per pay period, in preferred_currency.",
        examples=[450000],
    )

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("country")
    @classmethod
    def _validate_country(cls, v: str) -> str:
        return normalize_country(v)

    @field_validator("preferred_currency")
    @classmethod
    def _validate_currency(cls, v: str) -> str:
        return normalize_currency(v)

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, v: str) -> str:
        name = (v or "").strip()
        if len(name) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return name

    @field_validator("department", "role")
    @classmethod
    def _clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned or None


class EmployeeUpdateRequest(BaseModel):
    """Payload for PUT /employees/{id}.

    Every field is optional — only what you send gets changed. An omitted field
    is left alone; this is a partial update, not a replace.
    """

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    country: Optional[str] = Field(default=None)
    preferred_currency: Optional[str] = Field(default=None, max_length=10)
    department: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default=None, max_length=100)
    expected_salary: Optional[float] = Field(default=None, gt=0, le=1_000_000_000)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: Optional[str]) -> Optional[str]:
        return normalize_email(v) if v is not None else None

    @field_validator("country")
    @classmethod
    def _validate_country(cls, v: Optional[str]) -> Optional[str]:
        return normalize_country(v) if v is not None else None

    @field_validator("preferred_currency")
    @classmethod
    def _validate_currency(cls, v: Optional[str]) -> Optional[str]:
        return normalize_currency(v) if v is not None else None

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        name = v.strip()
        if len(name) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return name

    @field_validator("department", "role")
    @classmethod
    def _clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned or None


#: Backwards-compatible alias — /employees/invite takes the same payload.
EmployeeInviteRequest = EmployeeCreateRequest


class EmployeeMutationResponse(BaseModel):
    """Standard envelope returned by create / update / invite.

    Documented in API_CONTRACT.md — the frontend reads `.employee`.
    """

    employee: EmployeeResponse
    status: str = Field(
        ..., description="One of: created, updated, invited.",
        examples=["created"],
    )


class EmployeeDeleteResponse(BaseModel):
    status: str = "deleted"
    employee_id: str


class StatsBucket(BaseModel):
    """One row of a breakdown: a value, how many employees have it, and the
    share of headcount it represents.

    The percentage is computed server-side on purpose. Four clients (web, the
    PDF export, the mobile shell and Person 4's dashboard) all render these
    numbers; if each divides for itself they will disagree on rounding and the
    columns will not add up the same way in two places.
    """
    value: str = Field(..., description="The country / currency / status.")
    count: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100, description="Share of active headcount, 1dp.")


class SalaryStats(BaseModel):
    """Salary aggregates, always scoped to ONE currency.

    Never sum salaries across currencies: adding 500,000 NGN to 4,000 USD gives
    504,000 of nothing. Each currency gets its own total.
    """
    currency: str
    employees: int = Field(..., ge=0, description="Employees with a salary set, in this currency.")
    total: float = Field(..., ge=0, description="Monthly payroll cost in this currency.")
    average: float = Field(..., ge=0)
    minimum: float = Field(..., ge=0)
    maximum: float = Field(..., ge=0)


class EmployeeStatsResponse(BaseModel):
    """Headline numbers for the dashboard."""
    total_employees: int = Field(..., ge=0, description="Active, non-deleted employees.")
    active: int = Field(..., ge=0)
    inactive: int = Field(..., ge=0, description="Suspended: is_active = false.")
    onboarding_complete: int = Field(..., ge=0, description="onboarding_status = READY.")
    onboarding_pending: int = Field(..., ge=0, description="Everyone not yet READY.")
    completion_rate: float = Field(..., ge=0, le=100, description="READY as a % of headcount, 1dp.")
    missing_salary: int = Field(
        ..., ge=0,
        description="Active employees with no expected_salary. These are invisible to payroll "
                    "forecasting, so the dashboard should surface them as an action item.",
    )
    by_country: list[StatsBucket]
    by_currency: list[StatsBucket]
    by_status: list[StatsBucket]
    by_department: list[StatsBucket]
    salary_by_currency: list[SalaryStats]


class EmployeeDetailResponse(BaseModel):
    employee: EmployeeResponse
    onboarding_issue: Optional["OnboardingIssueResponse"] = None


class ResendInviteResponse(BaseModel):
    status: str = "resent"
    employee_id: str


class ImportRowResult(BaseModel):
    row: int = Field(..., description="1-based line number as seen in a spreadsheet.")
    email: str = ""
    status: str = Field(..., description="created | restored | skipped | failed")
    message: str = ""
    errors: Optional[List[dict]] = None


class EmployeeImportResponse(BaseModel):
    """Outcome of POST /employees/import."""

    dry_run: bool = Field(..., description="True when nothing was written.")
    total_rows: int = 0
    recognised_columns: List[str] = []
    created: int = 0
    restored: int = 0
    skipped: int = 0
    failed: int = 0
    results: List[ImportRowResult] = []


class OnboardingIssueResponse(BaseModel):
    issue: str
    severity: str
    admin_explanation: str
    recommended_action: str
    employee_email_message: str
    employee_whatsapp_message: str


# ─── Payroll ───────────────────────────────────────────────────────────────────

class PayrollBatchResponse(BaseModel):
    id: str
    batch_name: str
    status: str
    total_items: int
    total_amount_usd: float
    safety_score: Optional[int] = None
    safety_label: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollItemResponse(BaseModel):
    id: str
    batch_id: str
    employee_id: Optional[str] = None
    employee_name: str
    employee_email: str
    country: str
    currency: str
    amount: float
    department: Optional[str] = None
    role: Optional[str] = None
    payment_note: Optional[str] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_reasons: Optional[List[str]] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    validation_errors: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollBatchDetailResponse(BaseModel):
    batch: PayrollBatchResponse
    items: List[PayrollItemResponse]
    currency_totals: dict[str, float] = {}
    risk_summary: dict[str, int] = {}
    decision_summary: dict[str, int] = {}


class PayrollApproveRequest(BaseModel):
    override_reason: Optional[str] = None
    item_decisions: dict[str, str] = {}  # item_id -> APPROVE/HOLD/REVIEW/REJECT


# ─── Forecast ──────────────────────────────────────────────────────────────────

class WalletBalanceResponse(BaseModel):
    id: str
    currency: str
    wallet_code: str
    balance: float
    updated_at: datetime

    class Config:
        from_attributes = True


class ForecastItem(BaseModel):
    currency: str
    wallet_code: str
    balance: float
    required: float
    shortfall: float
    surplus: float
    status: str  # SUFFICIENT, SHORTFALL, LOW
    message: str


class PayrollRunwayResponse(BaseModel):
    forecasts: List[ForecastItem]
    overall_status: str  # SAFE, WARNING, CRITICAL
    generated_at: datetime


# ─── Webhook ───────────────────────────────────────────────────────────────────

class WebhookEventResponse(BaseModel):
    id: str
    event_id: str
    source_event_id: Optional[str] = None
    event_type: str
    payload: dict
    signature_valid: bool
    state: str
    processed: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookSimulateRequest(BaseModel):
    event_type: str
    payload: dict


# ─── Copilot ───────────────────────────────────────────────────────────────────

class CopilotQueryRequest(BaseModel):
    question: str


class CopilotQueryResponse(BaseModel):
    answer: str
    evidence: List[str] = []
    actions: List[str] = []
    warnings: List[str] = []


# ─── Cards ─────────────────────────────────────────────────────────────────────

class CardResponse(BaseModel):
    id: str
    employee_id: Optional[str] = None
    bmoni_card_id: Optional[str] = None
    card_name: str
    card_color: str
    currency: str
    card_type: str
    status: str
    spending_limit: Optional[float] = None
    spent_amount: float
    is_frozen: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardUpdateRequest(BaseModel):
    status: Optional[str] = None
    spending_limit: Optional[float] = None
    is_frozen: Optional[bool] = None
