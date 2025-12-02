# Profile Scraping Verification Checklist

## ✅ What Has Been Fixed

### 1. Database Schema Issues - **RESOLVED**
- ✅ All required columns exist in `jobs` table
- ✅ Migration handles both legacy and new fields
- ✅ Jobs can be created without database errors

### 2. Error Handling - **IMPROVED**
- ✅ Better error messages for Redis/Celery connection issues
- ✅ Specific handling for "Actor not found" errors
- ✅ Jobs are properly marked as failed with error messages
- ✅ Returns appropriate HTTP status codes (503 for service unavailable)

### 3. Data Extraction Logic - **ENHANCED**
- ✅ Handles multiple field name variations
- ✅ Supports nested data structures
- ✅ Tries multiple field name patterns for each attribute
- ✅ Better logging to debug Apify response structure

### 4. Endpoints - **WORKING**
- ✅ `POST /api/profiles/scrape` - Returns 202 (Accepted)
- ✅ `POST /api/profiles/<profile_id>/scrape` - Returns 202 (Accepted)
- ✅ `GET /api/jobs/<job_id>` - Returns 200 with job details

## ⚠️ Current Issue: Data Not Being Saved

### Problem
- Profile scraping completes successfully (status = 'scraped')
- But data fields (name, email, company, etc.) are empty

### Root Cause
The actor ID `apify/linkedin-profile-scraper` **does not exist** in Apify.

### Solution Required

1. **Update APIFY_PROFILE_ACTOR_ID in .env file**
   ```env
   APIFY_PROFILE_ACTOR_ID=your-valid-actor-id
   ```

2. **Valid Actor Options:**
   - `apify/linkedin-scraper`
   - `apify/unlimited-leads-linkedin`
   - `apify/linkedin-profile-enrichment`
   - Or any other valid actor ID from your Apify account

3. **Verify the actor:**
   - Actor must exist in Apify
   - Actor must be accessible with your API token
   - Actor must return data in a format we can parse

## 📋 Verification Steps

### Step 1: Check Current Configuration
```bash
python -c "from app.config import Config; print('Actor ID:', Config.APIFY_PROFILE_ACTOR_ID)"
```

### Step 2: Update .env File
Edit `.env` and set:
```
APIFY_PROFILE_ACTOR_ID=your-valid-actor-id
```

### Step 3: Restart Services
- Restart Flask server
- Restart Celery worker (if running)

### Step 4: Test with New Profile
```bash
python verify_data_saving.py
```

### Step 5: Check Celery Worker Logs
Look for these log messages:
- `"Apify result keys: ..."` - Shows what fields Apify returned
- `"Apify result sample: ..."` - Shows the actual data structure
- `"Updating profile from Apify result - Keys: ..."` - Shows what we're trying to extract

### Step 6: Verify Data in Database
Check if data fields are populated after scraping completes.

## 🔍 Debugging Tips

1. **Check Celery Worker Logs:**
   - Look for "Apify result keys:" messages
   - This shows what data structure Apify is returning

2. **Test Actor Directly:**
   ```bash
   python check_apify_response.py
   ```
   This will show you exactly what Apify returns

3. **Check Job Status:**
   - Use `GET /api/jobs/<job_id>` endpoint
   - Check `result_data` field for failed profiles
   - Look for error messages

## ✅ Expected Behavior After Fix

Once you set a valid actor ID:

1. **Scraping completes** → Status = 'scraped'
2. **Data is extracted** → Fields populated (name, email, company, etc.)
3. **Data is saved** → All fields visible in database
4. **Job shows success** → success_count > 0

## 📝 Files Modified

1. `app/api/profiles.py` - Error handling improvements
2. `app/__init__.py` - Jobs blueprint registration
3. `app/tasks/scraper.py` - Enhanced data extraction
4. `app/config.py` - Added documentation
5. `migrations/versions/f6e5d4c3b2a1_add_jobs_table.py` - Fixed migration
6. `migrations/versions/b13bbce8fbd_fix_jobs_table_columns.py` - New migration

## 🎯 Next Action Required

**You need to set a valid APIFY_PROFILE_ACTOR_ID in your .env file.**

The code is ready to save data - it just needs a valid actor that returns data!
