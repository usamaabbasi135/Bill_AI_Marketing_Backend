# OAuth Email Sending Setup Guide

This guide will help you complete the setup for OAuth delegated email sending.

## Step 1: Database Migration

Run the migration to create the `user_email_providers` table:

```bash
flask db upgrade
```

**Note:** Make sure your database is running and `DATABASE_URL` is set in your environment variables.

## Step 2: Environment Variables

Add the following environment variables to your `.env` file or deployment environment:

### Microsoft OAuth Configuration

```env
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_REDIRECT_URI=http://localhost:5000/api/auth/oauth/microsoft/callback
```

**For production**, update `MICROSOFT_REDIRECT_URI` to your production URL:
```env
MICROSOFT_REDIRECT_URI=https://yourdomain.com/api/auth/oauth/microsoft/callback
```

### Google OAuth Configuration

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/oauth/google/callback
```

**For production**, update `GOOGLE_REDIRECT_URI` to your production URL:
```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/oauth/google/callback
```

## Step 3: Set Up Microsoft OAuth Application

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: Your app name (e.g., "Bill AI Marketing Email")
   - **Supported account types**: Accounts in any organizational directory and personal Microsoft accounts
   - **Redirect URI**: 
     - Type: Web
     - URI: `http://localhost:5000/api/auth/oauth/microsoft/callback` (for development)
     - Add production URI: `https://yourdomain.com/api/auth/oauth/microsoft/callback`
5. Click **Register**
6. Copy the **Application (client) ID** → This is your `MICROSOFT_CLIENT_ID`
7. Go to **Certificates & secrets** > **New client secret**
8. Copy the secret value → This is your `MICROSOFT_CLIENT_SECRET`
9. Go to **API permissions** > **Add a permission** > **Microsoft Graph** > **Delegated permissions**
10. Add permissions:
    - `Mail.Send`
    - `offline_access`
11. Click **Grant admin consent** (if you have admin rights)

## Step 4: Set Up Google OAuth Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **Gmail API**:
   - Go to **APIs & Services** > **Library**
   - Search for "Gmail API"
   - Click **Enable**
4. Go to **APIs & Services** > **Credentials**
5. Click **Create Credentials** > **OAuth client ID**
6. Configure OAuth consent screen (if not done):
   - User Type: External (or Internal for Google Workspace)
   - App name, support email, developer contact
   - Scopes: Add `https://www.googleapis.com/auth/gmail.send`
   - Save
7. Create OAuth client:
   - Application type: **Web application**
   - Name: Your app name
   - Authorized redirect URIs:
     - `http://localhost:5000/api/auth/oauth/google/callback` (for development)
     - `https://yourdomain.com/api/auth/oauth/google/callback` (for production)
   - Click **Create**
8. Copy the **Client ID** → This is your `GOOGLE_CLIENT_ID`
9. Copy the **Client secret** → This is your `GOOGLE_CLIENT_SECRET`

## Step 5: Test the Implementation

### Test Microsoft OAuth Flow

1. **Get authorization URL:**
   ```bash
   GET /api/auth/oauth/microsoft/authorize
   Headers: Authorization: Bearer <your_jwt_token>
   ```
   
   Response:
   ```json
   {
     "authorization_url": "https://login.microsoftonline.com/...",
     "state": "..."
   }
   ```

2. **Open the authorization_url in browser** and complete OAuth flow

3. **Verify connection:**
   ```bash
   GET /api/auth/oauth/providers
   Headers: Authorization: Bearer <your_jwt_token>
   ```

### Test Google OAuth Flow

1. **Get authorization URL:**
   ```bash
   GET /api/auth/oauth/google/authorize
   Headers: Authorization: Bearer <your_jwt_token>
   ```

2. **Open the authorization_url in browser** and complete OAuth flow

3. **Verify connection:**
   ```bash
   GET /api/auth/oauth/providers
   Headers: Authorization: Bearer <your_jwt_token>
   ```

### Test Email Sending

1. **Send an email:**
   ```bash
   POST /api/emails/<email_id>/send
   Headers: Authorization: Bearer <your_jwt_token>
   ```

   The system will:
   - Try to send via OAuth if user has connected account
   - Fall back to AWS SES if OAuth is not available

## Step 6: Production Considerations

### Token Encryption

The current implementation uses base64 encoding as a placeholder. **For production**, implement proper encryption:

1. Install cryptography library:
   ```bash
   pip install cryptography
   ```

2. Update `app/services/oauth_service.py`:
   - Replace `_encrypt_token()` and `_decrypt_token()` methods
   - Use Fernet symmetric encryption or AES encryption
   - Store encryption key securely (environment variable, secrets manager)

### State Storage

The current implementation stores OAuth state in memory. **For production**:

- Use Redis for state storage (recommended)
- Or use database table for state storage
- Implement state cleanup job to remove expired states

### Error Handling

- Monitor OAuth token refresh failures
- Set up alerts for OAuth connection issues
- Log all OAuth operations for debugging

## API Endpoints Summary

### OAuth Endpoints

- `GET /api/auth/oauth/microsoft/authorize` - Start Microsoft OAuth
- `GET /api/auth/oauth/microsoft/callback` - Microsoft OAuth callback
- `GET /api/auth/oauth/google/authorize` - Start Google OAuth
- `GET /api/auth/oauth/google/callback` - Google OAuth callback
- `GET /api/auth/oauth/providers` - List connected providers
- `DELETE /api/auth/oauth/providers/<provider_id>` - Disconnect provider

### Email Endpoints (Updated)

- `POST /api/emails/<email_id>/send` - Send email (now uses OAuth with SES fallback)

## Troubleshooting

### Migration Issues

If migration fails:
```bash
# Check current migration status
flask db current

# Check migration history
flask db history

# Rollback if needed
flask db downgrade -1
```

### OAuth Connection Issues

1. **Check redirect URIs match exactly** (including trailing slashes, http vs https)
2. **Verify scopes are correct** in OAuth provider settings
3. **Check token expiration** - tokens auto-refresh, but verify refresh tokens are stored
4. **Review logs** for detailed error messages

### Email Sending Issues

1. **OAuth not working?** System automatically falls back to SES
2. **Check user has connected OAuth account** via `/api/auth/oauth/providers`
3. **Verify OAuth tokens are valid** - check `token_expires_at` in database
4. **Check email provider API quotas** - Microsoft and Google have rate limits

## Security Notes

- ✅ State parameter validation implemented
- ✅ User authentication required for all OAuth operations
- ✅ Users can only access their own providers
- ⚠️ Token encryption needs proper implementation for production
- ⚠️ State storage should use Redis/database in production

## Support

For issues or questions:
1. Check application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test OAuth flows in development before deploying to production

