# 🚀 XAMPP Setup Guide for PayPilot Global

Complete guide to set up PayPilot Global using XAMPP on Linux (EASIEST METHOD!)

---

## 🎯 Why XAMPP?

XAMPP makes database management **super easy** with:
- ✅ **PHPMyAdmin** - Visual database management (no command line!)
- ✅ **One-click installation** - Everything included
- ✅ **Easy start/stop** - Simple control panel
- ✅ **Perfect for beginners** - No MySQL expertise needed

---

## 📥 Step 1: Download XAMPP

### Option A: Download from Official Website (Recommended)

1. Go to: https://www.apachefriends.org/download.html
2. Select **Linux** version
3. Download the `.run` file (e.g., `xampp-linux-x64-8.2.12-0-installer.run`)

### Option B: Direct Download Links

**Latest XAMPP for Linux (64-bit):**
```bash
# Copy this URL to your browser
https://www.apachefriends.org/xampp-files/8.2.12/xampp-linux-x64-8.2.12-0-installer.run
```

---

## 🔧 Step 2: Install XAMPP

### 2.1 Make the Installer Executable

Open terminal and navigate to where you downloaded the file:

```bash
# Navigate to Downloads folder (or wherever you saved it)
cd ~/Downloads

# Make the installer executable
chmod +x xampp-linux-x64-*-installer.run
```

### 2.2 Run the Installer

```bash
# Run the installer (requires sudo)
sudo ./xampp-linux-x64-*-installer.run
```

### 2.3 Follow the Installation Wizard

1. **Setup Wizard** - Click "Next"
2. **Select Components** - Keep all defaults:
   - ✅ XAMPP Core Files
   - ✅ XAMPP Developer Files
   - Click "Next"
3. **Installation Folder** - Keep default: `/opt/lampp`
   - Click "Next"
4. **Ready to Install** - Click "Next"
5. **Finish** - Click "Finish"

### 2.4 Verify Installation

```bash
# Check if XAMPP is installed
ls /opt/lampp
```

You should see directories like: `apache`, `mysql`, `phpmyadmin`, etc.

---

## 🚀 Step 3: Start XAMPP

### 3.1 Start XAMPP Services

```bash
# Start all XAMPP services (Apache, MySQL, etc.)
sudo /opt/lampp/lampp start
```

You should see:
```
Starting XAMPP for Linux ...
XAMPP: Starting Apache...ok.
XAMPP: Starting MySQL...ok.
```

### 3.2 Verify Services are Running

```bash
# Check status
sudo /opt/lampp/lampp status
```

You should see:
```
PID of Apache: XXXX
PID of MySQL: XXXX
```

### 3.3 Stop XAMPP (when needed)

```bash
# Stop all services
sudo /opt/lampp/lampp stop
```

### 3.4 Restart XAMPP (when needed)

```bash
# Restart all services
sudo /opt/lampp/lampp restart
```

---

## 🗄️ Step 4: Create Database Using PHPMyAdmin (EASY!)

This is where XAMPP shines - you get a **visual interface**!

### 4.1 Open PHPMyAdmin

Open your web browser and go to:
```
http://localhost/phpmyadmin
```

You should see the PHPMyAdmin login page.

### 4.2 Login to PHPMyAdmin

- **Username:** `root`
- **Password:** (leave empty - no password by default)
- Click **"Log In"** or **"Go"**

### 4.3 Create the Database

1. Click on **"New"** in the left sidebar
2. **Database name:** `paypilot_global`
3. **Collation:** Select `utf8mb4_unicode_ci`
4. Click **"Create"**

✅ You should now see `paypilot_global` in the left sidebar!

### 4.4 Create Database User (Optional but Recommended)

For security, create a dedicated user:

1. Click on **"User accounts"** tab at the top
2. Click **"Add user account"**
3. Fill in:
   - **User name:** `paypilot_user`
   - **Host name:** Select **"Local"** from dropdown
   - **Password:** `PayPilot2024!`
   - **Re-type:** `PayPilot2024!`
4. Scroll down to **"Global privileges"**
5. Check **"Check all"** (grant all privileges)
6. Click **"Go"** at the bottom

✅ User created! You can now use this user to connect.

---

## 🔐 Step 5: Update .env File

Now update your PayPilot backend to use XAMPP's MySQL:

### 5.1 Open the .env File

```bash
# Navigate to your project
cd paypilot-global/backend

# Open .env in your editor
nano .env
# OR
code .  # If using VS Code
```

### 5.2 Update Database URL

Find the `DATABASE_URL` line and update it:

```env
# For XAMPP MySQL (default - no password)
DATABASE_URL=mysql+pymysql://root@localhost:3306/paypilot_global
```

**OR** if you created a dedicated user:

```env
# For dedicated user
DATABASE_URL=mysql+pymysql://paypilot_user:PayPilot2024!@localhost:3306/paypilot_global
```

**Note:** XAMPP's MySQL default has no password for root, so the connection string is simpler!

### 5.3 Save the File

- In nano: Press `Ctrl + O`, then `Enter`, then `Ctrl + X`
- In VS Code: Press `Ctrl + S`

---

## 🐍 Step 6: Set Up PayPilot Backend

### 6.1 Navigate to Backend Directory

```bash
cd paypilot-global/backend
```

### 6.2 Create Virtual Environment

```bash
python3 -m venv venv
```

### 6.3 Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### 6.4 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6.5 Seed the Database

```bash
python -m app.seed
```

You should see:
```
✅ Database seeded successfully!
   Employer: Acme Global Technologies (demo-employer-001)
   Users: admin@acmeglobal.com, finance@acmeglobal.com, viewer@acmeglobal.com
   Employees: 8
   Wallet balances: 6 currencies
   Payroll batch: September 2026 Payroll (8 items)
   Webhook events: 4
   Cards: 3
```

### 6.6 Verify Database in PHPMyAdmin

1. Go back to: http://localhost/phpmyadmin
2. Click on `paypilot_global` in the left sidebar
3. You should see all the tables:
   - employees
   - payroll_batches
   - payroll_items
   - wallet_balances
   - webhook_events
   - cards
   - users
   - employers

4. Click on any table to view the data! 🎉

---

## 🎨 Step 7: Set Up Frontend

### 7.1 Open a New Terminal

Press `Ctrl + Shift + T` in VS Code, or open a new terminal window.

### 7.2 Navigate to Frontend Directory

```bash
cd paypilot-global/frontend
```

### 7.3 Install Dependencies

```bash
npm install
```

---

## 🚀 Step 8: Run the Application

### 8.1 Start Backend (Terminal 1)

```bash
# Make sure you're in the backend directory
cd paypilot-global/backend

# Make sure venv is activated
source venv/bin/activate

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 8.2 Start Frontend (Terminal 2)

```bash
# Open new terminal first!
cd paypilot-global/frontend

# Start the frontend server
npm run dev
```

You should see:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## 🎯 Step 9: Access Your Application

### Frontend
- **URL:** http://localhost:3000
- **Login Email:** `admin@acmeglobal.com`
- **Login Password:** `password123`

### Backend API
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### PHPMyAdmin
- **URL:** http://localhost/phpmyadmin
- **Username:** `root`
- **Password:** (leave empty)

---

## 🔥 Managing XAMPP

### Start XAMPP
```bash
sudo /opt/lampp/lampp start
```

### Stop XAMPP
```bash
sudo /opt/lampp/lampp stop
```

### Restart XAMPP
```bash
sudo /opt/lampp/lampp restart
```

### Check Status
```bash
sudo /opt/lampp/lampp status
```

### Start Only MySQL
```bash
sudo /opt/lampp/lampp startmysql
```

### Stop Only MySQL
```bash
sudo /opt/lampp/lampp stopmysql
```

---

## 💡 Using PHPMyAdmin (Visual Database Management)

### View Tables
1. Open http://localhost/phpmyadmin
2. Click `paypilot_global` in left sidebar
3. Click any table to view data

### Run SQL Queries
1. Click `paypilot_global` database
2. Click **"SQL"** tab at the top
3. Write your query:
   ```sql
   SELECT * FROM employees WHERE country = 'Nigeria';
   ```
4. Click **"Go"**

### Edit Data
1. Click on a table
2. Click the **edit** icon (pencil) next to any row
3. Make changes
4. Click **"Go"** to save

### Export Database
1. Click `paypilot_global` database
2. Click **"Export"** tab
3. Choose format (SQL)
4. Click **"Go"**
5. Save the `.sql` file

### Import Database
1. Click `paypilot_global` database
2. Click **"Import"** tab
3. Click **"Choose File"** and select your `.sql` file
4. Click **"Go"**

---

## 🐛 Troubleshooting

### Problem: "Can't connect to MySQL server"
**Solution:** XAMPP MySQL not running
```bash
# Start XAMPP
sudo /opt/lampp/lampp start

# Or start only MySQL
sudo /opt/lampp/lampp startmysql
```

### Problem: "Access denied for user 'root'@'localhost'"
**Solution:** Update `.env` to use correct credentials
```env
# XAMPP default (no password)
DATABASE_URL=mysql+pymysql://root@localhost:3306/paypilot_global
```

### Problem: "Port 3306 already in use"
**Solution:** Another MySQL instance is running
```bash
# Check what's using port 3306
sudo lsof -i :3306

# Stop the other MySQL service
sudo systemctl stop mysql

# Or kill the process
sudo kill -9 <PID>
```

### Problem: "phpmyadmin not accessible"
**Solution:** Apache not running
```bash
# Start XAMPP (includes Apache)
sudo /opt/lampp/lampp start
```

### Problem: "Permission denied" when starting XAMPP
**Solution:** Use sudo
```bash
sudo /opt/lampp/lampp start
```

### Problem: XAMPP won't start
**Solution:** Check for conflicts
```bash
# Stop any existing MySQL/Apache services
sudo systemctl stop mysql
sudo systemctl stop apache2

# Then start XAMPP
sudo /opt/lampp/lampp start
```

---

## 🎓 XAMPP vs Manual MySQL Installation

| Aspect | XAMPP | Manual MySQL |
|--------|-------|--------------|
| **Installation Time** | 5 minutes | 15-20 minutes |
| **Setup Complexity** | Very Easy | Moderate |
| **Database Management** | PHPMyAdmin (GUI) | Command line |
| **Start/Stop** | Simple command | Service commands |
| **Perfect For** | Local development | Production |
| **Learning Curve** | Minimal | Moderate |

---

## 📚 Quick Commands Reference

### XAMPP Control
```bash
sudo /opt/lampp/lampp start     # Start all
sudo /opt/lampp/lampp stop      # Stop all
sudo /opt/lampp/lampp restart   # Restart all
sudo /opt/lampp/lampp status    # Check status
```

### Database Operations
```bash
# Via PHPMyAdmin (recommended)
http://localhost/phpmyadmin

# Via command line (if needed)
/opt/lampp/bin/mysql -u root
```

### Project Setup
```bash
# Backend
cd paypilot-global/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.seed

# Frontend (new terminal)
cd paypilot-global/frontend
npm install
npm run dev
```

---

## ✅ Checklist

- [ ] Download XAMPP from https://www.apachefriends.org/download.html
- [ ] Install XAMPP: `sudo ./xampp-linux-x64-*-installer.run`
- [ ] Start XAMPP: `sudo /opt/lampp/lampp start`
- [ ] Open PHPMyAdmin: http://localhost/phpmyadmin
- [ ] Create database `paypilot_global`
- [ ] Update `backend/.env` with MySQL connection
- [ ] Install backend dependencies: `pip install -r requirements.txt`
- [ ] Seed database: `python -m app.seed`
- [ ] Install frontend dependencies: `npm install`
- [ ] Start backend: `python -m uvicorn app.main:app --reload --port 8000`
- [ ] Start frontend: `npm run dev`
- [ ] Test at http://localhost:3000

---

## 🎉 You're All Set!

With XAMPP, you have:
- ✅ **MySQL database** running
- ✅ **PHPMyAdmin** for easy database management
- ✅ **Visual interface** to view/edit data
- ✅ **Simple start/stop** controls

### Quick Access:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **PHPMyAdmin:** http://localhost/phpmyadmin

### Login:
- **Email:** `admin@acmeglobal.com`
- **Password:** `password123`

---

**XAMPP makes everything so much easier! Enjoy your visual database management!** 🚀
