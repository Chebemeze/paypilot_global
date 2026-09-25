"""
PayPilot Global — pytest fixtures.

Owner: Person 1 (Backend Core — Auth & Employees)

WHY THIS EXISTS
---------------
The shell scripts (test_auth.sh, test_rbac.sh, ...) run against the live MySQL
database. That made them brittle in four separate ways during development:

  * leftover fixtures from a previous run changed the expected counts
  * the seeded demo data collided with test data (6 real "Engineer" job titles)
  * soft-deleted rows turned `created` into `restored` on every re-run
  * assertions grepped raw JSON and broke on whitespace

Every one of those is an assumption about the ENVIRONMENT rather than a
statement about the BEHAVIOUR. This file removes the environment from the
equation: each test function gets a brand-new in-memory SQLite database with a
freshly created schema, and talks to the app through parsed response objects.

IMPORTANT
---------
DATABASE_URL is set before any `app.*` module is imported, because
app/database.py builds its engine at import time. Nothing here can ever touch
your real MySQL database.
"""
from __future__ import annotations

import os

# MUST run before importing anything from `app`.
os.environ["DATABASE_URL"] = "sqlite://"          # in-memory
os.environ.setdefault("JWT_SECRET", "test-secret-not-used-in-production")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Employer, User, Employee  # noqa: E402
from app.api.auth import hash_password  # noqa: E402
from app.api import auth as auth_module  # noqa: E402

TEST_PASSWORD = "password123"

# --- Why we weaken the password hash in tests -------------------------------
# hash_password() runs PBKDF2-SHA256 at 100,000 iterations. That slowness is
# the whole point in production: it caps an attacker who has stolen the
# database at a handful of guesses per second.
#
# But the `seeded` fixture builds 5 users for EVERY test, so a 161-test run
# pays that cost ~1,000 times and takes over three minutes. A suite that slow
# stops being run, and a suite nobody runs protects nobody.
#
# So tests use 1,000 iterations. The algorithm, the salting and the stored
# format are all completely unchanged — only the work factor moves, and no
# test asserts anything about how long hashing takes. The production constant
# is captured below and asserted on in test_auth.py, so if someone ever drops
# the real number this suite still fails.
PRODUCTION_HASH_ITERATIONS = auth_module._HASH_ITERATIONS
TEST_HASH_ITERATIONS = 1_000
auth_module._HASH_ITERATIONS = TEST_HASH_ITERATIONS
EMPLOYER_ID = "test-employer-1"
OTHER_EMPLOYER_ID = "test-employer-2"


@pytest.fixture
def db_session():
    """A fresh, empty in-memory database for one test.

    StaticPool keeps every connection pointed at the SAME in-memory database.
    Without it, SQLAlchemy hands out a new blank database per connection and the
    tables you just created vanish.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def seeded(db_session):
    """Two employers, three users with different roles, a few employees.

    Two employers is deliberate: it lets every test assert that one company can
    never see another company's data.
    """
    db_session.add_all([
        Employer(id=EMPLOYER_ID, name="Acme", company_name="Acme Global"),
        Employer(id=OTHER_EMPLOYER_ID, name="Rival", company_name="Rival Inc"),
    ])
    db_session.add_all([
        User(id="u-admin", employer_id=EMPLOYER_ID, email="admin@test.com",
             full_name="Admin User", hashed_password=hash_password(TEST_PASSWORD),
             role="ADMIN", is_active=True),
        User(id="u-finance", employer_id=EMPLOYER_ID, email="finance@test.com",
             full_name="Finance User", hashed_password=hash_password(TEST_PASSWORD),
             role="FINANCE", is_active=True),
        User(id="u-viewer", employer_id=EMPLOYER_ID, email="viewer@test.com",
             full_name="Viewer User", hashed_password=hash_password(TEST_PASSWORD),
             role="VIEWER", is_active=True),
        User(id="u-inactive", employer_id=EMPLOYER_ID, email="inactive@test.com",
             full_name="Inactive User", hashed_password=hash_password(TEST_PASSWORD),
             role="ADMIN", is_active=False),
        # Belongs to the OTHER company — must never be visible to Acme.
        User(id="u-rival", employer_id=OTHER_EMPLOYER_ID, email="rival@test.com",
             full_name="Rival Admin", hashed_password=hash_password(TEST_PASSWORD),
             role="ADMIN", is_active=True),
    ])
    db_session.add_all([
        Employee(id="emp-1", employer_id=EMPLOYER_ID, full_name="Ada Lovelace",
                 email="ada@test.com", country="NG", department="Engineering",
                 role="Backend Engineer", expected_salary=500000,
                 preferred_currency="NGN", onboarding_status="READY"),
        Employee(id="emp-2", employer_id=EMPLOYER_ID, full_name="Bob Marley",
                 email="bob@test.com", country="US", department="Engineering",
                 role="Frontend Engineer", expected_salary=4000,
                 preferred_currency="USD", onboarding_status="INVITED"),
        Employee(id="emp-3", employer_id=EMPLOYER_ID, full_name="Chidi Okonkwo",
                 email="chidi@test.com", country="NG", department="Finance",
                 role="Analyst", expected_salary=300000,
                 preferred_currency="NGN", onboarding_status="WALLET_PENDING"),
        # Another company's employee — leakage canary.
        Employee(id="emp-rival", employer_id=OTHER_EMPLOYER_ID,
                 full_name="Rival Employee", email="secret@rival.com",
                 country="US", preferred_currency="USD",
                 onboarding_status="READY"),
    ])
    db_session.commit()
    return db_session


@pytest.fixture
def client(db_session):
    """TestClient wired to the throwaway database.

    The dependency override is what makes this safe: every `Depends(get_db)` in
    the app resolves to our in-memory session instead of the real engine.
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # the db_session fixture owns the lifecycle

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def login(client: TestClient, email: str, password: str = TEST_PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_header(client: TestClient, email: str) -> dict[str, str]:
    token = login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(client, seeded):
    return auth_header(client, "admin@test.com")


@pytest.fixture
def finance(client, seeded):
    return auth_header(client, "finance@test.com")


@pytest.fixture
def viewer(client, seeded):
    return auth_header(client, "viewer@test.com")


@pytest.fixture
def rival(client, seeded):
    """Admin of the OTHER employer — for tenant-isolation tests."""
    return auth_header(client, "rival@test.com")
