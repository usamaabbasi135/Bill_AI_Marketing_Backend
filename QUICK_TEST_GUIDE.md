# Quick Test Guide - Google OAuth

## Flask App Status
✅ Flask app is running on http://localhost:5000

## Step-by-Step Testing

### Step 1: Get JWT Token

First, you need to login to get a JWT token:

**Option A: Using existing user**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

**Option B: Register new user**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company"
  }'
```

Copy the `access_token` from the response.

### Step 2: Get Google OAuth Authorization URL

```bash
curl -X GET http://localhost:5000/api/auth/oauth/google/authorize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "..."
}
```

### Step 3: Complete OAuth Flow

1. Copy the `authorization_url` from Step 2
2. Open it in your browser
3. Sign in with your Google account
4. Click "Allow" to grant permissions
5. You'll be redirected back to the callback URL

### Step 4: Verify Connection

```bash
curl -X GET http://localhost:5000/api/auth/oauth/providers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

**Expected Response:**
```json
{
  "providers": [
    {
      "provider_id": "...",
      "email": "your-email@gmail.com",
      "provider": "google",
      "is_active": true,
      ...
    }
  ]
}
```

### Step 5: Test Email Sending

```bash
curl -X POST http://localhost:5000/api/emails/EMAIL_ID_HERE/send \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

**Note:** Replace `EMAIL_ID_HERE` with an actual email ID from your database.

## Using the Test Script

For easier testing, use the provided test script:

```bash
python test_google_oauth.py your-email@example.com your-password
```

Or with email sending:
```bash
python test_google_oauth.py your-email@example.com your-password email-uuid-here
```

## Troubleshooting

### "Cannot connect to Flask app"
- Make sure Flask is running: `python run.py`
- Check if port 5000 is available

### "Unauthorized" error
- Make sure you're using a valid JWT token
- Token might be expired, login again

### "redirect_uri_mismatch" in browser
- Check `GOOGLE_REDIRECT_URI` in .env matches exactly
- Must be: `http://localhost:5000/api/auth/oauth/google/callback`
- No trailing slashes!

### "No providers found"
- Complete the OAuth flow in browser first (Step 3)
- Make sure you clicked "Allow" in the Google consent screen

