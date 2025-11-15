# How to Run the Server and Test

## Prerequisites

1. **Docker containers running** (PostgreSQL & Redis)
2. **Python dependencies installed**
3. **Environment variables set** (optional for local dev)

## Step-by-Step Guide

### 1. Start Database Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify they're running
docker-compose ps
```

### 2. Run Database Migrations

```bash
# Apply all migrations (including analyzed_at field)
flask db upgrade
```

### 3. Start Flask Server

**Option A: Using run.py (Development)**
```bash
python run.py
```

**Option B: Using Flask CLI**
```bash
flask run
```

**Option C: Using Gunicorn (Production-like)**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

The server will start on: `http://localhost:5000`

### 4. Start Celery Worker (for AI analysis)

**Open a NEW terminal window** and run:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

This is required for the AI analysis tasks to execute.

### 5. Set Environment Variables (Optional)

For local development, defaults are provided, but you can override:

**Windows PowerShell:**
```powershell
$env:CLAUDE_API_KEY="your-claude-api-key"
$env:REDIS_URL="redis://localhost:6379/0"
$env:DATABASE_URL="postgresql://dev:dev123@localhost:5432/billy_ai"
```

**Windows CMD:**
```cmd
set CLAUDE_API_KEY=your-claude-api-key
set REDIS_URL=redis://localhost:6379/0
```

**Linux/Mac:**
```bash
export CLAUDE_API_KEY="your-claude-api-key"
export REDIS_URL="redis://localhost:6379/0"
```

### 6. Test the Server

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

**Or use the test script:**
```bash
python test_api.py
```

**Test AI Analysis endpoints:**
```bash
python test_ai_endpoints.py
```

## Quick Start Commands

```bash
# Terminal 1: Start services
docker-compose up -d
flask db upgrade
python run.py

# Terminal 2: Start Celery worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info

# Terminal 3: Run tests
python test_api.py
python test_ai_endpoints.py
```

## Verification Checklist

- [ ] Docker containers running (`docker-compose ps`)
- [ ] Database migrated (`flask db upgrade`)
- [ ] Flask server running (`http://localhost:5000/api/health` returns 200)
- [ ] Celery worker running (see worker logs)
- [ ] Can authenticate (test login/register)

## Troubleshooting

**Port 5000 already in use:**
```bash
# Change port in run.py or use:
flask run --port 5001
```

**Database connection error:**
```bash
# Restart containers
docker-compose restart
```

**Celery not processing tasks:**
- Make sure Redis is running
- Check Celery worker logs for errors
- Verify REDIS_URL is correct

**JWT errors:**
- Default keys are provided for development
- For production, set SECRET_KEY and JWT_SECRET_KEY

