# How to Update Google Client Secret

## Step 1: Create New Client Secret in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID and click on it
4. Scroll down to **"Client secrets"** section
5. Click **"+ ADD SECRET"** or **"CREATE SECRET"** button
6. **IMPORTANT**: Copy the secret value immediately - it's only shown once!
7. The new secret will be created and enabled

## Step 2: Update .env File

After getting the new secret, update your `.env` file:

```env
GOOGLE_CLIENT_SECRET=your_new_secret_here
```

## Step 3: Restart Flask App

After updating the .env file, restart your Flask app to load the new secret.

## Note

- Old secrets can be disabled but don't need to be deleted immediately
- You can have multiple secrets active for rotation
- Make sure to copy the secret exactly (no extra spaces)

