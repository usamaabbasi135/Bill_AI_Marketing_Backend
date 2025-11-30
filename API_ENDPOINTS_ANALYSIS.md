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

### Campaigns (8/8) ✅
- ✅ GET `/api/campaigns` - List Campaigns
- ✅ GET `/api/campaigns/<campaign_id>` - Get Campaign by ID
- ✅ POST `/api/campaigns` - Create Campaign
- ✅ POST `/api/campaigns/<campaign_id>/add-profiles` - Add Profiles to Campaign
- ✅ DELETE `/api/campaigns/<campaign_id>/profiles/<profile_id>` - Remove Profile from Campaign
- ✅ POST `/api/campaigns/<campaign_id>/generate-emails` - Generate Campaign Emails
- ✅ POST `/api/campaigns/<campaign_id>/send-emails` - Send Campaign Emails
- ✅ DELETE `/api/campaigns/<campaign_id>` - Delete Campaign

### Emails (6/6) ✅
- ✅ GET `/api/emails` - List Emails
- ✅ POST `/api/emails/generate` - Generate Single Email
- ✅ GET `/api/emails/<email_id>` - Get Email by ID
- ✅ PATCH `/api/emails/<email_id>` - Update Email
- ✅ DELETE `/api/emails/<email_id>` - Delete Email (Soft Delete)
- ✅ POST `/api/emails/<email_id>/send` - Send Single Email

### Posts (3/3) ✅
- ✅ GET `/api/posts` - List Posts (with filtering, pagination, sorting)
- ✅ POST `/api/posts/<post_id>/analyze` - Analyze Single Post
- ✅ POST `/api/posts/analyze-batch` - Analyze Batch Posts

### Health Check (1/1) ✅
- ✅ GET `/api/health` - Health Check

---

## 📊 Statistics

- **Total Endpoints in Code:** 40
- **Endpoints in Postman:** 40
- **Missing from Postman:** 0 ✅

---

## ✅ All Endpoints Complete!

All endpoints from the codebase are now included in the Postman collection. The collection is complete and ready for testing.

---

## 📝 Notes

- All endpoints require JWT authentication except `/api/health`
- Campaign endpoints support adding/removing profiles dynamically
- Email endpoints support soft delete (deleted_at timestamp)
- Email generation can be done individually or in bulk via campaigns

