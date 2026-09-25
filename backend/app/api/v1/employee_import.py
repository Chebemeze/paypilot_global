"""
PayPilot Global — Bulk employee CSV import.

Owner: Person 1 (Backend Core — Auth & Employees)

WHY THIS FILE IS HERE AND NOT IN app/services/
----------------------------------------------
Business logic normally belongs in app/services/, but that directory is owned by
Person 2 (see PROJECT_SPLIT.md). Putting an employee-import module there would
mean their sign-off on every change and a standing merge-conflict risk on a file
only Person 1 ever touches. It lives beside the employee routes instead.

The one thing that IS shared is the country/currency normalisation — that comes
from app/schemas/schemas.py so this importer and Person 2's payroll importer
agree on what "Nigeria" means.

DESIGN NOTES
------------
* Row-level isolation — one bad row does not abort the other 499.
* Every row reports its own 1-based line number, matching what the user sees in
  Excel, so "row 37 is wrong" is actionable.
* dry_run=true validates and reports without writing anything. Always offer a
  preview before a bulk write.
* Duplicate emails are detected both against the database AND within the file
  itself — the same person listed twice in one spreadsheet is a common mistake.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Employee
from app.schemas import EmployeeCreateRequest

#: Column headers we accept, mapped to the EmployeeCreateRequest field they fill.
#: Multiple aliases per field because every HR system exports different headers.
COLUMN_ALIASES: dict[str, str] = {
    # full_name
    "full_name": "full_name",
    "fullname": "full_name",
    "name": "full_name",
    "employee_name": "full_name",
    "employee": "full_name",
    # email
    "email": "email",
    "email_address": "email",
    "work_email": "email",
    "e-mail": "email",
    # country
    "country": "country",
    "country_code": "country",
    "location": "country",
    # currency
    "preferred_currency": "preferred_currency",
    "currency": "preferred_currency",
    "pay_currency": "preferred_currency",
    # department
    "department": "department",
    "dept": "department",
    "team": "department",
    # role / job title
    "role": "role",
    "job_title": "role",
    "title": "role",
    "position": "role",
    # salary
    "expected_salary": "expected_salary",
    "salary": "expected_salary",
    "amount": "expected_salary",
    "gross_salary": "expected_salary",
}

#: Headers that must be present for the file to be importable at all.
REQUIRED_FIELDS = ("full_name", "email", "country")


def _normalise_header(name: str) -> str:
    """'  Full Name ' / 'E-Mail' -> 'full_name' / 'e_mail'.

    Header matching has to be forgiving: the same column is exported as
    "Full Name", "full name", "FULL_NAME" and "Full-Name" by different systems.
    """
    return (name or "").strip().lower().replace(" ", "_").replace("-", "_")


# Run every alias key through the same normaliser used on incoming headers.
# Without this, an alias written as "e-mail" could never match, because the
# header "E-Mail" arrives normalised to "e_mail". Normalising both sides means
# a new alias can be added in any spelling and still work.
COLUMN_ALIASES = {_normalise_header(k): v for k, v in COLUMN_ALIASES.items()}


@dataclass
class RowResult:
    """Outcome for a single CSV row."""

    row: int                      # 1-based line number as seen in a spreadsheet
    email: str = ""
    status: str = ""              # created | restored | skipped | failed
    message: str = ""
    errors: list[dict[str, str]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "row": self.row,
            "email": self.email,
            "status": self.status,
            "message": self.message,
        }
        if self.errors:
            out["errors"] = self.errors
        return out


class CsvImportError(Exception):
    """The file as a whole is unusable — wrong headers, not CSV, empty, etc."""

    def __init__(self, message: str, *, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint


def _strip_bom(text: str) -> str:
    """Excel saves CSVs with a UTF-8 BOM, which corrupts the first header."""
    return text.lstrip("\ufeff")


def parse_csv(content: str) -> tuple[list[dict[str, str]], list[str]]:
    """Parse CSV text into normalised row dicts.

    Returns (rows, recognised_fields). Raises CsvImportError if the file cannot
    be used at all.
    """
    text = _strip_bom(content).strip()
    if not text:
        raise CsvImportError("The file is empty.")

    try:
        # Sniff the delimiter — European exports often use ';'
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.get_dialect("excel")
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        raw_rows = list(reader)
    except csv.Error as exc:
        raise CsvImportError(f"Could not read the file as CSV: {exc}")

    if reader.fieldnames is None:
        raise CsvImportError("The file has no header row.")

    # Map the file's headers onto our field names.
    header_map: dict[str, str] = {}
    unknown: list[str] = []
    for raw_header in reader.fieldnames:
        key = _normalise_header(raw_header)
        target = COLUMN_ALIASES.get(key)
        if target:
            header_map[raw_header] = target
        elif key:
            unknown.append(raw_header.strip())

    recognised = sorted(set(header_map.values()))
    missing = [f for f in REQUIRED_FIELDS if f not in recognised]
    if missing:
        raise CsvImportError(
            f"Missing required column(s): {', '.join(missing)}.",
            hint=(
                f"Found columns: {', '.join(reader.fieldnames)}. "
                f"Required: {', '.join(REQUIRED_FIELDS)}. "
                "Accepted aliases include name/employee_name for full_name and "
                "job_title/title for role."
            ),
        )

    rows: list[dict[str, str]] = []
    for raw in raw_rows:
        mapped: dict[str, str] = {}
        for raw_header, target in header_map.items():
            value = raw.get(raw_header)
            if value is not None and str(value).strip():
                mapped[target] = str(value).strip()
        rows.append(mapped)

    return rows, recognised


def _coerce_salary(row: dict[str, str]) -> None:
    """Turn '₦450,000.00' / '1 200' into something float() accepts.

    Spreadsheets are full of thousands separators and currency symbols; failing
    an otherwise-valid row over a comma would be needlessly strict.
    """
    raw = row.get("expected_salary")
    # Strip before the emptiness test: a cell holding only spaces is an empty
    # cell, not a salary of "   ". parse_csv already strips, but this helper is
    # public and must not depend on its caller having done so.
    if raw is None or not str(raw).strip():
        row.pop("expected_salary", None)
        return
    raw = str(raw).strip()

    cleaned = "".join(ch for ch in str(raw) if ch.isdigit() or ch in ".-")
    if cleaned in ("", "-", ".", "-."):
        # Leave the original in place so validation reports a clear error.
        return
    row["expected_salary"] = cleaned


def import_employees(
    db: Session,
    employer_id: str,
    content: str,
    *,
    dry_run: bool = False,
    max_rows: int = 5000,
) -> dict[str, Any]:
    """Validate and (unless dry_run) insert employees from CSV text.

    Never raises for a bad row — bad rows are reported in `results`.
    Raises CsvImportError only when the whole file is unusable.
    """
    rows, recognised = parse_csv(content)

    if not rows:
        raise CsvImportError("The file has a header row but no data rows.")

    if len(rows) > max_rows:
        raise CsvImportError(
            f"The file has {len(rows)} data rows, which exceeds the limit of {max_rows}.",
            hint="Split the file into smaller batches and import them one at a time.",
        )

    # Emails already taken by LIVE employees for this employer.
    live_emails = {
        e[0] for e in db.query(Employee.email).filter(
            Employee.employer_id == employer_id,
            Employee.deleted_at == None,
        ).all()
    }
    # Emails held by ARCHIVED employees — importing these restores the record.
    archived: dict[str, Employee] = {
        e.email: e for e in db.query(Employee).filter(
            Employee.employer_id == employer_id,
            Employee.deleted_at != None,
        ).all()
    }

    results: list[RowResult] = []
    seen_in_file: dict[str, int] = {}
    to_insert: list[Employee] = []
    to_restore: list[tuple[Employee, EmployeeCreateRequest]] = []

    for index, row in enumerate(rows):
        # +2 == 1 for the header line, 1 because spreadsheets are 1-based.
        line = index + 2
        result = RowResult(row=line, email=row.get("email", ""))

        if not any(row.values()):
            result.status = "skipped"
            result.message = "Blank row."
            results.append(result)
            continue

        _coerce_salary(row)

        try:
            payload = EmployeeCreateRequest(**row)
        except ValidationError as exc:
            result.status = "failed"
            result.errors = [
                {
                    "field": ".".join(str(p) for p in err.get("loc", ())) or "row",
                    "message": str(err.get("msg", "")).removeprefix("Value error, "),
                }
                for err in exc.errors()
            ]
            result.message = "; ".join(
                f"{e['field']}: {e['message']}" for e in result.errors
            )
            results.append(result)
            continue

        result.email = payload.email

        # Duplicate inside the uploaded file itself.
        if payload.email in seen_in_file:
            result.status = "skipped"
            result.message = (
                f"Duplicate of row {seen_in_file[payload.email]} in this file."
            )
            results.append(result)
            continue
        seen_in_file[payload.email] = line

        # Already on the books.
        if payload.email in live_emails:
            result.status = "skipped"
            result.message = "An employee with this email already exists."
            results.append(result)
            continue

        # Previously deleted — restore rather than collide with the unique index
        # on (employer_id, email). Same rule as POST /employees.
        if payload.email in archived:
            result.status = "restored"
            result.message = "Restored a previously deleted employee."
            to_restore.append((archived[payload.email], payload))
            results.append(result)
            continue

        result.status = "created"
        to_insert.append(
            Employee(
                employer_id=employer_id,
                full_name=payload.full_name,
                email=payload.email,
                country=payload.country,
                department=payload.department,
                role=payload.role,
                expected_salary=payload.expected_salary,
                preferred_currency=payload.preferred_currency,
                onboarding_status="INVITED",
            )
        )
        results.append(result)

    # ── commit ────────────────────────────────────────────────────────────
    # All-or-nothing: if anything fails mid-write the caller must not be left
    # with half an import and no way to know where it stopped.
    if not dry_run and (to_insert or to_restore):
        for employee, payload in to_restore:
            employee.deleted_at = None
            employee.is_active = True
            employee.onboarding_status = "INVITED"
            employee.full_name = payload.full_name
            employee.country = payload.country
            employee.department = payload.department
            employee.role = payload.role
            employee.expected_salary = payload.expected_salary
            employee.preferred_currency = payload.preferred_currency
        db.add_all(to_insert)
        db.commit()

    counts = {
        "created": sum(1 for r in results if r.status == "created"),
        "restored": sum(1 for r in results if r.status == "restored"),
        "skipped": sum(1 for r in results if r.status == "skipped"),
        "failed": sum(1 for r in results if r.status == "failed"),
    }

    return {
        "dry_run": dry_run,
        "total_rows": len(rows),
        "recognised_columns": recognised,
        **counts,
        "results": [r.as_dict() for r in results],
    }
