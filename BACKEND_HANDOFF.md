# Backend Handoff — Auth & Employees (Person 1)

**Status:** shipped and stable · 194 automated tests green · 2026-09-25
**Contract:** [`API_CONTRACT.md`](./API_CONTRACT.md) v1.1.0 — the authority. This page is the "how do I work with it" companion.

This exists so you can build against Auth & Employees **without asking me anything**.
If you find something here that's wrong or missing, tell me — a wrong answer in a
doc is worse than no doc, and I'd rather fix it than have you guess.

---

## 0. Read this first if you do nothing else

**1. `.env` must never be committed.** The repo now has a `.gitignore` that
excludes it, plus a committed `backend/.env.example` template. Anything pushed
to GitHub is public forever — deleting it in a later commit does not remove it
from history; the only real fix is rotating the secret. Set up with:

```bash
cd backend && cp .env.example .env    # then fill in your values
```

**2. `country` is an ISO-3166 alpha-2 code on the way out.** `"NG"`, never
`"Nigeria"`. Input accepts both; **output is always the 2-letter code**. Render
it through a lookup table. `"UK"` normalises to `"GB"` — `UK` is not a real ISO
code, and storing it makes Flutterwave reject every British payout.

**3. Errors have one shape.** `{"error": {code, message, status, fields, request_id}}`.
Branch on `error.code`, never on `error.message`.

---

## 1. Run the backend in five minutes

```bash
# 1. Start MySQL (XAMPP control panel, or:)
sudo /opt/lampp/lampp startmysql

# 2. Create the database once
mysql -u root -e "CREATE DATABASE IF NOT EXISTS paypilot_global;"

# 3. Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in values; defaults work for local demo
python3 -m app.seed           # demo employer + 3 users + 6 employees
uvicorn app.main:app --reload --port 8000
```

**Interactive API docs:** <http://localhost:8000/docs> — every endpoint, live,
with a "Try it out" button. Faster than reading the contract for a quick check.

**Health check:** `curl http://localhost:8000/health`

### Demo logins (all password `password123`)

| Email | Role | Can do |
|---|---|---|
| `admin@acmeglobal.com` | ADMIN | everything, including delete |
| `finance@acmeglobal.com` | FINANCE | read + create/update/import, **no delete** |
| `viewer@acmeglobal.com` | VIEWER | read only |

Use all three. If your feature only ever gets tested as ADMIN, you will ship a
screen that 403s for the people who actually use it.

### Port 3306 already in use?

Linux ships its own MySQL that fights XAMPP's:

```bash
sudo systemctl stop mysql && sudo systemctl disable mysql
```

---

## 2. Getting a token

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}'
```

```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400, "user": { "...": "..." } }
```

Then send `Authorization: Bearer <access_token>` on every request except
`/auth/login`, `/health` and `/`.

Handy for shell testing:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@acmeglobal.com","password":"password123"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s http://localhost:8000/api/v1/employees -H "Authorization: Bearer $TOKEN"
```

`expires_in` is seconds (86400 = 24h). Don't hard-code the duration — read the
field, so you inherit it automatically when we shorten token life for production.

---

## 3. The five rules that will save you a day each

### 3.1 — 401 and 403 are not the same thing

| | Meaning | UI response |
|---|---|---|
| **401** `UNAUTHENTICATED` | no / bad / expired / revoked token | redirect to login |
| **403** `FORBIDDEN` | valid token, wrong role | stay put, "no permission" |

A logged-out user must never see a permissions error; a VIEWER clicking Delete
must never be kicked to the login screen. This is the most common integration
bug on projects like this. There is a ready-made handler in `API_CONTRACT.md` →
Common Patterns.

### 3.2 — Deletion is soft, and creation can *restore*

`DELETE /employees/{id}` hides the row but keeps it, so payroll history survives.

The consequence: `POST /employees` with a previously-deleted email returns
**`201` with `"status": "restored"`** and the **original `id`** — not `"created"`,
not a `409`. Show "Employee restored." The user is usually undoing a mistake.

So: **never assume a 201 means a brand-new id.** Read `status`.

### 3.3 — Everything is scoped to your employer

Every query filters on the `employer_id` inside your token. There is no
parameter to widen it. An employee belonging to another company returns **404**,
not 403 — telling you "it exists but isn't yours" would leak that a rival is a
customer. Don't build an admin screen expecting cross-company access; it doesn't
exist and won't be added.

### 3.4 — Money has a currency attached

`GET /employees/stats` returns `salary_by_currency` as one row **per currency**,
deliberately. ₦500,000 + $4,000 is not 504,000 of anything. Render separate rows.
If you need a single headline figure, that needs live FX rates and a product
decision — come to me, don't sum them.

Likewise: `expected_salary: null` means "not set", **not** zero. It's excluded
from averages and reported separately as `missing_salary`.

### 3.5 — Validation errors tell you which field

On a `422`, `error.fields` is `[{field, message}]`. Map it onto your inputs and
highlight the offending box. One red banner saying "validation failed" on a
seven-field form is a support ticket waiting to happen.

---

## 4. Patterns to copy, not reinvent

These are solved in `employee_routes.py`. Copying them costs minutes; rediscovering
the bugs costs days. Person 2 especially — payroll and cards need all four.

| Pattern | Where | Why you need it |
|---|---|---|
| `_escape_like()` | `employee_routes.py` | Without it, a user searching `50%` matches **every row** — `%` is a SQL wildcard. Escape `\` first, then `%` and `_`. |
| `.order_by(col, Model.id.asc())` | every paginated query | Without a tie-breaker, rows with equal sort values **reshuffle between pages** and the same record shows up twice. In payroll that means paying someone twice. |
| `SORTABLE_FIELDS` allowlist | `employee_routes.py` | Never interpolate a user-supplied column into `ORDER BY`. `?sort_by=hashed_password` lets an attacker binary-search password hashes. Map strings → Column objects; reject the rest with 422. |
| `paginate()` | `app/schemas/schemas.py` | Shared helper. Gives every list the same envelope including `has_next`/`prev_page`. |
| `normalize_country()` | `app/schemas/schemas.py` | Accepts ISO-2 **and** full names, returns ISO-2. **Use it** rather than writing another one — and check yours doesn't pass `"UK"` through unchanged. |
| `_find_archived()` / `_restore_employee()` | `employee_routes.py` | The soft-delete + unique-index reconciliation. Copy the approach rather than editing `models.py`. |

---

## 5. Shared-file etiquette

Four people, one repo. These files are touched by more than one of us:

| File | Rule |
|---|---|
| `app/schemas/schemas.py` | **Add** your models at the end. Don't edit anyone else's. Don't reorder. |
| `app/main.py` | Router registration only. One line each. |
| `app/models/models.py` | 🚫 **Do not edit without telling the group.** A schema change breaks everyone's local DB at once. Propose it in standup first. |
| `requirements.txt` | Pin exact versions (`package==1.2.3`). Say so in your PR description. |
| `app/database.py` | Don't touch. Engine setup is environment-sensitive. |
| `API_CONTRACT.md` | Edit **only your own section**. Bump the version and note breaking changes at the top. |

**Pull before you push, every time.** These six files are where merge conflicts live.

---

## 6. Known gaps — mine and otherwise

Being honest about these so nobody builds on a false assumption:

- **Token revocation is in-memory.** Restarting the API un-revokes outstanding
  tokens, and it won't work across multiple server processes. Production fix is
  Redis with a TTL matching token expiry. No effect on frontend integration.
- **No rate limiting on `/auth/login`.** Brute-forcing a password is currently
  unthrottled. `RATE_LIMIT_PER_MINUTE=60` exists in `.env` and `429 RATE_LIMITED`
  is defined but unused. On my list.
- **Tokens last 24 hours.** Long for a payroll app. Fine for the demo; should
  drop to ~1h with refresh before production.
- **⚠️ `payroll_routes.py` and `card_routes.py` have no role checks and take
  `body: dict` with no validation.** As of today **a VIEWER can approve and
  disburse payroll.** That's the single most serious issue in the codebase.
  Person 2 — import `require_finance` / `require_admin` from `app.api.auth` and
  replace `body: dict` with Pydantic models. Happy to pair on it.

---

## 7. Before you ask me a question

1. **<http://localhost:8000/docs>** — live, always current, has Try It Out.
2. **`API_CONTRACT.md`** — request/response shapes, every error code.
3. **`backend/app/tests/`** — 194 tests that double as executable examples.
   Want to know exactly how restore-on-create behaves? `test_employees.py` →
   `test_deleted_employee_is_restored_not_duplicated`.
4. **Run the suite** — `cd backend && python3 -m pytest`. Takes ~25s. If it's
   green and your call still fails, it's your request, not my endpoint. If it's
   **red**, someone broke a shared file — that's worth a message to the group.

Then ask me. Genuinely — a five-minute question beats a day of wrong assumptions.
I'd just rather answer the ones the docs can't.
