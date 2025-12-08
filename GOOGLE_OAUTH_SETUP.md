# Google OAuth Setup - Step by Step Guide

This guide will walk you through setting up Google OAuth for sending emails via Gmail API.

## Prerequisites

- A Google account
- Access to Google Cloud Console (https://console.cloud.google.com/)

## Step 1: Create or Select a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. If you don't have a project:
   - Click the project dropdown at the top
   - Click **"New Project"**
   - Enter a project name (e.g., "Bill AI Marketing")
   - Click **"Create"**
3. If you have an existing project, select it from the dropdown

## Step 2: Enable Gmail API

1. In the Google Cloud Console, go to **"APIs & Services"** > **"Library"** (or search for "APIs & Services" in the top search bar)
2. In the search box, type **"Gmail API"**
3. Click on **"Gmail API"** from the results
4. Click the **"Enable"** button
5. Wait for the API to be enabled (this may take a few seconds)

## Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"** (in the left sidebar)
2. Select **"External"** user type (unless you're using Google Workspace, then select "Internal")
   - Click **"Create"**
3. Fill in the required information:
   - **App name**: "Bill AI Marketing" (or your preferred name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
   - Click **"Save and Continue"**
4. **Scopes** (Step 2):
   - Click **"Add or Remove Scopes"**
   - In the filter box, search for: `https://www.googleapis.com/auth/gmail.send`
   - Check the box next to `.../auth/gmail.send`
   - Click **"Update"**
   - Click **"Save and Continue"**
5. **Test users** (Step 3):
   - Click **"Add Users"**
   - Add your Google email address (the one you'll use to send emails)
   - Click **"Add"**
   - Click **"Save and Continue"**
6. **Summary** (Step 4):
   - Review the information
   - Click **"Back to Dashboard"**

**Note**: If your app is in "Testing" mode, only the test users you added can use it. For production, you'll need to submit for verification later.

## Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"** (in the left sidebar)
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. If prompted, select **"Web application"** as the application type
5. Fill in the OAuth client details:
   - **Name**: "Bill AI Marketing Email Sender" (or your preferred name)
   - **Authorized redirect URIs**: Click **"+ ADD URI"** and add:
     - For development: `http://localhost:5000/api/auth/oauth/google/callback`
     - For production: `https://yourdomain.com/api/auth/oauth/google/callback`
     - **Important**: Make sure there are no trailing slashes and the URL matches exactly
6. Click **"CREATE"**
7. **IMPORTANT**: A popup will appear with your credentials:
   - **Client ID**: Copy this value (you'll need it for `GOOGLE_CLIENT_ID`)
   - **Client secret**: Copy this value (you'll need it for `GOOGLE_CLIENT_SECRET`)
   - **⚠️ WARNING**: The client secret is only shown once! Copy it immediately or you'll need to create new credentials.

## Step 5: Set Environment Variables

Add these to your `.env` file in your project root:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/oauth/google/callback
```

**For production**, update `GOOGLE_REDIRECT_URI`:
```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/oauth/google/callback
```

## Step 6: Test the OAuth Connection

### 6.1: Get Authorization URL

Make a request to your API (you'll need a JWT token):

```bash
GET http://localhost:5000/api/auth/oauth/google/authorize
Headers:
  Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "..."
}
```

### 6.2: Complete OAuth Flow

1. Copy the `authorization_url` from the response
2. Open it in your browser
3. Sign in with the Google account you want to use for sending emails
4. Review the permissions and click **"Allow"**
5. You'll be redirected back to your callback URL

### 6.3: Verify Connection

Check if the connection was successful:

```bash
GET http://localhost:5000/api/auth/oauth/providers
Headers:
  Authorization: Bearer <your_jwt_token>
```

**Expected Response:**
```json
{
  "providers": [
    {
      "provider_id": "...",
      "user_id": "...",
      "email": "your-email@gmail.com",
      "provider": "google",
      "is_active": true,
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

## Step 7: Test Email Sending

Once connected, emails will automatically use your Google account:

```bash
POST http://localhost:5000/api/emails/<email_id>/send
Headers:
  Authorization: Bearer <your_jwt_token>
```

The system will:
1. Try to send via your Google OAuth account
2. Fall back to AWS SES if OAuth fails or isn't available

## Troubleshooting

### Issue: "redirect_uri_mismatch" error

**Solution**: 
- Make sure the redirect URI in Google Cloud Console matches exactly (including http/https, port, and path)
- No trailing slashes
- Check both development and production URLs if applicable

### Issue: "access_denied" error

**Solution**:
- Make sure you added your email as a test user in OAuth consent screen
- Make sure you're signing in with the correct Google account

### Issue: "invalid_client" error

**Solution**:
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Make sure there are no extra spaces in your `.env` file
- Restart your Flask application after updating environment variables

### Issue: Token refresh fails

**Solution**:
- Make sure you selected "offline_access" scope (it's included automatically with `gmail.send`)
- Re-authenticate by disconnecting and reconnecting your Google account

## Production Checklist

Before deploying to production:

- [ ] Update `GOOGLE_REDIRECT_URI` to production URL
- [ ] Add production redirect URI in Google Cloud Console
- [ ] Submit OAuth consent screen for verification (if needed)
- [ ] Test OAuth flow in production environment
- [ ] Monitor logs for any OAuth errors

## Security Notes

- ✅ Never commit your `GOOGLE_CLIENT_SECRET` to version control
- ✅ Use environment variables or secrets manager
- ✅ Keep your OAuth credentials secure
- ✅ Regularly rotate credentials if compromised

## Next Steps

After setting up Google OAuth:

1. Test sending emails to verify everything works
2. Monitor email sending logs
3. Set up proper token encryption for production (see `OAUTH_SETUP_GUIDE.md`)
4. Consider adding Microsoft OAuth as well for more flexibility

