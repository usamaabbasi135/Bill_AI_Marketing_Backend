# API Endpoints Analysis

## Summary
This document lists all API endpoints found in the codebase and indicates which ones are included in the Postman collection.

## ✅ Endpoints in Postman Collection

### Auth (4/4) ✅
- ✅ POST `/api/auth/register`
- ✅ POST `/api/auth/login`
- ✅ POST `/api/auth/refresh`
- ✅ GET `/api/auth/me`

### Companies (7/7) ✅
- ✅ POST `/api/companies` - Create Company
- ✅ GET `/api/companies` - List Companies
- ✅ GET `/api/companies?is_active=true` - List Active Companies
- ✅ GET `/api/companies?is_active=false` - List Inactive Companies
- ✅ PATCH `/api/companies/<company_id>` - Update Company
- ✅ DELETE `/api/companies/<company_id>` - Delete Company (Soft Delete)
- ✅ POST `/api/companies/<company_id>/scrape` - Scrape Company Posts (with query param)
- ✅ POST `/api/companies/<company_id>/scrape` - Scrape Company Posts (with JSON body)

### Profiles (8/8) ✅
- ✅ POST `/api/profiles` - Add Single Profile
- ✅ GET `/api/profiles` - List Profiles
- ✅ GET `/api/profiles?status=scraped` - List Profiles by Status
- ✅ GET `/api/profiles?search=John` - Search Profiles
- ✅ GET `/api/profiles?status=scraped&company=Tech&location=San Francisco&...` - Combined Filters
- ✅ POST `/api/profiles/bulk-upload` - Bulk Upload Profiles (CSV)
- ✅ GET `/api/profiles/bulk-upload/template` - Download Bulk Upload Template
- ✅ POST `/api/profiles/scrape` - Scrape All Profiles
- ✅ POST `/api/profiles/<profile_id>/scrape` - Scrape Single Profile

### Jobs (1/1) ✅
- ✅ GET `/api/jobs/<job_id>` - Get Job Status

### Templates (6/6) ✅
- ✅ GET `/api/templates` - List Templates
- ✅ GET `/api/templates/<template_id>` - Get Template by ID
- ✅ POST `/api/templates` - Create Custom Template
- ✅ PATCH `/api/templates/<template_id>` - Update Template
- ✅ DELETE `/api/templates/<template_id>` - Delete Template
- ✅ POST `/api/templates/<template_id>/preview` - Preview Template

### Campaigns (4/7) ⚠️ **MISSING 3 ENDPOINTS**
- ✅ GET `/api/campaigns` - List Campaigns
- ✅ GET `/api/campaigns/<campaign_id>` - Get Campaign by ID
- ✅ POST `/api/campaigns` - Create Campaign
- ✅ DELETE `/api/campaigns/<campaign_id>` - Delete Campaign
- ❌ **MISSING:** POST `/api/campaigns/<campaign_id>/add-profiles` - Add Profiles to Campaign
- ❌ **MISSING:** DELETE `/api/campaigns/<campaign_id>/profiles/<profile_id>` - Remove Profile from Campaign
- ❌ **MISSING:** POST `/api/campaigns/<campaign_id>/generate-emails` - Generate Campaign Emails

### Emails (1/5) ⚠️ **MISSING 4 ENDPOINTS**
- ✅ GET `/api/emails` - List Emails
- ❌ **MISSING:** POST `/api/emails/generate` - Generate Single Email
- ❌ **MISSING:** GET `/api/emails/<email_id>` - Get Email by ID
- ❌ **MISSING:** PATCH `/api/emails/<email_id>` - Update Email
- ❌ **MISSING:** DELETE `/api/emails/<email_id>` - Delete Email (Soft Delete)

### Posts (3/3) ✅
- ✅ GET `/api/posts` - List Posts (with filtering, pagination, sorting)
- ✅ POST `/api/posts/<post_id>/analyze` - Analyze Single Post
- ✅ POST `/api/posts/analyze-batch` - Analyze Batch Posts

### Health Check (1/1) ✅
- ✅ GET `/api/health` - Health Check

---

## 📊 Statistics

- **Total Endpoints in Code:** 36
- **Endpoints in Postman:** 29
- **Missing from Postman:** 7

### Missing Endpoints Breakdown:
1. **Campaigns:** 3 missing endpoints
   - Add profiles to campaign
   - Remove profile from campaign
   - Generate emails for campaign

2. **Emails:** 4 missing endpoints
   - Generate single email
   - Get email by ID
   - Update email
   - Delete email

---

## 🔧 Recommendations

To complete the Postman collection, add the following 7 endpoints:

### Campaigns Endpoints:
1. `POST /api/campaigns/<campaign_id>/add-profiles`
   - Body: `{"profile_ids": ["uuid1", "uuid2"]}`
   - Description: Add profiles to an existing campaign

2. `DELETE /api/campaigns/<campaign_id>/profiles/<profile_id>`
   - Description: Remove a profile from a campaign

3. `POST /api/campaigns/<campaign_id>/generate-emails`
   - Body: `{"template_id": "template-uuid"}`
   - Description: Generate emails for all profiles in a campaign (async task)

### Emails Endpoints:
4. `POST /api/emails/generate`
   - Body: `{"post_id": "uuid", "profile_id": "uuid", "template_id": "uuid"}`
   - Description: Generate a single personalized email using Claude API

5. `GET /api/emails/<email_id>`
   - Description: Get single email details with related data

6. `PATCH /api/emails/<email_id>`
   - Body: `{"subject": "...", "body": "...", "status": "draft|sent|failed"}`
   - Description: Update email (subject, body, status). Cannot update if status='sent'.

7. `DELETE /api/emails/<email_id>`
   - Description: Soft delete email (sets deleted_at timestamp). Cannot delete if status='sent'.

---

## 📝 Notes

- All endpoints require JWT authentication except `/api/health`
- Campaign endpoints support adding/removing profiles dynamically
- Email endpoints support soft delete (deleted_at timestamp)
- Email generation can be done individually or in bulk via campaigns

