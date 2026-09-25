# 🎯 Quick File Reference - Who Owns What?

## 📁 Visual Overview

```
paypilot-global/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py                      👤 PERSON 1
│   │   │   └── v1/
│   │   │       ├── auth_routes.py           👤 PERSON 1
│   │   │       ├── employee_routes.py       👤 PERSON 1
│   │   │       ├── payroll_routes.py        👤 PERSON 2
│   │   │       ├── card_routes.py           👤 PERSON 2
│   │   │       ├── forecast_routes.py       👤 PERSON 2
│   │   │       ├── webhook_routes.py        👤 PERSON 2
│   │   │       ├── dashboard_routes.py      👤 PERSON 2
│   │   │       └── copilot_routes.py        👤 PERSON 2
│   │   │
│   │   ├── models/
│   │   │   └── models.py                    🤝 SHARED
│   │   │
│   │   ├── schemas/
│   │   │   └── schemas.py                   🤝 SHARED
│   │   │
│   │   ├── services/
│   │   │   ├── flutterwave_client.py        👤 PERSON 2
│   │   │   ├── bmoni_client.py              👤 PERSON 2
│   │   │   ├── payroll_service.py           👤 PERSON 2
│   │   │   ├── risk_engine.py               👤 PERSON 2
│   │   │   ├── forecast_engine.py           👤 PERSON 2
│   │   │   ├── webhook_service.py           👤 PERSON 2
│   │   │   ├── copilot.py                   👤 PERSON 2
│   │   │   └── onboarding_rescue.py         👤 PERSON 2
│   │   │
│   │   ├── main.py                          🤝 SHARED
│   │   ├── config.py                        🤝 SHARED
│   │   ├── database.py                      🤝 SHARED
│   │   └── seed.py                          🤝 SHARED
│   │
│   ├── .env                                 🤝 SHARED
│   └── requirements.txt                     🤝 SHARED
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/
│   │   │   │   └── page.tsx                 👤 PERSON 3
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx                 👤 PERSON 3
│   │   │   ├── employees/
│   │   │   │   └── page.tsx                 👤 PERSON 3
│   │   │   ├── payroll/
│   │   │   │   └── page.tsx                 👤 PERSON 4
│   │   │   ├── cards/
│   │   │   │   └── page.tsx                 👤 PERSON 4
│   │   │   ├── forecast/
│   │   │   │   └── page.tsx                 👤 PERSON 4
│   │   │   ├── webhooks/
│   │   │   │   └── page.tsx                 👤 PERSON 4
│   │   │   ├── copilot/
│   │   │   │   └── page.tsx                 👤 PERSON 4
│   │   │   ├── layout.tsx                   👤 PERSON 3
│   │   │   ├── page.tsx                     👤 PERSON 3
│   │   │   ├── providers.tsx                👤 PERSON 3
│   │   │   └── globals.css                  👤 PERSON 3
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Layout.tsx               👤 PERSON 3
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx               👤 PERSON 3
│   │   │   │   ├── Card.tsx                 👤 PERSON 3
│   │   │   │   ├── Input.tsx                👤 PERSON 3
│   │   │   │   ├── Badge.tsx                👤 PERSON 3
│   │   │   │   ├── Modal.tsx                👤 PERSON 3
│   │   │   │   └── Table.tsx                👤 PERSON 3
│   │   │   └── icons.tsx                    👤 PERSON 3
│   │   │
│   │   └── lib/
│   │       ├── api.ts                       👤 PERSON 3
│   │       ├── auth.ts                      👤 PERSON 3
│   │       └── utils.ts                     👤 PERSON 3
│   │
│   ├── package.json                         🤝 SHARED
│   ├── next.config.js                       👤 PERSON 3
│   ├── tailwind.config.js                   👤 PERSON 3
│   ├── postcss.config.js                    👤 PERSON 3
│   └── tsconfig.json                        👤 PERSON 3
│
└── examples/                                🤝 SHARED
```

---

# 👤 PERSON 1 — Backend Core (Auth & Employees)

## 📦 Your Files (3 total)

```
backend/app/api/auth.py                      ← Auth logic (JWT, passwords)
backend/app/api/v1/auth_routes.py            ← Login, logout endpoints
backend/app/api/v1/employee_routes.py        ← Employee CRUD, invite
```

## 🎯 What You Do
- Build authentication system
- Manage employee data
- Handle user sessions

## 🔗 You Integrate With
- **Person 2** → When changing database models
- **Person 3** → When changing auth/employee API responses
- **Person 4** → When adding new employee query parameters

---

# 👤 PERSON 2 — Backend Features (Payroll, Cards, Forecast, Webhooks, Dashboard, Copilot)

## 📦 Your Files (15 total)

### API Routes (6 files)
```
backend/app/api/v1/payroll_routes.py         ← Payroll batches
backend/app/api/v1/card_routes.py            ← Card management
backend/app/api/v1/forecast_routes.py        ← Wallet forecasting
backend/app/api/v1/webhook_routes.py         ← Webhook handling
backend/app/api/v1/dashboard_routes.py       ← Dashboard summary
backend/app/api/v1/copilot_routes.py         ← AI copilot
```

### Services (8 files)
```
backend/app/services/flutterwave_client.py   ← Flutterwave API
backend/app/services/bmoni_client.py         ← Legacy BMONI
backend/app/services/payroll_service.py      ← Payroll logic
backend/app/services/risk_engine.py          ← Risk scoring
backend/app/services/forecast_engine.py      ← Forecast logic
backend/app/services/webhook_service.py      ← Webhook processing
backend/app/services/copilot.py              ← AI assistant
backend/app/services/onboarding_rescue.py    ← Onboarding help
```

### Mock Data (1 file)
```
backend/app/mocks/__init__.py                ← Demo data
```

## 🎯 What You Do
- Process payroll
- Manage virtual cards
- Handle webhooks
- Build forecasting
- Integrate Flutterwave
- Create AI copilot

## 🔗 You Integrate With
- **Person 1** → When changing models/schemas or using auth
- **Person 3** → When changing dashboard API response
- **Person 4** → When changing any API response format

---

# 👤 PERSON 3 — Frontend Core (Dashboard, Employees, Login & Design System)

## 📦 Your Files (22 total)

### Pages (3 files)
```
frontend/src/app/login/page.tsx              ← Login page
frontend/src/app/dashboard/page.tsx          ← Dashboard
frontend/src/app/employees/page.tsx          ← Employee management
```

### App Setup (4 files)
```
frontend/src/app/layout.tsx                  ← Root layout
frontend/src/app/page.tsx                    ← Home redirect
frontend/src/app/providers.tsx               ← React Query
frontend/src/app/globals.css                 ← Global styles
```

### Layout (1 file)
```
frontend/src/components/layout/Layout.tsx    ← Sidebar + header
```

### UI Components (6 files)
```
frontend/src/components/ui/Button.tsx        ← Buttons
frontend/src/components/ui/Card.tsx          ← Cards
frontend/src/components/ui/Input.tsx         ← Inputs
frontend/src/components/ui/Badge.tsx         ← Badges
frontend/src/components/ui/Modal.tsx         ← Modals
frontend/src/components/ui/Table.tsx         ← Tables
```

### Icons (1 file)
```
frontend/src/components/icons.tsx            ← SVG icons
```

### Utilities (3 files)
```
frontend/src/lib/api.ts                      ← API client
frontend/src/lib/auth.ts                     ← Auth helpers
frontend/src/lib/utils.ts                    ← Helper functions
```

### Config (4 files)
```
frontend/next.config.js                      ← Next.js config
frontend/tailwind.config.js                  ← Tailwind config
frontend/postcss.config.js                   ← PostCSS config
frontend/tsconfig.json                       ← TypeScript config
```

## 🎯 What You Do
- Build the design system
- Create core pages (login, dashboard, employees)
- Manage navigation and layout
- Handle auth flow on frontend
- Create reusable UI components

## 🔗 You Integrate With
- **Person 1** → When login/auth response changes
- **Person 2** → When dashboard API structure changes
- **Person 4** → ⚠️ **CRITICAL** → Before changing ANY UI component

---

# 👤 PERSON 4 — Frontend Features (Payroll, Cards, Forecast, Webhooks, Copilot)

## 📦 Your Files (5 total)

```
frontend/src/app/payroll/page.tsx            ← Payroll management
frontend/src/app/cards/page.tsx              ← Card management
frontend/src/app/forecast/page.tsx           ← Wallet forecast
frontend/src/app/webhooks/page.tsx           ← Webhook viewer
frontend/src/app/copilot/page.tsx            ← AI chat
```

## 🎯 What You Do
- Build complex feature pages
- Handle file uploads (CSV)
- Manage real-time data displays
- Create interactive workflows
- Build the AI chat interface

## 🔗 You Integrate With
- **Person 1** → When employee data format changes
- **Person 2** → When you need new backend endpoints
- **Person 3** → ⚠️ **CRITICAL** → Ask before modifying UI components

## ⚠️ Important Note
You **USE** these files owned by Person 3 (but don't modify them):
- All UI components (Button, Card, Input, Badge, Modal, Table)
- `api.ts`, `auth.ts`, `utils.ts`
- `Layout.tsx`

**Always ask Person 3 before changing these!**

---

# 🤝 SHARED FILES (Everyone - Coordinate Changes)

## 📦 Shared Files (22 total)

### Database (4 files)
```
backend/app/models/models.py                 ← Database schema
backend/app/models/__init__.py               ← Model imports
backend/app/schemas/schemas.py               ← API contracts
backend/app/schemas/__init__.py              ← Schema imports
```

### Core Backend (4 files)
```
backend/app/main.py                          ← FastAPI app
backend/app/config.py                        ← Configuration
backend/app/database.py                      ← DB connection
backend/app/seed.py                          ← Demo data seeder
```

### Dependencies (3 files)
```
backend/.env                                 ← Environment variables
backend/requirements.txt                     ← Python packages
frontend/package.json                        ← Node packages
```

### Example Files (3 files)
```
examples/payroll.csv                         ← Sample payroll
examples/webhook_kyc_action_required.json    ← Sample webhook
examples/webhook_onboarding_completed.json   ← Sample webhook
```

### Init Files (6 files - rarely change)
```
backend/app/__init__.py
backend/app/api/__init__.py
backend/app/api/v1/__init__.py
backend/app/services/__init__.py
backend/app/tests/__init__.py
backend/app/workers/__init__.py
```

### Other (2 files)
```
frontend/next-env.d.ts                       ← Auto-generated
start-servers.sh                             ← Startup script
```

## ⚠️ Rules for Shared Files

1. **Never modify without team discussion**
2. **Get approval from affected team members**
3. **Test thoroughly before committing**
4. **Document the change**
5. **Tell the team in standup**

---

# 📊 Summary by Person

| Person | Role | Files Owned | % of Total |
|--------|------|-------------|-----------|
| **Person 1** | Backend Core | 3 files | 5% |
| **Person 2** | Backend Features | 15 files | 26% |
| **Person 3** | Frontend Core | 22 files | 38% |
| **Person 4** | Frontend Features | 5 files | 9% |
| **Shared** | Everyone | 22 files | 38% |

**Total:** 67 files (some overlap with shared)

---

# 🎯 Quick Decision Guide

## "Can I modify this file?"

### ✅ YES - You Own It
- It's in your file list above
- No one else needs to approve
- Just test and commit

### 🤝 MAYBE - Shared File
- It's in the shared list
- Discuss in standup first
- Get team approval
- Test with everyone

### ❌ NO - Someone Else Owns It
- It's in another person's list
- Ask them to make the change
- Or ask if you can modify it
- Coordinate the change

---

# 🔥 Most Critical Files

These files affect the most people. **Extra care needed:**

1. **`backend/app/models/models.py`** 🤝
   - Affects: Person 1, Person 2, both frontend devs
   - Change when: Adding new database tables/fields

2. **`backend/app/schemas/schemas.py`** 🤝
   - Affects: Person 1, Person 2, both frontend devs
   - Change when: Modifying API request/response formats

3. **`frontend/src/components/ui/*.tsx`** 👤 Person 3
   - Affects: Person 3, Person 4
   - Change when: Updating design system

4. **`frontend/src/lib/api.ts`** 👤 Person 3
   - Affects: Person 3, Person 4
   - Change when: Modifying API client

5. **`backend/.env`** 🤝
   - Affects: Everyone
   - Change when: Adding new environment variables

---

# 🚀 Remember

✅ **Your files** = Modify freely (after testing)  
🤝 **Shared files** = Discuss first, get approval  
❌ **Other's files** = Ask them to change or coordinate  

**When in doubt, ask in standup!**
