# 🚀 PayPilot Global - Local Setup Guide

Complete guide to set up PayPilot Global on your local PC using VS Code.

---

## 📋 Prerequisites

Before you start, make sure you have these installed on your PC:

### 1. Python 3.11+
- Download from: https://www.python.org/downloads/
- Verify installation: `python --version` or `python3 --version`

### 2. Node.js 18+ and npm
- Download from: https://nodejs.org/ (LTS version recommended)
- Verify installation: `node --version` and `npm --version`

### 3. MySQL 8.0+
- Download from: https://dev.mysql.com/downloads/installer/
- **Detailed installation guide:** See `MYSQL_INSTALLATION_GUIDE.md`
- Verify installation: `mysql --version`
- **Create database:** See Step 2 below

### 4. VS Code
- Download from: https://code.visualstudio.com/
- Recommended extensions (see below)

### 5. Git (optional but recommended)
- Download from: https://git-scm.com/downloads
- Verify installation: `git --version`

---

## 📦 Step 1: Download and Extract

1. Download the `paypilot-global-complete.zip` file
2. Extract it to your desired location, for example:
   - **Windows:** `C:\Projects\paypilot-global`
   - **macOS:** `/Users/yourname/Projects/paypilot-global`
   - **Linux:** `/home/yourname/projects/paypilot-global`

---

## 🗄️ Step 2: Create MySQL Database

After installing MySQL, create the database for PayPilot:

### 2.1 Connect to MySQL
```bash
mysql -u root -p
```
Enter your root password when prompted.

### 2.2 Create Database and User
Run these SQL commands (copy-paste them):
```sql
-- Create the database
CREATE DATABASE paypilot_global CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user
CREATE USER 'paypilot_user'@'localhost' IDENTIFIED BY 'PayPilot2024!';

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON paypilot_global.* TO 'paypilot_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify database was created
SHOW DATABASES;

-- Exit
exit;
```

You should see `paypilot_global` in the list of databases.

### 2.3 Verify Connection
```bash
mysql -u paypilot_user -p paypilot_global
```
Enter password: `PayPilot2024!`

If you can connect successfully, you're all set! Type `exit` to quit.

---

## 💻 Step 3: Open in VS Code

1. Open VS Code
2. Click **File → Open Folder** (or **File → Open** on macOS)
3. Navigate to the extracted `paypilot-global` folder
4. Click **Select Folder**

---

## 🔧 Step 4: Install VS Code Extensions

Install these recommended extensions for the best development experience:

### Essential Extensions:
1. **Python** (ms-python.python)
   - Python language support, debugging, IntelliSense
   
2. **Pylance** (ms-python.vscode-pylance)
   - Fast language support for Python
   
3. **ES7+ React/Redux/React-Native snippets** (dsznajder.es7-react-js-snippets)
   - React code snippets
   
4. **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
   - Tailwind CSS autocomplete
   
5. **ESLint** (dbaeumer.vscode-eslint)
   - JavaScript/TypeScript linting
   
6. **Prettier - Code formatter** (esbenp.prettier-vscode)
   - Code formatting

### Optional Extensions:
7. **SQLite Viewer** (FlorianSeidl.sqlite-viewer)
   - View SQLite databases directly in VS Code
   
8. **Thunder Client** (rangav.vscode-thunder-client)
   - API testing (alternative to Postman)

---

## 🐍 Step 5: Set Up Backend

### 4.1 Open Terminal in VS Code
- Press `Ctrl + `` (backtick) or go to **Terminal → New Terminal**

### 4.2 Navigate to Backend Directory
```bash
cd paypilot-global/backend
```

### 4.3 Create Virtual Environment
**Windows:**
```bash
python -m venv venv
```

**macOS/Linux:**
```bash
python3 -m venv venv
```

### 4.4 Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the beginning of your terminal prompt.

### 4.5 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- **PyMySQL** (MySQL client for Python)
- And all other backend dependencies

### 4.6 Verify Database Connection
The application is configured to use MySQL. Verify the connection:
```bash
python -c "from app.database import engine; print('Database connection:', engine)"
```

You should see a MySQL connection string.

### 4.7 Seed the Database
Seed the MySQL database with demo data:
```bash
python -m app.seed
```

This will:
- Create all tables in MySQL
- Insert demo data (employees, payroll batches, wallets, cards, etc.)
- Create user accounts for testing

### 4.8 Test Backend Setup
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser and visit: http://localhost:8000/health

You should see: `{"status":"healthy","service":"paypilot-global"}`

Press `Ctrl + C` to stop the server.

---

## 🎨 Step 6: Set Up Frontend

### 5.1 Open a New Terminal
- Press `Ctrl + Shift + `` (backtick) to open a second terminal
- Or go to **Terminal → New Terminal**

### 5.2 Navigate to Frontend Directory
```bash
cd paypilot-global/frontend
```

### 5.3 Install Node Dependencies
```bash
npm install
```

This will install:
- Next.js
- React
- TypeScript
- Tailwind CSS
- And all other frontend dependencies

### 5.4 Build the Frontend
```bash
npm run build
```

### 5.5 Test Frontend Setup
```bash
npm start
```

Open your browser and visit: http://localhost:3000

You should see the PayPilot Global login page.

Press `Ctrl + C` to stop the server.

---

## 🚀 Step 7: Run Both Servers

### Option A: Using Two Terminals (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd paypilot-global/backend
# Activate virtual environment if not already active
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd paypilot-global/frontend
npm run dev
```

Note: Use `npm run dev` for development (hot reload) instead of `npm start`

### Option B: Using the Start Script (Linux/macOS only)

```bash
cd paypilot-global
chmod +x start-servers.sh
./start-servers.sh
```

---

## 🔐 Step 8: Access the Application

### Frontend
- **URL:** http://localhost:3000
- **Login Credentials:**
  - Email: `admin@acmeglobal.com`
  - Password: `password123`

### Backend API
- **URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🧪 Step 9: Test the Application

### 1. Login
- Open http://localhost:3000
- Login with the credentials above
- You should see the dashboard

### 2. Test Each Page
- **Dashboard:** View metrics and wallet balances
- **Employees:** Create, edit, delete employees
- **Payroll:** Upload CSV, approve batches
- **Forecast:** View wallet forecasts
- **Webhooks:** Filter and retry webhooks
- **Copilot:** Ask questions about payroll
- **Cards:** Create and manage cards

### 3. Test API Endpoints
Open http://localhost:8000/docs to see all available API endpoints and test them directly.

---

## ⚙️ MySQL Configuration

The `.env` file is already configured with MySQL settings:

```env
DATABASE_URL=mysql+pymysql://paypilot_user:PayPilot2024!@localhost:3306/paypilot_global
```

### Connection String Format
```
mysql+pymysql://<username>:<password>@<host>:<port>/<database>
```

### If You Changed MySQL Credentials
If you used different credentials during MySQL setup, update the `.env` file:

1. Open `paypilot-global/backend/.env`
2. Find the `DATABASE_URL` line
3. Update with your credentials:
   ```env
   DATABASE_URL=mysql+pymysql://your_username:your_password@localhost:3306/paypilot_global
   ```
4. Save the file

---

## 🛠️ VS Code Configuration

### Recommended Settings

Create or update `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.python"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Debug Configurations

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Next.js: Full Stack",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}/frontend",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## 📁 Project Structure

```
paypilot-global/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── v1/           # Version 1 endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── seed.py          # Database seeder
│   ├── venv/                # Python virtual environment
│   ├── requirements.txt     # Python dependencies
│   └── paypilot.db         # SQLite database
│
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   │   ├── ui/         # Reusable UI components
│   │   │   └── layout/     # Layout components
│   │   └── lib/            # Utilities and API client
│   ├── node_modules/       # Node dependencies
│   ├── package.json        # Node dependencies list
│   └── next.config.js      # Next.js configuration
│
└── README.md                # This file
```

---

## 🔥 Development Workflow

### Backend Development

1. **Make changes** to Python files in `backend/app/`
2. **Auto-reload** is enabled with `--reload` flag
3. **Test endpoints** at http://localhost:8000/docs
4. **Check logs** in the terminal

### Frontend Development

1. **Make changes** to TypeScript/React files in `frontend/src/`
2. **Hot reload** is automatic with `npm run dev`
3. **View changes** at http://localhost:3000
4. **Check console** for errors

### Common Tasks

**Add a new API endpoint:**
1. Create route in `backend/app/api/v1/`
2. Add business logic in `backend/app/services/`
3. Test at http://localhost:8000/docs

**Add a new page:**
1. Create page in `frontend/src/app/[page-name]/page.tsx`
2. Add navigation link in `frontend/src/components/layout/Layout.tsx`
3. View at http://localhost:3000/[page-name]

**Modify database:**
1. Update models in `backend/app/models/models.py`
2. Delete `paypilot.db` and re-run `python -m app.seed`
3. Restart backend server

---

## 🐛 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
**Solution:** Make sure virtual environment is activated:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

**Problem:** `Can't connect to MySQL server on 'localhost'`
**Solution:** MySQL service is not running:
- **Windows:** Open Services → Find MySQL80 → Start
- **macOS:** `brew services start mysql`
- **Linux:** `sudo systemctl start mysql`

**Problem:** `Access denied for user 'paypilot_user'@'localhost'`
**Solution:** Database credentials are wrong:
- Verify the credentials in `backend/.env` match what you created in Step 2
- Or reset the password:
  ```bash
  mysql -u root -p
  ALTER USER 'paypilot_user'@'localhost' IDENTIFIED BY 'PayPilot2024!';
  ```

**Problem:** `Unknown database 'paypilot_global'`
**Solution:** Database doesn't exist:
- Go back to Step 2 and create the database
- Or run: `mysql -u root -p -e "CREATE DATABASE paypilot_global;"`

**Problem:** `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`
**Solution:** Check if MySQL is running on port 3306:
```bash
# Windows
netstat -an | findstr 3306

# Mac/Linux
netstat -an | grep 3306
```

**Problem:** `Address already in use`
**Solution:** Another process is using port 8000. Kill it or use a different port:
```bash
python -m uvicorn app.main:app --port 8001
```

**Problem:** Database errors
**Solution:** Delete `paypilot.db` and re-seed:
```bash
rm paypilot.db
python -m app.seed
```

### Frontend Issues

**Problem:** `npm: command not found`
**Solution:** Install Node.js from https://nodejs.org/

**Problem:** Port 3000 already in use
**Solution:** Use a different port:
```bash
npm run dev -- -p 3001
```

**Problem:** Build errors
**Solution:** Clear cache and reinstall:
```bash
rm -rf node_modules .next
npm install
npm run build
```

**Problem:** TypeScript errors
**Solution:** Make sure all dependencies are installed:
```bash
npm install
```

### General Issues

**Problem:** Frontend can't connect to backend
**Solution:** 
- Make sure backend is running on port 8000
- Check `frontend/next.config.js` has correct proxy configuration
- Restart both servers

**Problem:** Login doesn't work
**Solution:** 
- Make sure database is seeded: `python -m app.seed`
- Use credentials: `admin@acmeglobal.com` / `password123`

---

## 📚 Useful Commands

### Backend
```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Seed database (MySQL)
python -m app.seed

# Reset database (drop and recreate)
python -c "from app.database import Base, engine; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"
python -m app.seed

# Run tests (if available)
pytest
```

### MySQL
```bash
# Connect to MySQL
mysql -u root -p

# Connect to paypilot database
mysql -u paypilot_user -p paypilot_global

# Show all databases
mysql -u root -p -e "SHOW DATABASES;"

# Show all tables in paypilot database
mysql -u paypilot_user -p -e "USE paypilot_global; SHOW TABLES;"

# Backup database
mysqldump -u paypilot_user -p paypilot_global > paypilot_backup.sql

# Restore database
mysql -u paypilot_user -p paypilot_global < paypilot_backup.sql
```

### Frontend
```bash
# Development mode (hot reload)
npm run dev

# Production build
npm run build

# Production server
npm start

# Install new package
npm install <package-name>
```

---

## 🎯 Next Steps

1. ✅ Set up the project locally
2. ✅ Test all features
3. 🔄 Continue Flutterwave migration (Phase 2)
4. 🔄 Add more features
5. 🔄 Test with real data
6. 🔄 Deploy to production

---

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Check VS Code terminal for error messages
4. Review the migration guides:
   - `FLUTTERWAVE_MIGRATION_GUIDE.md`
   - `FLUTTERWAVE_MIGRATION_STATUS.md`
   - `MIGRATION_SUMMARY.md`

---

## 🎉 You're All Set!

Your PayPilot Global application is now running locally on your PC!

**Quick Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Login:**
- Email: `admin@acmeglobal.com`
- Password: `password123`

Happy coding! 🚀
