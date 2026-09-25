# PayPilot Global - API Contract

**Version:** 1.1.0  
**Last Updated:** 2026-09-25  
**Base URL:** `http://localhost:8000/api/v1`

This document defines the complete API contract between backend and frontend. Both teams must adhere to this contract to ensure seamless integration.

> ### ⚠️ v1.1.0 — changes to Auth & Employees (Person 1)
>
> The **Authentication**, **Employees** and **Common Patterns** sections were rewritten on
> 2026-09-25 to match the shipped implementation. Everything below is verified by
> 194 automated tests (`cd backend && python3 -m pytest`).
>
> **Two of these will break existing frontend code. Please read before your next commit:**
>
> 1. **`country` is now an ISO-3166 alpha-2 code, not a display name.** The old
>    examples showed `"country": "Nigeria"`; the API returns and stores `"NG"`.
>    Input is forgiving — `"Nigeria"`, `"nigeria"` and `"NG"` are all accepted —
>    but **output is always the 2-letter code**, so render it through a lookup
>    table. Note `"UK"` normalises to `"GB"`, its real ISO code.
> 2. **The error body changed shape.** It is now
>    `{"error": {"code", "message", "status", "fields", "request_id"}}`, with the
>    old `detail` string preserved alongside it for backwards compatibility.
>    **Branch on `error.code`, never on `error.message`** — messages get reworded,
>    codes do not.
>
> Also new since 1.0.0: `POST /auth/refresh`, `POST /auth/logout`,
> `POST /auth/change-password`, `expires_in` on login, filtering/search/sorting on
> `GET /employees`, `POST /employees/import`, `GET /employees/stats`, and
> `status: "restored"` on employee creation.

---

## 📋 Table of Contents

1. [Authentication](#-authentication) — login, refresh, logout, change password, roles, 401 vs 403
2. [Dashboard](#-dashboard)
3. [Employees](#-employees) — CRUD, search/filter/sort, stats, CSV import
4. [Payroll](#-payroll)
5. [Forecast](#-forecast)
6. [Cards](#-cards)
7. [Webhooks](#-webhooks)
8. [Copilot](#-copilot)
9. [Common Patterns](#-common-patterns) — pagination, **error envelope**
10. [Status Enums](#-status-enums)

---

## 🔐 Authentication

Owner: **Person 1**. All endpoints verified by automated tests.

### Login

**Endpoint:** `POST /auth/login`  ·  **Auth:** none

**Request:**
```json
{ "email": "admin@acmeglobal.com", "password": "password123" }
```

Email is trimmed and lower-cased server-side, so `" ADMIN@Acme.com "` logs in fine.

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user-admin-001",
    "employer_id": "demo-employer-001",
    "email": "admin@acmeglobal.com",
    "full_name": "Sarah Johnson",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

`expires_in` is **seconds** from now (currently 86400 — a 24-hour token). Use it to schedule a silent refresh rather
than hard-coding an hour; if the backend shortens token life you inherit it free.

**Errors:**

| Status | `error.code` | Meaning |
|---|---|---|
| 401 | `UNAUTHENTICATED` | Wrong password **or** unknown email |
| 403 | `FORBIDDEN` | Account exists but is deactivated |
| 422 | `VALIDATION_ERROR` | Missing/malformed email or password |

> Unknown email and wrong password deliberately return the **identical** message.
> Do not try to tell the user which one it was — differing responses let an
> attacker discover who banks with us. Show "Incorrect email or password."
> A deactivated account is a distinct 403 because "contact your administrator"
> is genuinely different advice.

---

### Get Current User

**Endpoint:** `GET /auth/me`  ·  **Auth:** any authenticated role

**Response (200):**
```json
{
  "id": "user-admin-001",
  "employer_id": "demo-employer-001",
  "email": "admin@acmeglobal.com",
  "full_name": "Sarah Johnson",
  "role": "ADMIN",
  "is_active": true,
  "created_at": "2026-09-01T10:00:00Z"
}
```

Good for rehydrating session state on page load. A `401` here means the stored
token is dead — clear it and redirect to login.

---

### Refresh Token

**Endpoint:** `POST /auth/refresh`  ·  **Auth:** any authenticated role

**Response (200):** same shape as login (`access_token`, `token_type`, `expires_in`, `user`).

⚠️ **The old token is revoked immediately.** Replace the stored token in the same
tick you receive the new one. If two tabs refresh concurrently, the loser's token
is already dead — on a `401` following a refresh, retry once with the newest
stored token before logging the user out.

---

### Logout

**Endpoint:** `POST /auth/logout`  ·  **Auth:** any authenticated role

**Response (200):** `{ "status": "logged_out", "message": "Token revoked successfully." }`

Revokes the current token server-side, so it stops working instantly rather than
lingering until expiry. Still clear it from client storage.

> **Known limitation:** the revocation list is in-memory, so restarting the API
> un-revokes outstanding tokens. Production fix is Redis with a TTL matching
> token expiry. Does not affect frontend integration.

---

### Change Password

**Endpoint:** `POST /auth/change-password`  ·  **Auth:** any authenticated role

**Request:**
```json
{ "current_password": "password123", "new_password": "my-new-secret" }
```

**Response (200):** `{ "status": "password_changed", "message": "Password updated. Please log in again." }`

**Errors:** `401` current password wrong · `422` new password shorter than 8
characters, or identical to the current one.

⚠️ **All the user's tokens are revoked on success**, including the one that made
the request. Send the user to the login screen immediately — every subsequent
call returns 401.

---

### 401 vs 403 — the rule

These mean different things and need different UI. Never collapse them.

| | Meaning | What the UI should do |
|---|---|---|
| **401** `UNAUTHENTICATED` | No token, malformed token, expired or revoked token | Redirect to `/login` |
| **403** `FORBIDDEN` | Token is valid, but this role may not do this | Stay put, show "You don't have permission" |

A logged-out user must **never** see a permissions error, and a VIEWER clicking
Delete must **never** be bounced to the login screen.

---

### Roles

Three roles. `GET /auth/me` returns the caller's.

| Action | ADMIN | FINANCE | VIEWER |
|---|:---:|:---:|:---:|
| Read anything (list, detail, stats) | ✅ | ✅ | ✅ |
| Create / update employees, invite, resend invite, CSV import | ✅ | ✅ | ❌ |
| Delete employees | ✅ | ❌ | ❌ |

Hide buttons the role can't use, but treat the server as the authority — the API
enforces this independently of what the UI shows.

---

## 📊 Dashboard

### Get Dashboard Summary

**Endpoint:** `GET /dashboard/summary`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "total_employees": 8,
  "ready_employees": 5,
  "stuck_employees": 3,
  "high_risk_items": 2,
  "safety_score": 75,
  "safety_label": "MODERATE",
  "payroll_totals_by_currency": {
    "NGN": 830000,
    "USD": 5000,
    "EUR": 1500,
    "MXN": 12000,
    "CAD": 2000
  },
  "wallet_balances": [
    {
      "id": "wb-001",
      "currency": "NGN",
      "wallet_code": "CNGN",
      "balance": 15000000,
      "updated_at": "2026-09-22T10:00:00Z"
    }
  ],
  "forecast_shortfalls": [
    {
      "currency": "USD",
      "wallet_code": "USDB",
      "balance": 8950,
      "required": 5000,
      "shortfall": 0,
      "surplus": 3950,
      "status": "SUFFICIENT",
      "message": "Sufficient balance"
    }
  ],
  "recent_webhooks": [
    {
      "id": "evt-001",
      "event_id": "evt_001",
      "source_event_id": "bmoni_evt_001",
      "event_type": "employee.linked",
      "payload": {},
      "signature_valid": true,
      "state": "PROCESSED",
      "processed": true,
      "error_message": null,
      "created_at": "2026-09-08T10:00:00Z"
    }
  ]
}
```

---

## 👥 Employees

Owner: **Person 1**. Every endpoint is scoped to the caller's `employer_id` from
the token — you can never see or touch another company's staff, and there is no
parameter to override that.

**Deletion is soft.** A deleted employee disappears from every read, but the row
survives so payroll history stays intact. This has one visible consequence, in
Create below.

### The Employee object

```json
{
  "id": "emp-001",
  "full_name": "Ada Okafor",
  "email": "ada@acme.com",
  "country": "NG",
  "department": "Engineering",
  "role": "Frontend Engineer",
  "expected_salary": 250000,
  "preferred_currency": "NGN",
  "onboarding_status": "READY",
  "kyc_status": "verified",
  "wallet_status": "active",
  "payout_wallet_address": "0xaaaa...",
  "payout_wallet_last_changed": null,
  "is_active": true,
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-22T10:00:00Z"
}
```

| Field | Notes |
|---|---|
| `country` | **ISO-3166 alpha-2, always.** `"NG"`, not `"Nigeria"`. Changed in v1.1.0. |
| `preferred_currency` | One of `NGN USD EUR GBP CAD MXN KES GHS ZAR`. Defaults to `USD`. |
| `department`, `role` | Nullable. Blank input is stored as `null`, never `""`. |
| `expected_salary` | Nullable number. `null` means "not set yet", **not** zero. |
| `role` | Job title, e.g. "Frontend Engineer". Unrelated to the *permission* role on User. |

> `Employee.role` (job title) and `User.role` (ADMIN/FINANCE/VIEWER) are different
> things that share a name. Don't wire one to the other.

---

### List Employees

**Endpoint:** `GET /employees`  ·  **Auth:** any authenticated role

**Query parameters** — all optional, combined with AND:

| Param | Values |
|---|---|
| `search` | Free text; matches `full_name`, `email`, `department`, `role`. Case-insensitive, substring. |
| `country` | ISO-2 or full name (`NG` or `Nigeria`) |
| `currency` | `NGN` `USD` `EUR` `GBP` `CAD` `MXN` `KES` `GHS` `ZAR` |
| `department` | Exact match |
| `status` | `INVITED` `KYC_ACTION_REQUIRED` `WALLET_PENDING` `READY` |
| `is_active` | `true` / `false` |
| `sort_by` | `created_at` `updated_at` `full_name` `email` `country` `department` `onboarding_status` `expected_salary` (default `created_at`) |
| `sort_order` | `asc` / `desc` (default `desc`) |
| `page` | Default `1` |
| `limit` | Default `50`, max `200` |

`%` and `_` in `search` are treated as **literal characters**, so a search for
`50%` matches the text "50%" rather than every row.

**Response (200):**
```json
{
  "items": [ { "...": "Employee object" } ],
  "page": 1,
  "limit": 50,
  "total": 8,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false,
  "next_page": null,
  "prev_page": null
}
```

Wire Next/Prev buttons to `has_next` / `has_prev` and `next_page` / `prev_page`
rather than computing them — the backend already handles the edges.

**Errors:** `422 VALIDATION_ERROR` for an unknown `status`, `currency`,
`sort_by` or `sort_order`. The message lists the valid options, so it's safe to
surface directly while debugging.

---

### Get Employee by ID

**Endpoint:** `GET /employees/{id}`  ·  **Auth:** any authenticated role

**Response (200):**
```json
{
  "employee": { "...": "Employee object" },
  "onboarding_issue": {
    "issue": "KYC_INCOMPLETE",
    "summary": "Ada has not submitted a government ID.",
    "suggested_action": "Send a reminder"
  }
}
```

`onboarding_issue` is `null` when the employee is `READY`.

**Errors:** `404 NOT_FOUND` if the id doesn't exist, is soft-deleted, **or
belongs to another employer**. All three are deliberately indistinguishable —
a different response for "exists but not yours" would leak that a company is a
customer.

---

### Get Employee Stats

**Endpoint:** `GET /employees/stats`  ·  **Auth:** any authenticated role  ·  *New in 1.1.0*

Pre-aggregated dashboard figures. One call replaces paging the whole roster and
counting client-side.

**Response (200):**
```json
{
  "total_employees": 8,
  "active": 7,
  "inactive": 1,
  "onboarding_complete": 5,
  "onboarding_pending": 3,
  "completion_rate": 62.5,
  "missing_salary": 2,
  "by_country":    [ { "value": "NG", "count": 5, "percentage": 62.5 } ],
  "by_currency":   [ { "value": "NGN", "count": 5, "percentage": 62.5 } ],
  "by_status":     [ { "value": "READY", "count": 5, "percentage": 62.5 } ],
  "by_department": [ { "value": "Engineering", "count": 4, "percentage": 50.0 } ],
  "salary_by_currency": [
    {
      "currency": "NGN", "employees": 5, "total": 1250000.0,
      "average": 250000.0, "minimum": 150000.0, "maximum": 400000.0
    }
  ]
}
```

Notes for the dashboard:

- **Buckets arrive sorted by `count` descending** — no client-side sorting needed
  for a "top countries" list.
- **Percentages are computed server-side** so every client rounds identically.
- Every breakdown **sums to `total_employees`**; employees with no department
  appear under `"Unassigned"` rather than being dropped.
- **`salary_by_currency` is never summed across currencies.** ₦500,000 + $4,000
  is not 504,000 of anything. Render one row per currency. If a single headline
  number is needed, that requires FX rates and a product decision — ask Person 1.
- Employees with no salary are **excluded** from averages and counted separately
  in `missing_salary`. Treating them as 0 would make forecasts under-budget.
- A brand-new employer gets zeros and empty arrays, not an error.

---

### Create Employee

**Endpoint:** `POST /employees`  ·  **Auth:** ADMIN or FINANCE

**Request:**
```json
{
  "full_name": "Ada Okafor",
  "email": "ada@acme.com",
  "country": "Nigeria",
  "preferred_currency": "NGN",
  "department": "Engineering",
  "role": "Frontend Engineer",
  "expected_salary": 250000
}
```

Required: `full_name`, `email`, `country`. Everything else optional.

**Validation:**

| Field | Rule |
|---|---|
| `full_name` | 2–100 chars after trimming |
| `email` | ≤255, valid format, lower-cased on save |
| `country` | ISO-2 **or** full name. `UK`/`England`/`Great Britain` → `GB`. Unknown → 422 |
| `preferred_currency` | In the supported set. Defaults to `USD` |
| `department`, `role` | ≤100 chars, blank → `null` |
| `expected_salary` | `> 0` and `≤ 1,000,000,000` |

**Response (201):**
```json
{ "status": "created", "employee": { "...": "Employee object" } }
```

⚠️ **`status` can also be `"restored"`.** If that email belonged to a
soft-deleted employee, the original row is reactivated and reused — you get
`201` with `"status": "restored"` and the **original `id`**, with
`onboarding_status` reset to `INVITED`. Show "Employee restored" rather than
"Employee created"; the user is likely undoing an accidental deletion, and their
payroll history is intact.

**Errors:** `409 CONFLICT` if a **live** employee already has that email ·
`422 VALIDATION_ERROR` · `403 FORBIDDEN` for VIEWER.

The same email may exist under two different employers; uniqueness is per-company.

---

### Update Employee

**Endpoint:** `PUT /employees/{id}`  ·  **Auth:** ADMIN or FINANCE

Partial update — send only the fields you're changing; omitted fields are left
alone. Same validation rules as Create.

**Response (200):** `{ "status": "updated", "employee": { ... } }`

**Errors:** `400 BAD_REQUEST` empty body · `404` · `409` email belongs to another
live employee (re-sending the employee's own email is fine) · `422` · `403`.

---

### Delete Employee

**Endpoint:** `DELETE /employees/{id}`  ·  **Auth:** ADMIN only

**Response (200):** `{ "status": "deleted", "employee_id": "emp-001" }`

Soft delete: gone from all reads, row retained for payroll history. Re-creating
the same email later restores this exact record (see Create).

**Errors:** `404` · `403` for FINANCE and VIEWER.

---

### Invite Employee (Flutterwave)

**Endpoint:** `POST /employees/invite`  ·  **Auth:** ADMIN or FINANCE

Creates the employee **and** kicks off Flutterwave onboarding. Same request body,
validation, `409`/`422` behaviour and `"restored"` semantics as Create.

**Response (201):** `{ "status": "created", "employee": { ... } }`

Calls an external provider, so it is slower than plain Create — show a spinner
and don't let the user double-submit. `502 UPSTREAM_ERROR` / `504
UPSTREAM_TIMEOUT` mean Flutterwave failed, not that the input was bad; offer a
retry rather than a validation message.

---

### Resend Invite

**Endpoint:** `POST /employees/{id}/resend-invite`  ·  **Auth:** ADMIN or FINANCE

**Response (200):** `{ "status": "resent", "employee_id": "emp-001" }`

**Errors:** `404` · `403` · `502`/`504` from the provider.

---

### Bulk Import Employees (CSV)

**Endpoint:** `POST /employees/import`  ·  **Auth:** ADMIN or FINANCE  ·  *New in 1.1.0*

`multipart/form-data`:

| Field | Notes |
|---|---|
| `file` | The CSV. Required. Max 5 MB, max 5,000 data rows |
| `dry_run` | `true` / `false` (default `false`). Validate and report, write nothing |

**Required columns:** `full_name`, `email`, `country`.
**Optional:** `preferred_currency`, `department`, `role`, `expected_salary`.

Header matching is deliberately forgiving — case, spaces, hyphens and underscores
are all normalised, and these aliases are accepted:

| Canonical | Also accepted |
|---|---|
| `full_name` | `name`, `employee_name` |
| `email` | `e-mail`, `work_email` |
| `role` | `job_title`, `title`, `position` |
| `expected_salary` | `salary`, `amount` |
| `department` | `dept`, `team` |

Also handled: Excel's UTF-8 BOM, `,` `;` `tab` `|` delimiters, and salaries
written as `"₦450,000.00"`. Unknown columns are ignored, not rejected.

**Response (200):**
```json
{
  "dry_run": true,
  "total_rows": 3,
  "recognised_columns": ["full_name", "email", "country", "expected_salary"],
  "created": 1, "restored": 1, "skipped": 0, "failed": 1,
  "results": [
    { "row": 2, "email": "ada@acme.com",  "status": "created" },
    { "row": 3, "email": "bob@acme.com",  "status": "restored" },
    {
      "row": 4, "email": "bad-email", "status": "failed",
      "errors": [ { "field": "email", "message": "Invalid email address." } ]
    }
  ]
}
```

| `status` | Meaning |
|---|---|
| `created` | New employee added |
| `restored` | Matched a soft-deleted employee; reactivated |
| `skipped` | A live employee already has this email; nothing changed |
| `failed` | Validation failed; see `errors[]` |

- **`row` is the 1-based spreadsheet line**, so row 1 is the header and the first
  data row is `2`. Display it verbatim — the user can jump straight to that line
  in Excel.
- **One bad row never aborts the batch.** Good rows still import.
- `errors[]` is a list of `{field, message}` so you can highlight the exact cell.

**Recommended flow:** upload → POST with `dry_run=true` → show the per-row
preview table → on confirm, re-POST the same file with `dry_run=false`.

**Whole-file errors:** `422 VALIDATION_ERROR` — empty file, missing required
columns, no data rows, over 5,000 rows, or undecodable text. `413
PAYLOAD_TOO_LARGE` — over 5 MB. In these cases **nothing** was imported.

---

### Generate Onboarding Reminder

**Endpoint:** `POST /employees/{id}/generate-reminder`  ·  **Auth:** ADMIN or FINANCE

**Response (200):**
```json
{
  "issue": "KYC_INCOMPLETE",
  "summary": "Ada has not submitted a government ID.",
  "suggested_action": "Send a reminder"
}
```

---

## 💰 Payroll

### Upload Payroll CSV

**Endpoint:** `POST /payroll/upload`

**Request:** `multipart/form-data`
- `file`: CSV file
- `batch_name`: "September 2026 Payroll"

**Response (200):**
```json
{
  "batch_id": "batch-002",
  "batch_name": "September 2026 Payroll",
  "items_count": 8,
  "total_amount_usd": 12400,
  "status": "UPLOADED"
}
```

---

### List Payroll Batches

**Endpoint:** `GET /payroll/batches`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 25, max: 100)

**Response (200):**
```json
{
  "items": [
    {
      "id": "batch-001",
      "batch_name": "September 2026 Payroll",
      "status": "RISK_SCORING",
      "total_items": 8,
      "total_amount_usd": 12400,
      "safety_score": 75,
      "safety_label": "MODERATE",
      "approved_by": null,
      "approved_at": null,
      "created_at": "2026-09-01T10:00:00Z",
      "updated_at": "2026-09-22T10:00:00Z"
    }
  ],
  "page": 1,
  "limit": 25,
  "total": 1,
  "total_pages": 1
}
```

---

### Get Payroll Batch Details

**Endpoint:** `GET /payroll/batches/{batch_id}`

**Response (200):**
```json
{
  "batch": {
    "id": "batch-001",
    "batch_name": "September 2026 Payroll",
    "status": "RISK_SCORING",
    "total_items": 8,
    "total_amount_usd": 12400,
    "safety_score": 75,
    "safety_label": "MODERATE",
    "approved_by": null,
    "approved_at": null,
    "created_at": "2026-09-01T10:00:00Z",
    "updated_at": "2026-09-22T10:00:00Z"
  },
  "items": [
    {
      "id": "item-001",
      "batch_id": "batch-001",
      "employee_id": "emp-001",
      "employee_name": "Ada Okafor",
      "employee_email": "ada@acme.com",
      "country": "Nigeria",
      "currency": "NGN",
      "amount": 250000,
      "department": "Engineering",
      "role": "Frontend Engineer",
      "payment_note": "September salary",
      "risk_score": 5,
      "risk_level": "LOW",
      "risk_reasons": [],
      "decision": "APPROVE",
      "decision_reason": null,
      "validation_errors": [],
      "created_at": "2026-09-01T10:00:00Z"
    }
  ],
  "currency_totals": {
    "NGN": 830000,
    "USD": 5000
  },
  "risk_summary": {
    "LOW": 5,
    "MEDIUM": 2,
    "HIGH": 1
  },
  "decision_summary": {
    "APPROVE": 5,
    "HOLD": 2,
    "REVIEW": 1
  }
}
```

---

### Score Risk for Batch

**Endpoint:** `POST /payroll/batches/{batch_id}/score-risk`

**Response (200):** Updated batch object

---

### Approve Batch

**Endpoint:** `POST /payroll/batches/{batch_id}/approve`

**Request:**
```json
{
  "override_reason": "Manager approved high-risk items",
  "item_decisions": {
    "item-006": "APPROVE",
    "item-005": "HOLD"
  }
}
```

**Response (200):** Updated batch object

---

### Simulate Disbursement

**Endpoint:** `POST /payroll/batches/{batch_id}/simulate-disbursement`

**Response (200):**
```json
{
  "message": "Disbursement simulated successfully",
  "batch_id": "batch-001",
  "disbursed_items": 8,
  "total_amount_usd": 12400
}
```

---

## 📈 Forecast

### Get Payroll Runway Forecast

**Endpoint:** `GET /forecast/payroll-runway`

**Response (200):**
```json
{
  "forecasts": [
    {
      "currency": "NGN",
      "wallet_code": "CNGN",
      "balance": 15000000,
      "required": 830000,
      "shortfall": 0,
      "surplus": 14170000,
      "status": "SUFFICIENT",
      "message": "Sufficient balance for 18 payroll cycles"
    }
  ],
  "overall_status": "SAFE",
  "generated_at": "2026-09-22T10:00:00Z"
}
```

---

### Get Forecast for Specific Batch

**Endpoint:** `GET /forecast/batch/{batch_id}`

**Response (200):** Same as above

---

## 💳 Cards

### List Cards

**Endpoint:** `GET /cards`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 200)

**Response (200):**
```json
{
  "items": [
    {
      "id": "card-001",
      "employee_id": "emp-001",
      "bmoni_card_id": "bmoni_card_001",
      "card_name": "Ada's Payroll Card",
      "card_color": "#4285F4",
      "currency": "NGN",
      "card_type": "virtual",
      "status": "ACTIVE",
      "spending_limit": 100000,
      "spent_amount": 45000,
      "is_frozen": false,
      "created_at": "2026-09-01T10:00:00Z",
      "updated_at": "2026-09-22T10:00:00Z"
    }
  ],
  "page": 1,
  "limit": 50,
  "total": 3,
  "total_pages": 1
}
```

---

### Create Card

**Endpoint:** `POST /cards`

**Request:**
```json
{
  "employee_id": "emp-001",
  "card_name": "Ada's Expense Card",
  "card_color": "#34A853",
  "currency": "NGN",
  "card_type": "virtual",
  "spending_limit": 50000
}
```

**Response (201):**
```json
{
  "card": {
    "id": "card-004",
    "employee_id": "emp-001",
    "bmoni_card_id": "bmoni_card_1234",
    "card_name": "Ada's Expense Card",
    "card_color": "#34A853",
    "currency": "NGN",
    "card_type": "virtual",
    "status": "ACTIVE",
    "spending_limit": 50000,
    "spent_amount": 0,
    "is_frozen": false,
    "created_at": "2026-09-22T12:00:00Z",
    "updated_at": "2026-09-22T12:00:00Z"
  },
  "status": "created"
}
```

---

### Update Card Status (Freeze/Unfreeze)

**Endpoint:** `PUT /cards/{card_id}/status`

**Request:**
```json
{
  "is_frozen": true
}
```

**Response (200):** Updated card object

---

### Update Card Limit

**Endpoint:** `PUT /cards/{card_id}/limit`

**Request:**
```json
{
  "spending_limit": 75000
}
```

**Response (200):** Updated card object

---

## 🔔 Webhooks

### Receive Webhook from BMONI/Flutterwave

**Endpoint:** `POST /webhooks/bmoni`

**Request:** (varies by event type)

**Response (200):**
```json
{
  "message": "Webhook received successfully"
}
```

---

### Simulate Webhook Event

**Endpoint:** `POST /webhooks/simulate`

**Request:**
```json
{
  "event_type": "employee.linked",
  "payload": {
    "userId": "bmoni_ada001",
    "email": "ada@acme.com"
  }
}
```

**Response (200):**
```json
{
  "message": "Webhook simulated successfully",
  "event_id": "evt-123"
}
```

---

### List Webhook Events

**Endpoint:** `GET /webhooks/events`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50, max: 200)

**Response (200):**
```json
{
  "items": [
    {
      "id": "evt-001",
      "event_id": "evt_001",
      "source_event_id": "bmoni_evt_001",
      "event_type": "employee.linked",
      "payload": {},
      "signature_valid": true,
      "state": "PROCESSED",
      "processed": true,
      "error_message": null,
      "created_at": "2026-09-08T10:00:00Z"
    }
  ],
  "page": 1,
  "limit": 50,
  "total": 4,
  "total_pages": 1
}
```

---

## 🤖 Copilot

### Query AI Copilot

**Endpoint:** `POST /copilot/query`

**Request:**
```json
{
  "question": "How many employees are stuck in onboarding?"
}
```

**Response (200):**
```json
{
  "answer": "There are 3 employees currently stuck in the onboarding process.",
  "evidence": [
    "Employee emp-005: KYC action required",
    "Employee emp-007: Duplicate wallet address",
    "Employee emp-008: Wallet pending"
  ],
  "actions": [
    "Send reminder emails to stuck employees",
    "Review duplicate wallet addresses"
  ],
  "warnings": [
    "2 employees have been stuck for more than 7 days"
  ]
}
```

---

## 📝 Common Patterns

### Pagination

All list endpoints return the same envelope:

```json
{
  "items": [],
  "page": 1,
  "limit": 50,
  "total": 100,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false,
  "next_page": 2,
  "prev_page": null
}
```

`has_next` / `has_prev` / `next_page` / `prev_page` were added in v1.1.0 on
`GET /employees`. Bind pagination controls to them instead of computing
`page < total_pages` in four different components.

---

### Error Responses  *(changed in v1.1.0)*

**Every** error from the API — validation, auth, 404, and unhandled crashes —
uses one shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "full_name must be at least 2 characters.",
    "status": 422,
    "fields": [
      { "field": "full_name", "message": "must be at least 2 characters" }
    ],
    "request_id": "req_8f2c1a"
  },
  "detail": "full_name must be at least 2 characters."
}
```

- **`code`** — stable machine-readable string. **Branch on this.**
- **`message`** — human-readable, safe to show. **Never branch on this**; wording
  changes without notice, and a `if (msg === "...")` check will break silently.
- **`fields`** — present on `422` only. Map it onto form inputs to highlight the
  offending box instead of showing one banner.
- **`request_id`** — echoed in the server log. Put it in the corner of error
  toasts; it turns "it broke" into a one-line log lookup.
- **`detail`** — mirrors `message`. Kept so v1.0.0 code keeps working. Treat it
  as deprecated.

**Codes:**

| Status | `code` |
|---|---|
| 400 | `BAD_REQUEST` |
| 401 | `UNAUTHENTICATED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `CONFLICT` |
| 413 | `PAYLOAD_TOO_LARGE` |
| 415 | `UNSUPPORTED_MEDIA_TYPE` |
| 422 | `VALIDATION_ERROR` |
| 429 | `RATE_LIMITED` |
| 500 | `INTERNAL_ERROR` |
| 502 | `UPSTREAM_ERROR` |
| 503 | `SERVICE_UNAVAILABLE` |
| 504 | `UPSTREAM_TIMEOUT` |

Suggested shared handler:

```js
async function apiCall(path, options) {
  const res = await fetch(`/api/v1${path}`, options);
  if (res.ok) return res.json();

  const { error } = await res.json();
  switch (error.code) {
    case "UNAUTHENTICATED": clearToken(); redirect("/login"); break;
    case "FORBIDDEN":       toast("You don't have permission to do that."); break;
    case "VALIDATION_ERROR": return highlightFields(error.fields);
    case "UPSTREAM_ERROR":
    case "UPSTREAM_TIMEOUT": toast("Payment provider unavailable. Try again."); break;
    default: toast(`${error.message} (ref: ${error.request_id})`);
  }
  throw error;
}
```

`UNAUTHENTICATED` → login screen. `FORBIDDEN` → stay put. Collapsing the two is
the single most common integration bug here.

---

### Authentication

Every endpoint except `POST /auth/login` requires:

```
Authorization: Bearer <access_token>
```

A missing or malformed header returns **401**, never 403.

---

## 🔄 Status Enums

### Employee Onboarding Status
- `INVITED` - Employee invited, waiting to complete onboarding
- `KYC_ACTION_REQUIRED` - Employee needs to complete KYC
- `WALLET_PENDING` - Wallet creation pending
- `READY` - Employee is ready for payroll

### Payroll Batch Status
- `DRAFT` - Batch created but not finalized
- `UPLOADED` - CSV uploaded
- `RISK_SCORING` - Risk scoring in progress
- `PENDING_APPROVAL` - Waiting for approval
- `APPROVED` - Approved for disbursement
- `DISBURSED` - Funds disbursed
- `FAILED` - Disbursement failed

### Risk Level
- `LOW` - Score 0-30
- `MEDIUM` - Score 31-70
- `HIGH` - Score 71-100

### Decision
- `APPROVE` - Item approved for disbursement
- `HOLD` - Item held pending review
- `REVIEW` - Item requires manual review
- `REJECT` - Item rejected

### Card Status
- `ACTIVE` - Card is active
- `FROZEN` - Card is frozen
- `BLOCKED` - Card is blocked

### Forecast Status
- `SUFFICIENT` - Balance covers payroll
- `SHORTFALL` - Balance insufficient
- `LOW` - Balance low but sufficient

### Overall Forecast Status
- `SAFE` - All currencies have sufficient balance
- `WARNING` - Some currencies have low balance
- `CRITICAL` - One or more currencies have shortfall

---

## 📚 Additional Resources

- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Example Data:** See `backend/app/seed.py`

---

## 🚨 Breaking Changes Policy

Any changes to this API contract must be:
1. Discussed in team sync meeting
2. Documented in this file
3. Communicated to both teams
4. Version bumped (e.g., 1.0.0 → 1.1.0)

**Never** make breaking changes without following this process.

---

**Last Reviewed:** 2026-09-22  
**Next Review:** 2026-09-29
