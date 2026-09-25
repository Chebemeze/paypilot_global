"""
Tests for authentication and authorisation.

Owner: Person 1. Covers app/api/auth.py and app/api/v1/auth_routes.py.
"""
from __future__ import annotations

import pytest

from app.api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from app.tests.conftest import (
    login, auth_header, TEST_PASSWORD, PRODUCTION_HASH_ITERATIONS,
)

PROTECTED = [
    "/api/v1/auth/me",
    "/api/v1/employees",
    "/api/v1/dashboard/summary",
    "/api/v1/payroll/batches",
    "/api/v1/cards",
    "/api/v1/forecast/payroll-runway",
    "/api/v1/webhooks/events",
]


# ─── Password hashing ─────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_round_trip(self):
        h = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", h)

    def test_wrong_password_rejected(self):
        assert not verify_password("wrong", hash_password("right"))

    def test_plaintext_never_stored(self):
        assert "hunter2" not in hash_password("hunter2")

    def test_salt_is_random(self):
        """Two identical passwords must NOT produce identical hashes.

        If they did, cracking one account would crack every user who picked the
        same password.
        """
        assert hash_password("same") != hash_password("same")

    def test_production_work_factor_is_not_weakened(self):
        """conftest lowers the iteration count so the suite runs in seconds.

        This guards the real constant in app/api/auth.py. If someone lowers it
        for speed, or the test override leaks into the shipped code, this fails.
        OWASP's floor for PBKDF2-SHA256 is 600k; 100k is the older widely-cited
        minimum and is what this codebase ships.
        """
        assert PRODUCTION_HASH_ITERATIONS >= 100_000

    def test_malformed_hash_is_false_not_an_exception(self):
        for junk in ("", "no-dollar-sign", "$", None):
            assert verify_password("x", junk) is False


# ─── Tokens ───────────────────────────────────────────────────────────────────

class TestTokens:
    def test_payload_contents(self):
        payload = decode_token(create_access_token("u1", "e1", "ADMIN"))
        assert payload["sub"] == "u1"
        assert payload["employer_id"] == "e1"
        assert payload["role"] == "ADMIN"
        assert "exp" in payload and "jti" in payload

    def test_jti_is_unique_per_token(self):
        a = decode_token(create_access_token("u1", "e1", "ADMIN"))["jti"]
        b = decode_token(create_access_token("u1", "e1", "ADMIN"))["jti"]
        assert a != b

    def test_tampered_token_rejected(self):
        from fastapi import HTTPException
        token = create_access_token("u1", "e1", "ADMIN")
        head, payload, sig = token.split(".")
        tampered = f"{head}.{payload}.{sig[:-4]}AAAA"
        with pytest.raises(HTTPException) as exc:
            decode_token(tampered)
        assert exc.value.status_code == 401

    def test_revocation(self):
        jti = decode_token(create_access_token("u1", "e1", "ADMIN"))["jti"]
        assert not is_token_revoked(jti)
        revoke_token(jti)
        assert is_token_revoked(jti)


# ─── Login ────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_success(self, client, seeded):
        r = login(client, "admin@test.com")
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0
        assert body["user"]["role"] == "ADMIN"
        assert "hashed_password" not in body["user"]

    def test_wrong_password(self, client, seeded):
        assert login(client, "admin@test.com", "nope").status_code == 401

    def test_unknown_email_and_wrong_password_are_indistinguishable(self, client, seeded):
        """Different messages would let an attacker enumerate valid accounts."""
        a = login(client, "nobody@test.com", "x")
        b = login(client, "admin@test.com", "x")
        assert a.status_code == b.status_code == 401
        assert a.json()["error"]["message"] == b.json()["error"]["message"]

    def test_email_is_case_and_space_insensitive(self, client, seeded):
        assert login(client, "  ADMIN@TEST.COM  ").status_code == 200

    def test_deactivated_account_gets_a_distinct_403(self, client, seeded):
        r = login(client, "inactive@test.com")
        assert r.status_code == 403
        assert "deactivated" in r.json()["error"]["message"].lower()


# ─── Protecting endpoints ─────────────────────────────────────────────────────

class TestEndpointProtection:
    @pytest.mark.parametrize("path", PROTECTED)
    def test_missing_token_is_401_not_403(self, client, seeded, path):
        """401 sends the user to /login; 403 shows "permission denied".

        HTTPBearer's default auto_error raises 403 for a missing header, which
        would strand logged-out users on a permission screen.
        """
        r = client.get(path)
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHENTICATED"

    @pytest.mark.parametrize("header", [
        {"Authorization": "Bearer garbage"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic abc123"},
        {"Authorization": ""},
    ])
    def test_bad_authorization_headers(self, client, seeded, header):
        assert client.get("/api/v1/employees", headers=header).status_code == 401

    def test_valid_token_allows_access(self, client, admin):
        for path in PROTECTED:
            assert client.get(path, headers=admin).status_code == 200, path

    def test_public_endpoints_need_no_token(self, client, seeded):
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200


# ─── Roles ────────────────────────────────────────────────────────────────────

class TestRoles:
    NEW = {"full_name": "New Person", "email": "new@test.com", "country": "NG"}

    def test_everyone_can_read(self, client, admin, finance, viewer):
        for hdr in (admin, finance, viewer):
            assert client.get("/api/v1/employees", headers=hdr).status_code == 200

    def test_viewer_cannot_create(self, client, viewer):
        r = client.post("/api/v1/employees", json=self.NEW, headers=viewer)
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"

    def test_viewer_cannot_delete(self, client, viewer):
        assert client.delete("/api/v1/employees/emp-1", headers=viewer).status_code == 403

    def test_finance_can_create(self, client, finance):
        assert client.post("/api/v1/employees", json=self.NEW, headers=finance).status_code == 201

    def test_finance_cannot_delete(self, client, finance):
        assert client.delete("/api/v1/employees/emp-1", headers=finance).status_code == 403

    def test_admin_can_delete(self, client, admin):
        assert client.delete("/api/v1/employees/emp-1", headers=admin).status_code == 200

    def test_403_message_names_the_required_role(self, client, viewer):
        msg = client.delete("/api/v1/employees/emp-1", headers=viewer).json()["error"]["message"]
        assert "VIEWER" in msg and "ADMIN" in msg


# ─── Session endpoints ────────────────────────────────────────────────────────

class TestSessionEndpoints:
    def test_me(self, client, admin):
        body = client.get("/api/v1/auth/me", headers=admin).json()
        assert body["email"] == "admin@test.com"
        assert body["role"] == "ADMIN"

    def test_refresh_issues_new_token_and_kills_the_old(self, client, seeded):
        hdr = auth_header(client, "admin@test.com")
        r = client.post("/api/v1/auth/refresh", headers=hdr)
        assert r.status_code == 200
        new = r.json()["access_token"]
        assert new != hdr["Authorization"].removeprefix("Bearer ")
        assert client.get("/api/v1/auth/me", headers=hdr).status_code == 401
        assert client.get("/api/v1/auth/me",
                          headers={"Authorization": f"Bearer {new}"}).status_code == 200

    def test_logout_revokes_immediately(self, client, seeded):
        hdr = auth_header(client, "admin@test.com")
        assert client.post("/api/v1/auth/logout", headers=hdr).status_code == 200
        assert client.get("/api/v1/auth/me", headers=hdr).status_code == 401

    @pytest.mark.parametrize("payload,expected", [
        ({"current_password": "wrong", "new_password": "longenough"}, 401),
        ({"current_password": TEST_PASSWORD, "new_password": "short"}, 422),
        ({"current_password": TEST_PASSWORD, "new_password": TEST_PASSWORD}, 422),
    ])
    def test_change_password_guards(self, client, seeded, payload, expected):
        hdr = auth_header(client, "admin@test.com")
        assert client.post("/api/v1/auth/change-password",
                           json=payload, headers=hdr).status_code == expected

    def test_change_password_succeeds_and_forces_relogin(self, client, seeded):
        hdr = auth_header(client, "admin@test.com")
        r = client.post("/api/v1/auth/change-password", headers=hdr,
                        json={"current_password": TEST_PASSWORD, "new_password": "brand-new-pw"})
        assert r.status_code == 200
        assert client.get("/api/v1/auth/me", headers=hdr).status_code == 401
        assert login(client, "admin@test.com", TEST_PASSWORD).status_code == 401
        assert login(client, "admin@test.com", "brand-new-pw").status_code == 200


# ─── Multi-tenancy ────────────────────────────────────────────────────────────

class TestTenantIsolation:
    """The single most important property in a payroll system."""

    def test_list_excludes_other_employers(self, client, admin):
        emails = [e["email"] for e in client.get("/api/v1/employees", headers=admin).json()["items"]]
        assert "secret@rival.com" not in emails
        assert len(emails) == 3

    def test_cannot_read_another_employers_employee(self, client, admin):
        assert client.get("/api/v1/employees/emp-rival", headers=admin).status_code == 404

    def test_cannot_update_another_employers_employee(self, client, admin):
        r = client.put("/api/v1/employees/emp-rival", json={"department": "Hacked"}, headers=admin)
        assert r.status_code == 404

    def test_cannot_delete_another_employers_employee(self, client, admin):
        assert client.delete("/api/v1/employees/emp-rival", headers=admin).status_code == 404

    def test_each_side_sees_only_its_own(self, client, admin, rival):
        ours = client.get("/api/v1/employees", headers=admin).json()
        theirs = client.get("/api/v1/employees", headers=rival).json()
        assert ours["total"] == 3
        assert theirs["total"] == 1
        assert theirs["items"][0]["email"] == "secret@rival.com"

    def test_same_email_allowed_across_different_employers(self, client, admin, rival):
        payload = {"full_name": "Shared Email", "email": "shared@test.com", "country": "NG"}
        assert client.post("/api/v1/employees", json=payload, headers=admin).status_code == 201
        assert client.post("/api/v1/employees", json=payload, headers=rival).status_code == 201
