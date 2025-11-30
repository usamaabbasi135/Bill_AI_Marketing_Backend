# 🚨 URGENT: Create Celery Worker Service on Render

## Why You're Getting the Error

The error `'NoneType' object has no attribute 'Redis'` happens because:
1. **No Worker Service**: Tasks can't run without a worker
2. **Connection Issue**: Celery can't connect to Redis when queuing tasks

## Step-by-Step: Create Worker Service NOW

### Step 1: Go to Render Dashboard
1. Open https://dashboard.render.com
2. Make sure you're in the correct project/account

### Step 2: Create Background Worker
1. Click the **"+ New"** button (top right)
2. Select **"Background Worker"**

### Step 3: Connect Repository
- **Repository**: `usamaabbasi135/Bill_AI_Marketing_Backend`
- **Branch**: `main` (or `develop` if you prefer)
- Click **"Connect"**

### Step 4: Configure Service Settings

**Basic Settings:**
```
Name: billy-ai-celery-worker
Environment: Python 3
Region: Oregon (same as your other services)
Branch: main
Root Directory: (leave empty)
```

**Build & Start Commands:**
```
Build Command: pip install -r requirements.txt
Start Command: celery -A celery_worker worker --loglevel=info --pool=solo
```

**Python Version:**
- Add environment variable: `PYTHON_VERSION` = `3.11.0`

### Step 5: Add Environment Variables

Click **"Add Environment Variable"** and add these:

**Required Variables:**
1. `DATABASE_URL` - Click "Link Database" → Select `billy-ai-db`
2. `REDIS_URL` - Click "Link Key Value" → Select `billy-ai-redis`
   - OR manually set: `redis://red-d41gbp63jp1c739c7g2g:6379` (your Redis URL)
3. `CELERY_BROKER_URL` - Same as REDIS_URL
4. `CELERY_RESULT_BACKEND` - Same as REDIS_URL
5. `JWT_SECRET_KEY` - Copy from your web service
6. `SECRET_KEY` - Copy from your web service
7. `FLASK_ENV` = `production`

**API Keys (Copy from web service):**
8. `APIFY_API_TOKEN` - Your Apify token
9. `APIFY_PROFILE_ACTOR_ID` - Optional, if different from default
10. `CLAUDE_API_KEY` - Your Claude API key

### Step 6: Link Services

**Link Database:**
- Click "Link Database" → Select `billy-ai-db`

**Link Key Value (Redis):**
- Click "Link Key Value" → Select `billy-ai-redis`

### Step 7: Create Service
- Click **"Create Background Worker"**
- Wait for deployment (2-3 minutes)

### Step 8: Verify Worker is Running

1. Go to the worker service
2. Click **"Logs"** tab
3. You should see:
   ```
   [CELERY CONFIG] Using broker: redis://red-xxxxx:6379
   celery@hostname ready.
   ```

## After Worker is Created

1. **Test the scraping endpoint again**
2. **Check worker logs** - you should see task execution
3. **Check web service logs** - should show task queued successfully

## If You Still Get Errors

### Error: "NoneType object has no attribute 'Redis'"
- This means Celery can't connect to Redis
- **Fix**: Make sure `REDIS_URL` is set correctly in worker service
- **Fix**: Verify Redis service is running and accessible

### Error: "Task not found"
- Worker can't find the task
- **Fix**: Make sure worker and web service use the same codebase
- **Fix**: Check that tasks are registered in worker logs

### Error: "Database connection failed"
- Worker can't connect to database
- **Fix**: Link the database to worker service
- **Fix**: Verify `DATABASE_URL` is set

## Quick Checklist

- [ ] Worker service created
- [ ] `REDIS_URL` set correctly
- [ ] `DATABASE_URL` linked
- [ ] All environment variables copied from web service
- [ ] Worker logs show "celery ready"
- [ ] Test scraping endpoint
- [ ] Check worker logs for task execution

## Need Help?

If you're stuck, check:
1. Worker service logs for errors
2. Web service logs for connection issues
3. Redis service status (should be "Available")

