# 🗄️ MySQL Installation Guide

Complete step-by-step guide to install MySQL on your PC for PayPilot Global.

---

## 🪟 Windows Installation

### Step 1: Download MySQL Installer

1. Go to: https://dev.mysql.com/downloads/installer/
2. Download **MySQL Installer for Windows** (the larger file, ~300MB)
3. Or use the direct link: https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-community-8.0.36.0.msi

### Step 2: Run the Installer

1. Double-click the downloaded `.msi` file
2. Choose **"Developer Default"** setup type
3. Click **Next** through the prompts

### Step 3: Configure MySQL

During installation, you'll be asked to:

1. **Set Root Password**
   - Choose a strong password (e.g., `YourPassword123!`)
   - **IMPORTANT:** Write this down - you'll need it!
   - Click **Next**

2. **Configure Server**
   - Keep default settings
   - Server Type: **Development Computer**
   - Port: **3306** (default)
   - Click **Next**

3. **Windows Service**
   - Keep default: "Configure MySQL Server as a Windows Service"
   - Service Name: **MySQL80**
   - Start at System Startup: ✅ (recommended)
   - Click **Next**

4. **Accounts**
   - Keep default settings
   - Click **Next**

5. **Service**
   - Click **Execute** to apply configuration
   - Wait for it to complete
   - Click **Next** → **Next** → **Finish**

### Step 4: Add MySQL to PATH (Important!)

1. Press `Windows + R`, type `sysdm.cpl`, press Enter
2. Click **Advanced** tab → **Environment Variables**
3. Under "System variables", find **Path** and click **Edit**
4. Click **New** and add:
   ```
   C:\Program Files\MySQL\MySQL Server 8.0\bin
   ```
5. Click **OK** on all windows
6. **Restart VS Code** (or your terminal) to apply changes

### Step 5: Verify Installation

Open a **new** Command Prompt or PowerShell and run:

```bash
mysql --version
```

You should see something like:
```
mysql  Ver 8.0.36 for Win64 on x86_64 (MySQL Community Server - GPL)
```

### Step 6: Test MySQL Connection

```bash
mysql -u root -p
```

Enter your root password when prompted. You should see:
```
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is ...
mysql>
```

Type `exit` to quit.

---

## 🍎 macOS Installation

### Option A: Using Homebrew (Recommended)

1. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install MySQL**:
   ```bash
   brew install mysql
   ```

3. **Start MySQL Service**:
   ```bash
   brew services start mysql
   ```

4. **Set Root Password**:
   ```bash
   mysqladmin -u root password 'YourPassword123!'
   ```

### Option B: Using Official Installer

1. Download from: https://dev.mysql.com/downloads/mysql/
2. Choose **macOS** and download the DMG archive
3. Double-click to install
4. Follow the prompts
5. **IMPORTANT:** Note the temporary root password shown at the end!
6. Change the password:
   ```bash
   mysql -u root -p
   ```
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourPassword123!';
   ```

---

## 🐧 Linux Installation

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql

# Set root password
sudo mysql
```
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourPassword123!';
exit;
```

### CentOS/RHEL/Fedora

```bash
sudo dnf install mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld

# Set root password
sudo mysql
```
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourPassword123!';
exit;
```

---

## 🔧 Create PayPilot Database

After installing MySQL, create the database for PayPilot:

### Step 1: Connect to MySQL

```bash
mysql -u root -p
```

Enter your root password.

### Step 2: Create Database and User

Run these SQL commands:

```sql
-- Create the database
CREATE DATABASE paypilot_global CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user (recommended for security)
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

---

## ✅ Verify Everything Works

### Test Connection with New User

```bash
mysql -u paypilot_user -p paypilot_global
```

Enter password: `PayPilot2024!`

If you can connect successfully, you're all set!

---

## 🔐 MySQL Credentials for PayPilot

Save these - you'll need them in your `.env` file:

| Setting | Value |
|---------|-------|
| **Host** | `localhost` |
| **Port** | `3306` |
| **Database** | `paypilot_global` |
| **Username** | `paypilot_user` |
| **Password** | `PayPilot2024!` |

---

## 🐛 Troubleshooting

### Problem: "mysql: command not found"
**Solution:** MySQL bin directory not in PATH
- **Windows:** Follow Step 4 above
- **Mac/Linux:** Add to your shell profile:
  ```bash
  echo 'export PATH="/usr/local/mysql/bin:$PATH"' >> ~/.bash_profile
  source ~/.bash_profile
  ```

### Problem: "Access denied for user 'root'"
**Solution:** Wrong password
- Try resetting the password:
  - **Windows:** https://dev.mysql.com/doc/refman/8.0/en/resetting-permissions.html
  - **Mac/Linux:** `sudo mysql_secure_installation`

### Problem: MySQL service won't start
**Solution:**
- **Windows:** Open Services → Find MySQL80 → Start
- **Mac:** `brew services restart mysql`
- **Linux:** `sudo systemctl restart mysql`

### Problem: "Can't connect to MySQL server on 'localhost'"
**Solution:** MySQL isn't running
- Start the MySQL service:
  - **Windows:** Services → MySQL80 → Start
  - **Mac:** `brew services start mysql`
  - **Linux:** `sudo systemctl start mysql`

---

## 🎯 Next Steps

After installing MySQL:

1. ✅ Update the `.env` file with MySQL credentials
2. ✅ Install Python MySQL client: `pip install mysqlclient`
3. ✅ Run database migration: `python -m app.database_migrate`
4. ✅ Seed the database: `python -m app.seed`
5. ✅ Start the backend server

All these steps are in the updated **LOCAL_SETUP_GUIDE.md**!

---

## 📚 Additional Resources

- **MySQL Documentation:** https://dev.mysql.com/doc/
- **MySQL Workbench** (GUI tool): https://dev.mysql.com/downloads/workbench/
- **MySQL Tutorial:** https://www.mysqltutorial.org/

---

**You're ready to install MySQL!** 🚀

Once installed, follow the updated LOCAL_SETUP_GUIDE.md to configure PayPilot to use MySQL instead of SQLite.
