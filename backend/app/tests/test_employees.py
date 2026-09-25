"""
Tests for employee CRUD, validation, search, filtering and sorting.

Owner: Person 1. Covers app/api/v1/employee_routes.py.
"""
from __future__ import annotations

import pytest

from app.models import Employee

VALID = {
    "full_name": "New Person",
    "email": "new@test.com",
    "country": "NG",
    "preferred_currency": "NGN",
    "department": "Engineering",
    "role": "Developer",
    "expected_salary": 400000,
}


# ─── Create ───────────────────────────────────────────────────────────────────

class TestCreate:
    def test_returns_201_and_the_employee(self, client, admin):
        r = client.post("/api/v1/employees", json=VALID, headers=admin)
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == "created"
        assert body["employee"]["email"] == "new@test.com"
        assert body["employee"]["onboarding_status"] == "INVITED"

    def test_input_is_normalised(self, client, admin):
        r = client.post("/api/v1/employees", headers=admin, json={
            "full_name": "  Spaced  Name  ",
            "email": "  MiXeD@TEST.com ",
            "country": "ng",
            "preferred_currency": "ngn",
            "department": "   ",
        })
        e = r.json()["employee"]
        assert e["full_name"] == "Spaced  Name"
        assert e["email"] == "mixed@test.com"
        assert e["country"] == "NG"
        assert e["preferred_currency"] == "NGN"
        assert e["department"] is None

    def test_country_full_name_accepted(self, client, admin):
        r = client.post("/api/v1/employees", headers=admin,
                        json={**VALID, "email": "ng@test.com", "country": "Nigeria"})
        assert r.json()["employee"]["country"] == "NG"

    def test_uk_maps_to_gb_not_uk(self, client, admin):
        """UK is not an ISO-3166 code. Storing it would break payouts."""
        r = client.post("/api/v1/employees", headers=admin,
                        json={**VALID, "email": "uk@test.com", "country": "UK",
                              "preferred_currency": "GBP"})
        assert r.json()["employee"]["country"] == "GB"

    @pytest.mark.parametrize("field,value", [
        ("email", "not-an-email"),
        ("email", ""),
        ("country", "Atlantis"),
        ("country", "N"),
        ("preferred_currency", "XYZ"),
        ("expected_salary", -100),
        ("expected_salary", 0),
        ("expected_salary", "banana"),
        ("full_name", "A"),
        ("full_name", "X" * 101),
    ])
    def test_invalid_field_is_422(self, client, admin, field, value):
        r = client.post("/api/v1/employees", json={**VALID, field: value}, headers=admin)
        assert r.status_code == 422
        assert any(e["field"] == field for e in r.json()["error"]["fields"])

    def test_missing_required_fields(self, client, admin):
        r = client.post("/api/v1/employees", json={"full_name": "Only Name"}, headers=admin)
        assert r.status_code == 422
        bad = {e["field"] for e in r.json()["error"]["fields"]}
        assert {"email", "country"} <= bad

    def test_duplicate_live_email_is_409(self, client, admin):
        r = client.post("/api/v1/employees", json={**VALID, "email": "ada@test.com"}, headers=admin)
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "CONFLICT"

    def test_deleted_employee_is_restored_not_duplicated(self, client, admin, db_session):
        """models.py has a UNIQUE index on (employer_id, email) that ignores
        deleted_at, so re-creating a deleted employee must reuse the row."""
        client.delete("/api/v1/employees/emp-1", headers=admin)
        r = client.post("/api/v1/employees", headers=admin,
                        json={**VALID, "email": "ada@test.com", "full_name": "Ada Returns"})
        assert r.status_code == 201
        assert r.json()["status"] == "restored"
        assert r.json()["employee"]["id"] == "emp-1"
        rows = db_session.query(Employee).filter(Employee.email == "ada@test.com").count()
        assert rows == 1


# ─── Read ─────────────────────────────────────────────────────────────────────

class TestRead:
    def test_detail(self, client, admin):
        body = client.get("/api/v1/employees/emp-1", headers=admin).json()
        assert body["employee"]["full_name"] == "Ada Lovelace"
        assert "onboarding_issue" in body

    def test_missing_is_404(self, client, admin):
        r = client.get("/api/v1/employees/nope", headers=admin)
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"

    def test_deleted_is_404(self, client, admin):
        client.delete("/api/v1/employees/emp-1", headers=admin)
        assert client.get("/api/v1/employees/emp-1", headers=admin).status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

class TestUpdate:
    def test_partial_update_preserves_other_fields(self, client, admin):
        r = client.put("/api/v1/employees/emp-1", json={"department": "Research"}, headers=admin)
        assert r.status_code == 200
        e = r.json()["employee"]
        assert e["department"] == "Research"
        assert e["full_name"] == "Ada Lovelace"      # untouched
        assert e["expected_salary"] == 500000         # untouched

    def test_empty_body_is_400(self, client, admin):
        assert client.put("/api/v1/employees/emp-1", json={}, headers=admin).status_code == 400

    def test_invalid_value_is_422(self, client, admin):
        assert client.put("/api/v1/employees/emp-1",
                          json={"email": "bad"}, headers=admin).status_code == 422

    def test_email_clash_is_409(self, client, admin):
        r = client.put("/api/v1/employees/emp-1", json={"email": "bob@test.com"}, headers=admin)
        assert r.status_code == 409

    def test_setting_same_email_on_self_is_fine(self, client, admin):
        assert client.put("/api/v1/employees/emp-1",
                          json={"email": "ada@test.com"}, headers=admin).status_code == 200

    def test_missing_is_404(self, client, admin):
        assert client.put("/api/v1/employees/nope",
                          json={"department": "X"}, headers=admin).status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

class TestDelete:
    def test_soft_delete_keeps_the_row(self, client, admin, db_session):
        assert client.delete("/api/v1/employees/emp-1", headers=admin).status_code == 200
        row = db_session.query(Employee).filter(Employee.id == "emp-1").first()
        assert row is not None
        assert row.deleted_at is not None

    def test_deleted_disappears_from_the_list(self, client, admin):
        client.delete("/api/v1/employees/emp-1", headers=admin)
        emails = [e["email"] for e in client.get("/api/v1/employees", headers=admin).json()["items"]]
        assert "ada@test.com" not in emails

    def test_missing_is_404(self, client, admin):
        assert client.delete("/api/v1/employees/nope", headers=admin).status_code == 404


# ─── Search / filter / sort ───────────────────────────────────────────────────

class TestListing:
    def names(self, client, hdr, qs=""):
        r = client.get(f"/api/v1/employees?{qs}", headers=hdr)
        assert r.status_code == 200, r.text
        return [e["full_name"] for e in r.json()["items"]]

    def test_no_filters_returns_all(self, client, admin):
        assert len(self.names(client, admin)) == 3

    @pytest.mark.parametrize("qs,expected", [
        ("country=NG", 2),
        ("country=US", 1),
        ("currency=NGN", 2),
        ("department=Engineering", 2),
        ("status=READY", 1),
        ("status=INVITED", 1),
        ("country=NG&currency=NGN", 2),
        ("country=NG&department=Finance", 1),
    ])
    def test_filters(self, client, admin, qs, expected):
        assert len(self.names(client, admin, qs)) == expected

    @pytest.mark.parametrize("qs,expected", [
        ("search=ada", 1),            # name
        ("search=bob@test.com", 1),   # email
        ("search=Finance", 1),        # department
        ("search=Engineer", 2),       # job title
        ("search=ENGINEER", 2),       # case-insensitive
    ])
    def test_search_spans_four_columns(self, client, admin, qs, expected):
        assert len(self.names(client, admin, qs)) == expected

    @pytest.mark.parametrize("term", ["%", "_", "%%", "50%"])
    def test_like_wildcards_are_escaped(self, client, admin, term):
        """Unescaped, '%' would match every row in the table."""
        import urllib.parse
        q = urllib.parse.quote(term)
        assert len(self.names(client, admin, f"search={q}")) == 0

    def test_wildcard_matches_only_the_literal(self, client, admin):
        client.post("/api/v1/employees", headers=admin,
                    json={**VALID, "full_name": "Fifty 50% Bonus", "email": "fifty@test.com"})
        import urllib.parse
        found = self.names(client, admin, f"search={urllib.parse.quote('50%')}")
        assert found == ["Fifty 50% Bonus"]

    def test_sorting(self, client, admin):
        assert self.names(client, admin, "sort_by=full_name&sort_order=asc") == \
            ["Ada Lovelace", "Bob Marley", "Chidi Okonkwo"]
        assert self.names(client, admin, "sort_by=full_name&sort_order=desc") == \
            ["Chidi Okonkwo", "Bob Marley", "Ada Lovelace"]
        assert self.names(client, admin, "sort_by=expected_salary&sort_order=desc")[0] == "Ada Lovelace"

    @pytest.mark.parametrize("qs", [
        "status=BOGUS", "country=Nigeriaaa", "currency=XYZ",
        "sort_by=hashed_password", "sort_by=employer_id", "sort_order=sideways",
    ])
    def test_invalid_filters_are_422_with_guidance(self, client, admin, qs):
        r = client.get(f"/api/v1/employees?{qs}", headers=admin)
        assert r.status_code == 422
        assert len(r.json()["error"]["message"]) > 20   # explains the options

    def test_sort_by_is_an_allowlist(self, client, admin):
        """Interpolating a user-supplied column into ORDER BY is injectable."""
        r = client.get("/api/v1/employees?sort_by=1;DROP TABLE users", headers=admin)
        assert r.status_code == 422

    def test_pagination_metadata(self, client, admin):
        p1 = client.get("/api/v1/employees?limit=2&page=1&sort_by=full_name&sort_order=asc",
                        headers=admin).json()
        assert (p1["total"], p1["total_pages"]) == (3, 2)
        assert (p1["has_prev"], p1["has_next"]) == (False, True)
        assert (p1["prev_page"], p1["next_page"]) == (None, 2)

        p2 = client.get("/api/v1/employees?limit=2&page=2&sort_by=full_name&sort_order=asc",
                        headers=admin).json()
        assert (p2["has_prev"], p2["has_next"]) == (True, False)
        assert (p2["prev_page"], p2["next_page"]) == (1, None)

    def test_pages_do_not_overlap(self, client, admin):
        """Ties need a deterministic tie-breaker or rows repeat across pages."""
        for i in range(7):
            client.post("/api/v1/employees", headers=admin, json={
                "full_name": f"Tie Person {i}", "email": f"tie{i}@test.com",
                "country": "NG", "department": "Same",
            })
        seen = []
        for page in range(1, 6):
            body = client.get(f"/api/v1/employees?limit=3&page={page}&sort_by=department",
                              headers=admin).json()
            seen += [e["id"] for e in body["items"]]
        assert len(seen) == len(set(seen)), "an employee appeared on two pages"
        assert len(seen) == 10
