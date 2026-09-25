# Contributing Guide — PayPilot Global

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- MySQL (via XAMPP recommended)
- Git
- VS Code (recommended)

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_ORG/paypilot-global.git
cd paypilot-global

# 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows
pip install -r requirements.txt

# 3. Create MySQL database (via PHPMyAdmin or CLI)
# Database: paypilot_global
# User: root (or paypilot_user)
# See MYSQL_INSTALLATION_GUIDE.md for details

# 4. Seed the database
python -m app.seed

# 5. Frontend setup (new terminal)
cd frontend
npm install

# 6. Start both servers
# Terminal 1: Backend
cd backend && source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Login Credentials
- **Email:** `admin@acmeglobal.com`
- **Password:** `password123`

---

## 🌿 Git Branch Strategy

### Branch Names

| Person | Branch Name | Area |
|--------|-------------|------|
| Person 1 (Backend Core) | `backend/p1-auth-employees` | Auth + Employee endpoints |
| Person 2 (Backend Features) | `backend/p2-payroll-cards` | Payroll + Cards + Webhooks |
| Person 3 (Frontend Core) | `frontend/p3-core-ui` | Dashboard + Employees + Design System |
| Person 4 (Frontend Features) | `frontend/p4-feature-pages` | Payroll + Cards + Forecast + Webhooks + Copilot |

### Creating Your Branch

```bash
# Make sure you're on main and up to date
git checkout main
git pull origin main

# Create your branch
git checkout -b backend/p1-auth-employees    # Person 1
git checkout -b backend/p2-payroll-cards     # Person 2
git checkout -b frontend/p3-core-ui          # Person 3
git checkout -b frontend/p4-feature-pages    # Person 4
```

---

## 📝 Daily Workflow

### Morning (5 minutes)

```bash
# 1. Switch to your branch
git checkout your-branch-name

# 2. Pull latest changes from main
git fetch origin
git merge origin/main

# 3. Resolve any conflicts (ask for help if needed)

# 4. Start working!
```

### During the Day

```bash
# Make small, focused commits
git add .
git commit -m "[FEAT] Add employee search by country"

# Push regularly (at least end of day)
git push origin your-branch-name
```

### End of Day

```bash
# 1. Make sure everything is committed
git status   # Should be clean

# 2. Push your branch
git push origin your-branch-name

# 3. Tell the team what you did (in standup or chat)
```

---

## 🔀 Weekly Merge Process

### Friday Merge (30 minutes)

**Step 1: Everyone pushes their branches**
```bash
git push origin your-branch-name
```

**Step 2: One person merges (rotate weekly)**

```bash
# Checkout main
git checkout main
git pull origin main

# Merge Person 1's branch
git merge backend/p1-auth-employees
# Resolve conflicts if any

# Merge Person 2's branch
git merge backend/p2-payroll-cards
# Resolve conflicts if any

# Merge Person 3's branch
git merge frontend/p3-core-ui
# Resolve conflicts if any

# Merge Person 4's branch
git merge frontend/p4-feature-pages
# Resolve conflicts if any

# Push merged main
git push origin main
```

**Step 3: Everyone pulls the merged main**
```bash
git checkout your-branch-name
git merge main
```

**Step 4: Full team tests the application**
- Start backend and frontend
- Test ALL pages
- Report any issues immediately

---

## 💬 Commit Message Format

### Structure
```
[TYPE] Brief description

Optional: Longer explanation of what changed and why
```

### Types

| Type | When to Use |
|------|-------------|
| `[FEAT]` | New feature |
| `[FIX]` | Bug fix |
| `[DOCS]` | Documentation changes |
| `[STYLE]` | Code formatting (no logic change) |
| `[REFACTOR]` | Code restructuring (no feature change) |
| `[TEST]` | Adding or updating tests |
| `[CHORE]` | Maintenance, dependency updates |
| `[PERF]` | Performance improvements |
| `[API]` | API contract changes |

### Examples

```
[FEAT] Add employee search by country and department
[FIX] Fix cards page data.map error on empty response
[DOCS] Update API contract with new card endpoints
[STYLE] Format models.py with consistent spacing
[REFACTOR] Extract validation logic into separate module
[TEST] Add unit tests for risk scoring engine
[CHORE] Update PyMySQL to latest version
[PERF] Add database indexes for employee queries
[API] Change dashboard response to include wallet forecasts
```

---

## 🔍 Code Review Guidelines

### Before Requesting Review

- [ ] Code runs without errors
- [ ] No console errors in browser
- [ ] API endpoints tested in Swagger
- [ ] Commit messages follow the format
- [ ] No debug code or console.logs left in
- [ ] Code follows existing style

### When Reviewing

1. **Be kind** — Suggest, don't demand
2. **Be specific** — "This could be improved by..." not "This is wrong"
3. **Test it** — Pull the branch and test locally
4. **Ask questions** — "Why did you choose X over Y?"
5. **Approve when ready** — Don't hold up progress for minor things

### Review Checklist

- [ ] Code does what it says it does
- [ ] No security issues (hardcoded secrets, SQL injection, etc.)
- [ ] Error handling is present
- [ ] No unnecessary code duplication
- [ ] API responses match the contract
- [ ] UI is responsive (if frontend)
- [ ] Loading states are handled (if frontend)

---

## ⚠️ Conflict Resolution

### When Conflicts Happen

```bash
# 1. See which files have conflicts
git status

# 2. Open the conflicting files
# Look for these markers:
# <<<<<<< HEAD (your changes)
# =======
# >>>>>>> branch-name (their changes)

# 3. Manually edit to keep the correct code
# 4. Remove the markers
# 5. Stage and commit
git add .
git commit -m "[FIX] Resolve merge conflicts"
```

### If You're Unsure

1. **Don't guess** — Ask the person who wrote the other code
2. **Call a huddle** — Get both people together to resolve
3. **Keep it simple** — When in doubt, keep both versions and test

### Prevention

- Pull from main daily
- Communicate changes in standup
- Don't work on the same files (check the file ownership map)
- Merge small, frequent changes (not big batch changes)

---

## 🧪 Testing Before Merge

### Backend Testing

```bash
# 1. Start the backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# 2. Check health
curl http://localhost:8000/health

# 3. Open Swagger docs
# http://localhost:8000/docs

# 4. Test your endpoints manually
# 5. Test that existing endpoints still work
```

### Frontend Testing

```bash
# 1. Start the frontend
cd frontend
npm run dev

# 2. Open browser
# http://localhost:3000

# 3. Test your pages
# 4. Test responsive design (resize browser)
# 5. Check browser console for errors
# 6. Test with backend stopped (error states)
```

### Integration Testing

```bash
# 1. Both backend and frontend running
# 2. Test the full flow:
#    - Login
#    - View dashboard
#    - Create/edit/delete employees
#    - Upload payroll
#    - Create cards
#    - View webhooks
# 3. Test on mobile view
# 4. Check for console errors
```

---

## 📋 Pull Request Template

When creating a PR (for weekly merge), use this template:

```markdown
## What I Did
- [Brief description of changes]

## Tasks Completed
- [ ] Task 1
- [ ] Task 2

## Testing
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] All my endpoints/pages work
- [ ] Existing functionality not broken
- [ ] Tested on mobile (if frontend)

## API Changes (if any)
- [ ] Updated API_CONTRACT.md
- [ ] Notified frontend team
- [ ] Swagger docs updated

## Screenshots (if frontend)
[Add screenshots of your changes]

## Notes for Reviewer
[Anything the reviewer should know]
```

---

## 🤝 Communication Guidelines

### Daily Standup Format

Each person answers (2 minutes max):
1. ✅ What did I complete yesterday?
2. 🔄 What am I working on today?
3. 🚧 Any blockers?

### When to Communicate

| Situation | Who to Tell | How |
|-----------|-------------|-----|
| Changing an API response | Affected frontend dev(s) | Standup + message |
| Changing a shared component | Other frontend dev | Standup + message |
| Changing database schema | All 4 team members | Meeting |
| Found a bug in someone's code | That person | Direct message (be kind!) |
| Blocked on a task | Team lead / everyone | Standup |
| Finished a major task | Everyone | Standup + celebration 🎉 |

### Tools

- **Git** — Code sharing and version control
- **Daily standup** — Sync meeting (10 min)
- **Group chat** — Quick questions and updates
- **API_CONTRACT.md** — Single source of truth for API
- **Swagger docs** — http://localhost:8000/docs

---

## 📚 Additional Resources

- **API Contract:** `API_CONTRACT.md`
- **Project Split:** `PROJECT_SPLIT.md`
- **Individual Tasks:** `INDIVIDUAL_TASKS.md`
- **Local Setup:** `LOCAL_SETUP_GUIDE.md`
- **MySQL Setup:** `MYSQL_INSTALLATION_GUIDE.md`
- **XAMPP Setup:** `XAMPP_SETUP_GUIDE.md`

---

## 🎯 Rules of the Road

1. **Never push directly to main** — Always use your branch
2. **Always test before merging** — No exceptions
3. **Communicate changes** — Especially API and shared files
4. **Help each other** — If someone is blocked, unblock them
5. **Keep branches up to date** — Merge main into your branch daily
6. **Small commits** — Easier to review and revert
7. **Clear commit messages** — Future you will thank present you
8. **No secrets in code** — Use `.env` for all secrets
9. **Document as you go** — Don't leave it for later
10. **Have fun!** — Building things together is awesome 🚀

---

**Questions? Ask in the group chat or during standup!**
