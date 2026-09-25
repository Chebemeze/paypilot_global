"""
Tests for bulk CSV employee import.

Owner: Person 1. Covers app/api/v1/employee_import.py and POST /employees/import.
"""
from __future__ import annotations

import io

import pytest

from app.api.v1.employee_import import (
    _normalise_header, _strip_bom, _coerce_salary, parse_csv, CsvImportError,
)

URL = "/api/v1/employees/import"

HEADER = "full_name,email,country\n"
GOOD = HEADER + "Zara Zed,zara@test.com,Nigeria\nYuri Yang,yuri@test.com,US\n"


def upload(client, headers, csv_text, *, name="employees.csv", dry_run=None, encoding="utf-8"):
    data = csv_text.encode(encoding) if isinstance(csv_text, str) else csv_text
    # dry_run is a Form field on a multipart request, not a query param.
    form = {} if dry_run is None else {"dry_run": str(dry_run).lower()}
    return client.post(
        URL,
        files={"file": (name, io.BytesIO(data), "text/csv")},
        data=form,
        headers=headers,
    )


# ─── Pure helpers (no HTTP, no DB) ────────────────────────────────────────────

class TestHelpers:
    @pytest.mark.parametrize("raw,expected", [
        ("Full Name", "full_name"), ("  E-Mail  ", "e_mail"),
        ("EXPECTED SALARY", "expected_salary"), ("Job-Title", "job_title"),
    ])
    def test_normalise_header(self, raw, expected):
        assert _normalise_header(raw) == expected

    def test_strip_bom(self):
        """Excel prefixes UTF-8 CSVs with \\ufeff, which corrupts column one."""
        assert _strip_bom("\ufefffull_name") == "full_name"
        assert _strip_bom("full_name") == "full_name"

    @pytest.mark.parametrize("raw,expected", [
        ("450000", "450000"), ("450,000", "450000"), ("\u20a6450,000.00", "450000.00"),
        ("$1,200.50", "1200.50"), (" 300 ", "300"),
    ])
    def test_coerce_salary_strips_formatting(self, raw, expected):
        """_coerce_salary edits the row in place and leaves the float() to Pydantic."""
        row = {"expected_salary": raw}
        _coerce_salary(row)
        assert row["expected_salary"] == expected

    @pytest.mark.parametrize("raw", ["", "   ", None])
    def test_blank_salary_is_dropped_entirely(self, raw):
        """Dropping the key lets the schema default apply instead of failing."""
        row = {"expected_salary": raw}
        _coerce_salary(row)
        assert "expected_salary" not in row

    @pytest.mark.parametrize("raw", ["abc", "-", "."])
    def test_unsalvageable_salary_is_left_for_validation_to_report(self, raw):
        """Silently dropping junk would hide a typo; keep it so the row fails loudly."""
        row = {"expected_salary": raw}
        _coerce_salary(row)
        assert row["expected_salary"] == raw

    @pytest.mark.parametrize("delim", [",", ";", "\t", "|"])
    def test_parse_csv_sniffs_delimiters(self, delim):
        text = delim.join(["full_name", "email", "country"]) + "\n" + \
               delim.join(["Zara", "z@test.com", "NG"]) + "\n"
        rows, recognised = parse_csv(text)
        assert recognised == ["country", "email", "full_name"]
        assert rows[0]["email"] == "z@test.com"

    def test_parse_csv_maps_aliases(self):
        rows, recognised = parse_csv("Employee Name,E-Mail,Country,Job Title,Salary\n"
                                     "Zara,z@test.com,NG,Dev,500\n")
        assert set(recognised) >= {"full_name", "email", "country", "role", "expected_salary"}
        assert rows[0]["full_name"] == "Zara"

    @pytest.mark.parametrize("payload", [
        "", "   \n  \n",
        "nickname,fav_colour\nZara,blue\n",         # no required columns
        "full_name,email\nZara,z@test.com\n",       # country missing
    ])
    def test_parse_csv_rejects_unusable_files(self, payload):
        with pytest.raises(CsvImportError):
            parse_csv(payload)

    def test_header_only_file_yields_no_rows(self):
        rows, recognised = parse_csv(HEADER)
        assert rows == []


# ─── Access control ───────────────────────────────────────────────────────────

class TestAccess:
    def test_anonymous_is_401(self, client, seeded):
        assert upload(client, {}, GOOD).status_code == 401

    def test_viewer_is_403(self, client, viewer):
        assert upload(client, viewer, GOOD).status_code == 403

    def test_finance_allowed(self, client, finance):
        assert upload(client, finance, GOOD).status_code == 200

    def test_admin_allowed(self, client, admin):
        assert upload(client, admin, GOOD).status_code == 200


# ─── Happy path ───────────────────────────────────────────────────────────────

class TestImport:
    def test_creates_employees(self, client, admin):
        body = upload(client, admin, GOOD).json()
        assert (body["total_rows"], body["created"], body["failed"]) == (2, 2, 0)
        assert body["dry_run"] is False
        assert len(client.get("/api/v1/employees", headers=admin).json()["items"]) == 5

    def test_row_numbers_match_the_spreadsheet(self, client, admin):
        """Row 1 is the header, so the first data row must report row 2 —
        otherwise 'fix row 7' points the user at the wrong line in Excel."""
        results = upload(client, admin, GOOD).json()["results"]
        assert [r["row"] for r in results] == [2, 3]

    def test_country_names_are_converted(self, client, admin):
        upload(client, admin, HEADER + "Zara Zed,zara@test.com,United Kingdom\n")
        e = client.get("/api/v1/employees?search=zara", headers=admin).json()["items"][0]
        assert e["country"] == "GB"

    def test_recognised_columns_reported(self, client, admin):
        body = upload(client, admin, "Employee Name,E-Mail,Country,Salary\n"
                                     "Zara,z@test.com,NG,500\n").json()
        assert set(body["recognised_columns"]) >= {"full_name", "email", "country",
                                                   "expected_salary"}

    def test_unknown_columns_are_ignored_not_fatal(self, client, admin):
        body = upload(client, admin, "full_name,email,country,favourite_colour\n"
                                     "Zara,z@test.com,NG,blue\n").json()
        assert body["created"] == 1

    def test_utf8_bom_file_works(self, client, admin):
        body = upload(client, admin, "\ufeff" + GOOD).json()
        assert body["created"] == 2

    def test_crlf_line_endings(self, client, admin):
        body = upload(client, admin, GOOD.replace("\n", "\r\n")).json()
        assert body["created"] == 2


# ─── Dry run ──────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_writes_nothing(self, client, admin):
        body = upload(client, admin, GOOD, dry_run=True).json()
        assert body["dry_run"] is True
        assert body["created"] == 2                     # what *would* happen
        assert len(client.get("/api/v1/employees", headers=admin).json()["items"]) == 3

    def test_dry_run_then_real_run_agree(self, client, admin):
        preview = upload(client, admin, GOOD, dry_run=True).json()
        real = upload(client, admin, GOOD, dry_run=False).json()
        assert [r["status"] for r in preview["results"]] == [r["status"] for r in real["results"]]

    def test_dry_run_still_reports_errors(self, client, admin):
        body = upload(client, admin, HEADER + "Zara,zara@test.com,Atlantis\n",
                      dry_run=True).json()
        assert body["failed"] == 1


# ─── Per-row outcomes ─────────────────────────────────────────────────────────

class TestRowOutcomes:
    def test_one_bad_row_does_not_abort_the_batch(self, client, admin):
        body = upload(client, admin, HEADER +
                      "Zara Zed,zara@test.com,NG\n"
                      "Broken,not-an-email,NG\n"
                      "Yuri Yang,yuri@test.com,US\n").json()
        assert (body["created"], body["failed"]) == (2, 1)
        assert [r["status"] for r in body["results"]] == ["created", "failed", "created"]

    def test_failed_rows_carry_actionable_errors(self, client, admin):
        body = upload(client, admin, HEADER + "Broken,not-an-email,Atlantis\n").json()
        row = body["results"][0]
        assert row["row"] == 2
        # errors[] is a list of {field, message} so the UI can highlight the cell.
        assert row["errors"]
        fields = {e["field"] for e in row["errors"]}
        assert {"email", "country"} <= fields
        assert all(e["message"].strip() for e in row["errors"])

    def test_existing_employee_is_skipped(self, client, admin):
        body = upload(client, admin, HEADER + "Ada Again,ada@test.com,NG\n").json()
        assert (body["skipped"], body["created"]) == (1, 0)

    def test_deleted_employee_is_restored(self, client, admin):
        client.delete("/api/v1/employees/emp-1", headers=admin)
        body = upload(client, admin, HEADER + "Ada Again,ada@test.com,NG\n").json()
        assert body["restored"] == 1
        assert client.get("/api/v1/employees/emp-1", headers=admin).status_code == 200

    def test_duplicate_within_the_same_file(self, client, admin):
        """Both rows are new to the DB, so only in-file tracking catches this."""
        body = upload(client, admin, HEADER +
                      "Zara One,zara@test.com,NG\n"
                      "Zara Two,zara@test.com,NG\n").json()
        assert body["created"] == 1
        assert body["results"][1]["status"] in ("skipped", "failed")

    def test_blank_rows_are_ignored(self, client, admin):
        body = upload(client, admin, HEADER + "Zara,zara@test.com,NG\n\n,,\n").json()
        assert body["created"] == 1
        assert body["failed"] == 0

    def test_import_is_tenant_scoped(self, client, rival):
        """Importing an email another employer owns must not touch their row."""
        body = upload(client, rival, HEADER + "Ada Copy,ada@test.com,NG\n").json()
        assert body["created"] == 1


# ─── Whole-file rejections ────────────────────────────────────────────────────

class TestFileRejections:
    @pytest.mark.parametrize("payload", [
        "", "   \n", HEADER, "nickname,colour\nZara,blue\n", "full_name,email\nZara,z@t.com\n",
    ])
    def test_unusable_file_is_422(self, client, admin, payload):
        r = upload(client, admin, payload)
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_too_many_rows_is_422(self, client, admin):
        big = HEADER + "".join(f"P{i},p{i}@test.com,NG\n" for i in range(5001))
        assert upload(client, admin, big).status_code == 422

    def test_oversized_file_is_413(self, client, admin):
        payload = HEADER + "X,pad@test.com," + ("N" * 6 * 1024 * 1024) + "\n"
        assert upload(client, admin, payload).status_code == 413

    def test_binary_upload_is_rejected_cleanly(self, client, admin):
        """A user picking the wrong file must get a 4xx, never a 500."""
        r = upload(client, admin, b"%PDF-1.4\n\x00\x01\x02binary junk\xff\xfe", name="cv.pdf")
        assert 400 <= r.status_code < 500

    def test_no_file_is_422(self, client, admin):
        assert client.post(URL, headers=admin).status_code == 422
