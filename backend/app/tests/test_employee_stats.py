"""
Tests for GET /employees/stats.

Owner: Person 1. Covers the stats endpoint in app/api/v1/employee_routes.py.
"""
from __future__ import annotations

import pytest

URL = "/api/v1/employees/stats"


def bucket(buckets, value):
    """Pull one row out of a breakdown list, or None."""
    return next((b for b in buckets if b["value"] == value), None)


@pytest.fixture
def stats(client, admin):
    r = client.get(URL, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()


# ─── Routing ──────────────────────────────────────────────────────────────────

class TestRouting:
    def test_stats_is_not_swallowed_by_the_employee_id_route(self, client, admin):
        """FastAPI matches routes in declaration order.

        If GET /{employee_id} were declared first it would treat "stats" as an
        id and return 404. This test fails the moment someone reorders them.
        """
        r = client.get(URL, headers=admin)
        assert r.status_code == 200
        assert "total_employees" in r.json()

    def test_a_real_employee_id_still_works(self, client, admin):
        """The guard above must not have broken normal detail lookups."""
        assert client.get("/api/v1/employees/emp-1", headers=admin).status_code == 200


# ─── Access ───────────────────────────────────────────────────────────────────

class TestAccess:
    def test_anonymous_is_401(self, client, seeded):
        assert client.get(URL).status_code == 401

    @pytest.mark.parametrize("role", ["admin", "finance", "viewer"])
    def test_all_authenticated_roles_may_read(self, client, request, role):
        hdr = request.getfixturevalue(role)
        assert client.get(URL, headers=hdr).status_code == 200


# ─── Headline numbers ─────────────────────────────────────────────────────────

class TestHeadlineCounts:
    def test_totals_match_the_fixture(self, stats):
        assert stats["total_employees"] == 3
        assert stats["active"] == 3
        assert stats["inactive"] == 0

    def test_onboarding_split(self, stats):
        assert stats["onboarding_complete"] == 1          # one READY
        assert stats["onboarding_pending"] == 2
        assert stats["completion_rate"] == pytest.approx(33.3)

    def test_complete_and_pending_always_sum_to_total(self, stats):
        assert stats["onboarding_complete"] + stats["onboarding_pending"] == \
            stats["total_employees"]

    def test_active_and_inactive_always_sum_to_total(self, stats):
        assert stats["active"] + stats["inactive"] == stats["total_employees"]

    def test_deleted_employees_are_excluded(self, client, admin):
        before = client.get(URL, headers=admin).json()["total_employees"]
        client.delete("/api/v1/employees/emp-1", headers=admin)
        after = client.get(URL, headers=admin).json()["total_employees"]
        assert after == before - 1

    def test_new_employee_moves_the_numbers(self, client, admin):
        client.post("/api/v1/employees", headers=admin, json={
            "full_name": "Zara Zed", "email": "zara@test.com",
            "country": "KE", "preferred_currency": "KES", "expected_salary": 100000,
        })
        s = client.get(URL, headers=admin).json()
        assert s["total_employees"] == 4
        assert bucket(s["by_country"], "KE")["count"] == 1


# ─── Breakdowns ───────────────────────────────────────────────────────────────

class TestBreakdowns:
    def test_by_country(self, stats):
        assert bucket(stats["by_country"], "NG")["count"] == 2
        assert bucket(stats["by_country"], "US")["count"] == 1

    def test_by_currency(self, stats):
        assert bucket(stats["by_currency"], "NGN")["count"] == 2

    def test_by_status(self, stats):
        assert bucket(stats["by_status"], "READY")["count"] == 1

    @pytest.mark.parametrize("key", ["by_country", "by_currency", "by_status", "by_department"])
    def test_every_breakdown_sums_to_headcount(self, stats, key):
        """A breakdown that loses rows is worse than no breakdown: the dashboard
        shows a confident number that is quietly wrong."""
        assert sum(b["count"] for b in stats[key]) == stats["total_employees"]

    @pytest.mark.parametrize("key", ["by_country", "by_currency", "by_status", "by_department"])
    def test_buckets_are_sorted_by_count_descending(self, stats, key):
        counts = [b["count"] for b in stats[key]]
        assert counts == sorted(counts, reverse=True)

    def test_percentages_are_computed_server_side(self, stats):
        ng = bucket(stats["by_country"], "NG")
        assert ng["percentage"] == pytest.approx(66.7)

    def test_employees_without_a_department_are_labelled_not_dropped(self, client, admin):
        """department is nullable. COALESCE keeps those people countable."""
        client.post("/api/v1/employees", headers=admin, json={
            "full_name": "No Dept", "email": "nodept@test.com", "country": "NG",
        })
        s = client.get(URL, headers=admin).json()
        assert bucket(s["by_department"], "Unassigned")["count"] == 1
        assert sum(b["count"] for b in s["by_department"]) == s["total_employees"]


# ─── Salary ───────────────────────────────────────────────────────────────────

class TestSalary:
    def test_salaries_are_never_summed_across_currencies(self, stats):
        """500,000 NGN + 4,000 USD = 504,000 of nothing.

        Each currency must be reported on its own line.
        """
        currencies = [s["currency"] for s in stats["salary_by_currency"]]
        assert len(currencies) == len(set(currencies))
        assert "NGN" in currencies

    def test_aggregates_are_correct(self, client, admin):
        for i, salary in enumerate([100000, 200000, 300000]):
            client.post("/api/v1/employees", headers=admin, json={
                "full_name": f"Salaried {i}", "email": f"sal{i}@test.com",
                "country": "KE", "preferred_currency": "KES", "expected_salary": salary,
            })
        kes = next(s for s in client.get(URL, headers=admin).json()["salary_by_currency"]
                   if s["currency"] == "KES")
        assert kes["employees"] == 3
        assert kes["total"] == 600000
        assert kes["average"] == 200000
        assert kes["minimum"] == 100000
        assert kes["maximum"] == 300000

    def test_employees_without_a_salary_are_excluded_from_averages(self, client, admin):
        """Treating a missing salary as 0 would drag the average down and make
        payroll forecasting under-budget."""
        client.post("/api/v1/employees", headers=admin, json={
            "full_name": "Unpaid Yet", "email": "unpaid@test.com",
            "country": "KE", "preferred_currency": "KES",
        })
        client.post("/api/v1/employees", headers=admin, json={
            "full_name": "Paid", "email": "paid@test.com", "country": "KE",
            "preferred_currency": "KES", "expected_salary": 100000,
        })
        kes = next(s for s in client.get(URL, headers=admin).json()["salary_by_currency"]
                   if s["currency"] == "KES")
        assert kes["employees"] == 1
        assert kes["average"] == 100000

    def test_missing_salary_is_surfaced_as_an_action_item(self, client, admin):
        before = client.get(URL, headers=admin).json()["missing_salary"]
        client.post("/api/v1/employees", headers=admin, json={
            "full_name": "No Salary", "email": "nosalary@test.com", "country": "NG",
        })
        assert client.get(URL, headers=admin).json()["missing_salary"] == before + 1


# ─── Tenancy and edge cases ───────────────────────────────────────────────────

class TestTenancyAndEdges:
    def test_stats_never_leak_across_employers(self, client, admin, rival):
        """The rival employer has exactly one employee, in GH."""
        ours = client.get(URL, headers=admin).json()
        theirs = client.get(URL, headers=rival).json()
        assert ours["total_employees"] == 3
        assert theirs["total_employees"] == 1
        assert bucket(ours["by_country"], "GH") is None

    def test_another_employers_data_does_not_move_our_numbers(self, client, admin, rival):
        before = client.get(URL, headers=admin).json()
        client.post("/api/v1/employees", headers=rival, json={
            "full_name": "Rival Hire", "email": "rivalhire@test.com",
            "country": "BR", "preferred_currency": "USD", "expected_salary": 999999,
        })
        assert client.get(URL, headers=admin).json() == before

    def test_empty_employer_returns_zeros_not_an_error(self, client, admin, rival):
        """A brand-new customer's first dashboard load must not 500 or divide
        by zero."""
        client.delete("/api/v1/employees/emp-rival", headers=rival)
        s = client.get(URL, headers=rival).json()
        assert s["total_employees"] == 0
        assert s["completion_rate"] == 0.0
        assert s["by_country"] == []
        assert s["salary_by_currency"] == []
