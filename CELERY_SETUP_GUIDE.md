# Celery Worker Setup Guide for Render

## What is Celery?

**Celery** is a distributed task queue system for Python that allows you to run time-consuming tasks asynchronously in the background. This keeps your web server responsive while heavy tasks (like web scraping, AI analysis, email sending) run separately.

## Architecture Overview

```
┌─────────────┐         ┌─────────┐         ┌──────────────┐
│  Web Server │────────▶│  Redis  │────────▶│   Worker    │
│  (Flask)    │  Queue  │ (Queue) │  Fetch  │  (Celery)   │
│             │  Task   │         │  Task   │             │
└─────────────┘         └─────────┘         └──────────────┘
     │                                            │
     │                                            │
     └────────────────────────────────────────────┘
                    Store Results
```

## Services Required

### 1. **Web Service** (Flask/Gunicorn)
- Handles HTTP requests
- Queues tasks to Redis
- **Status**: ✅ You have this (`billy-ai-backend`)

### 2. **Redis Service** (Message Broker)
- Stores task queue
- Acts as communication channel between web and worker
- **Status**: ✅ You have this (`billy-ai-redis`)

### 3. **Worker Service** (Celery)
- Processes tasks from Redis
- Runs scraping, AI analysis, email sending
- **Status**: ❌ Need to create this (`billy-ai-celery-worker`)

## How to Create Worker Service on Render

### Method 1: Using render.yaml (Automatic)

Your `render.yaml` already has the worker service defined. Render should create it automatically when you deploy via Blueprint.

**If it wasn't created:**
1. Go to Render Dashboard
2. Find your Blueprint
3. Click "Update" or "Redeploy"
4. Render will read `render.yaml` and create the worker service

### Method 2: Manual Creation (Step-by-Step)

1. **Go to Render Dashboard**
   - Navigate to https://dashboard.render.com

2. **Create New Background Worker**
   - Click "New +" button
   - Select "Background Worker"

3. **Connect Repository**
   - Connect to: `usamaabbasi135/Bill_AI_Marketing_Backend`
   - Branch: `main` (or `develop`)

4. **Configure Service**
   ```
   Name: billy-ai-celery-worker
   Environment: Python 3
   Region: Oregon (or your preferred region)
   Branch: main
   Root Directory: (leave empty)
   ```

5. **Build & Start Commands**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: celery -A celery_worker worker --loglevel=info --pool=solo
   ```

6. **Python Version**
   ```
   PYTHON_VERSION: 3.11.0
   ```

7. **Environment Variables**
   Copy these from your web service:
   
   **Required:**
   - `DATABASE_URL` - Connect to your database
   - `REDIS_URL` - Connect to your Redis service
   - `CELERY_BROKER_URL` - Same as REDIS_URL
   - `CELERY_RESULT_BACKEND` - Same as REDIS_URL
   - `JWT_SECRET_KEY` - Same as web service
   - `SECRET_KEY` - Same as web service
   - `FLASK_ENV` = `production`
   
   **API Keys (set manually):**
   - `APIFY_API_TOKEN` - Your Apify token
   - `APIFY_PROFILE_ACTOR_ID` - Apify actor ID (optional)
   - `CLAUDE_API_KEY` - Your Claude API key

8. **Connect Services**
   - **Database**: Connect to `billy-ai-db`
   - **Redis**: Connect to `billy-ai-redis`

9. **Create Service**
   - Click "Create Background Worker"
   - Wait for deployment to complete

## Verifying Worker is Running

### Check Logs
1. Go to your worker service in Render
2. Click "Logs" tab
3. You should see:
   ```
   [CELERY CONFIG] Using broker: redis://red-xxxxx:6379
   [CELERY CONFIG] Registered tasks: ['scrape_company_posts', 'scrape_profiles', ...]
   celery@hostname ready.
   ```

### Test Task Execution
1. Make a request to scrape a company
2. Check worker logs - you should see task execution
3. Check web service logs - should show task queued successfully

## Common Issues

### Issue: Worker not picking up tasks
**Solution**: 
- Verify `REDIS_URL` is set correctly in worker
- Ensure Redis service is running
- Check that worker and web service use the same Redis instance

### Issue: Tasks failing with database errors
**Solution**:
- Ensure worker has `DATABASE_URL` set
- Verify database connection from worker
- Check that worker has same database access as web service

### Issue: "No module named 'app'"
**Solution**:
- Ensure `PYTHONPATH` is set correctly
- Check that `celery_worker.py` is in project root
- Verify all dependencies in `requirements.txt`

## Worker Command Options

### Basic Worker
```bash
celery -A celery_worker worker --loglevel=info --pool=solo
```

### With Concurrency (for production)
```bash
celery -A celery_worker worker --loglevel=info --concurrency=4
```

### With Auto-reload (development)
```bash
celery -A celery_worker worker --loglevel=info --pool=solo --autoreload
```

## Monitoring

### Check Worker Status
- Render Dashboard → Worker Service → Logs
- Look for: `celery@hostname ready.`

### Check Task Queue
- Worker logs show: `Received task: scrape_company_posts[...]`
- Worker logs show: `Task scrape_company_posts[...] succeeded`

## Next Steps

1. ✅ Create worker service (using method above)
2. ✅ Verify worker is running (check logs)
3. ✅ Test scraping endpoint
4. ✅ Monitor worker logs for task execution

## Architecture Summary

```
User Request
    ↓
Web Service (Flask)
    ↓ (queues task)
Redis (Message Queue)
    ↓ (worker picks up)
Celery Worker
    ↓ (executes)
Task Complete → Results stored in Redis
```

Your scraping tasks will now run in the background! 🚀

