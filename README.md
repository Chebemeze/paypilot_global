# PayPilot Global

**AI payroll operations for borderless teams using BMONI Embedded.**

PayPilot Global helps employers safely pay remote teams across currencies by combining BMONI wallets, virtual accounts, onboarding intelligence, payroll fraud scoring, funding forecasts, and verified real-time webhook evidence.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.seed   # Seeds demo database
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Login Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@acmeglobal.com | password123 |
| Finance | finance@acmeglobal.com | password123 |
| Viewer | viewer@acmeglobal.com | password123 |

---

## 🏗 Architecture

```
Next.js React UI (port 3000)
      ↓
FastAPI Backend (port 8000)
      ↓
SQLite Database
      ↓
BMONI demo/mock client + webhook simulator
```

---

## 📋 Features

### Core Features
1. **Employer Dashboard** — Team overview, wallet balances, risk indicators, webhook timeline
2. **Employee Management** — Searchable table, onboarding status tracking, smart rescue messages
3. **Smart Onboarding Rescue** — Automatic issue classification with copy-paste email/WhatsApp messages
4. **Payroll CSV Upload** — Streaming validation, row-level errors, duplicate detection
5. **Risk Engine** — 10 fraud signals per item, O(n) duplicate detection, batch Safety Score (0-100)
6. **Wallet Funding Forecast** — Per-currency shortfall detection with top-up suggestions
7. **Webhook Command Center** — HMAC-SHA256 verification, deduplication, event state machine
8. **AI Payroll Copilot** — Deterministic answers with evidence, actions, and warnings
9. **Team Expense Cards** — Virtual card management with freeze/unfreeze

### Security
- HMAC-SHA256 webhook signature verification with constant-time comparison
- JWT-based authentication with role-based access control
- Employer-scoped authorization on every query (tenant isolation)
- Idempotency keys for payroll approval and disbursement
- Audit logging for all payroll overrides and approvals
- BMONI API keys and webhook secrets never exposed to frontend

---

## 🌍 Multi-Currency Support

| Display Currency | BMONI Wallet Code | Rail |
|---|---|---|
| NGN | CNGN | Virtual account deposits, bank withdrawals |
| USD | USDB | Virtual bank account (ACH/wire) |
| EUR | EURe | SEPA payouts to IBAN |
| CAD | CADC | Canadian rails via PayTrie |
| MXN | MEXe | SPEI/CLABE on/offramp |
| GBP | GBPe | Wallet holding |

---

## 🧪 Demo Flow (under 3 minutes)

1. **Login** to employer dashboard (admin@acmeglobal.com)
2. **Show global team** across 4+ currencies on the dashboard
3. **View stuck employee** — Chiamaka Nwosu needs KYC liveness
4. **Generate reminder** — Copy email/WhatsApp message
5. **Upload payroll CSV** — See validation results
6. **Score risk** — See John Bello flagged HIGH (wallet changed, salary 260% above expected)
7. **View Payroll Safety Score** — 71 (REVIEW_REQUIRED)
8. **Check forecast** — USD wallet shortfall detected
9. **Ask Copilot** — "Can we run payroll today?"
10. **Approve/hold items** — Override high-risk with reason
11. **Simulate webhook** — See verified event in timeline

---

## 📡 API Endpoints

### Auth
- `POST /api/v1/auth/login` — Authenticate
- `GET /api/v1/auth/me` — Current user

### Dashboard
- `GET /api/v1/dashboard/summary` — Full dashboard metrics

### Employees
- `GET /api/v1/employees` — List with pagination, filter, search
- `GET /api/v1/employees/{id}` — Detail with onboarding issue
- `POST /api/v1/employees/invite` — Invite new employee
- `POST /api/v1/employees/{id}/generate-reminder` — AI rescue message
- `POST /api/v1/employees/{id}/resend-invite` — Resend invite

### Payroll
- `POST /api/v1/payroll/upload` — Upload CSV
- `GET /api/v1/payroll/batches` — List batches
- `GET /api/v1/payroll/batches/{id}` — Batch detail with items
- `POST /api/v1/payroll/batches/{id}/score-risk` — Run risk scoring
- `POST /api/v1/payroll/batches/{id}/approve` — Approve with decisions
- `POST /api/v1/payroll/batches/{id}/simulate-disbursement` — Demo disbursement

### Forecast
- `GET /api/v1/forecast/payroll-runway` — Wallet funding forecast
- `GET /api/v1/forecast/batch/{id}` — Batch-specific forecast

### Copilot
- `POST /api/v1/copilot/query` — Ask the AI Copilot

### Webhooks
- `POST /api/v1/webhooks/bmoni` — Receive BMONI webhooks
- `POST /api/v1/webhooks/simulate` — Simulate webhook (demo)
- `GET /api/v1/webhooks/events` — List webhook events

### Cards
- `GET /api/v1/cards` — List cards
- `PUT /api/v1/cards/{id}/status` — Freeze/unfreeze
- `PUT /api/v1/cards/{id}/limit` — Update spending limit

---

## 🛡 Demo Seed Data

### 8 Employees
1. Ada Okafor — Nigeria — NGN — Ready ✅
2. Daniel Mensah — Ghana — USD — Ready ✅
3. Sofia Ruiz — Mexico — MXN — Ready ✅
4. Marie Keller — Germany — EUR — Ready ✅
5. Chiamaka Nwosu — Nigeria — NGN — KYC Action Required ⚠️
6. John Bello — Nigeria — USD — High Risk (wallet changed) 🔴
7. Victor James — Nigeria — NGN — Duplicate destination 🟡
8. Lina Chen — Canada — CAD — Wallet Pending ⏳

### Wallet Balances
- CNGN: ₦15,000,000 (sufficient)
- USDB: $8,950 (shortfall)
- EURe: €5,000 (sufficient)
- MEXe: MX$250,000 (sufficient)
- CADC: C$500 (low)
- GBPe: £1,000 (holding)

---

## 📦 Tech Stack

### Frontend
- Next.js 14 + React + TypeScript
- Tailwind CSS
- TanStack Query
- Recharts
- React Hook Form + Zod

### Backend
- Python 3.11+ / FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- SQLite (demo) / PostgreSQL (production)
- PBKDF2-SHA256 password hashing
- JWT authentication

---

## 📄 License

Built for the BMONI Embedded hackathon.
