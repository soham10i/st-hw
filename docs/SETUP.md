# STF Digital Twin - Complete Setup Guide

This guide provides detailed instructions for setting up the STF Digital Twin system on Windows, macOS, and Linux, including local MySQL database configuration.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Windows Setup](#windows-setup)
3. [macOS Setup](#macos-setup)
4. [Linux Setup](#linux-setup)
5. [Local MySQL Installation](#local-mysql-installation)
6. [Docker Alternative](#docker-alternative)
7. [Environment Configuration](#environment-configuration)
8. [Running the Application](#running-the-application)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9+ | 3.11+ |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB | 5 GB |
| MySQL | 8.0+ | 8.0+ |

**Required Python Packages:**
- FastAPI, Uvicorn (API server)
- SQLAlchemy, PyMySQL (Database)
- Streamlit, Plotly, Pandas (Dashboard)
- httpx, paho-mqtt (Communication)

---

## Windows Setup

### Step 1: Install Python

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer and **check "Add Python to PATH"**
3. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### Step 2: Install Git (Optional)

1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default options
3. Verify: `git --version`

### Step 3: Clone or Download Project

```powershell
# Using Git
git clone <repository-url> stf_project
cd stf_project

# Or extract downloaded ZIP to a folder
```

### Step 4: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Verify activation (should show (venv) prefix)
```

### Step 5: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 6: Configure Environment

Create a `.env` file in the project root:

```powershell
# Create .env file
notepad .env
```

Add the following content:
```env
DATABASE_URL=mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse
STF_API_URL=http://localhost:8000
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### Step 7: Start Services

Open **four separate PowerShell windows**:

**Terminal 1 - FastAPI Server:**
```powershell
cd path\to\stf_project
.\venv\Scripts\activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Mock Hardware:**
```powershell
cd path\to\stf_project
.\venv\Scripts\activate
python -m hardware.mock_hbw
```

**Terminal 3 - Main Controller:**
```powershell
cd path\to\stf_project
.\venv\Scripts\activate
python -m controller.main_controller
```

**Terminal 4 - Streamlit Dashboard:**
```powershell
cd path\to\stf_project
.\venv\Scripts\activate
streamlit run dashboard/app.py
```

---

## macOS Setup

### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python

```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

### Step 3: Clone Project

```bash
git clone <repository-url> stf_project
cd stf_project
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show (venv) prefix)
```

### Step 5: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 6: Configure Environment

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse
STF_API_URL=http://localhost:8000
MQTT_BROKER=localhost
MQTT_PORT=1883
EOF
```

### Step 7: Start Services

Open **four separate Terminal windows** (or use tmux/screen):

**Terminal 1 - FastAPI Server:**
```bash
cd ~/stf_project
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Mock Hardware:**
```bash
cd ~/stf_project
source venv/bin/activate
python -m hardware.mock_hbw
```

**Terminal 3 - Main Controller:**
```bash
cd ~/stf_project
source venv/bin/activate
python -m controller.main_controller
```

**Terminal 4 - Streamlit Dashboard:**
```bash
cd ~/stf_project
source venv/bin/activate
streamlit run dashboard/app.py
```

---

## Linux Setup

### Step 1: Install Python and Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git -y
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.11 python3-pip git -y
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip git
```

### Step 2: Clone and Setup

```bash
git clone <repository-url> stf_project
cd stf_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure and Run

Follow the same environment configuration and service startup steps as macOS.

---

## Local MySQL Installation

### Windows

1. **Download MySQL Installer:**
   - Go to [MySQL Downloads](https://dev.mysql.com/downloads/installer/)
   - Download "MySQL Installer for Windows"

2. **Run Installer:**
   - Choose "Custom" installation
   - Select "MySQL Server 8.0" and "MySQL Workbench"
   - Click Next and install

3. **Configure MySQL:**
   - Set root password (remember this!)
   - Create a user account for STF:
     - Username: `stf_user`
     - Password: `stf_password`
     - Host: `localhost`

4. **Create Database:**
   Open MySQL Workbench or command line:
   ```sql
   CREATE DATABASE stf_warehouse;
   GRANT ALL PRIVILEGES ON stf_warehouse.* TO 'stf_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

5. **Verify Connection:**
   ```powershell
   mysql -u stf_user -p -e "SHOW DATABASES;"
   ```

### macOS

1. **Install via Homebrew:**
   ```bash
   brew install mysql
   ```

2. **Start MySQL Service:**
   ```bash
   brew services start mysql
   ```

3. **Secure Installation:**
   ```bash
   mysql_secure_installation
   ```

4. **Create Database and User:**
   ```bash
   mysql -u root -p
   ```
   ```sql
   CREATE DATABASE stf_warehouse;
   CREATE USER 'stf_user'@'localhost' IDENTIFIED BY 'stf_password';
   GRANT ALL PRIVILEGES ON stf_warehouse.* TO 'stf_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. **Verify Connection:**
   ```bash
   mysql -u stf_user -p stf_warehouse -e "SELECT 1;"
   ```

### Linux (Ubuntu/Debian)

1. **Install MySQL:**
   ```bash
   sudo apt update
   sudo apt install mysql-server -y
   ```

2. **Start and Enable Service:**
   ```bash
   sudo systemctl start mysql
   sudo systemctl enable mysql
   ```

3. **Secure Installation:**
   ```bash
   sudo mysql_secure_installation
   ```

4. **Create Database and User:**
   ```bash
   sudo mysql
   ```
   ```sql
   CREATE DATABASE stf_warehouse;
   CREATE USER 'stf_user'@'localhost' IDENTIFIED BY 'stf_password';
   GRANT ALL PRIVILEGES ON stf_warehouse.* TO 'stf_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

---

## Docker Alternative

If you prefer Docker over local MySQL installation:

### Prerequisites

1. Install Docker Desktop:
   - **Windows:** [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - **macOS:** [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - **Linux:** [Docker Engine](https://docs.docker.com/engine/install/)

### Start Infrastructure

```bash
cd stf_project
docker-compose up -d
```

This starts:
- MySQL on port 3306
- Mosquitto MQTT on port 1883
- Adminer (DB UI) on port 8080

### Verify Services

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f mysql
docker-compose logs -f mosquitto
```

### Stop Services

```bash
docker-compose down

# To remove data volumes as well:
docker-compose down -v
```

---

## Environment Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | Required |
| `STF_API_URL` | FastAPI server URL | `http://localhost:8000` |
| `MQTT_BROKER` | MQTT broker hostname | `localhost` |
| `MQTT_PORT` | MQTT broker port | `1883` |

### Connection String Format

```
mysql+pymysql://username:password@host:port/database
```

**Examples:**
```env
# Local MySQL
DATABASE_URL=mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse

# Docker MySQL
DATABASE_URL=mysql+pymysql://stf_user:stf_password@localhost:3306/stf_warehouse

# Remote MySQL
DATABASE_URL=mysql+pymysql://stf_user:stf_password@192.168.1.100:3306/stf_warehouse

# MySQL with SSL
DATABASE_URL=mysql+pymysql://stf_user:stf_password@host:3306/stf_warehouse?ssl=true
```

---

## Running the Application

### Quick Start Script

**Linux/macOS:**
```bash
chmod +x run_all.sh
./run_all.sh
```

**Windows (create run_all.bat):**
```batch
@echo off
start "FastAPI" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"
timeout /t 3
start "Hardware" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m hardware.mock_hbw"
start "Controller" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m controller.main_controller"
start "Dashboard" cmd /k "cd /d %~dp0 && venv\Scripts\activate && streamlit run dashboard/app.py"
echo All services started!
echo FastAPI: http://localhost:8000/docs
echo Dashboard: http://localhost:8501
pause
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:8501 | Streamlit UI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API ReDoc | http://localhost:8000/redoc | ReDoc UI |
| Adminer | http://localhost:8080 | Database UI (Docker) |

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'xxx'"

**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

#### 2. "Access denied for user 'stf_user'@'localhost'"

**Solution:** Verify MySQL user credentials:
```sql
-- Check user exists
SELECT User, Host FROM mysql.user WHERE User = 'stf_user';

-- Reset password if needed
ALTER USER 'stf_user'@'localhost' IDENTIFIED BY 'stf_password';
FLUSH PRIVILEGES;
```

#### 3. "Can't connect to MySQL server on 'localhost'"

**Solutions:**
- Verify MySQL is running:
  ```bash
  # Linux
  sudo systemctl status mysql
  
  # macOS
  brew services list
  
  # Windows
  Get-Service -Name MySQL*
  ```
- Check port 3306 is not blocked by firewall
- Verify connection string in `.env`

#### 4. "Address already in use" (Port conflict)

**Solution:** Find and kill the process using the port:
```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### 5. Streamlit "Connection refused"

**Solution:** Ensure FastAPI server is running before starting Streamlit:
```bash
# Check if API is accessible
curl http://localhost:8000/health
```

#### 6. MQTT Connection Failed

**Solutions:**
- If using Docker: `docker-compose up -d mosquitto`
- If local: Install Mosquitto broker
  ```bash
  # Ubuntu
  sudo apt install mosquitto mosquitto-clients
  
  # macOS
  brew install mosquitto
  
  # Windows: Download from mosquitto.org
  ```

### Getting Help

1. Check the logs in each terminal window
2. Verify all environment variables are set correctly
3. Ensure database is accessible and tables are created
4. Test API endpoints directly: http://localhost:8000/docs

---

## Next Steps

After successful setup:

1. **Initialize Database:** The API will auto-create tables on first run
2. **Access Dashboard:** Open http://localhost:8501
3. **Initialize System:** Click "Initialize System" in the dashboard
4. **Test Operations:** Use Store/Retrieve buttons to test functionality
5. **View Analytics:** Navigate to the Analytics page for historical data

For development and customization, refer to the main README.md file.
