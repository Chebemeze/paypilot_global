# PayPilot Global - Individual Task Assignments

## 🎯 How to Use This Document

Each person has a dedicated section with:
- **Your mission** — What you own
- **Immediate tasks** — What to work on first
- **Integration points** — Who you work with
- **Testing checklist** — How to verify your work
- **AI assistant prompts** — What to ask me (your AI agent)

---

# 👤 PERSON 1 — Backend Core (Auth & Employees)

## Your Mission
You own everything related to authentication and employee management on the backend. You make sure users can log in securely and employees can be created, updated, and managed properly.

## Files You Own
```
backend/app/api/v1/auth_routes.py
backend/app/api/v1/employee_routes.py
backend/app/api/auth.py
```

---

## 📋 Your Task List (Priority Order)

### 🔴 HIGH PRIORITY (Week 1)

#### Task 1: Add JWT Auth Middleware to All Routes
**What:** Currently, some routes don't properly verify JWT tokens. Add proper auth checking to EVERY endpoint except `/auth/login`.

**How to test:**
1. Try accessing `/employees` without a token → should get 401
2. Try with an expired token → should get 401
3. Try with a valid token → should work

**Ask me:** "Add JWT authentication middleware to protect all API routes except login"

---

#### Task 2: Add Input Validation on Employee Endpoints
**What:** Currently, the create/update employee endpoints accept any data. Add proper validation:
- Email must be valid format
- Country must be a valid country code
- Currency must be one of: NGN, USD, EUR, GBP, MXN, CAD
- Salary must be a positive number
- Name cannot be empty

**How to test:**
1. Try creating employee with invalid email → should get 400 error
2. Try with empty name → should get 400 error
3. Try with invalid currency → should get 400 error

**Ask me:** "Add Pydantic validation schemas for employee create/update endpoints"

---

#### Task 3: Add Proper Error Responses
**What:** Replace generic errors with specific, helpful error messages:
- "Email already exists" (409 Conflict)
- "Employee not found" (404)
- "Invalid currency: XYZ" (400)

**How to test:**
1. Create employee with duplicate email → should get 409
2. Update non-existent employee → should get 404

**Ask me:** "Add proper HTTP error responses to all employee endpoints"

---

### 🟡 MEDIUM PRIORITY (Week 2)

#### Task 4: Add Employee Search and Filtering
**What:** Add query parameters to GET /employees:
- `?search=john` — Search by name or email
- `?country=Nigeria` — Filter by country
- `?status=READY` — Filter by onboarding status
- `?department=Engineering` — Filter by department
- `?sort=name` — Sort by name
- `?sort=created_at&order=desc` — Sort by date

**How to test:**
1. GET /employees?search=ada → should return only Ada
2. GET /employees?country=Nigeria → should return Nigerian employees only

**Ask me:** "Add search, filter, and sort parameters to the GET /employees endpoint"

---

#### Task 5: Add Soft Delete for Employees
**What:** Instead of hard-deleting employees (removing from database), mark them as deleted with a timestamp. This preserves payroll history.

**Changes needed:**
- Add `deleted_at` column (already exists in model)
- Update DELETE endpoint to set `deleted_at` instead of removing
- Update GET endpoints to exclude soft-deleted employees

**Ask me:** "Implement soft delete for employees instead of hard delete"

---

#### Task 6: Add Bulk Employee Import (CSV)
**What:** Create endpoint to upload a CSV of employees:
- `POST /employees/bulk-import`
- Accepts CSV file with columns: name, email, country, department, role, salary, currency
- Validates each row
- Returns success/failure count

**Ask me:** "Create a bulk employee import endpoint that accepts CSV files"

---

### 🟢 NICE TO HAVE (Week 3+)

#### Task 7: Add Unit Tests for Auth Module
**What:** Write tests for:
- Login with correct credentials
- Login with wrong password
- Login with non-existent email
- Token expiration
- Token refresh

**Ask me:** "Write unit tests for the authentication module using pytest"

---

#### Task 8: Add Employee Status Dashboard Endpoint
**What:** Create a quick stats endpoint:
- `GET /employees/stats`
- Returns: total count, count by status, count by country, count by department

**Ask me:** "Add an employee statistics endpoint"

---

## 🔗 Your Integration Points

| With Whom | What You Share | Communication Needed |
|-----------|----------------|----------------------|
| **Person 2** | Database models, schemas | Before changing models.py |
| **Person 3** | Auth endpoints, employee endpoints | When changing response formats |
| **Person 4** | Employee endpoints | When adding new query params |

---

## ✅ Your Testing Checklist

Before marking any task as done:
- [ ] Endpoint works in Swagger docs
- [ ] Frontend can consume the endpoint (test with Person 3 or 4)
- [ ] Error cases return proper error codes
- [ ] No existing functionality is broken
- [ ] Code follows the existing style

---

## 💬 Prompts to Ask Me

Copy-paste these to get help:

```
"Add JWT authentication middleware to protect all API routes except login"

"Add Pydantic validation schemas for employee create/update endpoints"

"Add proper HTTP error responses to all employee endpoints"

"Add search, filter, and sort parameters to the GET /employees endpoint"

"Implement soft delete for employees instead of hard delete"

"Create a bulk employee import endpoint that accepts CSV files"

"Write unit tests for the authentication module using pytest"

"Add an employee statistics endpoint at GET /employees/stats"
```

---
---

# 👤 PERSON 2 — Backend Features (Payroll, Cards, Forecast & Webhooks)

## Your Mission
You own the core business logic — payroll processing, card management, webhook handling, forecasting, and the Flutterwave integration. You make the money move safely.

## Files You Own
```
backend/app/api/v1/payroll_routes.py
backend/app/api/v1/card_routes.py
backend/app/api/v1/forecast_routes.py
backend/app/api/v1/webhook_routes.py
backend/app/api/v1/copilot_routes.py
backend/app/api/v1/dashboard_routes.py
backend/app/services/flutterwave_client.py
backend/app/services/risk_engine.py
backend/app/services/payroll_service.py
backend/app/services/forecast_engine.py
backend/app/services/webhook_service.py
backend/app/services/copilot.py
```

---

## 📋 Your Task List (Priority Order)

### 🔴 HIGH PRIORITY (Week 1)

#### Task 1: Update Payroll Routes to Use Flutterwave
**What:** Currently payroll uses BMONI mocks. Update to use Flutterwave's transfer API:
- `POST /payroll/batches/{id}/simulate-disbursement` should call Flutterwave's transfer endpoint
- Handle success/failure responses
- Update batch status accordingly

**How to test:**
1. Create a payroll batch
2. Approve it
3. Simulate disbursement → should create Flutterwave transfer

**Ask me:** "Update payroll disbursement endpoint to use Flutterwave transfers instead of BMONI"

---

#### Task 2: Update Webhook Routes for Flutterwave
**What:** Flutterwave sends different webhook events than BMONI. Update the webhook handler to:
- Verify Flutterwave webhook signatures
- Parse Flutterwave event types
- Process: charge.completed, transfer.completed, transfer.failed

**Ask me:** "Update webhook handler to process Flutterwave webhook events with signature verification"

---

#### Task 3: Add Proper Error Responses on All Routes
**What:** Every endpoint should return clear, consistent errors:
- Card not found → 404
- Batch already approved → 409
- Insufficient balance → 422
- Invalid webhook signature → 401

**Ask me:** "Add proper HTTP error responses to all payroll, card, forecast, and webhook endpoints"

---

### 🟡 MEDIUM PRIORITY (Week 2)

#### Task 4: Add Card Transaction History Endpoint
**What:** Currently there's no way to see what a card was used for. Add:
- `GET /cards/{card_id}/transactions`
- Returns list of transactions with: date, amount, merchant, status

**Note:** In demo mode, generate mock transactions

**Ask me:** "Add a card transaction history endpoint with mock transaction data"

---

#### Task 5: Add Webhook Retry Mechanism
**What:** If a webhook fails to process, it should be retried:
- Add `retry_count` and `next_retry_at` fields to webhook_events table
- Create a background task that retries failed webhooks
- Max 3 retries with exponential backoff

**Ask me:** "Add a webhook retry mechanism with exponential backoff"

---

#### Task 6: Add Payroll Batch Email Notifications
**What:** When a batch is approved or disbursed, send a notification:
- Add a `notifications` table (or just log to console in demo mode)
- Notify when: batch approved, batch disbursed, batch failed

**Ask me:** "Add email notification system for payroll batch status changes"

---

#### Task 7: Add Real-Time Dashboard Updates
**What:** Dashboard should update in real-time when:
- New webhook received
- Payroll batch status changes
- Card transaction occurs

**Implementation:** Use WebSocket or Server-Sent Events (SSE)

**Ask me:** "Add WebSocket or SSE endpoint for real-time dashboard updates"

---

### 🟢 NICE TO HAVE (Week 3+)

#### Task 8: Add Background Worker for Payroll Processing
**What:** Move risk scoring to a background task so the API doesn't block:
- Use Celery or similar
- Return 202 Accepted immediately
- Client polls for result

**Ask me:** "Add a background worker for payroll risk scoring using Celery"

---

#### Task 9: Add Flutterwave Virtual Account Creation
**What:** When an employee is invited, create a Flutterwave virtual account for them:
- Update `POST /employees/{id}/invite`
- Call Flutterwave's virtual account API
- Store the account number

**Ask me:** "Add Flutterwave virtual account creation to the employee invite flow"

---

#### Task 10: Add Unit Tests for Payroll Service
**What:** Test the core payroll logic:
- Risk scoring algorithm
- Batch approval flow
- Disbursement simulation

**Ask me:** "Write unit tests for the payroll service and risk engine"

---

## 🔗 Your Integration Points

| With Whom | What You Share | Communication Needed |
|-----------|----------------|----------------------|
| **Person 1** | Auth middleware, database models | Before changing models.py |
| **Person 3** | Dashboard endpoint | When changing dashboard response format |
| **Person 4** | All your endpoints | When changing any response format |

---

## ✅ Your Testing Checklist

- [ ] All Flutterwave calls work in demo mode
- [ ] Webhook signature verification works
- [ ] Payroll batch lifecycle works (upload → score → approve → disburse)
- [ ] Card CRUD works (create → freeze → unfreeze → update limit)
- [ ] Error responses are clear and consistent
- [ ] Frontend can consume all endpoints

---

## 💬 Prompts to Ask Me

```
"Update payroll disbursement endpoint to use Flutterwave transfers instead of BMONI"

"Update webhook handler to process Flutterwave webhook events with signature verification"

"Add proper HTTP error responses to all payroll, card, forecast, and webhook endpoints"

"Add a card transaction history endpoint with mock transaction data"

"Add a webhook retry mechanism with exponential backoff"

"Add email notification system for payroll batch status changes"

"Add WebSocket or SSE endpoint for real-time dashboard updates"

"Add Flutterwave virtual account creation to the employee invite flow"

"Write unit tests for the payroll service and risk engine"
```

---
---

# 👤 PERSON 3 — Frontend Core (Dashboard, Employees, Login & Design System)

## Your Mission
You own the user's first impression — login, dashboard, employee management, and the overall look and feel. You make the app beautiful, responsive, and a joy to use.

## Files You Own
```
frontend/src/app/login/page.tsx
frontend/src/app/dashboard/page.tsx
frontend/src/app/employees/page.tsx
frontend/src/app/layout.tsx
frontend/src/app/page.tsx
frontend/src/app/providers.tsx
frontend/src/app/globals.css
frontend/src/components/layout/Layout.tsx
frontend/src/components/ui/Button.tsx
frontend/src/components/ui/Card.tsx
frontend/src/components/ui/Input.tsx
frontend/src/components/ui/Badge.tsx
frontend/src/components/ui/Modal.tsx
frontend/src/components/ui/Table.tsx
frontend/src/components/icons.tsx
frontend/src/lib/api.ts
frontend/src/lib/auth.ts
frontend/src/lib/utils.ts
```

---

## 📋 Your Task List (Priority Order)

### 🔴 HIGH PRIORITY (Week 1)

#### Task 1: Add Error Boundaries and Error UI
**What:** When something fails, show a helpful error instead of a white screen:
- Create an ErrorBoundary component
- Show friendly error messages
- Add "Try Again" buttons
- Add network offline detection

**How to test:**
1. Stop the backend → frontend should show "Cannot connect to server"
2. Trigger an API error → should show error message, not crash

**Ask me:** "Add error boundary components and error UI to all pages"

---

#### Task 2: Add Skeleton Loading States
**What:** Instead of showing a blank page or spinner, show skeleton placeholders that match the content shape:
- Skeleton for tables (rows with gray bars)
- Skeleton for cards (gray rectangles)
- Skeleton for metrics (gray numbers)

**How to test:**
1. Add artificial delay to API → should see skeleton, not spinner
2. All pages should have skeleton loading

**Ask me:** "Add skeleton loading components for tables, cards, and metrics"

---

#### Task 3: Improve Mobile Responsiveness
**What:** The app should work well on phones and tablets:
- Tables should scroll horizontally or use card layouts on mobile
- Forms should stack vertically
- Navigation should be a hamburger menu
- Buttons should be large enough to tap

**How to test:**
1. Open in Chrome DevTools → toggle mobile view
2. Test every page on 375px width
3. Test on an actual phone if possible

**Ask me:** "Improve mobile responsiveness for all pages with responsive table layouts and mobile navigation"

---

### 🟡 MEDIUM PRIORITY (Week 2)

#### Task 4: Add Toast Notifications
**What:** When a user performs an action, show a small popup:
- "Employee created successfully!" ✅
- "Failed to save changes" ❌
- Auto-dismiss after 3 seconds
- Stack multiple toasts

**Ask me:** "Add a toast notification system for success and error messages"

---

#### Task 5: Add Pagination UI Controls
**What:** Tables should have proper pagination:
- Show "Page 1 of 5"
- Previous/Next buttons
- Page size selector (10, 25, 50)
- Go to page input

**Ask me:** "Add pagination UI components to the Table component"

---

#### Task 6: Add Confirmation Dialogs
**What:** Before destructive actions, show a confirmation:
- Delete employee → "Are you sure?" dialog
- Freeze card → "This will disable the card" dialog
- Approve payroll → "This will disburse funds" dialog

**Ask me:** "Add confirmation dialog components for destructive actions"

---

#### Task 7: Add Empty State Illustrations
**What:** When there's no data, show a helpful message:
- No employees → "Add your first team member" with illustration
- No payroll batches → "Upload your first payroll" with illustration
- No cards → "Create your first card" with illustration

**Ask me:** "Add empty state components with illustrations for all pages"

---

### 🟢 NICE TO HAVE (Week 3+)

#### Task 8: Add Dark Mode Support
**What:** Add a dark mode toggle:
- Save preference to localStorage
- Use Tailwind dark: classes
- Smooth transition between modes

**Ask me:** "Add dark mode support with a toggle button and localStorage persistence"

---

#### Task 9: Add Data Table Sorting
**What:** Click column headers to sort:
- Click once → ascending
- Click again → descending
- Show sort indicator arrow

**Ask me:** "Add sortable column headers to the Table component"

---

#### Task 10: Add Keyboard Shortcuts
**What:** Power users love shortcuts:
- `Ctrl + K` → Search
- `Ctrl + N` → New employee
- `Esc` → Close modal
- `?` → Show shortcuts help

**Ask me:** "Add keyboard shortcuts for common actions"

---

## 🔗 Your Integration Points

| With Whom | What You Share | Communication Needed |
|-----------|----------------|----------------------|
| **Person 1** | Auth flow, employee API responses | When login response format changes |
| **Person 2** | Dashboard API response | When dashboard data structure changes |
| **Person 4** | UI components (Button, Modal, Table, etc.) | Before changing any component API |

---

## ✅ Your Testing Checklist

- [ ] All pages work on mobile (375px width)
- [ ] Loading states show on every page
- [ ] Error states show when backend is down
- [ ] UI components don't break Person 4's pages
- [ ] Login/logout flow works correctly
- [ ] Dashboard shows all metrics

---

## 💬 Prompts to Ask Me

```
"Add error boundary components and error UI to all pages"

"Add skeleton loading components for tables, cards, and metrics"

"Improve mobile responsiveness for all pages with responsive table layouts and mobile navigation"

"Add a toast notification system for success and error messages"

"Add pagination UI components to the Table component"

"Add confirmation dialog components for destructive actions"

"Add empty state components with illustrations for all pages"

"Add dark mode support with a toggle button and localStorage persistence"

"Add sortable column headers to the Table component"

"Add keyboard shortcuts for common actions"
```

---
---

# 👤 PERSON 4 — Frontend Features (Payroll, Cards, Forecast, Webhooks & Copilot)

## Your Mission
You own the feature-rich pages that make PayPilot powerful — payroll processing, card management, forecasting, webhook monitoring, and the AI copilot. You make complex workflows feel simple.

## Files You Own
```
frontend/src/app/payroll/page.tsx
frontend/src/app/cards/page.tsx
frontend/src/app/forecast/page.tsx
frontend/src/app/webhooks/page.tsx
frontend/src/app/copilot/page.tsx
```

---

## 📋 Your Task List (Priority Order)

### 🔴 HIGH PRIORITY (Week 1)

#### Task 1: Add Proper Error Handling on All Pages
**What:** Each page should handle errors gracefully:
- Show error messages when API calls fail
- Add "Retry" buttons
- Handle network errors specifically
- Don't let one error crash the whole page

**How to test:**
1. Stop backend → all pages should show error messages
2. Restart backend → "Retry" should work

**Ask me:** "Add proper error handling with retry buttons to payroll, cards, forecast, webhooks, and copilot pages"

---

#### Task 2: Add Loading States for All Async Operations
**What:** Every action should show loading feedback:
- Buttons show spinner while saving
- Tables show skeleton while loading
- Modals disable buttons while submitting
- Disable double-clicks

**Ask me:** "Add loading states for all async operations on payroll, cards, forecast, webhooks, and copilot pages"

---

### 🟡 MEDIUM PRIORITY (Week 2)

#### Task 3: Add CSV Export for Payroll Batches
**What:** Users need to export payroll data:
- Add "Export CSV" button on batch detail page
- Include all items with their risk scores and decisions
- Download as `.csv` file

**Ask me:** "Add CSV export functionality to the payroll batch detail page"

---

#### Task 4: Add PDF Export for Payroll Reports
**What:** Generate a PDF payroll summary:
- Company header
- Batch details
- Employee list with amounts
- Signature lines

**Ask me:** "Add PDF payroll report generation using a client-side library"

---

#### Task 5: Add Real-Time Card Transaction Display
**What:** Show card transactions as they happen:
- Add a transaction list below each card
- Show: date, merchant, amount, status
- Auto-update when new transaction arrives

**Ask me:** "Add a transaction history display to the cards page with auto-refresh"

---

#### Task 6: Add Webhook Event Timeline
**What:** Visualize webhook events as a timeline:
- Show events chronologically
- Color-code by event type
- Expandable details for each event
- Filter by event type

**Ask me:** "Add a timeline visualization component for webhook events"

---

#### Task 7: Improve Copilot Chat
**What:** Make the AI copilot feel more responsive:
- Add streaming responses (show text as it generates)
- Add suggested questions
- Add chat history
- Add "Copy response" button
- Add typing indicator

**Ask me:** "Improve the Copilot chat interface with streaming responses, suggested questions, and chat history"

---

### 🟢 NICE TO HAVE (Week 3+)

#### Task 8: Add Charts to Forecast Page
**What:** Visualize forecast data:
- Bar chart showing balance vs required per currency
- Line chart showing balance trend over time
- Color-coded status indicators

**Ask me:** "Add interactive charts to the forecast page using a charting library"

---

#### Task 9: Add Drag-and-Drop CSV Upload
**What:** Make payroll CSV upload easier:
- Drag and drop zone
- File preview before upload
- Validate CSV format client-side
- Show parsing errors before submit

**Ask me:** "Add drag-and-drop CSV upload with client-side validation to the payroll page"

---

#### Task 10: Add Notification Center
**What:** Central place for all notifications:
- Bell icon in header
- Unread count badge
- List of: webhook alerts, payroll updates, card alerts
- Mark as read

**Ask me:** "Add a notification center with bell icon, badge count, and notification list"

---

## 🔗 Your Integration Points

| With Whom | What You Share | Communication Needed |
|-----------|----------------|----------------------|
| **Person 1** | Employee data (used in payroll) | When employee format changes |
| **Person 2** | All backend endpoints you consume | When any response format changes |
| **Person 3** | UI components (Button, Modal, Table, etc.) | Ask before modifying shared components |

---

## ✅ Your Testing Checklist

- [ ] All 5 pages handle errors gracefully
- [ ] All pages show loading states
- [ ] Payroll upload → approve → disburse flow works
- [ ] Card create → freeze → edit limit flow works
- [ ] Forecast shows all currencies correctly
- [ ] Webhooks page shows events and allows retry
- [ ] Copilot answers questions and shows evidence

---

## 💬 Prompts to Ask Me

```
"Add proper error handling with retry buttons to payroll, cards, forecast, webhooks, and copilot pages"

"Add loading states for all async operations on payroll, cards, forecast, webhooks, and copilot pages"

"Add CSV export functionality to the payroll batch detail page"

"Add PDF payroll report generation using a client-side library"

"Add a transaction history display to the cards page with auto-refresh"

"Add a timeline visualization component for webhook events"

"Improve the Copilot chat interface with streaming responses, suggested questions, and chat history"

"Add interactive charts to the forecast page using a charting library"

"Add drag-and-drop CSV upload with client-side validation to the payroll page"

"Add a notification center with bell icon, badge count, and notification list"
```

---
---

# 🤝 Cross-Team Integration Guide

## How to Ensure Seamless Integration

### 1. Before Changing an API Response

**Backend Dev (Person 1 or 2):**
```
1. Open API_CONTRACT.md
2. Find the endpoint you want to change
3. Discuss with affected Frontend Dev in standup
4. Update API_CONTRACT.md together
5. Make the change
6. Test with frontend running
```

### 2. Before Changing a Shared Component

**Frontend Dev (Person 3):**
```
1. Check if Person 4 uses the component
2. Test your change on ALL pages that use it
3. Notify Person 4 in standup
4. Make the change
5. Verify Person 4's pages still work
```

### 3. Before Changing the Database Schema

**Anyone:**
```
1. Discuss in team sync (all 4 people)
2. Both backend devs approve
3. Update models.py together
4. Update seed.py if needed
5. Both backend devs test
6. Both frontend devs verify nothing broke
```

### 4. When Integration Breaks

```
1. DON'T PANIC — this is normal
2. Identify who changed what (git log)
3. Revert the breaking change
4. Fix together (person who broke it + person affected)
5. Test before re-merging
6. Add a test to prevent regression
```

---

## 🎯 Your First Week Checklist

### Day 1: Setup
- [ ] Everyone clones the repo
- [ ] Everyone sets up MySQL with XAMPP
- [ ] Everyone runs the full application
- [ ] Everyone tests all features

### Day 2: Planning
- [ ] Read API_CONTRACT.md together
- [ ] Read your individual task list
- [ ] Create your Git branches
- [ ] Pick your first task

### Day 3-5: First Feature
- [ ] Each person completes their first task
- [ ] Push to your branch
- [ ] Test your feature end-to-end
- [ ] Share in standup what you built

### End of Week 1:
- [ ] All 4 people have completed at least 1 task
- [ ] First weekly merge to main
- [ ] Full application still works
- [ ] Plan Week 2 tasks

---

**Remember: Communication > Code. Talk to each other daily!** 🗣️
