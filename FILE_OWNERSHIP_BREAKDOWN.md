# Complete File Ownership Breakdown

This document lists **every file** in the project and assigns ownership to one of the 4 team members.

---

## 📊 File Summary

**Total Files:** 57 code files (excluding documentation)

| Category | Count | Owner |
|----------|-------|-------|
| **Person 1 (Backend Core)** | 3 files | Auth & Employees |
| **Person 2 (Backend Features)** | 15 files | Payroll, Cards, Forecast, Webhooks, Dashboard, Copilot |
| **Person 3 (Frontend Core)** | 16 files | Dashboard, Employees, Login, Design System |
| **Person 4 (Frontend Features)** | 5 files | Payroll, Cards, Forecast, Webhooks, Copilot pages |
| **Shared/General** | 18 files | Everyone (coordinate changes) |

---

# 👤 PERSON 1 — Backend Core (Auth & Employees)

## Your Files (3 files)

```
backend/app/api/auth.py                    # Authentication logic (JWT, password hashing)
backend/app/api/v1/auth_routes.py          # Login, logout, get current user endpoints
backend/app/api/v1/employee_routes.py      # Employee CRUD, invite, reminder endpoints
```

## What You Own

1. **`backend/app/api/auth.py`**
   - JWT token generation and validation
   - Password hashing
   - `get_employer_id()` dependency for all routes
   - User authentication logic

2. **`backend/app/api/v1/auth_routes.py`**
   - `POST /auth/login` - User login
   - `GET /auth/me` - Get current user info
   - Token refresh (if you add it)

3. **`backend/app/api/v1/employee_routes.py`**
   - `GET /employees` - List employees (with pagination)
   - `GET /employees/{id}` - Get employee details
   - `POST /employees` - Create employee
   - `PUT /employees/{id}` - Update employee
   - `DELETE /employees/{id}` - Delete employee
   - `POST /employees/{id}/invite` - Send invite (Flutterwave)
   - `POST /employees/{id}/resend-invite` - Resend invite
   - `POST /employees/{id}/generate-reminder` - Generate onboarding reminder

## What You DON'T Own (But Use)

- `models.py` - Shared (coordinate with Person 2)
- `schemas.py` - Shared (coordinate with Person 2)
- `flutterwave_client.py` - Owned by Person 2 (you use their client)

---

# 👤 PERSON 2 — Backend Features (Payroll, Cards, Forecast, Webhooks, Dashboard, Copilot)

## Your Files (15 files)

### API Routes (6 files)
```
backend/app/api/v1/payroll_routes.py       # Payroll batch management
backend/app/api/v1/card_routes.py          # Card CRUD, freeze, limit updates
backend/app/api/v1/forecast_routes.py      # Wallet runway forecasting
backend/app/api/v1/webhook_routes.py       # Webhook handling and replay
backend/app/api/v1/dashboard_routes.py     # Dashboard summary endpoint
backend/app/api/v1/copilot_routes.py       # AI copilot query endpoint
```

### Services (8 files)
```
backend/app/services/flutterwave_client.py # Flutterwave API integration
backend/app/services/bmoni_client.py       # BMONI legacy client (deprecated)
backend/app/services/payroll_service.py    # Payroll processing logic
backend/app/services/risk_engine.py        # Risk scoring algorithm
backend/app/services/forecast_engine.py    # Forecast calculation logic
backend/app/services/webhook_service.py    # Webhook processing logic
backend/app/services/copilot.py            # AI copilot logic
backend/app/services/onboarding_rescue.py  # Employee onboarding assistance
```

### Supporting Files (1 file)
```
backend/app/mocks/__init__.py              # Mock data for demo mode
```

## What You Own

### API Endpoints

1. **Payroll Routes** (`payroll_routes.py`)
   - `POST /payroll/upload` - Upload payroll CSV
   - `GET /payroll/batches` - List payroll batches
   - `GET /payroll/batches/{id}` - Get batch details
   - `POST /payroll/batches/{id}/score-risk` - Score risk for batch
   - `POST /payroll/batches/{id}/approve` - Approve batch
   - `POST /payroll/batches/{id}/simulate-disbursement` - Simulate disbursement

2. **Card Routes** (`card_routes.py`)
   - `GET /cards` - List cards
   - `POST /cards` - Create card
   - `PUT /cards/{id}/status` - Freeze/unfreeze card
   - `PUT /cards/{id}/limit` - Update spending limit

3. **Forecast Routes** (`forecast_routes.py`)
   - `GET /forecast/payroll-runway` - Get forecast
   - `GET /forecast/batch/{id}` - Get forecast for specific batch

4. **Webhook Routes** (`webhook_routes.py`)
   - `POST /webhooks/bmoni` - Receive webhook (legacy)
   - `POST /webhooks/flutterwave` - Receive Flutterwave webhook (you'll add this)
   - `POST /webhooks/simulate` - Simulate webhook event
   - `GET /webhooks/events` - List webhook events

5. **Dashboard Routes** (`dashboard_routes.py`)
   - `GET /dashboard/summary` - Get dashboard metrics

6. **Copilot Routes** (`copilot_routes.py`)
   - `POST /copilot/query` - Query AI copilot

### Services (Business Logic)

1. **Flutterwave Client** - Main payment integration
2. **BMONI Client** - Legacy (keep for backward compatibility)
3. **Payroll Service** - Process payroll batches
4. **Risk Engine** - Score payroll risk
5. **Forecast Engine** - Calculate wallet runway
6. **Webhook Service** - Process incoming webhooks
7. **Copilot** - AI assistant logic
8. **Onboarding Rescue** - Help stuck employees

## What You DON'T Own (But Coordinate With)

- `models.py` - Shared with Person 1 (you both use it)
- `schemas.py` - Shared with Person 1 (you both use it)
- `auth.py` - Owned by Person 1 (you use their auth dependency)

---

# 👤 PERSON 3 — Frontend Core (Dashboard, Employees, Login, Design System)

## Your Files (16 files)

### Pages (3 files)
```
frontend/src/app/login/page.tsx            # Login page
frontend/src/app/dashboard/page.tsx        # Dashboard page
frontend/src/app/employees/page.tsx        # Employees page
```

### Layout & Navigation (2 files)
```
frontend/src/app/layout.tsx                # Root layout (all pages)
frontend/src/components/layout/Layout.tsx  # Main layout with sidebar
```

### App Setup (3 files)
```
frontend/src/app/page.tsx                  # Home page (redirects to dashboard)
frontend/src/app/providers.tsx             # React Query provider
frontend/src/app/globals.css               # Global styles
```

### UI Components (6 files)
```
frontend/src/components/ui/Button.tsx      # Button component
frontend/src/components/ui/Card.tsx        # Card component
frontend/src/components/ui/Input.tsx       # Input component
frontend/src/components/ui/Badge.tsx       # Badge component
frontend/src/components/ui/Modal.tsx       # Modal component
frontend/src/components/ui/Table.tsx       # Table component
```

### Icons (1 file)
```
frontend/src/components/icons.tsx          # SVG icon components
```

### Utilities (3 files)
```
frontend/src/lib/api.ts                    # API client (axios instance)
frontend/src/lib/auth.ts                   # Auth utilities (login, logout, token)
frontend/src/lib/utils.ts                  # Helper functions (formatCurrency, etc.)
```

### Config Files (4 files)
```
frontend/next.config.js                    # Next.js configuration
frontend/tailwind.config.js                # Tailwind CSS configuration
frontend/postcss.config.js                 # PostCSS configuration
frontend/tsconfig.json                     # TypeScript configuration
```

## What You Own

### Pages

1. **Login Page** - User authentication UI
2. **Dashboard Page** - Metrics, wallet balances, recent activity
3. **Employees Page** - Employee list, create, edit, delete

### Design System (UI Components)

You own **all** UI components. Person 4 uses them but doesn't modify them:
- Button (with variants: primary, secondary, danger, ghost)
- Card (with hover states)
- Input (with labels, errors, icons)
- Badge (with status variants)
- Modal (with header, footer, sizes)
- Table (with columns, pagination-ready)

### Core Infrastructure

1. **API Client** (`api.ts`) - Axios instance with auth headers
2. **Auth Utilities** (`auth.ts`) - Login, logout, token management
3. **Helper Functions** (`utils.ts`) - Currency formatting, date formatting, status variants

### Layout

1. **Root Layout** - HTML structure, fonts, metadata
2. **Main Layout** - Sidebar navigation, header, content area

## What You DON'T Own (But Person 4 Uses)

- All your UI components are used by Person 4
- Your `api.ts` is used by Person 4
- Your `auth.ts` is used by Person 4
- Your `utils.ts` is used by Person 4

**Rule:** If you change a component API (props), tell Person 4!

---

# 👤 PERSON 4 — Frontend Features (Payroll, Cards, Forecast, Webhooks, Copilot)

## Your Files (5 files)

```
frontend/src/app/payroll/page.tsx          # Payroll batch management
frontend/src/app/cards/page.tsx            # Card management
frontend/src/app/forecast/page.tsx         # Wallet forecast
frontend/src/app/webhooks/page.tsx         # Webhook event viewer
frontend/src/app/copilot/page.tsx          # AI copilot chat
```

## What You Own

### Pages

1. **Payroll Page** - Upload CSV, view batches, approve, simulate disbursement
2. **Cards Page** - Create cards, freeze/unfreeze, edit limits, view transactions
3. **Forecast Page** - View wallet runway, shortfall warnings
4. **Webhooks Page** - View webhook events, retry failed events, simulate new events
5. **Copilot Page** - Chat with AI assistant, ask questions

## What You DON'T Own (But Use)

You use these files owned by Person 3:
- `Button.tsx`, `Card.tsx`, `Input.tsx`, `Badge.tsx`, `Modal.tsx`, `Table.tsx`
- `api.ts`, `auth.ts`, `utils.ts`
- `Layout.tsx` (the sidebar and header)

**Rule:** Don't modify these files without asking Person 3!

---

# 🤝 SHARED/GENERAL FILES (Everyone - Coordinate Changes)

These files affect the entire project. **No one person owns them.** All changes require team discussion.

## Database & Models (3 files)
```
backend/app/models/models.py               # All database tables
backend/app/models/__init__.py             # Model imports
backend/app/schemas/schemas.py             # Request/response schemas
backend/app/schemas/__init__.py            # Schema imports
```

**Why Shared:**
- Person 1 uses them for employee endpoints
- Person 2 uses them for payroll, cards, etc.
- Both frontend developers consume the schemas

**Rule:** Never modify without team discussion!

## Core Backend (4 files)
```
backend/app/main.py                        # FastAPI app entry point
backend/app/config.py                      # Configuration (env vars)
backend/app/database.py                    # Database connection
backend/app/seed.py                        # Database seeder
```

**Why Shared:**
- `main.py` - Registers all routes (Person 1 & 2 both add routes)
- `config.py` - Environment variables (affects everyone)
- `database.py` - Database setup (affects all database operations)
- `seed.py` - Demo data (needs to match models)

**Rule:** Coordinate with team before changing!

## Environment & Dependencies (2 files)
```
backend/.env                               # Environment variables
backend/requirements.txt                   # Python dependencies
```

**Why Shared:**
- `.env` - Database URL, API keys (affects everyone)
- `requirements.txt` - Backend packages (affects both backend devs)

**Rule:** Add dependencies only when needed, tell the team!

## Package Management (2 files)
```
frontend/package.json                      # Node dependencies
frontend/next-env.d.ts                     # Next.js TypeScript definitions
```

**Why Shared:**
- `package.json` - Frontend packages (affects both frontend devs)

**Rule:** Add dependencies only when needed, tell the team!

## Example Files (3 files)
```
examples/payroll.csv                       # Sample payroll CSV
examples/webhook_kyc_action_required.json  # Sample webhook payload
examples/webhook_onboarding_completed.json # Sample webhook payload
```

**Why Shared:**
- Used for testing by everyone
- Documentation for API consumers

**Rule:** Anyone can add examples, but tell the team!

## Scripts (1 file)
```
start-servers.sh                           # Script to start both servers
```

**Why Shared:**
- Used by everyone to run the app locally

**Rule:** Coordinate changes!

## Backend Init Files (2 files)
```
backend/app/__init__.py                    # Empty init
backend/app/api/__init__.py                # Empty init
backend/app/api/v1/__init__.py             # Empty init
backend/app/services/__init__.py           # Empty init
backend/app/tests/__init__.py              # Empty init
backend/app/workers/__init__.py            # Empty init
```

**Why Shared:**
- These are empty Python init files
- They make directories into Python packages
- No one needs to modify them

**Rule:** Don't touch unless adding new modules!

---

# 📋 Complete File List by Owner

## Person 1 — Backend Core (3 files)
1. `backend/app/api/auth.py`
2. `backend/app/api/v1/auth_routes.py`
3. `backend/app/api/v1/employee_routes.py`

## Person 2 — Backend Features (15 files)
1. `backend/app/api/v1/payroll_routes.py`
2. `backend/app/api/v1/card_routes.py`
3. `backend/app/api/v1/forecast_routes.py`
4. `backend/app/api/v1/webhook_routes.py`
5. `backend/app/api/v1/dashboard_routes.py`
6. `backend/app/api/v1/copilot_routes.py`
7. `backend/app/services/flutterwave_client.py`
8. `backend/app/services/bmoni_client.py`
9. `backend/app/services/payroll_service.py`
10. `backend/app/services/risk_engine.py`
11. `backend/app/services/forecast_engine.py`
12. `backend/app/services/webhook_service.py`
13. `backend/app/services/copilot.py`
14. `backend/app/services/onboarding_rescue.py`
15. `backend/app/mocks/__init__.py`

## Person 3 — Frontend Core (16 files)
1. `frontend/src/app/login/page.tsx`
2. `frontend/src/app/dashboard/page.tsx`
3. `frontend/src/app/employees/page.tsx`
4. `frontend/src/app/layout.tsx`
5. `frontend/src/components/layout/Layout.tsx`
6. `frontend/src/app/page.tsx`
7. `frontend/src/app/providers.tsx`
8. `frontend/src/app/globals.css`
9. `frontend/src/components/ui/Button.tsx`
10. `frontend/src/components/ui/Card.tsx`
11. `frontend/src/components/ui/Input.tsx`
12. `frontend/src/components/ui/Badge.tsx`
13. `frontend/src/components/ui/Modal.tsx`
14. `frontend/src/components/ui/Table.tsx`
15. `frontend/src/components/icons.tsx`
16. `frontend/src/lib/api.ts`
17. `frontend/src/lib/auth.ts`
18. `frontend/src/lib/utils.ts`
19. `frontend/next.config.js`
20. `frontend/tailwind.config.js`
21. `frontend/postcss.config.js`
22. `frontend/tsconfig.json`

## Person 4 — Frontend Features (5 files)
1. `frontend/src/app/payroll/page.tsx`
2. `frontend/src/app/cards/page.tsx`
3. `frontend/src/app/forecast/page.tsx`
4. `frontend/src/app/webhooks/page.tsx`
5. `frontend/src/app/copilot/page.tsx`

## Shared/General (18 files)
1. `backend/app/models/models.py`
2. `backend/app/models/__init__.py`
3. `backend/app/schemas/schemas.py`
4. `backend/app/schemas/__init__.py`
5. `backend/app/main.py`
6. `backend/app/config.py`
7. `backend/app/database.py`
8. `backend/app/seed.py`
9. `backend/.env`
10. `backend/requirements.txt`
11. `frontend/package.json`
12. `frontend/next-env.d.ts`
13. `examples/payroll.csv`
14. `examples/webhook_kyc_action_required.json`
15. `examples/webhook_onboarding_completed.json`
16. `start-servers.sh`
17. `backend/app/__init__.py`
18. `backend/app/api/__init__.py`
19. `backend/app/api/v1/__init__.py`
20. `backend/app/services/__init__.py`
21. `backend/app/tests/__init__.py`
22. `backend/app/workers/__init__.py`

---

# 🔗 Integration Points Matrix

## Person 1 Integrates With:

| With Whom | What You Share | When to Communicate |
|-----------|----------------|---------------------|
| **Person 2** | `models.py`, `schemas.py` | Before adding/changing database tables |
| **Person 3** | Auth endpoints, employee endpoints | When changing response format |
| **Person 4** | Employee endpoints | When adding new query parameters |

## Person 2 Integrates With:

| With Whom | What You Share | When to Communicate |
|-----------|----------------|---------------------|
| **Person 1** | `models.py`, `schemas.py`, `auth.py` | Before changing models or using auth |
| **Person 3** | Dashboard endpoint | When changing dashboard response |
| **Person 4** | All your endpoints | When changing any response format |

## Person 3 Integrates With:

| With Whom | What You Share | When to Communicate |
|-----------|----------------|---------------------|
| **Person 1** | Auth flow | When login response changes |
| **Person 2** | Dashboard API | When dashboard data structure changes |
| **Person 4** | UI components, utilities | Before changing any component API |

## Person 4 Integrates With:

| With Whom | What You Share | When to Communicate |
|-----------|----------------|---------------------|
| **Person 1** | Employee data | When employee format changes |
| **Person 2** | All backend endpoints | When you need new endpoints |
| **Person 3** | UI components | Ask before modifying shared components |

---

# 🎯 Decision Matrix

## Who Decides What?

### Backend Decisions

| Decision | Who Decides | Who Must Approve |
|----------|-------------|------------------|
| Add new auth endpoint | Person 1 | Person 2 (if it uses models) |
| Add new employee field | Person 1 | Person 2 (models.py change) |
| Add new payroll endpoint | Person 2 | Person 1 (if it uses models) |
| Add new Flutterwave feature | Person 2 | Person 1 (if it affects auth) |
| Change database schema | Both backend devs | Both must approve |
| Add new dependency | Person adding it | Other backend dev |

### Frontend Decisions

| Decision | Who Decides | Who Must Approve |
|----------|-------------|------------------|
| Change Button component | Person 3 | Person 4 (they use it) |
| Change Table component | Person 3 | Person 4 (they use it) |
| Add new UI component | Person 3 | Person 4 (feedback) |
| Change API client | Person 3 | Person 4 (they use it) |
| Add new page | Person 3 or 4 | Other frontend dev (review) |
| Change auth flow | Person 3 | Person 1 (backend auth) |
| Add new dependency | Person adding it | Other frontend dev |

### Shared Decisions

| Decision | Who Decides | Who Must Approve |
|----------|-------------|------------------|
| Change `.env` structure | Anyone | All 4 team members |
| Change `main.py` | Anyone | All 4 team members |
| Change `config.py` | Anyone | All 4 team members |
| Add example file | Anyone | Tell the team |
| Change `seed.py` | Anyone | Both backend devs |

---

# 📊 Quick Reference

## File Count by Person

```
Person 1:  3 files  (5%)   - Backend Auth & Employees
Person 2: 15 files  (26%)  - Backend Features
Person 3: 22 files  (38%)  - Frontend Core & Design System
Person 4:  5 files  (9%)   - Frontend Feature Pages
Shared:   22 files  (38%)  - Everyone coordinates
```

## Most Critical Shared Files

These files affect everyone. **Extra care needed when modifying:**

1. `backend/app/models/models.py` - Database schema (both backend devs)
2. `backend/app/schemas/schemas.py` - API contracts (both backend devs)
3. `frontend/src/components/ui/*.tsx` - UI components (both frontend devs)
4. `frontend/src/lib/api.ts` - API client (both frontend devs)
5. `backend/.env` - Environment variables (everyone)

## Files That Never Change

These files rarely need modification:

1. `backend/app/__init__.py` (and other `__init__.py` files) - Empty init files
2. `frontend/next-env.d.ts` - Auto-generated by Next.js
3. `frontend/postcss.config.js` - PostCSS config (rarely changes)

---

# ✅ Rules of Engagement

## Rule 1: Stay in Your Lane

- **Person 1:** Only modify your 3 files + shared files (with approval)
- **Person 2:** Only modify your 15 files + shared files (with approval)
- **Person 3:** Only modify your 22 files + shared files (with approval)
- **Person 4:** Only modify your 5 files + shared files (with approval)

## Rule 2: Ask Before Touching Shared Files

Never modify shared files without:
1. Discussing in standup
2. Getting approval from affected team members
3. Testing thoroughly
4. Documenting the change

## Rule 3: Communicate Integration Points

If your change affects someone else:
1. Tell them in standup
2. Update `API_CONTRACT.md` if it's an API change
3. Give them time to adapt
4. Test together

## Rule 4: No Surprises

Never push a change that:
- Breaks another person's code
- Changes an API response without telling frontend
- Modifies a shared component without telling the other frontend dev
- Adds a new dependency without telling the team

## Rule 5: Help Each Other

If someone is blocked:
1. Drop what you're doing (if possible)
2. Help them unblock
3. The team succeeds together

---

# 🎉 You're All Set!

Now everyone knows:
✅ Exactly which files they own  
✅ Which files are shared  
✅ Who they integrate with  
✅ When to communicate  
✅ How to make decisions  

**Time to start building!** 🚀
