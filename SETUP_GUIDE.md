# Setup Guide - Bill AI Marketing Backend

## Prerequisites
- ✅ Docker Desktop (installed)
- ⚠️ Python 3.11+ (needs installation)

## Step-by-Step Setup

### 1. Install Python
- Download from: https://www.python.org/downloads/
- **Important:** Check "Add Python to PATH" during installation
- Restart your terminal after installation

### 2. Create `.env` File
Create a file named `.env` in the project root with this content:

```env
# Database - Local development (Docker)
DATABASE_URL=postgresql://dev:dev123@localhost:5432/billy_ai

# Redis - Local development (Docker)
REDIS_URL=redis://localhost:6379/0

# Security Keys - Generate new ones for production!
SECRET_KEY=dev-secret-key-change-in-production-12345
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production-67890

# APIs (Optional - add when needed)
# APIFY_API_TOKEN=your-apify-token
# CLAUDE_API_KEY=your-claude-key
```

### 3. Create Virtual Environment
```bash
python -m venv venv
```

### 4. Activate Virtual Environment
**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```bash
venv\Scripts\activate.bat
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Start Database & Redis (Docker)
```bash
docker-compose up -d
```

### 7. Run Database Migrations
```bash
flask db upgrade
```

### 8. Start the Server
```bash
python run.py
```

The server will run at: **http://localhost:5000**

## Verify Installation

### Test Health Check
```bash
curl http://localhost:5000/api/health
```

Or open in browser: http://localhost:5000/api/health

Expected response:
```json
{"status": "ok"}
```

## Troubleshooting

### Python not found
- Make sure Python is added to PATH
- Restart terminal after Python installation
- Try `python3` instead of `python`

### Docker not running
- Open Docker Desktop
- Wait for it to fully start

### Database connection error
```bash
# Restart Docker containers
docker-compose down
docker-compose up -d
```

### Migration errors
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
flask db upgrade
```

### Port already in use
- Change port in `run.py` (line 8)
- Or stop the process using port 5000

### IDE Linter Errors (Import "flask" could not be resolved)
If you see linter warnings like "Import 'flask' could not be resolved" in VS Code/Cursor:

**Quick Fix:**
1. Run the setup script to create venv and install dependencies:
   - **PowerShell:** `.\setup_env.ps1`
   - **CMD:** `setup_env.bat`

2. Select the correct Python interpreter in your IDE:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type: `Python: Select Interpreter`
   - Choose: `.\venv\Scripts\python.exe` (Windows) or `./venv/bin/python` (Mac/Linux)

3. Reload the window:
   - Press `Ctrl+Shift+P` → `Developer: Reload Window`

**Manual Fix:**
If the setup script doesn't work, manually:
1. Create virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install dependencies: `pip install -r requirements.txt`
4. Select the interpreter in your IDE as described above

The `.vscode/settings.json` file has been created to help your IDE find the correct interpreter automatically.

