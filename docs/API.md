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

## Posts Endpoints (Coming Soon)

### List Posts
**Endpoint:** `GET /api/posts`
**Auth Required:** Yes

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

### Coming Soon
- POST /api/auth/login
- POST /api/auth/refresh
- Company management endpoints
- Post detection endpoints
- Email generation endpoints