# Profile Scraping & API Response Documentation

## 🔄 What Happens During Scraping

When you trigger a profile scrape (via `POST /api/profiles/scrape` or `POST /api/profiles/<profile_id>/scrape`), the following happens:

### 1. **Job Creation**
- A job record is created with status `pending`
- Job type: `profile_scrape`
- The job is processed asynchronously via Celery

### 2. **Apify Actor Call**
- The system calls `dev_fusion/linkedin-profile-scraper` actor
- Uses `startUrls` format: `[{"url": "https://www.linkedin.com/in/username"}]`
- Waits for the actor to complete (with retries and timeout handling)

### 3. **Data Extraction & Storage**
The scraper extracts and saves the following data from the Apify response:

#### **Basic Information**
- `first_name` - First name
- `last_name` - Last name  
- `full_name` - Full name
- `person_name` - Full name (backward compatibility)
- `headline` - Professional headline
- `about` - About/bio section

#### **Contact Information**
- `email` - Email address
- `phone` - Phone number (from `phone` or `mobileNumber`)
- `mobile_number` - Mobile number specifically

#### **LinkedIn Identifiers**
- `linkedin_id` - LinkedIn internal ID
- `public_identifier` - Public username (e.g., "williamhgates")
- `linkedin_public_url` - Public LinkedIn URL
- `urn` - LinkedIn URN identifier

#### **Social Statistics**
- `connections` - Number of connections
- `followers` - Number of followers

#### **Current Job Information**
- `job_title` - Current job title
- `job_started_on` - When job started (e.g., "2000", "2022")
- `job_location` - Job location
- `job_still_working` - Boolean if still working there

#### **Company Information**
- `company` - Company name (backward compatibility)
- `company_name` - Company name
- `company_industry` - Industry sector
- `company_website` - Company website URL
- `company_linkedin` - Company LinkedIn page URL
- `company_founded_in` - Year company was founded
- `company_size` - Company size (e.g., "1001-5000", "51-200")

#### **Location Information**
- `location` - Location (backward compatibility)
- `address_country_only` - Country only (e.g., "United States")
- `address_with_country` - Full address with country
- `address_without_country` - Address without country

#### **Profile Media**
- `profile_pic` - Profile picture URL
- `profile_pic_high_quality` - High-quality profile picture URL
- `background_pic` - Background/banner picture URL

#### **Profile Flags (Boolean)**
- `is_premium` - Has LinkedIn Premium
- `is_verified` - Is verified account
- `is_job_seeker` - Is actively job seeking
- `is_retired` - Is retired
- `is_creator` - Is a creator
- `is_influencer` - Is an influencer

#### **Complex Data (Stored as JSON)**
- `experiences` - Array of work experiences (full JSON)
- `skills` - Array of skills (full JSON)
- `educations` - Array of education history (full JSON)

#### **Metadata**
- `status` - Updated to `scraped`
- `scraped_at` - Timestamp of when scraping completed
- `industry` - Industry (from company_industry for backward compatibility)

---

## 📡 API Endpoint Responses

### 1. **GET /api/profiles** - List Profiles

**Query Parameters:**
- `page` (default: 1) - Page number
- `limit` (default: 20, max: 100) - Items per page
- `status` - Filter: `url_only`, `scraped`, `scraping_failed`
- `company` - Filter by company name (partial match)
- `location` - Filter by location (partial match)
- `industry` - Filter by industry (partial match)
- `search` - Search in person_name, headline, company
- `sort` - Sort field: `created_at`, `person_name`, `scraped_at` (default: `created_at`)
- `order` - Sort order: `asc`, `desc` (default: `desc`)

**Response Structure:**
```json
{
  "profiles": [
    {
      "profile_id": "uuid-string",
      "tenant_id": "uuid-string",
      "person_name": "Bill Gates",
      "first_name": "Bill",
      "last_name": "Gates",
      "full_name": "Bill Gates",
      "headline": "Chair, Gates Foundation and Founder, Breakthrough Energy",
      "about": "Chair of the Gates Foundation...",
      "linkedin_url": "https://www.linkedin.com/in/williamhgates",
      "linkedin_public_url": "https://linkedin.com/in/williamhgates",
      "linkedin_id": "251749025",
      "public_identifier": "williamhgates",
      "urn": "ACoAAA8BYqEBCGLg_vT_ca6mMEqkpp9nVffJ3hc",
      "status": "scraped",
      "email": "bill.gates@gatesfoundation.org",
      "phone": null,
      "mobile_number": null,
      "company": "Gates Foundation",
      "company_name": "Gates Foundation",
      "company_industry": "Non-profit Organizations",
      "company_website": "https://www.gatesfoundation.org/about/careers",
      "company_linkedin": "https://www.linkedin.com/company/gates-foundation/",
      "company_founded_in": null,
      "company_size": "1001-5000",
      "job_title": "Co-chair",
      "job_started_on": "2000",
      "job_location": null,
      "job_still_working": true,
      "location": "Seattle, Washington United States",
      "address_country_only": "United States",
      "address_with_country": "Seattle, Washington United States",
      "address_without_country": "Seattle, Washington",
      "industry": "Non-profit Organizations",
      "connections": 8,
      "followers": 39427591,
      "profile_pic": "https://media.licdn.com/dms/image/...",
      "profile_pic_high_quality": "https://media.licdn.com/dms/image/...",
      "background_pic": "https://media.licdn.com/dms/image/...",
      "is_premium": true,
      "is_verified": false,
      "is_job_seeker": false,
      "is_retired": false,
      "is_creator": true,
      "is_influencer": true,
      "experiences": [
        {
          "companyId": "8736",
          "companyName": "Gates Foundation",
          "title": "Co-chair",
          "jobStartedOn": "2000",
          "jobStillWorking": true,
          "companySize": "1001-5000",
          "companyIndustry": "Non-profit Organizations",
          ...
        },
        ...
      ],
      "skills": [
        {
          "title": "Customer Service"
        },
        {
          "title": "Microsoft Office"
        },
        ...
      ],
      "educations": [
        {
          "companyId": "18483",
          "title": "Harvard University",
          "period": {
            "startedOn": {"year": 1973},
            "endedOn": {"year": 1975}
          },
          ...
        },
        ...
      ],
      "scraped_at": "2025-01-28T10:30:00.000000",
      "created_at": "2025-01-28T09:00:00.000000"
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  },
  "stats": {
    "total": 150,
    "scraped": 120,
    "pending": 25,
    "failed": 5
  }
}
```

**Note:** 
- For profiles with `status: "url_only"`, most fields will be `null` until scraping completes
- `experiences`, `skills`, and `educations` are parsed from JSON and returned as arrays
- All fields are nullable - they will be `null` if not available in the scraped data

---

### 2. **POST /api/profiles** - Add Single Profile

**Request Body:**
```json
{
  "linkedin_url": "https://www.linkedin.com/in/williamhgates"
}
```

**Response (201 Created):**
```json
{
  "profile": {
    "profile_id": "uuid-string",
    "tenant_id": "uuid-string",
    "linkedin_url": "https://www.linkedin.com/in/williamhgates",
    "username": "williamhgates",
    "status": "url_only",
    "person_name": null,
    "headline": null,
    "created_at": "2025-01-28T10:00:00.000000"
  }
}
```

**Error Response (400) - Profile Already Exists:**
```json
{
  "error": "Profile already exists",
  "profile_id": "existing-uuid"
}
```

---

### 3. **POST /api/profiles/scrape** - Scrape All Profiles

**Response (202 Accepted):**
```json
{
  "message": "Scraping job started",
  "job_id": "uuid-string",
  "profiles_found": 25,
  "profiles_in_batch": 25,
  "status_url": "/api/jobs/{job_id}"
}
```

**Response (200) - No Profiles to Scrape:**
```json
{
  "message": "No profiles to scrape",
  "profiles_found": 0
}
```

---

### 4. **POST /api/profiles/<profile_id>/scrape** - Scrape Single Profile

**Response (202 Accepted):**
```json
{
  "message": "Scraping job started",
  "job_id": "uuid-string",
  "profile_id": "profile-uuid",
  "status_url": "/api/jobs/{job_id}"
}
```

**Response (200) - Already Scraped:**
```json
{
  "message": "Profile already scraped",
  "profile_id": "profile-uuid",
  "status": "scraped"
}
```

---

### 5. **POST /api/profiles/bulk-upload** - Bulk Upload Profiles (CSV)

**Request:** Multipart form data with CSV file

**Response (201 Created):**
```json
{
  "added": 50,
  "skipped": 5,
  "failed": 2,
  "errors": [
    {
      "row": 10,
      "error": "Invalid linkedin_url format"
    },
    {
      "row": 15,
      "error": "linkedin_url must point to linkedin.com"
    }
  ],
  "total_rows": 57
}
```

---

## 📊 Data Flow Summary

1. **Profile Added** → Status: `url_only`, Only `linkedin_url` stored
2. **Scraping Triggered** → Job created, Celery task started
3. **Apify Actor Called** → Data fetched from LinkedIn
4. **Data Parsed** → All fields extracted and saved to database
5. **Status Updated** → Status: `scraped`, `scraped_at` timestamp set
6. **API Returns** → Full profile data with all new fields available

---

## ⚠️ Important Notes

- **Backward Compatibility**: Old fields (`person_name`, `company`, `location`, `industry`) are still populated for backward compatibility
- **Null Values**: Fields will be `null` if not available in the scraped data
- **JSON Fields**: `experiences`, `skills`, and `educations` are stored as JSON strings in the database but returned as parsed arrays in the API
- **Filtering**: You can filter by `company`, `location`, `industry` using the new fields
- **Search**: Search works on `person_name`, `headline`, and `company` fields

