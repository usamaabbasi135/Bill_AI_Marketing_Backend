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
    "role": "admin",
    "tenant_id": "uuid-456"
  },
  "tenant": {
    "tenant_id": "uuid-456",
    "company_name": "Acme Inc",
    "plan": "free",
    "status": "active"
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

### Login (Coming Soon - BACKEND-4)
**Endpoint:** `POST /api/auth/login`

---

## Company Endpoints (Coming Soon)

### List Companies
**Endpoint:** `GET /api/companies`
**Auth Required:** Yes

### Add Company
**Endpoint:** `POST /api/companies`
**Auth Required:** Yes

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