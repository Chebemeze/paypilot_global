# PayPilot Global - Team Structure & Project Split

## 👥 Team Overview

**Total Members:** 4  
**Structure:** 2 Backend Developers + 2 Frontend Developers  
**Goal:** Each person owns specific features end-to-end within their domain

---

## 🎯 Team Assignments

### Person 1 — Backend Core (Employees & Auth)

**Focus:** Authentication, Employee Management, and Core API Infrastructure

**Responsibilities:**
- Authentication system (JWT, login, session management)
- Employee CRUD operations
- Employee onboarding workflow
- Flutterwave customer creation (Phase 2 of employee invite)
- Input validation and error handling
- API middleware (rate limiting, request logging)

**Files Owned:**
```
backend/app/api/v1/auth_routes.py
backend/app/api/v1/employee_routes.py
backend/app/api/auth.py
backend/app/services/flutterwave_client.py  (customer creation parts)
```

**Priority Tasks:**
| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | Add proper JWT auth middleware on all routes | ⬜ Not Started |
| 🔴 High | Add input validation on all employee endpoints | ⬜ Not Started |
| 🟡 Medium | Add pagination controls (search, filter, sort) | ⬜ Not Started |
| 🟡 Medium | Add soft delete for employees (don't hard delete) | ⬜ Not Started |
| 🟡 Medium | Add bulk employee import (CSV upload) | ⬜ Not Started |
| 🟢 Nice | Add employee search by name/email/country | ⬜ Not Started |
| 🟢 Nice | Add unit tests for auth module | ⬜ Not Started |

**Integration Points:**
- Frontend Person 1 consumes these endpoints for Dashboard and Employees pages
- Backend Person 2 needs auth middleware on their endpoints too
- Both frontend developers need the employee endpoints to be stable

---

### Person 2 — Backend Features (Payroll, Cards, Forecast & Webhooks)

**Focus:** Business Logic, Flutterwave Integration, and Payment Processing

**Responsibilities:**
- Complete Flutterwave migration (Phase 2)
- Payroll batch processing
- Risk scoring engine
- Card management via Flutterwave
- Webhook handling and replay
- Forecast engine
- Copilot query engine

**Files Owned:**
```
backend/app/api/v1/payroll_routes.py
backend/app/api/v1/card_routes.py
backend/app/api/v1/forecast_routes.py
backend/app/api/v1/webhook_routes.py
backend/app/api/v1/copilot_routes.py
backend/app/api/v1/dashboard_routes.py
backend/app/services/flutterwave_client.py  (card/transfer parts)
backend/app/services/risk_engine.py
backend/app/services/payroll_service.py
backend/app/services/forecast_engine.py
backend/app/services/webhook_service.py
backend/app/services/copilot.py
```

**Priority Tasks:**
| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | Update payroll routes to use Flutterwave transfers | ⬜ Not Started |
| 🔴 High | Update webhook routes to handle Flutterwave webhooks | ⬜ Not Started |
| 🔴 High | Add proper API error responses on all routes | ⬜ Not Started |
| 🟡 Medium | Complete card transaction history endpoint | ⬜ Not Started |
| 🟡 Medium | Add webhook retry mechanism | ⬜ Not Started |
| 🟡 Medium | Add payroll batch email notifications | ⬜ Not Started |
| 🟡 Medium | Add real-time dashboard updates (WebSocket) | ⬜ Not Started |
| 🟢 Nice | Add background worker for payroll processing | ⬜ Not Started |
| 🟢 Nice | Add unit tests for payroll service | ⬜ Not Started |

**Integration Points:**
- All frontend pages depend on these endpoints
- Must coordinate with Person 1 on shared models
- Dashboard endpoint reads data from all other tables

---

### Person 3 — Frontend Core (Dashboard, Employees, Login & Design System)

**Focus:** Core UI Pages, Design System, and Navigation

**Responsibilities:**
- Login page and authentication flow
- Dashboard page (metrics, charts, wallet balances)
- Employees page (CRUD, search, filters)
- Layout and navigation
- Design system (UI components)
- Mobile responsiveness
- Loading states and error handling

**Files Owned:**
```
frontend/src/app/login/page.tsx
frontend/src/app/dashboard/page.tsx
frontend/src/app/employees/page.tsx
frontend/src/app/layout.tsx
frontend/src/app/page.tsx
frontend/src/app/providers.tsx
frontend/src/components/layout/Layout.tsx
frontend/src/components/ui/Button.tsx
frontend/src/components/ui/Card.tsx
frontend/src/components/ui/Input.tsx
frontend/src/components/ui/Badge.tsx
frontend/src/components/ui/Modal.tsx
frontend/src/components/ui/Table.tsx
frontend/src/components/icons.tsx
frontend/src/lib/auth.ts
frontend/src/lib/api.ts
frontend/src/lib/utils.ts
frontend/src/app/globals.css
```

**Priority Tasks:**
| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | Add proper error boundaries and error UI | ⬜ Not Started |
| 🔴 High | Add skeleton loading states for all pages | ⬜ Not Started |
| 🔴 High | Improve mobile responsiveness across all pages | ⬜ Not Started |
| 🟡 Medium | Add toast notifications for success/error messages | ⬜ Not Started |
| 🟡 Medium | Add pagination UI controls to tables | ⬜ Not Started |
| 🟡 Medium | Add confirmation dialogs for destructive actions | ⬜ Not Started |
| 🟡 Medium | Add empty state illustrations | ⬜ Not Started |
| 🟢 Nice | Add dark mode support | ⬜ Not Started |
| 🟢 Nice | Add data table sorting UI | ⬜ Not Started |
| 🟢 Nice | Add keyboard shortcuts | ⬜ Not Started |

**Integration Points:**
- Creates shared UI components used by Person 4
- Auth flow must match Backend Person 1's JWT implementation
- Dashboard needs all backend endpoints to be stable

---

### Person 4 — Frontend Features (Payroll, Cards, Forecast, Webhooks & Copilot)

**Focus:** Feature-Rich Pages and Advanced UI Interactions

**Responsibilities:**
- Payroll page (CSV upload, batch approval, risk review)
- Cards page (create, freeze, edit limits)
- Forecast page (wallet runway, shortfall warnings)
- Webhooks page (event list, retry, simulate)
- Copilot page (chat interface, streaming)
- Data export features (CSV, JSON, PDF)

**Files Owned:**
```
frontend/src/app/payroll/page.tsx
frontend/src/app/cards/page.tsx
frontend/src/app/forecast/page.tsx
frontend/src/app/webhooks/page.tsx
frontend/src/app/copilot/page.tsx
```

**Priority Tasks:**
| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | Add proper error handling on all pages | ⬜ Not Started |
| 🔴 High | Add loading states for all async operations | ⬜ Not Started |
| 🟡 Medium | Add CSV export for payroll batches | ⬜ Not Started |
| 🟡 Medium | Add PDF export for payroll reports | ⬜ Not Started |
| 🟡 Medium | Add real-time card transaction updates | ⬜ Not Started |
| 🟡 Medium | Add webhook event timeline visualization | ⬜ Not Started |
| 🟡 Medium | Improve Copilot chat with streaming responses | ⬜ Not Started |
| 🟢 Nice | Add charts/graphs to Forecast page | ⬜ Not Started |
| 🟢 Nice | Add drag-and-drop CSV upload | ⬜ Not Started |
| 🟢 Nice | Add notification center for webhook events | ⬜ Not Started |

**Integration Points:**
- Uses UI components from Person 3
- All pages consume backend endpoints from Person 2
- Must coordinate with Person 3 on shared design patterns

---

## 📁 File Ownership Map

### Backend

| File | Owner |
|------|-------|
| `app/api/v1/auth_routes.py` | Person 1 |
| `app/api/v1/employee_routes.py` | Person 1 |
| `app/api/v1/payroll_routes.py` | Person 2 |
| `app/api/v1/card_routes.py` | Person 2 |
| `app/api/v1/forecast_routes.py` | Person 2 |
| `app/api/v1/webhook_routes.py` | Person 2 |
| `app/api/v1/copilot_routes.py` | Person 2 |
| `app/api/v1/dashboard_routes.py` | Person 2 |
| `app/api/auth.py` | Person 1 |
| `app/config.py` | Shared (coordinate changes) |
| `app/database.py` | Shared (coordinate changes) |
| `app/main.py` | Shared (coordinate changes) |
| `app/models/models.py` | Shared (coordinate changes) |
| `app/schemas/schemas.py` | Shared (coordinate changes) |
| `app/seed.py` | Shared (coordinate changes) |
| `app/services/flutterwave_client.py` | Person 2 (primary), Person 1 (employee parts) |
| `app/services/risk_engine.py` | Person 2 |
| `app/services/payroll_service.py` | Person 2 |
| `app/services/forecast_engine.py` | Person 2 |
| `app/services/webhook_service.py` | Person 2 |
| `app/services/copilot.py` | Person 2 |

### Frontend

| File | Owner |
|------|-------|
| `app/login/page.tsx` | Person 3 |
| `app/dashboard/page.tsx` | Person 3 |
| `app/employees/page.tsx` | Person 3 |
| `app/payroll/page.tsx` | Person 4 |
| `app/cards/page.tsx` | Person 4 |
| `app/forecast/page.tsx` | Person 4 |
| `app/webhooks/page.tsx` | Person 4 |
| `app/copilot/page.tsx` | Person 4 |
| `app/layout.tsx` | Person 3 |
| `app/page.tsx` | Person 3 |
| `app/providers.tsx` | Person 3 |
| `app/globals.css` | Person 3 |
| `components/layout/Layout.tsx` | Person 3 |
| `components/ui/*` | Person 3 |
| `components/icons.tsx` | Person 3 |
| `lib/api.ts` | Person 3 |
| `lib/auth.ts` | Person 3 |
| `lib/utils.ts` | Person 3 |

---

## 🔗 Integration Rules

### Rule 1: Never Modify Shared Files Without Approval

These files are shared and require team discussion before changes:
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/models/models.py`
- `backend/app/schemas/schemas.py`

### Rule 2: API Changes Require Communication

If a backend developer changes an endpoint response format:
1. Update the `API_CONTRACT.md`
2. Notify the relevant frontend developer(s)
3. Update the Swagger docs (automatic)
4. Give at least 1 day notice before deploying

### Rule 3: UI Component Changes Affect Everyone

If Person 3 changes a shared UI component:
1. Test it doesn't break Person 4's pages
2. Notify Person 4
3. Update documentation

### Rule 4: Database Schema Changes

If anyone needs to change the database models:
1. Discuss in team sync
2. Update `models.py` together
3. Update `seed.py` if needed
4. Both backend devs must approve
5. Run migration and verify

---

## 📅 Sync Schedule

### Daily Standup (10 minutes)

**When:** Every day at start of work  
**Who:** All 4 team members  
**Format:** Each person answers:
1. What did I do yesterday?
2. What am I working on today?
3. Any blockers?

### Weekly Merge (30 minutes)

**When:** Every Friday  
**Who:** All 4 team members  
**Agenda:**
1. Demo what was built this week
2. Merge all branches to main
3. Test the full application together
4. Plan next week's priorities
5. Update the API contract if needed

### Bi-Weekly Review (1 hour)

**When:** Every 2 weeks  
**Who:** All 4 team members  
**Agenda:**
1. Review overall progress
2. Re-prioritize backlog
3. Identify integration issues early
4. Celebrate wins!

---

## 🚀 Git Workflow

### Branch Strategy

```
main (stable, always working)
├── backend/p1-auth      ← Person 1's work
├── backend/p2-payroll   ← Person 2's work
├── frontend/p3-core     ← Person 3's work
└── frontend/p4-features ← Person 4's work
```

### Daily Workflow

```
Morning:
  1. Pull latest from main
  2. Create/update your feature branch
  3. Work on your tasks

During the day:
  4. Commit small, meaningful changes
  5. Push your branch regularly

End of day:
  6. Push all changes to your branch
  7. Write a brief summary of what you did
```

### Weekly Merge Process

```
Friday:
  1. All branches pushed and up to date
  2. One person (rotate weekly) merges all branches to main
  3. Resolve any conflicts TOGETHER
  4. Full team tests the application
  5. Fix any issues before weekend
```

### Commit Message Format

```
[TYPE] Brief description

Types:
- [FEAT] New feature
- [FIX] Bug fix
- [DOCS] Documentation
- [STYLE] Code style (formatting, etc.)
- [REFACTOR] Code refactoring
- [TEST] Adding tests
- [CHORE] Maintenance tasks

Examples:
- [FEAT] Add employee search by country
- [FIX] Fix cards page data.map error
- [DOCS] Update API contract for payroll endpoints
- [STYLE] Format code with prettier
```

---

## 📊 Progress Tracking

### How to Track Progress

Use this simple status in daily standups:
- ⬜ Not Started
- 🔄 In Progress
- ✅ Completed
- ❌ Blocked

### Weekly Progress Report

Each person should provide:
1. Tasks completed this week
2. Tasks in progress
3. Tasks planned for next week
4. Any blockers or help needed

---

## 🎯 Success Metrics

### Week 1 Goals
- [ ] Everyone has their dev environment set up
- [ ] Git branches created for all 4 people
- [ ] First small feature deployed by each person
- [ ] Daily standups happening consistently

### Week 2 Goals
- [ ] All high-priority tasks started
- [ ] First integration test between backend and frontend
- [ ] Weekly merge completed successfully
- [ ] API contract updated with any changes

### Week 3 Goals
- [ ] All high-priority tasks completed
- [ ] Medium-priority tasks in progress
- [ ] Full application working end-to-end
- [ ] No critical bugs in main branch

### Week 4 Goals
- [ ] All medium-priority tasks completed
- [ ] Nice-to-have tasks started
- [ ] Application ready for demo
- [ ] Documentation complete

---

## 🤝 Conflict Resolution

### If Two People Need to Edit the Same File

1. **Talk first** — Discuss in standup or Slack
2. **Coordinate** — Decide who makes the change
3. **Review together** — Both review the final code
4. **Document** — Note the decision in PR comments

### If Frontend and Backend Disagree on API Format

1. Refer to `API_CONTRACT.md`
2. If it's not documented, discuss in standup
3. Both teams must agree on the format
4. Update `API_CONTRACT.md` immediately
5. Backend implements first, then frontend connects

### If Integration Breaks

1. **Don't panic** — This happens!
2. **Identify the breaking change** — Who changed what?
3. **Revert if needed** — Get main working again
4. **Fix together** — Both teams work on the fix
5. **Test before merging** — Never merge without testing

---

## 📚 Getting Started Checklist

### For All Team Members

- [ ] Read `API_CONTRACT.md` thoroughly
- [ ] Read `LOCAL_SETUP_GUIDE.md` and set up your environment
- [ ] Install MySQL and XAMPP (follow the guides)
- [ ] Run the full application locally
- [ ] Test all features end-to-end
- [ ] Create your Git branch
- [ ] Understand which files you own
- [ ] Know your integration points with other team members

### For Backend Developers

- [ ] Understand the database schema (`models.py`)
- [ ] Review the Flutterwave client implementation
- [ ] Test all API endpoints in Swagger docs
- [ ] Understand the seed data
- [ ] Know how to add new endpoints

### For Frontend Developers

- [ ] Understand the component structure
- [ ] Review the design system (Tailwind classes)
- [ ] Test all pages in the browser
- [ ] Understand the auth flow
- [ ] Know how to add new pages

---

## 🎉 You're Ready!

With clear ownership, defined integration points, and regular sync meetings, your team of 4 can work efficiently and deliver great results.

**Remember:**
- Communication is everything
- Test before you merge
- Update documentation as you go
- Help each other when blocked

**Good luck!** 🚀
