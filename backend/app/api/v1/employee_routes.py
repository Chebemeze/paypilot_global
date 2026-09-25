"""
PayPilot Global — Employee API Routes
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Employee
from app.schemas import (
    SUPPORTED_CURRENCIES,
    paginate,
    EmployeeResponse,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeMutationResponse,
    EmployeeDeleteResponse,
    EmployeeDetailResponse,
    EmployeeStatsResponse,
    StatsBucket,
    SalaryStats,
    ResendInviteResponse,
    EmployeeImportResponse,
    OnboardingIssueResponse,
    PaginatedResponse,
)
from app.api.auth import (
    get_employer_id,
    get_current_user,
    require_admin,
    require_finance,
)
from app.models import User
from app.services.onboarding_rescue import classify_employee_issue
from app.services.flutterwave_client import flutterwave_client
from app.api.v1.employee_import import import_employees, CsvImportError

router = APIRouter(prefix="/employees", tags=["Employees"])


# ─── Soft-delete / unique-email reconciliation ────────────────────────────────
# models.py declares a UNIQUE index on (employer_id, email):
#
#     Index("ix_employees_employer_email", "employer_id", "email", unique=True)
#
# That index knows nothing about `deleted_at`. So once an employee is soft
# deleted their email stays locked forever and re-adding that person fails with
# a raw database IntegrityError.
#
# models.py is a SHARED file (Person 1 + Person 2), and changing a unique index
# means a migration for the whole team, so we solve it in application code:
# creating an employee whose email belongs to a soft-deleted record RESTORES
# that record instead of inserting a second row.

def _find_archived(db: Session, employer_id: str, email: str) -> Optional[Employee]:
    """Return a soft-deleted employee holding this email, if any."""
    return db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.email == email,
        Employee.deleted_at != None,
    ).first()


def _restore_employee(db: Session, archived: Employee, body) -> Employee:
    """Bring a soft-deleted employee back and overwrite it with fresh details."""
    archived.deleted_at = None
    archived.is_active = True
    archived.onboarding_status = "INVITED"
    archived.full_name = body.full_name
    archived.country = body.country
    archived.department = body.department
    archived.role = body.role
    archived.expected_salary = body.expected_salary
    archived.preferred_currency = body.preferred_currency
    db.commit()
    db.refresh(archived)
    return archived


# ─── Filtering / sorting configuration ────────────────────────────────────────

#: Values Employee.onboarding_status is allowed to hold (see services/
#: onboarding_rescue.py, which branches on exactly these).
ONBOARDING_STATUSES = ("INVITED", "KYC_ACTION_REQUIRED", "WALLET_PENDING", "READY")

#: Columns a caller may sort by. An allowlist, NOT free text — interpolating a
#: user-supplied column name into order_by is a SQL injection vector.
SORTABLE_FIELDS = {
    "created_at": Employee.created_at,
    "updated_at": Employee.updated_at,
    "full_name": Employee.full_name,
    "email": Employee.email,
    "country": Employee.country,
    "department": Employee.department,
    "onboarding_status": Employee.onboarding_status,
    "expected_salary": Employee.expected_salary,
}


def _escape_like(term: str) -> str:
    """Escape LIKE wildcards so a search for "50%" means literally "50%".

    Without this, `%` matches any run of characters and `_` matches any single
    character, so searching for "50%" silently returns every row. The backslash
    is escaped first, otherwise we would double-escape the escapes we add next.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=PaginatedResponse)
def list_employees(
    page: int = Query(1, ge=1, description="1-based page number."),
    limit: int = Query(50, ge=1, le=200, description="Rows per page (max 200)."),
    search: Optional[str] = Query(
        None, max_length=100,
        description="Case-insensitive match against name, email, department or job title.",
    ),
    status: Optional[str] = Query(
        None, description=f"Filter by onboarding status. One of: {', '.join(ONBOARDING_STATUSES)}.",
    ),
    country: Optional[str] = Query(None, description="2-letter ISO country code, e.g. NG."),
    department: Optional[str] = Query(None, max_length=100, description="Exact department match."),
    currency: Optional[str] = Query(None, description="Payout currency, e.g. NGN."),
    is_active: Optional[bool] = Query(None, description="Filter by active flag."),
    sort_by: str = Query(
        "created_at", description=f"Sort column. One of: {', '.join(sorted(SORTABLE_FIELDS))}.",
    ),
    sort_order: str = Query("desc", description="asc or desc."),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """List employees with search, filtering, sorting and pagination.

    Every filter is optional and they combine with AND. Invalid filter values
    return 422 with the accepted options rather than silently returning zero
    rows — a silent empty list is indistinguishable from "no matches" and is a
    miserable thing to debug from the frontend.
    """
    query = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    )

    # ── status ────────────────────────────────────────────────────────────
    if status:
        value = status.strip().upper()
        if value not in ONBOARDING_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"'{status}' is not a valid onboarding status. "
                    f"Valid values: {', '.join(ONBOARDING_STATUSES)}."
                ),
            )
        query = query.filter(Employee.onboarding_status == value)

    # ── country ───────────────────────────────────────────────────────────
    if country:
        value = country.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise HTTPException(
                status_code=422,
                detail=f"'{country}' is not a valid country. Use a 2-letter ISO code, e.g. NG.",
            )
        query = query.filter(Employee.country == value)

    # ── currency ──────────────────────────────────────────────────────────
    if currency:
        value = currency.strip().upper()
        if value not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"'{currency}' is not a supported currency. "
                    f"Supported: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
                ),
            )
        query = query.filter(Employee.preferred_currency == value)

    # ── department ────────────────────────────────────────────────────────
    if department:
        query = query.filter(Employee.department == department.strip())

    # ── is_active ─────────────────────────────────────────────────────────
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)

    # ── search ────────────────────────────────────────────────────────────
    if search and search.strip():
        term = f"%{_escape_like(search.strip())}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(term, escape="\\"),
                Employee.email.ilike(term, escape="\\"),
                Employee.department.ilike(term, escape="\\"),
                Employee.role.ilike(term, escape="\\"),
            )
        )

    # ── sorting ───────────────────────────────────────────────────────────
    sort_key = sort_by.strip().lower()
    if sort_key not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot sort by '{sort_by}'. "
                f"Sortable fields: {', '.join(sorted(SORTABLE_FIELDS))}."
            ),
        )

    direction = sort_order.strip().lower()
    if direction not in ("asc", "desc"):
        raise HTTPException(
            status_code=422,
            detail=f"sort_order must be 'asc' or 'desc', got '{sort_order}'.",
        )

    column = SORTABLE_FIELDS[sort_key]
    order = column.asc() if direction == "asc" else column.desc()

    # Tie-break on id. Without it, rows with equal sort values can come back in
    # a different order on each request, so an employee can appear on both page
    # 1 and page 2 — or on neither.
    query = query.order_by(order, Employee.id.asc())

    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    return paginate(
        items=[EmployeeResponse.model_validate(e) for e in items],
        page=page,
        limit=limit,
        total=total,
    )


# ─── Stats ────────────────────────────────────────────────────────────────────
# NOTE ON ROUTE ORDER: this MUST stay above @router.get("/{employee_id}").
# FastAPI matches routes in declaration order, so if "/{employee_id}" came
# first it would happily accept "stats" as an employee id and return 404.
# Static path segments always go before the parameterised ones.


def _bucket(rows: list[tuple], total: int) -> list[StatsBucket]:
    """Turn (value, count) rows into sorted buckets with percentages.

    Sorted by count descending so the dashboard's "top countries" list needs no
    client-side sorting, then by name so equal counts have a stable order
    instead of shuffling between requests.
    """
    return [
        StatsBucket(
            value=value,
            count=count,
            percentage=round(count * 100 / total, 1) if total else 0.0,
        )
        for value, count in sorted(rows, key=lambda r: (-r[1], str(r[0])))
    ]


@router.get("/stats", response_model=EmployeeStatsResponse)
def employee_stats(
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Aggregate employee statistics for the dashboard.

    Read-only, so any authenticated role may call it.

    Every query below is scoped to the caller's employer_id and excludes
    soft-deleted rows. Counting is done with SQL GROUP BY rather than by
    loading employees into Python: an employer with 5,000 staff would otherwise
    pull 5,000 ORM objects across the wire to produce about 20 integers.
    """
    scope = [Employee.employer_id == employer_id, Employee.deleted_at == None]  # noqa: E711

    total = db.query(func.count(Employee.id)).filter(*scope).scalar() or 0
    active = db.query(func.count(Employee.id)).filter(
        *scope, Employee.is_active == True  # noqa: E712
    ).scalar() or 0
    ready = db.query(func.count(Employee.id)).filter(
        *scope, Employee.onboarding_status == "READY"
    ).scalar() or 0
    missing_salary = db.query(func.count(Employee.id)).filter(
        *scope, Employee.expected_salary == None  # noqa: E711
    ).scalar() or 0

    def grouped(column, *, coalesce_to: Optional[str] = None):
        col = func.coalesce(column, coalesce_to) if coalesce_to else column
        return db.query(col, func.count(Employee.id)).filter(*scope).group_by(col).all()

    # department is nullable; COALESCE keeps those employees visible in the
    # breakdown as "Unassigned" instead of silently dropping them, which would
    # make the column fail to add up to headcount.
    by_department = grouped(Employee.department, coalesce_to="Unassigned")

    salary_rows = db.query(
        Employee.preferred_currency,
        func.count(Employee.id),
        func.sum(Employee.expected_salary),
        func.avg(Employee.expected_salary),
        func.min(Employee.expected_salary),
        func.max(Employee.expected_salary),
    ).filter(
        *scope, Employee.expected_salary != None  # noqa: E711
    ).group_by(Employee.preferred_currency).all()

    return EmployeeStatsResponse(
        total_employees=total,
        active=active,
        inactive=total - active,
        onboarding_complete=ready,
        onboarding_pending=total - ready,
        completion_rate=round(ready * 100 / total, 1) if total else 0.0,
        missing_salary=missing_salary,
        by_country=_bucket(grouped(Employee.country), total),
        by_currency=_bucket(grouped(Employee.preferred_currency), total),
        by_status=_bucket(grouped(Employee.onboarding_status), total),
        by_department=_bucket(by_department, total),
        salary_by_currency=[
            SalaryStats(
                currency=cur,
                employees=cnt,
                total=round(float(tot or 0), 2),
                average=round(float(avg or 0), 2),
                minimum=round(float(lo or 0), 2),
                maximum=round(float(hi or 0), 2),
            )
            for cur, cnt, tot, avg, lo, hi in sorted(salary_rows, key=lambda r: -(r[2] or 0))
        ],
    )


@router.get("/{employee_id}", response_model=EmployeeDetailResponse)
def get_employee(
    employee_id: str,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Get employee detail with onboarding issue classification."""
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    issue = classify_employee_issue(employee)

    return EmployeeDetailResponse(
        employee=EmployeeResponse.model_validate(employee),
        onboarding_issue=issue,
    )


@router.post("", response_model=EmployeeMutationResponse, status_code=201)
def create_employee(
    body: EmployeeCreateRequest,
    _actor: User = Depends(require_finance),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Create a new employee.

    Requires role ADMIN or FINANCE. The payload is validated by
    EmployeeCreateRequest, so email/country/currency are already normalised
    (lowercased / uppercased) and within the database column limits.
    """
    # A live employee already owns this email -> genuine conflict.
    existing = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.email == body.email,
        Employee.deleted_at == None,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An employee with the email '{body.email}' already exists.",
        )

    # An ARCHIVED employee owns this email -> restore them rather than hitting
    # the unique index on (employer_id, email). See _find_archived above.
    archived = _find_archived(db, employer_id, body.email)
    if archived:
        restored = _restore_employee(db, archived, body)
        return EmployeeMutationResponse(
            employee=EmployeeResponse.model_validate(restored),
            status="restored",
        )

    employee = Employee(
        employer_id=employer_id,
        full_name=body.full_name,
        email=body.email,
        country=body.country,
        department=body.department,
        role=body.role,
        expected_salary=body.expected_salary,
        preferred_currency=body.preferred_currency,
        onboarding_status="INVITED",
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    return EmployeeMutationResponse(
        employee=EmployeeResponse.model_validate(employee),
        status="created",
    )


@router.put("/{employee_id}", response_model=EmployeeMutationResponse)
def update_employee(
    employee_id: str,
    body: EmployeeUpdateRequest,
    _actor: User = Depends(require_finance),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Partially update an employee.

    Requires role ADMIN or FINANCE. Only the fields present in the request body
    are changed — omitted fields are left untouched. Sending an empty body is a
    400, since that is almost always a frontend bug rather than an intent.
    """
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # exclude_unset=True is the key: it tells us which fields the caller actually
    # sent, so we can tell "field omitted" apart from "field explicitly set".
    updates = body.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No fields to update. Send at least one field.",
        )

    # Email changes need a uniqueness re-check against other employees.
    new_email = updates.get("email")
    if new_email and new_email != employee.email:
        clash = db.query(Employee).filter(
            Employee.employer_id == employer_id,
            Employee.email == new_email,
            Employee.id != employee_id,
            Employee.deleted_at == None,
        ).first()
        if clash:
            raise HTTPException(
                status_code=409,
                detail=f"The email '{new_email}' is already used by another employee.",
            )

    for field, value in updates.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    return EmployeeMutationResponse(
        employee=EmployeeResponse.model_validate(employee),
        status="updated",
    )


@router.delete("/{employee_id}", response_model=EmployeeDeleteResponse)
def delete_employee(
    employee_id: str,
    _actor: User = Depends(require_admin),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Soft delete an employee."""
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    from datetime import datetime
    employee.deleted_at = datetime.utcnow()
    db.commit()

    return EmployeeDeleteResponse(employee_id=employee_id)


@router.post("/invite", response_model=EmployeeMutationResponse, status_code=201)
async def invite_employee(
    body: EmployeeCreateRequest,
    user: User = Depends(require_finance),
    db: Session = Depends(get_db),
):
    """Create an employee AND register them as a Flutterwave customer.

    Requires role ADMIN or FINANCE. Same payload as POST /employees; the extra
    step is the Flutterwave customer creation. If Flutterwave is unreachable the
    employee is still created — the customer id can be backfilled later.
    """
    employer_id = user.employer_id

    existing = db.query(Employee).filter(
        Employee.employer_id == employer_id,
        Employee.email == body.email,
        Employee.deleted_at == None,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An employee with the email '{body.email}' already exists.",
        )

    # Reuse an archived record if one holds this email (see _find_archived).
    archived = _find_archived(db, employer_id, body.email)
    if archived:
        employee = _restore_employee(db, archived, body)
    else:
        employee = Employee(
            employer_id=employer_id,
            full_name=body.full_name,
            email=body.email,
            country=body.country,
            department=body.department,
            role=body.role,
            expected_salary=body.expected_salary,
            preferred_currency=body.preferred_currency,
            onboarding_status="INVITED",
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

    # Create Flutterwave customer
    try:
        customer_response = await flutterwave_client.create_customer(
            email=employee.email,
            name=employee.full_name,
            phone=None
        )
        
        if customer_response.get("status") == "success":
            customer_data = customer_response.get("data", {})
            employee.flutterwave_customer_id = customer_data.get("id")
            db.commit()
            db.refresh(employee)
    except Exception as e:
        # Log error but don't fail the employee creation
        # Customer can be created later
        pass

    return EmployeeMutationResponse(
        employee=EmployeeResponse.model_validate(employee),
        status="invited",
    )



@router.post("/import", response_model=EmployeeImportResponse)
async def import_employees_csv(
    file: UploadFile = File(..., description="CSV file with employee rows."),
    dry_run: bool = Form(
        False,
        description="Validate and report without writing anything. Do this first.",
    ),
    _actor: User = Depends(require_finance),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Bulk-create employees from a CSV file.

    Requires role ADMIN or FINANCE.

    Required columns: full_name, email, country.
    Optional: preferred_currency, department, role, expected_salary.
    Common header aliases are accepted (name, employee_name, job_title, salary,
    amount, dept, ...) and country may be an ISO code or a full name.

    Each row is handled independently — one bad row does not stop the rest.
    Every row comes back with its spreadsheet line number and outcome:

        created   inserted
        restored  a previously deleted employee was brought back
        skipped   duplicate (already on the books, or repeated in the file)
        failed    validation error, see `errors`

    Send `dry_run=true` first to preview the outcome without writing.
    """
    raw = await file.read()

    max_bytes = settings.csv_max_size_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is larger than the {settings.csv_max_size_mb}MB limit.",
        )

    if not raw.strip():
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")

    # Excel on Windows commonly saves CSVs as cp1252, not UTF-8.
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            content = raw.decode("cp1252")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=422,
                detail="Could not decode the file. Save it as UTF-8 CSV and try again.",
            )

    try:
        report = import_employees(
            db=db,
            employer_id=employer_id,
            content=content,
            dry_run=dry_run,
            max_rows=settings.csv_max_rows,
        )
    except CsvImportError as exc:
        message = exc.message if not exc.hint else f"{exc.message} {exc.hint}"
        raise HTTPException(status_code=422, detail=message)

    return EmployeeImportResponse(**report)


@router.post("/{employee_id}/resend-invite", response_model=ResendInviteResponse)
def resend_invite(
    employee_id: str,
    _actor: User = Depends(require_finance),
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Resend the BMONI app invite to an employee."""
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.onboarding_status != "INVITED":
        raise HTTPException(status_code=400, detail="Employee is not in INVITED status.")

    # In production, would call BMONI invite_employee
    return ResendInviteResponse(employee_id=employee_id)


@router.post("/{employee_id}/generate-reminder", response_model=OnboardingIssueResponse)
def generate_reminder(
    employee_id: str,
    employer_id: str = Depends(get_employer_id),
    db: Session = Depends(get_db),
):
    """Generate an onboarding rescue reminder for a stuck employee."""
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.employer_id == employer_id,
        Employee.deleted_at == None,
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    issue = classify_employee_issue(employee)
    if not issue:
        raise HTTPException(status_code=400, detail="Employee is not stuck — no reminder needed.")

    return OnboardingIssueResponse(**issue)
