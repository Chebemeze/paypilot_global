# Integration Checklist — PayPilot Global

## 🎯 Purpose

This checklist ensures that when 4 people work on different parts of the project, everything integrates seamlessly without breaking.

---

## 📋 Pre-Integration Checklist

### Before Any Merge to Main

#### Backend Developers (Person 1 & 2)

- [ ] **All endpoints work in Swagger docs** (`http://localhost:8000/docs`)
- [ ] **No breaking changes to existing API responses** (or documented in API_CONTRACT.md)
- [ ] **Database migrations tested** (if models changed)
- [ ] **Seed data still works** (`python -m app.seed` runs without errors)
- [ ] **Authentication works** (can login, token validates correctly)
- [ ] **Error responses are consistent** (proper HTTP status codes)
- [ ] **No hardcoded secrets** (all in .env)
- [ ] **Code follows existing style** (consistent formatting)
- [ ] **No debug prints or console.logs** left in
- [ ] **CORS is configured** (frontend can reach backend)

#### Frontend Developers (Person 3 & 4)

- [ ] **All pages load without errors** (check browser console)
- [ ] **API calls use correct endpoints** (matching API_CONTRACT.md)
- [ ] **Loading states show** (skeleton/spinner while data loads)
- [ ] **Error states show** (friendly message when API fails)
- [ ] **Empty states show** (when no data exists)
- [ ] **Responsive design works** (test at 375px, 768px, 1024px, 1440px)
- [ ] **No TypeScript errors** (`npm run build` succeeds)
- [ ] **Shared UI components still work** (Button, Modal, Table, etc.)
- [ ] **Auth flow works** (login → dashboard → logout)
- [ ] **No hardcoded URLs** (use environment variables)

---

## 🔗 Integration Points Matrix

This shows where different parts of the code depend on each other.

### Backend → Frontend Dependencies

| Backend Endpoint | Frontend Page | Owner (Backend) | Owner (Frontend) | Risk Level |
|------------------|---------------|-----------------|------------------|------------|
| `POST /auth/login` | Login page | Person 1 | Person 3 | 🔴 High |
| `GET /auth/me` | All pages (auth check) | Person 1 | Person 3 | 🔴 High |
| `GET /dashboard/summary` | Dashboard | Person 2 | Person 3 | 🔴 High |
| `GET /employees` | Employees page | Person 1 | Person 3 | 🟡 Medium |
| `POST /employees` | Employees page | Person 1 | Person 3 | 🟡 Medium |
| `PUT /employees/{id}` | Employees page | Person 1 | Person 3 | 🟡 Medium |
| `DELETE /employees/{id}` | Employees page | Person 1 | Person 3 | 🟡 Medium |
| `POST /payroll/upload` | Payroll page | Person 2 | Person 4 | 🟡 Medium |
| `GET /payroll/batches` | Payroll page | Person 2 | Person 4 | 🟡 Medium |
| `GET /payroll/batches/{id}` | Payroll page | Person 2 | Person 4 | 🟡 Medium |
| `POST /payroll/batches/{id}/approve` | Payroll page | Person 2 | Person 4 | 🔴 High |
| `GET /cards` | Cards page | Person 2 | Person 4 | 🟡 Medium |
| `POST /cards` | Cards page | Person 2 | Person 4 | 🟡 Medium |
| `PUT /cards/{id}/status` | Cards page | Person 2 | Person 4 | 🟡 Medium |
| `GET /forecast/payroll-runway` | Forecast page | Person 2 | Person 4 | 🟢 Low |
| `GET /webhooks/events` | Webhooks page | Person 2 | Person 4 | 🟢 Low |
| `POST /copilot/query` | Copilot page | Person 2 | Person 4 | 🟢 Low |

### Frontend → Frontend Dependencies

| Shared Component | Used By | Owner | Risk Level |
|------------------|---------|-------|------------|
| `Button.tsx` | All pages | Person 3 | 🔴 High |
| `Modal.tsx` | All pages | Person 3 | 🔴 High |
| `Table.tsx` | Employees, Payroll, Webhooks | Person 3 | 🔴 High |
| `Card.tsx` | All pages | Person 3 | 🔴 High |
| `Input.tsx` | All forms | Person 3 | 🔴 High |
| `Badge.tsx` | All pages | Person 3 | 🟡 Medium |
| `Layout.tsx` | All pages | Person 3 | 🔴 High |
| `auth.ts` | All pages | Person 3 | 🔴 High |
| `api.ts` | All pages | Person 3 | 🔴 High |

### Backend → Backend Dependencies

| Shared File | Used By | Risk Level |
|-------------|---------|------------|
| `models.py` | All endpoints | 🔴 High |
| `schemas.py` | All endpoints | 🔴 High |
| `config.py` | All modules | 🟡 Medium |
| `database.py` | All endpoints | 🔴 High |
| `main.py` | App entry | 🟡 Medium |
| `seed.py` | Database setup | 🟡 Medium |

---

## 🧪 Integration Test Scenarios

### Scenario 1: User Authentication Flow

**Who to test:** Person 1 (backend) + Person 3 (frontend)

**Steps:**
1. Start backend: `python -m uvicorn app.main:app --reload --port 8000`
2. Start frontend: `npm run dev`
3. Open http://localhost:3000
4. Login with `admin@acmeglobal.com` / `password123`
5. Verify: Redirected to dashboard
6. Verify: User name shows in header
7. Logout
8. Verify: Redirected to login page
9. Try accessing /dashboard without login
10. Verify: Redirected to login

**Pass criteria:** All steps complete without errors.

---

### Scenario 2: Employee Management Flow

**Who to test:** Person 1 (backend) + Person 3 (frontend)

**Steps:**
1. Login as admin
2. Navigate to Employees page
3. Verify: 8 seed employees show in table
4. Click "Add Employee"
5. Fill in form: "Test User", "test@acme.com", "Nigeria", "Engineering"
6. Click "Create"
7. Verify: New employee appears in table
8. Click "Edit" on the new employee
9. Change department to "Marketing"
10. Click "Save"
11. Verify: Department updated in table
12. Click "Delete" on the new employee
13. Confirm deletion
14. Verify: Employee removed from table
15. Search for "Ada"
16. Verify: Only Ada Okafor shows
17. Clear search
18. Verify: All employees show again

**Pass criteria:** All CRUD operations work, search works, no console errors.

---

### Scenario 3: Payroll Processing Flow

**Who to test:** Person 2 (backend) + Person 4 (frontend)

**Steps:**
1. Login as admin
2. Navigate to Payroll page
3. Verify: Existing payroll batch shows
4. Click "Upload CSV"
5. Upload `examples/payroll.csv`
6. Verify: Success message with item count
7. Verify: New batch appears in table
8. Click on the new batch
9. Verify: All items show with risk scores
10. Click "Score Risk"
11. Verify: Risk scores update
12. Click "Approve Batch"
13. Verify: Status changes to "APPROVED"
14. Click "Simulate Disbursement"
15. Verify: Success message
16. Verify: Status changes to "DISBURSED"

**Pass criteria:** Full payroll lifecycle works without errors.

---

### Scenario 4: Card Management Flow

**Who to test:** Person 2 (backend) + Person 4 (frontend)

**Steps:**
1. Login as admin
2. Navigate to Cards page
3. Verify: 3 seed cards show
4. Verify: Each card shows: name, currency, balance, progress bar
5. Click "Create Card"
6. Fill in: "Test Card", "USD", limit: 500
7. Click "Create"
8. Verify: New card appears
9. Click "Freeze" on a card
10. Confirm
11. Verify: Card shows "Frozen" badge
12. Click "Unfreeze"
13. Confirm
14. Verify: Badge removed
15. Click "Edit Limit" on a card
16. Change limit to 2000
17. Click "Update"
18. Verify: Limit updated
19. Click "Export"
20. Verify: JSON file downloads

**Pass criteria:** All card operations work, no data.map errors.

---

### Scenario 5: Dashboard Integration

**Who to test:** Person 2 (backend) + Person 3 (frontend)

**Steps:**
1. Login as admin
2. Navigate to Dashboard
3. Verify: Total employees shows (8)
4. Verify: Ready employees shows (5)
5. Verify: Stuck employees shows (3)
6. Verify: High risk items shows
7. Verify: Safety score/label shows
8. Verify: Wallet balances show for each currency
9. Verify: Recent webhooks show
10. Verify: Forecast shortfalls show
11. Create a new employee
12. Navigate back to dashboard
13. Verify: Total employees updated (9)
14. Stop backend server
15. Refresh dashboard
16. Verify: Error message shows (not blank page)
17. Start backend server
18. Click "Retry" (if available)
19. Verify: Dashboard loads again

**Pass criteria:** All metrics show correctly, error handling works.

---

### Scenario 6: Responsive Design

**Who to test:** Person 3 + Person 4 (both frontend devs)

**Steps for each page:**
1. Open Chrome DevTools
2. Toggle device toolbar
3. Test at 375px (iPhone SE)
4. Test at 390px (iPhone 12)
5. Test at 768px (iPad)
6. Test at 1024px (iPad Pro)
7. Test at 1440px (Desktop)

**Check for each page:**
- [ ] No horizontal scroll
- [ ] Text is readable
- [ ] Buttons are tappable (min 44px)
- [ ] Tables scroll horizontally or use card layouts
- [ ] Navigation works (hamburger menu on mobile)
- [ ] Modals are full-screen on mobile
- [ ] Images scale properly

**Pass criteria:** All pages look good at all breakpoints.

---

### Scenario 7: Error Handling

**Who to test:** All 4 team members

**Steps:**
1. Stop backend server
2. Open frontend
3. Navigate to each page
4. Verify: Each page shows error message (not blank)
5. Verify: "Retry" button works
6. Start backend
7. Click "Retry" on each page
8. Verify: Data loads

**Then:**
9. Login with wrong password
10. Verify: Error message shows
11. Login with correct password
12. Delete an employee, then try to view them
13. Verify: "Not found" error shows

**Pass criteria:** All error states handled gracefully.

---

## 🔄 Weekly Integration Checklist

### Every Friday

#### Step 1: Individual Verification (Each person - 10 min)

**Person 1:**
- [ ] My auth endpoints work in Swagger
- [ ] My employee endpoints work in Swagger
- [ ] I haven't changed any shared files without telling the team
- [ ] My branch is pushed and up to date

**Person 2:**
- [ ] My payroll endpoints work in Swagger
- [ ] My card endpoints work in Swagger
- [ ] My webhook endpoints work in Swagger
- [ ] My branch is pushed and up to date

**Person 3:**
- [ ] Login page works
- [ ] Dashboard page works
- [ ] Employees page works
- [ ] All my UI components work on Person 4's pages
- [ ] My branch is pushed and up to date

**Person 4:**
- [ ] Payroll page works
- [ ] Cards page works
- [ ] Forecast page works
- [ ] Webhooks page works
- [ ] Copilot page works
- [ ] My branch is pushed and up to date

#### Step 2: Merge to Main (One person - 15 min)

```bash
git checkout main
git pull origin main

# Merge each branch one at a time
git merge backend/p1-auth-employees
git merge backend/p2-payroll-cards
git merge frontend/p3-core-ui
git merge frontend/p4-feature-pages

# If conflicts, resolve together
# Then push
git push origin main
```

#### Step 3: Full Team Testing (All 4 - 30 min)

1. Everyone pulls main
2. Start backend and frontend
3. Run through integration test scenarios above
4. Report any issues
5. Fix together before ending the day

#### Step 4: Plan Next Week (All 4 - 10 min)

1. Review what was completed
2. Update task statuses
3. Assign next week's priorities
4. Identify any risks or blockers

---

## 🚨 Emergency Procedures

### If Main Branch Breaks

1. **Don't panic** — This happens to every team
2. **Identify the problem** — Who merged what?
3. **Revert if needed:**
   ```bash
   git revert HEAD  # Revert the last merge
   git push origin main
   ```
4. **Fix the issue** — Person who caused it + one other person
5. **Test thoroughly** — Run all integration scenarios
6. **Re-merge** — Only after everything works

### If Two Branches Conflict

1. **Identify the conflict** — Which files overlap?
2. **Talk it out** — Both people discuss what each change does
3. **Decide together** — Which version to keep? Both? Modified?
4. **Resolve carefully** — Don't lose either person's work
5. **Test thoroughly** — Make sure both features still work

### If API Contract Breaks

1. **Stop** — Don't continue working
2. **Identify the change** — What endpoint changed?
3. **Discuss** — Backend dev explains why
4. **Update contract** — Modify API_CONTRACT.md together
5. **Update both sides** — Backend implements, frontend adapts
6. **Test together** — Verify the integration works

---

## 📊 Integration Health Metrics

### Track These Weekly

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Merge success rate** | 100% | Merges without breaking main |
| **Integration bugs** | < 2 per week | Bugs found during Friday testing |
| **Time to fix integration bugs** | < 2 hours | From detection to fix |
| **API contract violations** | 0 | Frontend getting wrong data format |
| **Shared file conflicts** | < 1 per week | Git conflicts on shared files |
| **Test coverage** | > 80% | Integration scenarios passing |

---

## 🎯 Integration Success Rules

### Rule 1: Test Before You Merge

Never merge code you haven't tested locally. Always run the full application before pushing.

### Rule 2: Communicate Changes

If you change an API response, shared component, or database schema — tell the team BEFORE merging.

### Rule 3: Small, Frequent Merges

Merge small changes daily rather than big changes weekly. Smaller merges = fewer conflicts.

### Rule 4: Help Each Other

If someone is stuck on an integration issue, drop what you're doing and help. Integration problems block everyone.

### Rule 5: Document Everything

If it's not documented, it doesn't exist. Update API_CONTRACT.md, models, and comments as you go.

### Rule 6: No Heroes

Don't try to fix everything alone. Ask for help early. The team succeeds together.

---

## 📝 Integration Notes Template

After each weekly merge, fill this out:

```markdown
## Week of [DATE]

### Merged Features
- Person 1: [What was merged]
- Person 2: [What was merged]
- Person 3: [What was merged]
- Person 4: [What was merged]

### Conflicts Encountered
- [File] — [Resolution]

### Bugs Found
- [Bug] — [Who's fixing it] — [Due date]

### API Changes
- [Endpoint] — [What changed] — [Who was notified]

### Next Week Focus
- Person 1: [Priority tasks]
- Person 2: [Priority tasks]
- Person 3: [Priority tasks]
- Person 4: [Priority tasks]

### Risks
- [Any risks or blockers]
```

---

## ✅ Final Integration Sign-Off

Before declaring a feature "done":

- [ ] Backend developer confirms endpoint works
- [ ] Frontend developer confirms page works
- [ ] Both test the integration together
- [ ] API_CONTRACT.md is up to date
- [ ] No console errors
- [ ] No Swagger errors
- [ ] Works on mobile (if frontend)
- [ ] Works with error states (backend stopped)
- [ ] Code reviewed by at least one other person
- [ ] Merged to main without conflicts

---

**Integration is a team sport. Communicate, test, and help each other!** 🤝
