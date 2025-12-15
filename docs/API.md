# Billy AI Marketing Backend - API Documentation

## Base URL
```
Development: http://localhost:5000
Production: TBD
```

## Authentication
All protected endpoints require JWT token in header:
```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### Register User
Create new user account and tenant workspace.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Inc"
}
```

**Validation Rules:**
- Email: Valid email format
- Password: Min 8 chars, 1 uppercase, 1 number
- All fields: Required

**Success Response (201):**
```json
{
  "message": "Registration successful",
  "user": {
    "user_id": "uuid-123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "admin"
  },
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc..."
}
```

**Error Responses:**
```json
// 400 - Validation Error
{
  "error": "Validation failed",
  "details": {
    "password": ["Password must contain uppercase letter"]
  }
}

// 400 - Duplicate Email
{
  "error": "Email already registered"
}

// 500 - Server Error
{
  "error": "Internal server error",
  "details": "..."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "Acme Inc"
  }'
```

---

### Login (BACKEND-4)
**Endpoint:** `POST /api/auth/login

### Login User
Authenticate existing user and return JWT tokens..

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "test@test.com",
  "password": "Test1234"
}
```

**Validation Rules:**
- Email: Valid email format
- Password: Min 8 chars, 1 uppercase, 1 number
- All fields: Required

**Success Response (201):**
```json
{
  "message": "Login successful",
  "user": {
    "user_id": "uuid-123",
    "email": "test@test.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "admin"
  },
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1..."
}
```

**Error Responses:**
```json
// 404 - User not found
{
  "error": "User not found"
}

// 401 - Invalid password
{
  "error": "Invalid credentials"
}

// 400 - Missing input
{
  "error": "Email and password are required"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test12345@test.com",
    "password": "Test1234"
  }'
````
### Refresh Token
Use a refresh token to obtain a new access token.

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```Headers
Authorization: Bearer <refresh_token>
```

**Success Response (201):**
```json
{
  "access_token": "new_access_token_here"
}
```

**Error Responses:**
```json
// 401 - Missing or invalid token
{
  "msg": "Missing Authorization Header"
}

// 404 - User not found
{
  "error": "User not found"
}

```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
````

### Get Current User
Retrieve information about the currently authenticated user.

**Endpoint:** `GET /api/auth/me`

**Request Body:**
```Headers
Authorization: Bearer <refresh_token>
```

**Success Response (201):**
```json
{
  "user": {
    "user_id": "uuid-123",
    "tenant_id": "uuid-456",
    "email": "test@test.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "admin"
  }
}
```

**Error Responses:**
```json
// 401 - Missing or invalid access token
{
  "msg": "Missing Authorization Header"
}

// 404 - User not found
{
  "error": "User not found"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
````
---

## Company Endpoints

### Add Company
Create a LinkedIn company for the current tenant to track.

**Endpoint:** `POST /api/companies`

**Auth Required:** Yes (Bearer access token)

**Request Body:**
```json
{
  "name": "OpenAI",
  "linkedin_url": "https://www.linkedin.com/company/openai/"
}
```

**Validation Rules:**
- `name`: 2–255 characters
- `linkedin_url`: Must match LinkedIn company URL format, e.g. `https://www.linkedin.com/company/<slug>/`
- Duplicate prevention: Same `linkedin_url` cannot be added twice by the same tenant

**Success Response (201):**
```json
{
  "company": {
    "company_id": "uuid-123",
    "tenant_id": "uuid-456",
    "name": "OpenAI",
    "linkedin_url": "https://www.linkedin.com/company/openai/",
    "is_active": true,
    "created_at": "2025-11-04T12:34:56.000000"
  }
}
```

**Error Responses:**
```json
// 401 - Missing/invalid token
{
  "error": "Unauthorized"
}

// 400 - Invalid URL or validation failure
{
  "error": "Validation failed",
  "details": { "linkedin_url": ["Invalid LinkedIn company URL"] }
}

// 400 - Duplicate within tenant
{
  "error": "Company already added for this tenant"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/companies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "name": "OpenAI",
    "linkedin_url": "https://www.linkedin.com/company/openai/"
  }'
```

### List Companies
Return a paginated list of companies for the current tenant.

**Endpoint:** `GET /api/companies`

**Auth Required:** Yes (Bearer access token)

**Query Params:**
- `page` (number, default `1`)
- `limit` (number, default `20`, max `100`)
- `is_active` (boolean string: `true|false|1|0|yes|no`, optional)

**Success Response (200):**
```json
{
  "companies": [
    {
      "company_id": "uuid-123",
      "name": "OpenAI",
      "linkedin_url": "https://www.linkedin.com/company/openai/",
      "is_active": true,
      "created_at": "2025-11-04T12:34:56.000000"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

**Error Responses:**
```json
// 401 - Missing/invalid token
{ "error": "Unauthorized" }
```

**cURL Examples:**
```bash
# Default (page=1, limit=20)
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://localhost:5000/api/companies

# Page 2, 10 per page, only active companies
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "http://localhost:5000/api/companies?page=2&limit=10&is_active=true"
```

### Update Company
Update fields for a company that belongs to the current tenant.

**Endpoint:** `PATCH /api/companies/{company_id}`

**Auth Required:** Yes (Bearer access token)

**Request Body (any of):**
```json
{
  "name": "OpenAI Research",
  "linkedin_url": "https://www.linkedin.com/company/openai/",
  "is_active": true
}
```

**Success Response (200):**
```json
{
  "company": {
    "company_id": "uuid-123",
    "name": "OpenAI Research",
    "linkedin_url": "https://www.linkedin.com/company/openai/",
    "is_active": true,
    "created_at": "2025-11-04T12:34:56.000000"
  }
}
```

**Errors:**
```json
// 401 - Missing/invalid token
{ "error": "Unauthorized" }

// 403 - Company belongs to different tenant
{ "error": "Forbidden" }

// 404 - Not found
{ "error": "Company not found" }

// 400 - Validation failure or duplicate linkedin_url for tenant
{ "error": "Validation failed", "details": { "linkedin_url": ["Invalid LinkedIn company URL"] } }
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:5000/api/companies/<COMPANY_ID> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"name":"OpenAI Research","is_active":true}'
```

### Delete Company (Soft Delete)
Set `is_active=false` for a company that belongs to the current tenant.

**Endpoint:** `DELETE /api/companies/{company_id}`

**Auth Required:** Yes (Bearer access token)

**Success Response (200):**
```json
{
  "company": {
    "company_id": "uuid-123",
    "name": "OpenAI",
    "linkedin_url": "https://www.linkedin.com/company/openai/",
    "is_active": false,
    "created_at": "2025-11-04T12:34:56.000000"
  }
}
```

**Errors:** same as Update Company.

**cURL Example:**
```bash
curl -X DELETE http://localhost:5000/api/companies/<COMPANY_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### Bulk Upload Companies
Upload multiple LinkedIn company URLs at once via CSV file. This allows users to add many companies quickly instead of one-by-one.

**Endpoint:** `POST /api/companies/bulk-upload`

**Auth Required:** Yes (Bearer access token)

**Request:**
- Content-Type: `multipart/form-data`
- File field: `file` (CSV file)

**CSV Format Examples:**

**Simple format (URLs only):**
```
https://www.linkedin.com/company/openai/
https://www.linkedin.com/company/microsoft/
```

**With headers:**
```
linkedin_url,name,notes
https://www.linkedin.com/company/openai/,OpenAI,AI Research
https://www.linkedin.com/company/microsoft/,Microsoft,Tech Giant
```

**Validation Rules:**
- File must be CSV format (`.csv` extension)
- Maximum 1000 companies per upload
- LinkedIn URL format: `https://www.linkedin.com/company/<slug>/`
- Duplicate URLs are skipped (doesn't fail entire upload)
- If `name` is not provided, it will be auto-generated from the URL slug
- `notes` column is accepted but not stored (for future use)

**Success Response (201):**
```json
{
  "added": 5,
  "skipped": 2,
  "failed": 1,
  "errors": [
    {"row": 3, "error": "Invalid LinkedIn company URL"}
  ],
  "total_rows": 8
}
```

**Error Responses:**
```json
// 400 - No file provided
{
  "error": "No file provided"
}

// 400 - Wrong file type
{
  "error": "File must be CSV format"
}

// 400 - Too many rows
{
  "error": "Maximum 1000 companies allowed"
}

// 400 - Invalid CSV format
{
  "error": "Invalid CSV format"
}

// 401 - Missing/invalid token
{
  "error": "Unauthorized"
}

// 500 - Database error
{
  "error": "Database error occurred"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/companies/bulk-upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@companies.csv"
```

---

### Download Bulk Upload Template
Download a CSV template file for bulk company uploads.

**Endpoint:** `GET /api/companies/bulk-upload/template`

**Auth Required:** Yes (Bearer access token)

**Success Response (200):**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename=company_upload_template.csv`
- Body: CSV file with header row and example data

**Template Content:**
```
linkedin_url,name,notes
https://www.linkedin.com/company/openai/,OpenAI,AI research company
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/companies/bulk-upload/template \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -o company_upload_template.csv
```

---

### Scrape Company Posts
Trigger LinkedIn post scraping for a company using Apify. This is an asynchronous operation that returns immediately with a job_id. The actual scraping runs in the background via Celery, and scraped posts are saved to the database.

**Endpoint:** `POST /api/companies/{company_id}/scrape`

**Auth Required:** Yes (Bearer access token)

**Parameters:**
- `max_posts` (int, optional): Maximum number of posts to scrape (1-1000, default: 100)
  - Can be provided as query parameter: `?max_posts=5`
  - Or in request body: `{"max_posts": 5}`

**Request Body (Optional):**
```json
{
  "max_posts": 10
}
```

**Validation Rules:**
- Company must exist and belong to your tenant
- Company must be active (`is_active=true`)
- `max_posts` must be between 1 and 1000 (if provided)

**Success Response (202 Accepted):**
```json
{
  "message": "Scraping job started",
  "job_id": "679cf832-fe27-47ac-81d3-10ecd853bcce",
  "company_id": "2203cefa-abc7-4d6e-b98c-f8df028931c5",
  "max_posts": 5,
  "status_url": "/api/jobs/679cf832-fe27-47ac-81d3-10ecd853bcce"
}
```

**Error Responses:**
```json
// 401 - Missing/invalid token
{
  "error": "Unauthorized"
}

// 400 - Company is inactive
{
  "error": "Company is inactive"
}

// 400 - Invalid max_posts
{
  "error": "max_posts must be a valid integer"
}

// 403 - Company belongs to different tenant
{
  "error": "Forbidden"
}

// 404 - Company not found
{
  "error": "Company not found"
}

// 500 - Failed to start scraping job (Celery not running)
{
  "error": "Failed to start scraping job",
  "details": "..."
}
```

**cURL Examples:**

**Using Query Parameter:**
```bash
curl -X POST "http://localhost:5000/api/companies/<COMPANY_ID>/scrape?max_posts=5" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Using Request Body:**
```bash
curl -X POST "http://localhost:5000/api/companies/<COMPANY_ID>/scrape" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"max_posts": 10}'
```

**Notes:**
- This endpoint returns immediately with a `job_id`. The actual scraping happens asynchronously.
- Scraped posts are automatically saved to the `posts` table.
- The company's `last_scraped_at` timestamp is updated when scraping completes.
- Duplicate posts (same `source_url`) are skipped - existing posts are updated instead.
- Make sure Celery worker is running for the scraping to execute.

---

## Posts Endpoints

### Analyze Single Post
Analyze a LinkedIn post using Claude AI to detect product launches. Returns a job ID for async tracking.

**Endpoint:** `POST /api/posts/{post_id}/analyze`

**Auth Required:** Yes (Bearer access token)

**Path Parameters:**
- `post_id` (string, required) - UUID of the post to analyze

**Success Response (202 Accepted):**
```json
{
  "job_id": "celery-task-uuid-123",
  "post_id": "post-uuid-456",
  "status": "queued"
}
```

**Error Responses:**
```json
// 401 - Missing/invalid token
{
  "error": "Unauthorized"
}

// 404 - Post not found or doesn't belong to tenant
{
  "error": "Post not found"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/posts/{post_id}/analyze \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Notes:**
- Analysis runs asynchronously via Celery
- Use the `job_id` to track task status
- Results update the post's `score` (0-100), `ai_judgement` ("product_launch" or "other"), and `analyzed_at` timestamp
- Check task status using Celery's result backend or query the post after completion

---

### Batch Analyze Posts
Analyze multiple posts in a single request. Returns job IDs for each post.

**Endpoint:** `POST /api/posts/analyze-batch`

**Auth Required:** Yes (Bearer access token)

**Request Body:**
```json
{
  "post_ids": [
    "post-uuid-1",
    "post-uuid-2",
    "post-uuid-3"
  ]
}
```

**Validation Rules:**
- `post_ids`: Array of strings (required)
- Minimum 1 post ID
- Maximum 100 post IDs per request
- All post IDs must belong to the authenticated tenant

**Success Response (202 Accepted):**
```json
{
  "job_ids": [
    "celery-task-uuid-1",
    "celery-task-uuid-2",
    "celery-task-uuid-3"
  ],
  "posts": [
    {
      "post_id": "post-uuid-1",
      "job_id": "celery-task-uuid-1"
    },
    {
      "post_id": "post-uuid-2",
      "job_id": "celery-task-uuid-2"
    },
    {
      "post_id": "post-uuid-3",
      "job_id": "celery-task-uuid-3"
    }
  ],
  "count": 3,
  "status": "queued"
}
```

**Error Responses:**
```json
// 401 - Missing/invalid token
{
  "error": "Unauthorized"
}

// 400 - Validation error
{
  "error": "Validation failed",
  "details": {
    "post_ids": ["Cannot analyze more than 100 posts at once"]
  }
}

// 404 - Some posts not found or don't belong to tenant
{
  "error": "Some posts not found or access denied",
  "missing_post_ids": ["post-uuid-4", "post-uuid-5"]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/posts/analyze-batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "post_ids": [
      "post-uuid-1",
      "post-uuid-2",
      "post-uuid-3"
    ]
  }'
```

**Notes:**
- All posts are queued for analysis asynchronously
- Each post gets its own Celery task
- If any post IDs are invalid or don't belong to the tenant, the entire request fails with 404
- Results are updated in the database when analysis completes

---

### List Posts
List scraped LinkedIn posts with filtering, pagination, and sorting. Returns posts sorted by date (newest first) with company information.

**Endpoint:** `GET /api/posts`

**Auth Required:** Yes (Bearer access token)

**Query Parameters:**
- `page` (int, optional): Page number (default: 1, min: 1)
- `limit` (int, optional): Items per page (default: 20, min: 1, max: 100)
- `company_id` (string, optional): Filter by company ID (UUID)
- `start_date` (string, optional): Filter posts from this date (format: YYYY-MM-DD)
- `end_date` (string, optional): Filter posts until this date (format: YYYY-MM-DD)
- `ai_judgement` (string, optional): Filter by AI judgement category (e.g., "product_launch", "other")

**Success Response (200 OK):**
```json
{
  "posts": [
    {
      "post_id": "uuid-123",
      "company_id": "company-uuid-456",
      "company_name": "Google",
      "post_text": "Exciting news! We're launching our new product...",
      "post_date": "2024-11-15",
      "score": 85,
      "ai_judgement": "product_launch",
      "source_url": "https://www.linkedin.com/posts/...",
      "created_at": "2024-11-15T10:30:00",
      "analyzed_at": "2024-11-15T10:35:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**Example Requests:**
```bash
# List all posts (first page)
curl -X GET "http://localhost:5000/api/posts?page=1&limit=20" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Filter by company and AI judgement
curl -X GET "http://localhost:5000/api/posts?company_id=<COMPANY_ID>&ai_judgement=product_launch" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Notes:**
- Posts are sorted by `post_date` (newest first)
- Only returns posts from the authenticated user's tenant (multi-tenant isolation)
- Includes company name via JOIN with companies table

---

## Email Endpoints (Coming Soon)

### List Emails
**Endpoint:** `GET /api/emails`
**Auth Required:** Yes

### Generate Emails
**Endpoint:** `POST /api/emails/generate`
**Auth Required:** Yes

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting
TBD

## Pagination
TBD (for list endpoints)

---

## Testing

### Health Check
```bash
curl http://localhost:5000/api/health
# Response: {"status": "ok"}
```

### Register Test User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "Test1234",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company"
  }'
```

---

## Frontend Integration

### JavaScript/Axios Example
```javascript
// Register
const register = async (userData) => {
  const response = await axios.post('/api/auth/register', userData);
  
  // Save tokens
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Use token in requests
axios.defaults.headers.common['Authorization'] = 
  `Bearer ${localStorage.getItem('access_token')}`;
```

---

## Database Schema

See: [Database Documentation](DATABASE.md)

---

## Change Log

### 2025-11-04
- POST /api/companies - Add company to track (JWT, URL validation, duplicate prevention)

### 2025-11-01
- POST /api/auth/register - User registration
- Multi-tenant support
-  JWT authentication

### 2025-01-27
- POST /api/posts/{post_id}/analyze - Analyze single post with Claude AI
- POST /api/posts/analyze-batch - Batch analyze multiple posts
- Celery integration for async AI analysis
- Claude AI integration for product launch detection

### Completed
- GET /api/posts - List posts with filtering, pagination, and sorting ✅

### Coming Soon
- Email generation endpoints